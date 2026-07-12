"""诏令与事件路由。"""
from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from anshi.ai import generate_decree_candidates, load_config, polish_document
from anshi.campaign import ACT_NAMES
from anshi.conversation import confirm_decree, draft_freeform, promulgate_decrees
from anshi.management import draft as draft_directive, remove as remove_directive, DirectiveKind
from anshi.strategy import queue_move as queue_army_move

router = APIRouter()

_DIRECTIVE_DOMAINS = {
    "relief": "regions", "tax": "regions", "fortify": "regions",
    "supply": "armies", "mobilize": "armies",
    "investigate": "issues", "mediate": "issues", "appoint": "characters",
}


class DirectiveRequest(BaseModel):
    kind: DirectiveKind
    target: str
    amount: int = 10
    subject: str = ""


class FreeformDecreeRequest(BaseModel):
    text: str


class EventChoiceRequest(BaseModel):
    choice: str


class ArmyMoveRequest(BaseModel):
    army_id: str
    destination: str


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


def _decision_text(decision: dict) -> str:
    """构建御前裁决文本，避免 f-string 中的中文引号编码问题。"""
    title = decision["title"]
    choice = decision["choice"]
    return "\n\n御前裁决：就《" + title + "》，裁定“" + choice + "”。"


def register(router_: APIRouter, game) -> None:
    CAMPAIGN = game.campaign_data

    @router_.post("/api/decrees/freeform")
    def freeform_decree(request: FreeformDecreeRequest) -> dict:
        with game.lock:
            decision = game.progress.pending_event_choice if isinstance(game.progress.pending_event_choice, dict) else None
            decision_text = _decision_text(decision) if decision else ""
            source = request.text.strip() + decision_text
            raw_candidates, parser_model_used = generate_decree_candidates(source, _decree_targets(game.management))
            candidates, rejected = _validate_decree_candidates(raw_candidates, game.management)
            decree = draft_freeform(game.conversation, request.text, game.progress.total_turn, candidates)
            decree["rendered_text"], decree["model_used"] = polish_document(source)
            decree["parser_model_used"] = parser_model_used
            decree["rejected_candidates"] = rejected
            decree["decision"] = decision
            game.store.save_conversation(game.conversation)
            return {"decree": decree}

    @router_.post("/api/events/choice")
    def queue_event_choice(request: EventChoiceRequest) -> dict:
        with game.lock:
            event = game.progress.active_event
            if not event:
                return {"accepted": False, "detail": "当前没有待裁断的军国大事。"}
            if request.choice not in event.choices:
                return {"accepted": False, "detail": "该裁决不属于当前军国大事。"}
            game.progress.pending_event_choice = {"event_id": event.id, "title": event.title, "choice": request.choice}
            game.store.save_progress(game.progress)
            return {"accepted": True, "pending_event_choice": game.progress.pending_event_choice}

    @router_.post("/api/decrees/{decree_id}/confirm")
    def approve_freeform_decree(decree_id: int) -> dict:
        with game.lock:
            decree = confirm_decree(game.conversation, decree_id)
            if not decree["candidates"]:
                return {"decree": decree, "directives": [asdict(item) for item in game.management.directives], "accepted": False, "detail": "诏书尚未形成可执行事项，请修改后重拟。"}
            for candidate in decree["candidates"]:
                draft_directive(game.management, candidate["kind"], candidate["target"], candidate["amount"], candidate.get("subject", ""))
            game.store.save_conversation(game.conversation)
            game.store.save_management(game.management)
            return {"decree": decree, "directives": [asdict(item) for item in game.management.directives], "accepted": True}

    @router_.post("/api/armies/move")
    def move_field_army(request: ArmyMoveRequest) -> dict:
        with game.lock:
            try:
                result = queue_army_move(game.strategy, request.army_id, request.destination)
            except ValueError as error:
                raise HTTPException(status_code=400, detail=str(error)) from error
            game.store.save_strategy(game.strategy)
            return {"movement": result, "strategy": asdict(game.strategy)}

    @router_.post("/api/directives")
    def add_directive(request: DirectiveRequest) -> dict:
        with game.lock:
            queued = draft_directive(game.management, request.kind, request.target, request.amount, request.subject)
            game.store.save_management(game.management)
            return {"directive": asdict(queued), "directives": [asdict(item) for item in game.management.directives]}

    @router_.delete("/api/directives/{directive_id}")
    def delete_directive(directive_id: int) -> dict:
        with game.lock:
            removed = remove_directive(game.management, directive_id)
            game.store.save_management(game.management)
            return {"removed": removed, "directives": [asdict(item) for item in game.management.directives]}
