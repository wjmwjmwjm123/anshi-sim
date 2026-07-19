from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field


@dataclass
class Message:
    role: str
    text: str
    scene: str
    turn: int


@dataclass
class Memory:
    summary: str
    scene: str
    turn: int
    importance: int = 3
    tags: list[str] = field(default_factory=list)
    expires_at: int | None = None  # None = permanent (importance 5)
    created_year: int = 756
    created_month: int = 6

    @staticmethod
    def ttl_for(importance: int) -> int | None:
        return {1: 3, 2: 6, 3: 12, 4: 24, 5: None}.get(importance, 12)


@dataclass
class Relationship:
    trust: int = 50
    favor: int = 0
    fear: int = 20
    promises: list[str] = field(default_factory=list)


@dataclass
class ConversationState:
    chats: dict[str, list[Message]] = field(default_factory=dict)
    memories: dict[str, list[Memory]] = field(default_factory=dict)
    relationships: dict[str, Relationship] = field(default_factory=dict)
    freeform_decrees: list[dict] = field(default_factory=list)
    next_decree_id: int = 1


def context_for(state: ConversationState, character_id: str) -> dict:
    return {
        "近期对话": [asdict(item) for item in state.chats.get(character_id, [])[-8:]],
        "长期记忆": [asdict(item) for item in state.memories.get(character_id, [])[-6:]],
        "君臣关系": asdict(state.relationships.get(character_id, Relationship())),
    }


def record_exchange(state: ConversationState, character_id: str, topic: str, reply: str, scene: str, turn: int) -> None:
    chat = state.chats.setdefault(character_id, [])
    chat.extend([Message("皇帝", topic, scene, turn), Message("臣下", reply, scene, turn)])
    relationship = state.relationships.setdefault(character_id, Relationship())
    if scene == "密诏":
        relationship.trust = _clamp(relationship.trust + 1)
    if any(word in topic for word in ("罢", "罪", "杀", "斩", "追责")):
        relationship.fear = _clamp(relationship.fear + 5)
        relationship.favor = _clamp(relationship.favor - 3, -100, 100)
    promise = _extract_promise(topic)
    if promise and promise not in relationship.promises:
        relationship.promises.append(promise)
    if len(chat) % 6 == 0:
        remember(state, character_id, f"第{turn}回合，{scene}中围绕“{topic[:40]}”形成持续影响。", scene, turn)


def remember(state: ConversationState, character_id: str, summary: str, scene: str, turn: int, importance: int = 3, tags: list[str] | None = None, year: int = 756, month: int = 6) -> None:
    items = state.memories.setdefault(character_id, [])
    ttl = Memory.ttl_for(importance)
    expires_at = turn + ttl if ttl is not None else None
    items.append(Memory(summary, scene, turn, importance, tags or [], expires_at, year, month))
    # cap at 30, sort by importance then recency
    items.sort(key=lambda item: (item.importance, item.turn), reverse=True)
    if len(items) > 30:
        # trim oldest lowest-importance first
        items.sort(key=lambda item: (item.importance, item.turn))
        items[:] = items[len(items) - 30:]
        items.sort(key=lambda item: (item.importance, item.turn), reverse=True)


def expire_memories(state: ConversationState, current_turn: int) -> int:
    """Remove memories past their TTL. Returns count removed."""
    removed = 0
    for char_id in state.memories:
        before = len(state.memories[char_id])
        state.memories[char_id] = [
            m for m in state.memories[char_id]
            if m.expires_at is None or m.expires_at > current_turn
        ]
        removed += before - len(state.memories[char_id])
    return removed


def recall_by_tags(state: ConversationState, tags: list[str], exclude_character: str | None = None, current_turn: int = 0, limit: int = 10) -> list[Memory]:
    """Cross-character recall by tags. Used for context injection during conversations."""
    results: list[Memory] = []
    tags_lower = [t.lower() for t in tags]
    for char_id, memories in state.memories.items():
        if exclude_character and char_id == exclude_character:
            continue
        for m in memories:
            if m.expires_at is not None and m.expires_at <= current_turn:
                continue
            if any(t in [tag.lower() for tag in m.tags] for t in tags_lower):
                results.append(m)
    results.sort(key=lambda m: (m.importance, m.turn), reverse=True)
    return results[:limit]


def recall_by_time(state: ConversationState, start_turn: int, end_turn: int | None = None, character_id: str | None = None, limit: int = 20) -> list[Memory]:
    """Recall memories within a turn range. For 'what happened last month' queries."""
    end = end_turn or start_turn
    results: list[Memory] = []
    chars = [character_id] if character_id else state.memories.keys()
    for cid in chars:
        for m in state.memories.get(cid, []):
            if start_turn <= m.turn <= end:
                results.append(m)
    results.sort(key=lambda m: m.turn, reverse=True)
    return results[:limit]


def draft_freeform(state: ConversationState, text: str, turn: int, candidates: list[dict] | None = None) -> dict:
    clean = text.strip()
    if len(clean) < 6:
        raise ValueError("诏书内容过短，必须写明对象与意图")
    draft = {
        "id": state.next_decree_id,
        "text": clean,
        "turn": turn,
        "status": "待确认",
        "candidates": candidates if candidates is not None else [],
    }
    state.next_decree_id += 1
    state.freeform_decrees.append(draft)
    return draft


def confirm_decree(state: ConversationState, decree_id: int) -> dict:
    decree = next((item for item in state.freeform_decrees if item["id"] == decree_id), None)
    if not decree:
        raise ValueError("未找到该诏书草案")
    decree["status"] = "已确认"
    return decree


def promulgate_decrees(state: ConversationState, turn: int) -> list[dict]:
    issued = []
    for decree in state.freeform_decrees:
        if decree.get("status") == "已确认":
            decree["status"] = "已颁行"
            decree["promulgated_turn"] = turn
            issued.append(decree)
    return issued


def parse_decree(text: str) -> list[dict]:
    rules = [
        (("赈", "开仓", "恤民"), "relief", "changan"),
        (("加税", "加征", "征税"), "tax", "changan"),
        (("粮", "转运", "补给"), "supply", "tang_tongguan"),
        (("募兵", "征兵", "动员"), "mobilize", "tang_shuofang"),
        (("筑城", "修城", "城防"), "fortify", "changan"),
        (("查", "调查", "核实"), "investigate", "false_intelligence"),
        (("调停", "和解", "释疑"), "mediate", "yang_geshu_conflict"),
    ]
    amount_match = re.search(r"([一二三四五六七八九十百千万\d]+)", text)
    amount = _number(amount_match.group(1)) if amount_match else 10
    candidates = []
    for words, kind, target in rules:
        if any(word in text for word in words):
            candidates.append({"kind": kind, "target": target, "amount": max(1, min(100, amount)), "subject": "", "reason": f"诏文命中：{'/'.join(words)}"})
    return candidates or [{"kind": "investigate", "target": "false_intelligence", "amount": 10, "subject": "", "reason": "复杂诏令先立项核议"}]


def _extract_promise(text: str) -> str:
    match = re.search(r"(?:朕|朝廷)(?:答应|许诺|允你|将会)([^。！？]{2,40})", text)
    return match.group(1).strip() if match else ""


def _number(value: str) -> int:
    if value.isdigit():
        return int(value)
    digits = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}
    if "万" in value:
        return min(100, digits.get(value[0], 1) * 10)
    if "十" in value:
        left, _, right = value.partition("十")
        return digits.get(left, 1) * 10 + digits.get(right, 0)
    return digits.get(value[-1], 10)


def _clamp(value: int, low: int = 0, high: int = 100) -> int:
    return max(low, min(high, value))
