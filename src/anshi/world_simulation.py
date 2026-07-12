from __future__ import annotations

from typing import Any


RULES = {
    "regions": {"support": 4, "unrest": 6, "fortification": 2},
    "armies": {"morale": 6, "supply": 5},
    "issues": {"tension": 5, "progress": 5},
    "characters": {"loyalty": 3},
}


def apply_world_proposal(payload: dict[str, Any], management: Any) -> dict[str, Any]:
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    proposals = payload.get("proposals", [])
    if not isinstance(proposals, list):
        proposals = []

    for proposal in proposals[:20]:
        if not isinstance(proposal, dict):
            rejected.append({"proposal": proposal, "reason": "提案不是对象"})
            continue
        path = str(proposal.get("path", ""))
        parts = path.split(".")
        if len(parts) != 3 or parts[0] not in RULES or parts[2] not in RULES[parts[0]]:
            rejected.append({"proposal": proposal, "reason": "路径不在允许清单"})
            continue
        if proposal.get("operation") != "add":
            rejected.append({"proposal": proposal, "reason": "仅允许增量操作"})
            continue
        try:
            requested = int(round(float(proposal.get("value", 0))))
            confidence = float(proposal.get("confidence", 0))
        except (TypeError, ValueError):
            rejected.append({"proposal": proposal, "reason": "数值或置信度无效"})
            continue
        if confidence < 0.35 or requested == 0:
            rejected.append({"proposal": proposal, "reason": "置信度过低或没有变化"})
            continue
        collection = getattr(management, parts[0], {})
        target = collection.get(parts[1])
        if target is None:
            rejected.append({"proposal": proposal, "reason": "目标不存在"})
            continue
        limit = RULES[parts[0]][parts[2]]
        applied = max(-limit, min(limit, requested))
        before = int(getattr(target, parts[2]))
        after = max(0, min(100, before + applied))
        setattr(target, parts[2], after)
        accepted.append({
            "path": path,
            "before": before,
            "after": after,
            "requested": requested,
            "applied": after - before,
            "reason": str(proposal.get("reason", "世界推演")),
            "confidence": confidence,
        })

    npc_actions = payload.get("npc_actions", [])
    event_seeds = payload.get("event_seeds", [])
    return {
        "assessment": str(payload.get("assessment", ""))[:500],
        "accepted": accepted,
        "rejected": rejected,
        "situations": payload.get("situations", [])[:12] if isinstance(payload.get("situations", []), list) else [],
        "npc_actions": npc_actions[:12] if isinstance(npc_actions, list) else [],
        "event_seeds": [str(item)[:120] for item in event_seeds[:12]] if isinstance(event_seeds, list) else [],
    }
