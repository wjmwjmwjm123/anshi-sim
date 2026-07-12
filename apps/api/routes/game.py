"""游戏核心路由：回合推进、存档、快照。"""
from __future__ import annotations

import time
from dataclasses import asdict

import json as _json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from anshi.ai import generate_turn_narration, generate_world_proposal, load_config
from anshi.agents import create_gazette_agent, run_agent, run_agent_stream
from anshi.campaign import ACT_NAMES, advance as advance_campaign, CampaignEvent, CampaignProgress
from anshi.conversation import ConversationState, promulgate_decrees
from anshi.core import Order, apply_order
from anshi.management import resolve as resolve_management
from anshi.prompts import gazette_user
from anshi.situations import advance_situations, policy_catalog, resolve_policy, select_policy
from anshi.storage import management_from_payload, state_from_payload
from anshi.strategy import FieldArmy, Siege, initial_strategy, resolve_movements, simulate_month
from anshi.world_simulation import apply_world_proposal

router = APIRouter()


class TurnRequest(BaseModel):
    order: Order


class ResolveRequest(BaseModel):
    event_choice: str = ""


class SaveSlotRequest(BaseModel):
    slot_id: int
    name: str = ""


class PolicySelectRequest(BaseModel):
    policy_id: str


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


def _sync_metrics(state, management) -> None:
    regions = list(management.regions.values())
    armies = list(management.armies.values())
    state.popular_support = round(sum(region.support for region in regions) / max(1, len(regions)))
    state.fiscal_health = max(0, min(100, management.finance.cash // 12))
    state.military_power = max(0, min(100, sum(army.fit_strength for army in armies) // 7_000))


def register(router_: APIRouter, game) -> None:
    CAMPAIGN = game.campaign_data
    SCENARIO = game.scenario

    def activate_strategy() -> None:
        for item in CAMPAIGN["armies"]:
            if item["act_from"] <= game.progress.act and item["id"] not in game.strategy.armies:
                game.strategy.armies[item["id"]] = FieldArmy(item["id"], item["name"], item["power"], item["region"], item["present_strength"], item["supply"], item["morale"], item["status"])
        if game.progress.act >= 3 and not any(item.region == "suiyang" for item in game.strategy.sieges):
            game.strategy.sieges.append(Siege("suiyang", "yan_suiyang_siege", "tang_suiyang_garrison"))

    def model_roles_payload() -> dict:
        roles = {}
        for role in ("chat", "simulation", "utility"):
            config = load_config(role=role)
            roles[role] = {"configured": config is not None, "status": "已配置，调用时验证" if config else "未配置", "base_url": config.base_url if config else "", "model": config.model if config else ""}
        return roles

    @router_.get("/api/state")
    def state() -> dict:
        return {**game.campaign["state"].payload(), "save_revision": game.store.revision()}

    @router_.get("/api/scenario")
    def scenario() -> dict:
        return {"manifest": SCENARIO.manifest.model_dump(), "acts": [act.model_dump() for act in SCENARIO.acts], "regions": [region.model_dump() for region in SCENARIO.regions]}

    @router_.get("/api/situations")
    def situations() -> dict:
        return {"situations": game.progress.situations, "modifiers": game.progress.modifiers}

    @router_.get("/api/policies")
    def policies() -> dict:
        return {"policies": policy_catalog(game.progress), "completed": game.progress.completed_policies, "active": game.progress.active_policy}

    @router_.post("/api/policies/select")
    def choose_policy(request: PolicySelectRequest) -> dict:
        with game.lock:
            try:
                item = select_policy(game.progress, request.policy_id)
            except ValueError as error:
                return {"accepted": False, "detail": str(error), "policies": policy_catalog(game.progress)}
            game.store.save_progress(game.progress)
            return {"accepted": True, "selected": item, "policies": policy_catalog(game.progress)}

    @router_.get("/api/snapshot")
    def snapshot() -> dict:
        game.management  # ensure loaded
        model_roles = model_roles_payload()
        configured_models = sum(item["configured"] for item in model_roles.values())
        return {
            "state": {**game.campaign["state"].payload(), "save_revision": game.store.revision()},
            "management": asdict(game.management),
            "catalog": CAMPAIGN,
            "acts": [act.model_dump() for act in SCENARIO.acts],
            "progress": asdict(game.progress),
            "runtime": {"联网模型": f"已配置 {configured_models}/3" if configured_models else "未配置，使用中文模板", "模型": model_roles["chat"]["model"] or "中文模板", "模型职责": model_roles},
            "conversation": asdict(game.conversation),
            "strategy": asdict(game.strategy),
            "agent_runs": game.store.agent_runs(20),
            "save_slots": game.store.list_slots(),
        }

    @router_.post("/api/turn")
    def turn(request: TurnRequest) -> dict:
        with game.lock:
            result = apply_order(game.campaign["state"], request.order)
            game.store.record_turn(request.order, result)
            game.store.save(game.campaign["state"])
            result["state"]["save_revision"] = game.store.revision()
            return result

    @router_.post("/api/resolve")
    def resolve_campaign_turn(request: ResolveRequest = ResolveRequest()) -> dict:
        with game.lock:
            pending = game.progress.pending_event_choice if isinstance(game.progress.pending_event_choice, dict) else {}
            event_choice = request.event_choice or pending.get("choice", "")
            if game.progress.active_event and event_choice and event_choice not in game.progress.active_event.choices:
                return {"accepted": False, "detail": "暂存裁决已失效，请重新裁断。"}
            campaign_result = advance_campaign(game.progress, event_choice)
            if not campaign_result.get("advanced"):
                return {"requires_choice": True, "event": campaign_result.get("event"), "progress": asdict(game.progress)}
            game.progress.pending_event_choice = None
            result = resolve_management(game.management, game.progress.act).payload()
            result["world_events"].extend(resolve_policy(game.progress, game.campaign["state"], game.management))
            result["world_events"].extend(resolve_movements(game.strategy))
            result["world_events"].extend(simulate_month(game.strategy, game.progress.act, game.progress.total_turn))
            event_effects = _apply_event_choice(game.management, campaign_result.get("resolved"))
            result["world_events"].extend(event_effects)
            result["world_events"].extend(campaign_result.get("secret_updates", []))
            issued = promulgate_decrees(game.conversation, game.progress.total_turn)
            result["world_events"].extend(f"圣旨颁行：《{item.get('rendered_text') or item['text'][:24]}》" for item in issued)
            proposal_started = time.perf_counter()
            proposal, simulation_model_used = generate_world_proposal({
                "turn": result, "campaign": campaign_result, "state": game.campaign["state"].payload(),
                "management": asdict(game.management), "strategy": asdict(game.strategy),
                "situations": game.progress.situations, "modifiers": game.progress.modifiers,
                "date": f"{game.progress.year}年{game.progress.month}月", "act": ACT_NAMES[game.progress.act],
            })
            simulation = apply_world_proposal(proposal, game.management)
            result["llm_simulation"] = simulation
            if simulation["assessment"]:
                result["world_events"].append("推演判断：" + simulation["assessment"])
            result["world_events"].extend(f"推演影响：{item['path']} {item['before']}→{item['after']}（{item['reason']}）" for item in simulation["accepted"])
            result["world_events"].extend(f"人物动向：{item.get('actor', '未知')}：{item.get('intent', '')}" for item in simulation["npc_actions"] if isinstance(item, dict))
            result["world_events"].extend("事件伏线：" + item for item in simulation["event_seeds"])
            result["world_events"].extend(advance_situations(game.progress, game.campaign["state"], game.management, simulation.get("situations")))
            result["situations"] = game.progress.situations
            result["modifiers"] = game.progress.modifiers
            simulation_config = load_config(role="simulation")
            game.store.record_agent_run("世界状态推演", simulation_config.model if simulation_config else "未配置", round((time.perf_counter() - proposal_started) * 1000), simulation_model_used)
            _sync_metrics(game.campaign["state"], game.management)
            game.campaign["state"].act_id = f"act{game.progress.act}"
            game.campaign["state"].phase = ACT_NAMES[game.progress.act]
            game.campaign["state"].clock.date_label = f"公元{game.progress.year}年{game.progress.month}月"
            activate_strategy()
            game.campaign["state"].history.insert(0, f"至德纪元第{game.progress.total_turn}回合：{ACT_NAMES[game.progress.act]}局势结算。")
            started = time.perf_counter()
            narration, model_used = generate_turn_narration({"turn": result["turn"], "reports": result["reports"], "diff": result["diff"], "campaign": campaign_result, "strategy": result["world_events"], "llm_simulation": simulation}, with_status=True)
            config = load_config(role="simulation")
            game.store.record_agent_run("回合推演", config.model if config else "中文模板", round((time.perf_counter() - started) * 1000), model_used)
            game.campaign["state"].history.insert(0, narration)

            gazette_started = time.perf_counter()
            gazette_agent = create_gazette_agent()
            gazette_prompt = gazette_user({
                "日期": f"{game.progress.year}年{game.progress.month}月", "章节": ACT_NAMES[game.progress.act],
                "回合": game.progress.total_turn, "纪事": narration, "天下演化": result["world_events"][:15],
                "推演判断": simulation.get("assessment", ""),
                "推演影响": [f"{item['path']} {item['before']}→{item['after']}（{item['reason']}）" for item in simulation["accepted"][:8]],
                "人物动向": [f"{item.get('actor', '未知')}：{item.get('intent', '')}" for item in simulation["npc_actions"] if isinstance(item, dict)][:5],
                "局势": [f"{item.get('title','')} {item.get('status','')} {item.get('progress',0)}/100" if isinstance(item, dict) else f"{getattr(item,'title','')} {getattr(item,'status','')} {getattr(item,'progress',0)}/100" for item in game.progress.situations][:6],
                "财务": {"现银": game.management.finance.cash, "粮储": game.management.finance.grain},
            })
            gazette_fallback = f"【邸报】{game.progress.year}年{game.progress.month}月，{ACT_NAMES[game.progress.act]}。{narration}"
            gazette, gazette_model_used = run_agent(gazette_agent, gazette_prompt, fallback=gazette_fallback, with_status=True, tag="邸报")
            if gazette_model_used:
                game.store.record_agent_run("邸报", "文书模型", round((time.perf_counter() - gazette_started) * 1000), True)
            result["gazette"] = gazette

            game.store.record_turn("resolve", result)
            game.store.save_management(game.management)
            game.store.save_progress(game.progress)
            game.store.save_conversation(game.conversation)
            game.store.save_strategy(game.strategy)
            game.store.save(game.campaign["state"])
            game.store.save_slot(0, "自动存档", game.unified_payload())
            return {"result": result, "narration": narration, "gazette": gazette, "model_used": model_used, "simulation_model_used": simulation_model_used, "campaign_result": campaign_result, "progress": asdict(game.progress), "state": {**game.campaign["state"].payload(), "save_revision": game.store.revision()}, "management": asdict(game.management)}

    @router_.post("/api/resolve/stream")
    def resolve_stream(request: ResolveRequest = ResolveRequest()):
        """流式结算：先执行全部硬结算，再流式输出邸报。"""
        with game.lock:
            pending = game.progress.pending_event_choice if isinstance(game.progress.pending_event_choice, dict) else {}
            event_choice = request.event_choice or pending.get("choice", "")
            if game.progress.active_event and event_choice and event_choice not in game.progress.active_event.choices:
                def err(): yield f"data: {_json.dumps({'error': '暂存裁决已失效'}, ensure_ascii=False)}\n\n"
                return StreamingResponse(err(), media_type="text/event-stream")
            campaign_result = advance_campaign(game.progress, event_choice)
            if not campaign_result.get("advanced"):
                def err2(): yield f"data: {_json.dumps({'requires_choice': True, 'event': campaign_result.get('event')}, ensure_ascii=False)}\n\n"
                return StreamingResponse(err2(), media_type="text/event-stream")

            # --- 硬结算（与 /api/resolve 完全一致） ---
            game.progress.pending_event_choice = None
            result = resolve_management(game.management, game.progress.act).payload()
            result["world_events"].extend(resolve_policy(game.progress, game.campaign["state"], game.management))
            result["world_events"].extend(resolve_movements(game.strategy))
            result["world_events"].extend(simulate_month(game.strategy, game.progress.act, game.progress.total_turn))
            event_effects = _apply_event_choice(game.management, campaign_result.get("resolved"))
            result["world_events"].extend(event_effects)
            result["world_events"].extend(campaign_result.get("secret_updates", []))
            issued = promulgate_decrees(game.conversation, game.progress.total_turn)
            result["world_events"].extend(f"圣旨颁行：《{item.get('rendered_text') or item['text'][:24]}》" for item in issued)
            proposal_started = time.perf_counter()
            proposal, simulation_model_used = generate_world_proposal({
                "turn": result, "campaign": campaign_result, "state": game.campaign["state"].payload(),
                "management": asdict(game.management), "strategy": asdict(game.strategy),
                "situations": game.progress.situations, "modifiers": game.progress.modifiers,
                "date": f"{game.progress.year}年{game.progress.month}月", "act": ACT_NAMES[game.progress.act],
            })
            simulation = apply_world_proposal(proposal, game.management)
            result["llm_simulation"] = simulation
            if simulation["assessment"]:
                result["world_events"].append("推演判断：" + simulation["assessment"])
            result["world_events"].extend(f"推演影响：{item['path']} {item['before']}→{item['after']}（{item['reason']}）" for item in simulation["accepted"])
            result["world_events"].extend(f"人物动向：{item.get('actor', '未知')}：{item.get('intent', '')}" for item in simulation["npc_actions"] if isinstance(item, dict))
            result["world_events"].extend("事件伏线：" + item for item in simulation["event_seeds"])
            result["world_events"].extend(advance_situations(game.progress, game.campaign["state"], game.management, simulation.get("situations")))
            result["situations"] = game.progress.situations
            result["modifiers"] = game.progress.modifiers
            simulation_config = load_config(role="simulation")
            game.store.record_agent_run("世界状态推演", simulation_config.model if simulation_config else "未配置", round((time.perf_counter() - proposal_started) * 1000), simulation_model_used)
            _sync_metrics(game.campaign["state"], game.management)
            game.campaign["state"].act_id = f"act{game.progress.act}"
            game.campaign["state"].phase = ACT_NAMES[game.progress.act]
            game.campaign["state"].clock.date_label = f"公元{game.progress.year}年{game.progress.month}月"
            activate_strategy()
            game.campaign["state"].history.insert(0, f"至德纪元第{game.progress.total_turn}回合：{ACT_NAMES[game.progress.act]}局势结算。")
            started = time.perf_counter()
            narration, model_used = generate_turn_narration({"turn": result["turn"], "reports": result["reports"], "diff": result["diff"], "campaign": campaign_result, "strategy": result["world_events"], "llm_simulation": simulation}, with_status=True)
            config = load_config(role="simulation")
            game.store.record_agent_run("回合推演", config.model if config else "中文模板", round((time.perf_counter() - started) * 1000), model_used)
            game.campaign["state"].history.insert(0, narration)

            # 构建邸报 prompt
            gazette_agent = create_gazette_agent()
            gazette_prompt = gazette_user({
                "日期": f"{game.progress.year}年{game.progress.month}月", "章节": ACT_NAMES[game.progress.act],
                "回合": game.progress.total_turn, "纪事": narration, "天下演化": result["world_events"][:15],
                "推演判断": simulation.get("assessment", ""),
                "推演影响": [f"{item['path']} {item['before']}→{item['after']}（{item['reason']}）" for item in simulation["accepted"][:8]],
                "人物动向": [f"{item.get('actor', '未知')}：{item.get('intent', '')}" for item in simulation["npc_actions"] if isinstance(item, dict)][:5],
                "局势": [f"{item.get('title','')} {item.get('status','')} {item.get('progress',0)}/100" if isinstance(item, dict) else f"{getattr(item,'title','')} {getattr(item,'status','')} {getattr(item,'progress',0)}/100" for item in game.progress.situations][:6],
                "财务": {"现银": game.management.finance.cash, "粮储": game.management.finance.grain},
            })

            # 保存快照（在流式输出之前）
            game.store.record_turn("resolve", result)
            game.store.save_management(game.management)
            game.store.save_progress(game.progress)
            game.store.save_conversation(game.conversation)
            game.store.save_strategy(game.strategy)
            game.store.save(game.campaign["state"])
            game.store.save_slot(0, "自动存档", game.unified_payload())

            snapshot = {"result": result, "narration": narration, "model_used": model_used,
                        "simulation_model_used": simulation_model_used, "campaign_result": campaign_result,
                        "progress": asdict(game.progress),
                        "state": {**game.campaign["state"].payload(), "save_revision": game.store.revision()},
                        "management": asdict(game.management)}

        # --- 流式输出（锁外） ---
        def generate():
            # 先发结算快照（不含邸报）
            yield f"data: {_json.dumps({'type': 'snapshot', 'data': snapshot}, ensure_ascii=False)}\n\n"
            # 流式输出邸报
            yield f"data: {_json.dumps({'type': 'gazette_start'}, ensure_ascii=False)}\n\n"
            gazette_buf = []
            try:
                for chunk in run_agent_stream(gazette_agent, gazette_prompt, tag="邸报"):
                    gazette_buf.append(chunk)
                    yield f"data: {_json.dumps({'type': 'gazette_delta', 'delta': chunk}, ensure_ascii=False)}\n\n"
            except Exception:
                pass
            gazette = "".join(gazette_buf).strip()
            if not gazette:
                gazette = f"【邸报】{game.progress.year}年{game.progress.month}月，{ACT_NAMES[game.progress.act]}。{narration}"
            yield f"data: {_json.dumps({'type': 'gazette_end', 'gazette': gazette}, ensure_ascii=False)}\n\n"
            yield f"data: {_json.dumps({'done': True}, ensure_ascii=False)}\n\n"

        return StreamingResponse(generate(), media_type="text/event-stream")

    @router_.post("/api/reset")
    def reset() -> dict:
        with game.lock:
            game.campaign["state"] = game.store.reset()
            fresh = game.store.load_management()
            game.hydrate_management(fresh)
            game.management.__dict__.update(fresh.__dict__)
            game.store.save_management(game.management)
            fresh_progress = game.store.load_progress()
            game.progress.__dict__.update(fresh_progress.__dict__)
            game.conversation.__dict__.update(ConversationState().__dict__)
            game.strategy.__dict__.update(initial_strategy(CAMPAIGN).__dict__)
            game.persist_all()
            return {**game.campaign["state"].payload(), "save_revision": game.store.revision()}

    @router_.get("/api/saves")
    def saves() -> dict:
        return {"slots": game.store.list_slots()}

    @router_.post("/api/saves")
    def save_game(request: SaveSlotRequest) -> dict:
        with game.lock:
            game.store.save_slot(request.slot_id, request.name, game.unified_payload())
            return {"slots": game.store.list_slots()}

    @router_.post("/api/saves/{slot_id}/load")
    def load_game(slot_id: int) -> dict:
        with game.lock:
            payload = game.store.load_slot(slot_id)
            game.campaign["state"] = state_from_payload(payload["state"])
            game.management.__dict__.update(management_from_payload(payload["management"]).__dict__)
            progress_data = dict(payload["progress"])
            if progress_data.get("active_event"):
                progress_data["active_event"] = CampaignEvent(**progress_data["active_event"])
            game.progress.__dict__.update(CampaignProgress(**progress_data).__dict__)
            conv = payload.get("conversation") or {}
            game.store._save_aux("conversation", conv)
            game.conversation.__dict__.update(game.store.load_conversation().__dict__)
            strat = payload.get("strategy") or {}
            game.store._save_aux("strategy", strat)
            game.strategy.__dict__.update((game.store.load_strategy() or initial_strategy(CAMPAIGN)).__dict__)
            game.persist_all()
            return {"loaded": True, "snapshot": game.unified_payload()}
