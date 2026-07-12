from __future__ import annotations

import os
import json
import time
from dataclasses import asdict
from pathlib import Path
from threading import Lock

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from anshi.content import load_scenario
from anshi.core import Order, apply_order
from anshi.campaign import ACT_NAMES, add_secret_edict, advance as advance_campaign
from anshi.ai import generate_character_reply, generate_decree_candidates, generate_turn_narration, generate_world_proposal, load_config, polish_document
from anshi.conversation import ConversationState, confirm_decree, context_for, draft_freeform, promulgate_decrees, record_exchange
from anshi.strategy import StrategyState, initial_strategy, queue_move as queue_army_move, resolve_movements, simulate_month
from anshi.strategy import FieldArmy, Siege
from anshi.storage import management_from_payload, state_from_payload
from anshi.campaign import CampaignEvent, CampaignProgress
from anshi.management import (
    ArmyState as ManagedArmyState,
    CharacterState,
    DirectiveKind,
    IssueState,
    RegionState as ManagedRegionState,
    draft as draft_directive,
    remove as remove_directive,
    resolve as resolve_management,
)
from anshi.storage import GameStore
from anshi.world_simulation import apply_world_proposal
from anshi.situations import advance_situations, policy_catalog, resolve_policy, select_policy

ROOT = Path(__file__).parents[2]
SCENARIO = load_scenario(ROOT / "content" / "scenarios" / "tongguan_756")
CAMPAIGN = json.loads((ROOT / "content" / "scenarios" / "tongguan_756" / "campaign.json").read_text(encoding="utf-8"))
CAMPAIGN["characters"].extend(json.loads((ROOT / "content" / "scenarios" / "tongguan_756" / "characters_extra.json").read_text(encoding="utf-8")))


class TurnRequest(BaseModel):
    order: Order


class DirectiveRequest(BaseModel):
    kind: DirectiveKind
    target: str
    amount: int = 10
    subject: str = ""


class AudienceRequest(BaseModel):
    character_id: str
    topic: str = "当前最紧要之事是什么？"
    scene: str = "朝堂"


class CouncilRequest(BaseModel):
    character_ids: list[str]
    topic: str = "当前最紧要之事是什么？"


class ResolveRequest(BaseModel):
    event_choice: str = ""


class EventChoiceRequest(BaseModel):
    choice: str


class SecretEdictRequest(BaseModel):
    character_id: str
    text: str
    purpose: str = "军情"


class ModelConfigRequest(BaseModel):
    role: str = "chat"
    api_key: str = ""
    base_url: str = ""
    model: str = ""


class FreeformDecreeRequest(BaseModel):
    text: str


class SaveSlotRequest(BaseModel):
    slot_id: int
    name: str = ""


class ArmyMoveRequest(BaseModel):
    army_id: str
    destination: str


class PolicySelectRequest(BaseModel):
    policy_id: str


def _hydrate_management(management) -> None:
    aliases = {
        "regions": {"guanzhong", "henan"},
        "armies": {"tongguan", "shuofang"},
        "characters": {"geshu_han", "yang_guozhong"},
        "issues": {"refugees", "court_conflict"},
    }
    for domain, keys in aliases.items():
        values = getattr(management, domain)
        for key in keys:
            values.pop(key, None)
    management.directives = [item for item in management.directives if item.target not in set().union(*aliases.values())]
    for region in CAMPAIGN["regions"]:
        management.regions.setdefault(region["id"], ManagedRegionState(
            region["name"], region["support"], region["unrest"], min(100, region["tax"]["cp_per_30_days"] // 100),
            70 if "fort" in region["status"] else 20,
        ))
    for army in CAMPAIGN["armies"]:
        if army["act_from"] == 1:
            management.armies.setdefault(army["id"], ManagedArmyState(
                army["name"], army["region"], army["present_strength"], army["fit_strength"], army["supply"], army["morale"],
            ))
    for character in CAMPAIGN["characters"]:
        status = "active" if character["audience_status"] in {"available", "remote_only", "player_character"} else "offstage"
        management.characters.setdefault(character["id"], CharacterState(
            character["name"], character["identity"], character["attributes"]["loyalty"],
            max(character["attributes"]["administration"], character["attributes"]["military"]), status,
        ))
    for issue in CAMPAIGN["ongoing_issues"]:
        management.issues.setdefault(issue["id"], IssueState(issue["name"], issue["pressure"], 100 - issue["progress"]))


def _activate_content(management, act: int) -> None:
    for army in CAMPAIGN["armies"]:
        if army["act_from"] <= act and army["id"] not in management.armies:
            management.armies[army["id"]] = ManagedArmyState(
                army["name"], army["region"], army["present_strength"], army["fit_strength"], army["supply"], army["morale"]
            )
    for character in CAMPAIGN["characters"]:
        if character["id"] not in management.characters:
            continue
        available_act = 1
        if character["audience_status"].startswith("future"):
            available_act = 2 if character["available_from"] < "0757-01-01" else 3
            if character["available_from"] >= "0758-01-01":
                available_act = 4
            if character["available_from"] >= "0761-01-01":
                available_act = 5
        if act >= available_act and character["audience_status"] not in {"enemy_only", "future_enemy", "player_character"}:
            management.characters[character["id"]].status = "active"


def _apply_event_choice(management, resolved: dict | None) -> list[str]:
    if not resolved:
        return []
    event_id, choice = resolved["event_id"], resolved["choice"]
    effects: list[str] = []
    if any(word in choice for word in ("救援", "重金", "全力", "回师")):
        management.finance.cash = max(0, management.finance.cash - 120)
        management.finance.grain = max(0, management.finance.grain - 100)
        effects.append("朝廷投入大量钱粮")
    if any(word in choice for word in ("加征", "重金结盟")):
        for region in management.regions.values():
            region.support -= 2
            region.unrest += 1
        effects.append("各地民力受损")
    if any(word in choice for word in ("固守", "坚守", "整军", "围困")):
        for army in management.armies.values():
            if army.supply >= 40:
                army.morale += 2
        effects.append("军心因持重部署而稍稳")
    if any(word in choice for word in ("决战", "北伐", "并进", "进讨")):
        for army in management.armies.values():
            army.supply -= 5
            army.morale += 1
        effects.append("诸军进入高消耗作战准备")
    if event_id == "mawei_mutiny":
        issue = management.issues.get("succession_dual_court")
        if issue:
            issue.tension += -15 if choice == "诛杨国忠" else 15
        if "yang_guozhong" in management.characters and choice == "诛杨国忠":
            management.characters["yang_guozhong"].status = "offstage"
            effects.append("杨国忠退出朝局，禁军暂时平复")
    elif event_id == "lingwu_accession":
        if choice == "承认新帝":
            for key in ("guo_ziyi", "li_guangbi", "li_heng"):
                if key in management.characters:
                    management.characters[key].loyalty += 5
            effects.append("朔方集团与新皇统结合")
    elif event_id == "suiyang_siege" and "suiyang" in management.regions:
        management.regions["suiyang"].support += 8 if choice == "全力救援" else -8
        management.regions["suiyang"].unrest += -8 if choice == "全力救援" else 8
        effects.append("睢阳军民状态发生变化")
    elif event_id == "heshuo_surrender":
        issue = management.issues.get("frontier_autonomy_debt")
        if issue:
            issue.tension += 20 if choice == "授节度留任" else -10
        effects.append("河朔军镇格局被重新确定")
    elif event_id == "tibet_threat":
        for key in ("hexi", "longyou"):
            if key in management.regions:
                management.regions[key].unrest += -8 if choice == "回师西陲" else 8
        effects.append("河西陇右边防随裁断变化")
    return effects


_DIRECTIVE_DOMAINS = {
    "relief": "regions", "tax": "regions", "fortify": "regions",
    "supply": "armies", "mobilize": "armies",
    "investigate": "issues", "mediate": "issues", "appoint": "characters",
}


def _decree_targets(management) -> dict[str, dict[str, str]]:
    return {
        domain: {key: getattr(value, "name", getattr(value, "title", key)) for key, value in getattr(management, domain).items()}
        for domain in ("regions", "armies", "issues", "characters")
    }


def _validate_decree_candidates(raw: list[dict], management) -> tuple[list[dict], list[str]]:
    valid, rejected = [], []
    for item in raw[:12]:
        if not isinstance(item, dict) or item.get("kind") not in _DIRECTIVE_DOMAINS:
            rejected.append("未知诏令类型")
            continue
        kind, target = str(item["kind"]), str(item.get("target", ""))
        domain = _DIRECTIVE_DOMAINS[kind]
        if target not in getattr(management, domain):
            rejected.append(f"{kind} 的目标 {target or '为空'} 不存在")
            continue
        try:
            amount = max(1, min(100, int(round(float(item.get("amount", 10))))))
        except (TypeError, ValueError):
            rejected.append(f"{kind} 的投入规模无效")
            continue
        valid.append({"kind": kind, "target": target, "amount": amount, "subject": str(item.get("subject", ""))[:80], "reason": str(item.get("reason", "模型解析诏意"))[:160]})
    return valid, rejected


SCENE_KEYS = {"朝堂": "court", "密诏": "secret", "远奏": "remote", "court": "court", "secret": "secret", "remote": "remote"}


def create_app(db_path: str | Path | None = None) -> FastAPI:
    app = FastAPI(title="Anshi Sim", version="0.5.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["*"],
    )
    store = GameStore(db_path or os.environ.get("ANSHI_DB", ROOT / "data" / "anshi.db"))
    campaign = {"state": store.load()}
    management = store.load_management()
    progress = store.load_progress()
    conversation = store.load_conversation()
    strategy = store.load_strategy() or initial_strategy(CAMPAIGN)

    def activate_strategy() -> None:
        for item in CAMPAIGN["armies"]:
            if item["act_from"] <= progress.act and item["id"] not in strategy.armies:
                strategy.armies[item["id"]] = FieldArmy(item["id"], item["name"], item["power"], item["region"], item["present_strength"], item["supply"], item["morale"], item["status"])
        if progress.act >= 3 and not any(item.region == "suiyang" for item in strategy.sieges):
            strategy.sieges.append(Siege("suiyang", "yan_suiyang_siege", "tang_suiyang_garrison"))

    activate_strategy()
    _hydrate_management(management)
    _activate_content(management, progress.act)
    store.save_management(management)
    lock = Lock()
    app.state.game_store = store

    def unified_payload() -> dict:
        return {"state": campaign["state"].payload(), "management": asdict(management), "progress": asdict(progress), "conversation": asdict(conversation), "strategy": asdict(strategy)}

    def persist_all() -> None:
        store.save(campaign["state"])
        store.save_management(management)
        store.save_progress(progress)
        store.save_conversation(conversation)
        store.save_strategy(strategy)

    def model_roles_payload() -> dict:
        roles = {}
        for role in ("chat", "simulation", "utility"):
            config = load_config(role=role)
            roles[role] = {
                "configured": config is not None,
                "status": "已配置，调用时验证" if config else "未配置",
                "base_url": config.base_url if config else "",
                "model": config.model if config else "",
            }
        return roles

    @app.get("/api/health")
    def health() -> dict:
        roles = model_roles_payload()
        configured = sum(item["configured"] for item in roles.values())
        return {"status": "ok", "content_version": SCENARIO.manifest.content_version, "llm": f"已配置 {configured}/3" if configured else "未配置", "model": roles["chat"]["model"] or "中文模板", "models": roles}

    @app.get("/api/model-config")
    def model_config() -> dict:
        return {"roles": model_roles_payload()}

    @app.post("/api/model-config")
    def update_model_config(request: ModelConfigRequest) -> dict:
        if request.role not in {"chat", "simulation", "utility"}:
            return {"configured": False, "detail": "未知模型职责。"}
        prefix = request.role.upper()
        if request.api_key.strip():
            os.environ[f"{prefix}_API_KEY"] = request.api_key.strip()
        if request.base_url.strip():
            os.environ[f"{prefix}_BASE_URL"] = request.base_url.strip()
        if request.model.strip():
            os.environ[f"{prefix}_MODEL"] = request.model.strip()
        config = load_config(role=request.role)
        return {"configured": config is not None, "base_url": config.base_url if config else "", "model": config.model if config else "", "detail": "配置仅保存在当前游戏进程，密钥不会返回前端。"}

    @app.get("/api/state")
    def state() -> dict:
        return {**campaign["state"].payload(), "save_revision": store.revision()}

    @app.get("/api/scenario")
    def scenario() -> dict:
        return {
            "manifest": SCENARIO.manifest.model_dump(),
            "acts": [act.model_dump() for act in SCENARIO.acts],
            "regions": [region.model_dump() for region in SCENARIO.regions],
        }

    @app.get("/api/situations")
    def situations() -> dict:
        return {"situations": progress.situations, "modifiers": progress.modifiers}

    @app.get("/api/policies")
    def policies() -> dict:
        return {"policies": policy_catalog(progress), "completed": progress.completed_policies, "active": progress.active_policy}

    @app.post("/api/policies/select")
    def choose_policy(request: PolicySelectRequest) -> dict:
        with lock:
            try:
                item = select_policy(progress, request.policy_id)
            except ValueError as error:
                return {"accepted": False, "detail": str(error), "policies": policy_catalog(progress)}
            store.save_progress(progress)
            return {"accepted": True, "selected": item, "policies": policy_catalog(progress)}

    @app.get("/api/snapshot")
    def snapshot() -> dict:
        _activate_content(management, progress.act)
        model_roles = model_roles_payload()
        configured_models = sum(item["configured"] for item in model_roles.values())
        return {
            "state": {**campaign["state"].payload(), "save_revision": store.revision()},
            "management": asdict(management),
            "catalog": CAMPAIGN,
            "acts": [act.model_dump() for act in SCENARIO.acts],
            "progress": asdict(progress),
            "runtime": {
                "联网模型": f"已配置 {configured_models}/3" if configured_models else "未配置，使用中文模板",
                "模型": model_roles["chat"]["model"] or "中文模板",
                "模型职责": model_roles,
            },
            "conversation": asdict(conversation),
            "strategy": asdict(strategy),
            "agent_runs": store.agent_runs(20),
            "save_slots": store.list_slots(),
        }

    @app.post("/api/audience")
    def audience(request: AudienceRequest) -> dict:
        character = next((item for item in CAMPAIGN["characters"] if item["id"] == request.character_id), None)
        runtime_character = management.characters.get(request.character_id)
        if not character or not runtime_character or runtime_character.status != "active" or character["audience_status"] in {"enemy_only", "future_enemy", "player_character"}:
            return {"accepted": False, "detail": "此人当前不能入对或递交远奏。"}
        scene = SCENE_KEYS.get(request.scene)
        if not scene:
            return {"accepted": False, "detail": "奏对场景仅支持朝堂、密诏或远奏。"}
        started = time.perf_counter()
        reply, model_used = generate_character_reply(
            character,
            request.topic.strip() or "当前局势",
            scene,
            {"章节": ACT_NAMES[progress.act], "年月": f"{progress.year}年{progress.month}月", "事项": [asdict(issue) for issue in management.issues.values()], **context_for(conversation, character["id"])},
            with_status=True,
        )
        record_exchange(conversation, character["id"], request.topic, reply, request.scene, progress.total_turn)
        store.save_conversation(conversation)
        config = load_config(role="chat")
        store.record_agent_run("人物奏对", config.model if config else "中文模板", round((time.perf_counter() - started) * 1000), model_used, request.scene)
        return {"accepted": True, "scene": request.scene, "character_id": character["id"], "name": character["name"], "identity": character["identity"], "topic": request.topic, "reply": reply, "model_used": model_used}

    @app.post("/api/council")
    def council(request: CouncilRequest) -> dict:
        selected = [item for item in CAMPAIGN["characters"] if item["id"] in request.character_ids][:6]
        selected = [item for item in selected if management.characters.get(item["id"]) and management.characters[item["id"]].status == "active"]
        if len(selected) < 2:
            return {"accepted": False, "detail": "朝议至少需要两名当前可用人物。"}
        exchanges = []
        transcript = ""
        for character in selected:
            reply, model_used = generate_character_reply(character, request.topic, "court", {"前臣发言": transcript, "章节": ACT_NAMES[progress.act], "年月": f"{progress.year}年{progress.month}月"}, with_status=True)
            exchanges.append({"character_id": character["id"], "name": character["name"], "reply": reply, "model_used": model_used})
            transcript += f"\n{character['name']}：{reply}"
        return {"accepted": True, "topic": request.topic, "exchanges": exchanges}

    def _classify_stance(text: str) -> str:
        text_lower = text.lower()
        defense_words = ["固守", "守关", "坚守", "持重", "不可轻出", "险隘", "粮草未备", "稳扎稳打", "退守", "坚壁"]
        attack_words = ["出战", "出击", "奉诏", "决战", "锐意进取", "贼寇可击", "战机", "进兵", "剿贼", "进讨", "北伐"]
        defense_score = sum(1 for w in defense_words if w in text_lower)
        attack_score = sum(1 for w in attack_words if w in text_lower)
        if defense_score > attack_score:
            return "defense"
        if attack_score > defense_score:
            return "attack"
        return "neutral"

    @app.post("/api/council/stream")
    def council_stream(request: CouncilRequest):
        selected = [item for item in CAMPAIGN["characters"] if item["id"] in request.character_ids][:6]
        selected = [item for item in selected if management.characters.get(item["id"]) and management.characters[item["id"]].status == "active"]
        if len(selected) < 2:
            def error_stream():
                yield f"data: {json.dumps({'error': '朝议至少需要两名当前可用人物。'}, ensure_ascii=False)}\n\n"
            return StreamingResponse(error_stream(), media_type="text/event-stream")

        transcript = ""
        first_round: list[dict] = []

        def generate():
            nonlocal transcript
            # 第一轮：群臣依次表态
            for character in selected:
                reply, model_used = generate_character_reply(
                    character, request.topic, "court",
                    {"前臣发言": transcript, "章节": ACT_NAMES[progress.act], "年月": f"{progress.year}年{progress.month}月"},
                    with_status=True,
                )
                first_round.append({"character": character, "reply": reply, "stance": _classify_stance(reply)})
                chunk = {"character_id": character["id"], "name": character["name"], "reply": reply, "model_used": model_used, "round": 1}
                transcript += f"\n{character['name']}：{reply}"
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"

            # 第二轮：主战与主守双方各再辩一句
            defense_speaker = next((item for item in first_round if item["stance"] == "defense"), None)
            attack_speaker = next((item for item in first_round if item["stance"] == "attack"), None)

            if defense_speaker and attack_speaker:
                yield f"data: {json.dumps({'round_marker': 2, 'label': '群臣再辩'}, ensure_ascii=False)}\n\n"

                defense_character = defense_speaker["character"]
                attack_character = attack_speaker["character"]

                reply, model_used = generate_character_reply(
                    defense_character, request.topic, "court",
                    {
                        "前臣发言": transcript,
                        "再辩": f"{attack_character['name']}主战甚急，请直接驳其疏漏，限两句。",
                        "章节": ACT_NAMES[progress.act],
                        "年月": f"{progress.year}年{progress.month}月",
                    },
                    with_status=True,
                )
                transcript += f"\n{defense_character['name']}（再辩）：{reply}"
                yield f"data: {json.dumps({'character_id': defense_character['id'], 'name': defense_character['name'], 'reply': reply, 'model_used': model_used, 'round': 2}, ensure_ascii=False)}\n\n"

                reply, model_used = generate_character_reply(
                    attack_character, request.topic, "court",
                    {
                        "前臣发言": transcript,
                        "再辩": f"{defense_character['name']}主守再辩，请针锋相对回应，限两句。",
                        "章节": ACT_NAMES[progress.act],
                        "年月": f"{progress.year}年{progress.month}月",
                    },
                    with_status=True,
                )
                yield f"data: {json.dumps({'character_id': attack_character['id'], 'name': attack_character['name'], 'reply': reply, 'model_used': model_used, 'round': 2}, ensure_ascii=False)}\n\n"

            yield f"data: {json.dumps({'done': True}, ensure_ascii=False)}\n\n"

        return StreamingResponse(generate(), media_type="text/event-stream")

    @app.post("/api/secret-edicts")
    def secret_edict(request: SecretEdictRequest) -> dict:
        character = next((item for item in CAMPAIGN["characters"] if item["id"] == request.character_id), None)
        runtime_character = management.characters.get(request.character_id)
        if not character or not runtime_character or runtime_character.status != "active" or not request.text.strip():
            return {"accepted": False, "detail": "密诏必须指定可用人物并写明内容。"}
        with lock:
            edict = add_secret_edict(progress, character["name"], request.text, request.purpose)
            store.save_progress(progress)
            return {"accepted": True, "edict": edict, "progress": asdict(progress)}

    @app.post("/api/decrees/freeform")
    def freeform_decree(request: FreeformDecreeRequest) -> dict:
        with lock:
            decision = progress.pending_event_choice if isinstance(progress.pending_event_choice, dict) else None
            decision_text = ""
            if decision:
                decision_text = f"\n\n御前裁决：就《{decision['title']}》，裁定“{decision['choice']}”。"
            source = request.text.strip() + decision_text
            raw_candidates, parser_model_used = generate_decree_candidates(source, _decree_targets(management))
            candidates, rejected = _validate_decree_candidates(raw_candidates, management)
            decree = draft_freeform(conversation, request.text, progress.total_turn, candidates)
            decree["rendered_text"], decree["model_used"] = polish_document(source)
            decree["parser_model_used"] = parser_model_used
            decree["rejected_candidates"] = rejected
            decree["decision"] = decision
            store.save_conversation(conversation)
            return {"decree": decree}

    @app.post("/api/events/choice")
    def queue_event_choice(request: EventChoiceRequest) -> dict:
        with lock:
            event = progress.active_event
            if not event:
                return {"accepted": False, "detail": "当前没有待裁断的军国大事。"}
            if request.choice not in event.choices:
                return {"accepted": False, "detail": "该裁决不属于当前军国大事。"}
            progress.pending_event_choice = {"event_id": event.id, "title": event.title, "choice": request.choice}
            store.save_progress(progress)
            return {"accepted": True, "pending_event_choice": progress.pending_event_choice}

    @app.post("/api/decrees/{decree_id}/confirm")
    def approve_freeform_decree(decree_id: int) -> dict:
        with lock:
            decree = confirm_decree(conversation, decree_id)
            if not decree["candidates"]:
                return {"decree": decree, "directives": [asdict(item) for item in management.directives], "accepted": False, "detail": "诏书尚未形成可执行事项，请修改后重拟。"}
            for candidate in decree["candidates"]:
                draft_directive(management, candidate["kind"], candidate["target"], candidate["amount"], candidate.get("subject", ""))
            store.save_conversation(conversation)
            store.save_management(management)
            return {"decree": decree, "directives": [asdict(item) for item in management.directives], "accepted": True}

    @app.post("/api/armies/move")
    def move_field_army(request: ArmyMoveRequest) -> dict:
        with lock:
            try:
                result = queue_army_move(strategy, request.army_id, request.destination)
            except ValueError as error:
                raise HTTPException(status_code=400, detail=str(error)) from error
            store.save_strategy(strategy)
            return {"movement": result, "strategy": asdict(strategy)}

    @app.post("/api/directives")
    def add_directive(request: DirectiveRequest) -> dict:
        with lock:
            queued = draft_directive(management, request.kind, request.target, request.amount, request.subject)
            store.save_management(management)
            return {"directive": asdict(queued), "directives": [asdict(item) for item in management.directives]}

    @app.delete("/api/directives/{directive_id}")
    def delete_directive(directive_id: int) -> dict:
        with lock:
            removed = remove_directive(management, directive_id)
            store.save_management(management)
            return {"removed": removed, "directives": [asdict(item) for item in management.directives]}

    @app.post("/api/resolve")
    def resolve_campaign_turn(request: ResolveRequest = ResolveRequest()) -> dict:
        with lock:
            pending = progress.pending_event_choice if isinstance(progress.pending_event_choice, dict) else {}
            event_choice = request.event_choice or pending.get("choice", "")
            if progress.active_event and event_choice and event_choice not in progress.active_event.choices:
                return {"accepted": False, "detail": "暂存裁决已失效，请重新裁断。"}
            campaign_result = advance_campaign(progress, event_choice)
            if not campaign_result.get("advanced"):
                return {"requires_choice": True, "event": campaign_result.get("event"), "progress": asdict(progress)}
            progress.pending_event_choice = None
            result = resolve_management(management, progress.act).payload()
            result["world_events"].extend(resolve_policy(progress, campaign["state"], management))
            result["world_events"].extend(resolve_movements(strategy))
            result["world_events"].extend(simulate_month(strategy, progress.act, progress.total_turn))
            event_effects = _apply_event_choice(management, campaign_result.get("resolved"))
            result["world_events"].extend(event_effects)
            result["world_events"].extend(campaign_result.get("secret_updates", []))
            issued = promulgate_decrees(conversation, progress.total_turn)
            result["world_events"].extend(f"圣旨颁行：《{item.get('rendered_text') or item['text'][:24]}》" for item in issued)
            proposal_started = time.perf_counter()
            proposal, simulation_model_used = generate_world_proposal({
                "turn": result,
                "campaign": campaign_result,
                "state": campaign["state"].payload(),
                "management": asdict(management),
                "strategy": asdict(strategy),
                "situations": progress.situations,
                "modifiers": progress.modifiers,
                "date": f"{progress.year}年{progress.month}月",
                "act": ACT_NAMES[progress.act],
            })
            simulation = apply_world_proposal(proposal, management)
            result["llm_simulation"] = simulation
            if simulation["assessment"]:
                result["world_events"].append("推演判断：" + simulation["assessment"])
            result["world_events"].extend(
                f"推演影响：{item['path']} {item['before']}→{item['after']}（{item['reason']}）"
                for item in simulation["accepted"]
            )
            result["world_events"].extend(
                f"人物动向：{item.get('actor', '未知')}：{item.get('intent', '')}"
                for item in simulation["npc_actions"] if isinstance(item, dict)
            )
            result["world_events"].extend("事件伏线：" + item for item in simulation["event_seeds"])
            result["world_events"].extend(advance_situations(progress, campaign["state"], management, simulation.get("situations")))
            result["situations"] = progress.situations
            result["modifiers"] = progress.modifiers
            simulation_config = load_config(role="simulation")
            store.record_agent_run("世界状态推演", simulation_config.model if simulation_config else "未配置", round((time.perf_counter() - proposal_started) * 1000), simulation_model_used)
            _sync_metrics(campaign["state"], management)
            campaign["state"].act_id = f"act{progress.act}"
            campaign["state"].phase = ACT_NAMES[progress.act]
            campaign["state"].clock.date_label = f"公元{progress.year}年{progress.month}月"
            _activate_content(management, progress.act)
            activate_strategy()
            campaign["state"].history.insert(0, f"至德纪元第{progress.total_turn}回合：{ACT_NAMES[progress.act]}局势结算。")
            started = time.perf_counter()
            narration, model_used = generate_turn_narration({"turn": result["turn"], "reports": result["reports"], "diff": result["diff"], "campaign": campaign_result, "strategy": result["world_events"], "llm_simulation": simulation}, with_status=True)
            config = load_config(role="simulation")
            store.record_agent_run("回合推演", config.model if config else "中文模板", round((time.perf_counter() - started) * 1000), model_used)
            campaign["state"].history.insert(0, narration)
            store.record_turn("resolve", result)
            store.save_management(management)
            store.save_progress(progress)
            store.save_conversation(conversation)
            store.save_strategy(strategy)
            store.save(campaign["state"])
            store.save_slot(0, "自动存档", unified_payload())
            return {"result": result, "narration": narration, "model_used": model_used, "simulation_model_used": simulation_model_used, "campaign_result": campaign_result, "progress": asdict(progress), "state": {**campaign["state"].payload(), "save_revision": store.revision()}, "management": asdict(management)}

    @app.post("/api/turn")
    def turn(request: TurnRequest) -> dict:
        with lock:
            result = apply_order(campaign["state"], request.order)
            store.record_turn(request.order, result)
            store.save(campaign["state"])
            result["state"]["save_revision"] = store.revision()
            return result

    @app.post("/api/reset")
    def reset() -> dict:
        with lock:
            campaign["state"] = store.reset()
            fresh = store.load_management()
            _hydrate_management(fresh)
            management.__dict__.update(fresh.__dict__)
            store.save_management(management)
            fresh_progress = store.load_progress()
            progress.__dict__.update(fresh_progress.__dict__)
            conversation.__dict__.update(ConversationState().__dict__)
            strategy.__dict__.update(initial_strategy(CAMPAIGN).__dict__)
            persist_all()
            return {**campaign["state"].payload(), "save_revision": store.revision()}

    @app.get("/api/saves")
    def saves() -> dict:
        return {"slots": store.list_slots()}

    @app.post("/api/saves")
    def save_game(request: SaveSlotRequest) -> dict:
        with lock:
            store.save_slot(request.slot_id, request.name, unified_payload())
            return {"slots": store.list_slots()}

    @app.post("/api/saves/{slot_id}/load")
    def load_game(slot_id: int) -> dict:
        with lock:
            payload = store.load_slot(slot_id)
            campaign["state"] = state_from_payload(payload["state"])
            management.__dict__.update(management_from_payload(payload["management"]).__dict__)
            progress_data = dict(payload["progress"])
            if progress_data.get("active_event"):
                progress_data["active_event"] = CampaignEvent(**progress_data["active_event"])
            progress.__dict__.update(CampaignProgress(**progress_data).__dict__)
            conv = payload.get("conversation") or {}
            store._save_aux("conversation", conv)
            conversation.__dict__.update(store.load_conversation().__dict__)
            strat = payload.get("strategy") or {}
            store._save_aux("strategy", strat)
            strategy.__dict__.update((store.load_strategy() or initial_strategy(CAMPAIGN)).__dict__)
            persist_all()
            return {"loaded": True, "snapshot": unified_payload()}

    app.mount("/", StaticFiles(directory=ROOT / "apps" / "web" / "dist", html=True), name="static")
    return app


app = create_app()


def _sync_metrics(state, management) -> None:
    regions = list(management.regions.values())
    armies = list(management.armies.values())
    state.popular_support = round(sum(region.support for region in regions) / max(1, len(regions)))
    state.fiscal_health = max(0, min(100, management.finance.cash // 12))
    state.military_power = max(0, min(100, sum(army.fit_strength for army in armies) // 7_000))
