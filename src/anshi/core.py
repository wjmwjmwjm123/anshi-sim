from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Literal

Order = Literal["hold", "verify", "reconcile", "constrain", "prepare_retreat", "sally"]
WindowStatus = Literal["scheduled", "open", "resolved", "expired"]
CommandStatus = Literal["draft", "validated", "dispatched", "executing", "completed", "refused"]


@dataclass
class ArmyState:
    paper_strength: int = 200_000
    present_strength: int = 178_000
    fit_strength: int = 150_000
    morale: int = 43
    cohesion: int = 36
    supply_ratio: float = 0.86


@dataclass
class CrisisState:
    tongguan: int = 65
    court_conflict: int = 80
    false_intel: int = 90


@dataclass
class EventWindow:
    id: str
    title: str
    opens_day: int
    closes_day: int
    consequence: str
    status: WindowStatus = "scheduled"


@dataclass
class EventClock:
    day: int = 1
    date_label: str = "天宝十五载 六月初一"
    scale: Literal["day", "week", "month"] = "day"
    last_advance_days: int = 0
    windows: list[EventWindow] = field(
        default_factory=lambda: [
            EventWindow("intel_review", "敌情复核", 1, 4, "未经复核的敌弱奏报将成为出关依据", "open"),
            EventWindow("command_integrity", "将相释疑", 1, 6, "统帅与中枢互疑将削弱军令执行", "open"),
            EventWindow("imperial_deadline", "出关诏限", 1, 7, "诏限过后继续固守可能被前军拒绝", "open"),
            EventWindow("retreat_route", "退路整备", 2, 8, "错过窗口将无法在狭道溃退时组织后撤"),
        ]
    )


@dataclass
class IntelligenceClaim:
    id: str
    summary: str
    source: str
    age_days: int
    confidence: int
    source_chain: str
    independent: bool
    status: Literal["unverified", "corroborated", "contradicted"] = "unverified"


@dataclass
class CommandState:
    sequence: int
    order: str
    label: str
    status: CommandStatus
    issued_day: int
    lifecycle: list[CommandStatus] = field(default_factory=lambda: ["draft"])
    refusal_reason: str = ""


def _initial_claims() -> list[IntelligenceClaim]:
    return [
        IntelligenceClaim("enemy_weak", "陕郡奏称崔乾佑兵不满四千", "陕郡奏报", 1, 42, "shaan_memorial", False),
        IntelligenceClaim("hold_advice", "哥舒翰请固守潼关，待河北战局变化", "潼关行营奏议", 0, 78, "geshu_command", True, "corroborated"),
        IntelligenceClaim("attack_order", "监军催促大军尽快出关", "御史中丞边令诚传诏", 0, 95, "imperial_edict", True, "corroborated"),
    ]


@dataclass
class GameState:
    phase: str = "潼关危局"
    central_prestige: int = 45
    military_power: int = 55
    popular_support: int = 35
    fiscal_health: int = 40
    intel_confidence: int = 28
    attention: int = 6
    tongguan_status: str = "坚守"
    army: ArmyState = field(default_factory=ArmyState)
    crises: CrisisState = field(default_factory=CrisisState)
    clock: EventClock = field(default_factory=EventClock)
    intel_claims: list[IntelligenceClaim] = field(default_factory=_initial_claims)
    preparations: list[str] = field(default_factory=list)
    history: list[str] = field(default_factory=lambda: ["六月初一：陕郡敌情奏报抵京。"])
    last_command: CommandState | None = None
    command_count: int = 0
    chapter_transition: dict | None = None
    ended: bool = False
    act_id: str = "act1"

    def payload(self) -> dict:
        data = asdict(self)
        data["day"] = self.clock.day
        data["date_label"] = self.clock.date_label
        data["known_intel"] = [claim.summary for claim in self.intel_claims]
        return data


def initial_state() -> GameState:
    return GameState()


def _clamp(value: int | float, low: int = 0, high: int = 100) -> int:
    return int(max(low, min(high, round(value))))


def _window(state: GameState, window_id: str) -> EventWindow:
    return next(window for window in state.clock.windows if window.id == window_id)


def _resolve_window(state: GameState, window_id: str) -> None:
    _window(state, window_id).status = "resolved"


def _advance(state: GameState, days: int) -> None:
    state.clock.day += days
    state.clock.last_advance_days = days
    state.clock.date_label = _date_label(state.clock.day)
    for claim in state.intel_claims:
        claim.age_days += days
    for window in state.clock.windows:
        if window.status == "resolved":
            continue
        if state.clock.day < window.opens_day:
            window.status = "scheduled"
        elif state.clock.day <= window.closes_day:
            window.status = "open"
        else:
            window.status = "expired"


def _date_label(day: int) -> str:
    numerals = {1: "初一", 2: "初二", 3: "初三", 4: "初四", 5: "初五", 6: "初六", 7: "初七", 8: "初八", 9: "初九", 10: "初十"}
    return f"天宝十五载 六月{numerals.get(day, f'{day}日')}"


ORDER_LABELS = {
    "hold": "闭关固守",
    "verify": "三路复核",
    "reconcile": "召对释疑",
    "constrain": "更易监军",
    "prepare_retreat": "整备退路",
    "sally": "奉诏出击",
}


def _new_command(state: GameState, order: str) -> CommandState:
    state.command_count += 1
    command = CommandState(state.command_count, order, ORDER_LABELS.get(order, order), "draft", state.clock.day)
    state.last_command = command
    return command


def _step(command: CommandState, status: CommandStatus) -> None:
    command.status = status
    command.lifecycle.append(status)


def _refuse(state: GameState, command: CommandState, reason: str) -> dict:
    command.refusal_reason = reason
    _step(command, "refused")
    headline = "军令留中，前军不受"
    state.history.insert(0, f"{state.clock.date_label}：{headline}。")
    return {
        "accepted": False,
        "headline": headline,
        "narrative": reason,
        "reasons": ["军令状态已记录为拒绝", "局势与时间均未推进"],
        "command": asdict(command),
        "state": state.payload(),
        "diff": [],
    }


def apply_order(state: GameState, order: Order) -> dict:
    command = _new_command(state, order)
    if order not in ORDER_LABELS:
        return _refuse(state, command, f"未知军令：{order}")
    if state.ended:
        return _refuse(state, command, "本章已经结束，需进入下一章后再发新令。")

    _step(command, "validated")
    if order == "hold" and _window(state, "imperial_deadline").status == "expired" and state.crises.court_conflict >= 80:
        return _refuse(state, command, "出关诏限已过，将相互疑未解，前军拒绝继续承担抗诏之名。")

    before = state.payload()
    _step(command, "dispatched")
    _step(command, "executing")

    if order == "hold":
        _advance(state, 2)
        state.attention -= 1
        state.central_prestige -= 1
        state.army.morale += 3
        state.army.cohesion += 4
        state.crises.tongguan -= 7
        state.crises.court_conflict += 5
        state.tongguan_status = "闭关固守"
        headline = "潼关闭门，前军未动"
        narrative = "哥舒翰奉诏整肃营垒，分兵守险。杨国忠一系继续催战，关城暂稳，朝中猜忌却更深。"
        reasons = ["避免进入灵宝狭道", "守军凝聚力上升", "拒绝催战损耗皇威"]
    elif order == "verify":
        _advance(state, 2)
        state.attention -= 2
        state.intel_confidence += 24
        state.crises.false_intel -= 22
        state.crises.tongguan -= 3
        state.intel_claims[0].confidence = 20
        state.intel_claims[0].status = "contradicted"
        state.intel_claims.insert(0, IntelligenceClaim(
            "south_mountain_movement", "南山道路有大队人马夜间调动", "斥候、商旅、降人三路互证", 0, 82,
            "scout+merchant+defector", True, "corroborated",
        ))
        if "intel_verified" not in state.preparations:
            state.preparations.append("intel_verified")
        _resolve_window(state, "intel_review")
        state.tongguan_status = "侦候戒备"
        headline = "三报互证，敌弱之说动摇"
        narrative = "商旅、斥候与降人所述不能相合。南山烟尘与粮车踪迹表明，陕郡表面兵弱不足为信。"
        reasons = ["三个独立来源交叉验证", "假情报压力下降", "消耗两点皇帝注意力"]
    elif order == "reconcile":
        _advance(state, 1)
        state.attention -= 2
        state.central_prestige -= 1
        state.army.cohesion += 8
        state.crises.court_conflict -= 24
        state.crises.tongguan -= 2
        if "command_reconciled" not in state.preparations:
            state.preparations.append("command_reconciled")
        if "supervisor_constrained" in state.preparations:
            _resolve_window(state, "command_integrity")
        headline = "将相入对，军令归一"
        narrative = "玄宗召杨国忠、哥舒翰当面对质，以守关期限和军报格式约束彼此。嫌隙未消，但前军不再同时承受两套命令。"
        reasons = ["将相倾轧显著下降", "统一军令提高凝聚力", "皇帝为调停承担少量威望"]
    elif order == "constrain":
        _advance(state, 1)
        state.attention -= 2
        state.central_prestige -= 2
        state.crises.false_intel -= 28
        state.crises.court_conflict -= 12
        if "supervisor_constrained" not in state.preparations:
            state.preparations.append("supervisor_constrained")
        if "command_reconciled" in state.preparations:
            _resolve_window(state, "command_integrity")
        headline = "监军易制，奏报分署"
        narrative = "边令诚仍传达诏令，但不得越过行营直接调动诸军；敌情奏报改由兵部与斥候分署具名。"
        reasons = ["削弱单一奏报链的垄断", "假报催战压力下降", "更易近侍损耗皇威"]
    elif order == "prepare_retreat":
        _advance(state, 2)
        state.attention -= 1
        state.army.cohesion += 5
        state.army.supply_ratio -= 0.03
        state.crises.tongguan += 2
        if "retreat_prepared" not in state.preparations:
            state.preparations.append("retreat_prepared")
        _resolve_window(state, "retreat_route")
        headline = "后队分营，退路已标"
        narrative = "行营清出回撤道路，分置引导旗与收容营。抽调民夫和粮车使关上压力稍增，却给狭道失利留下秩序。"
        reasons = ["预设分梯队撤退路线", "提高军阵凝聚力", "整备消耗少量粮秣"]
    elif order == "sally":
        _advance(state, 1)
        headline, narrative, reasons = _resolve_sally(state)
    else:  # pragma: no cover - Literal and validation guard this branch
        return _refuse(state, command, f"未知军令：{order}")

    _clamp_state(state)
    _step(command, "completed")
    state.history.insert(0, f"{state.clock.date_label}：{headline}。")
    after = state.payload()
    return {
        "accepted": True,
        "headline": headline,
        "narrative": narrative,
        "reasons": reasons,
        "command": asdict(command),
        "state": after,
        "diff": _diff(before, after),
    }


def _resolve_sally(state: GameState) -> tuple[str, str, list[str]]:
    engaged = 150_000
    verified = "intel_verified" in state.preparations or state.intel_confidence >= 50
    retreat = "retreat_prepared" in state.preparations
    reconciled = "command_reconciled" in state.preparations
    constrained = "supervisor_constrained" in state.preparations
    safeguards = (2 if verified else 0) + (2 if retreat else 0) + int(reconciled) + int(constrained)
    battle_losses = (22_000 if verified else 31_000) - (4_000 if constrained else 0)
    rout_losses = (34_000 if verified else 76_000) - (20_000 if retreat else 0) - (8_000 if reconciled else 0)
    state.army.present_strength -= battle_losses + rout_losses

    if safeguards >= 4:
        state.army.fit_strength = max(88_000, state.army.present_strength - 40_000)
        state.army.morale = 38
        state.army.cohesion = 42
        state.military_power -= 7
        state.central_prestige -= 3
        state.popular_support -= 1
        state.crises.tongguan = 70
        state.crises.court_conflict -= 5
        state.tongguan_status = "整军退关"
        headline = "伏兵虽发，诸军按旗而退"
        narrative = "敌军自南山出击，唐军仍受狭道所限；但复核情报、分段军令与预设退路使后队没有压垮前军，主力退回潼关重整。"
        reasons = [f"实际投入 {engaged:,} 人仍受狭道限制", f"战前防错措施 {safeguards}/6", "有序退路截断溃退级联"]
    elif safeguards >= 2:
        state.army.fit_strength = 77_000 if verified else 50_000
        state.army.morale = 31 if verified else 24
        state.army.cohesion = 29 if verified else 23
        state.military_power -= 9 if verified else 14
        state.central_prestige -= 5 if verified else 9
        state.popular_support -= 2 if verified else 4
        state.crises.tongguan = 82 if verified else 94
        state.crises.court_conflict = 91
        state.tongguan_status = "受创退关"
        headline = "伏兵虽发，前军有备而退"
        narrative = "唐军仍因狭道和烟火受创，但已有一项关键准备发挥作用，残部得以分梯队撤回潼关，未演成全军崩解。"
        reasons = [f"实际投入 {engaged:,} 人受限于狭道正面", f"战前防错措施 {safeguards}/6", "预警或退路准备削弱溃退级联"]
    else:
        state.army.fit_strength = 28_000
        state.army.morale = 18
        state.army.cohesion = 12
        state.military_power -= 19
        state.central_prestige -= 14
        state.popular_support -= 5
        state.crises.tongguan = 100
        state.crises.court_conflict = 96
        state.tongguan_status = "灵宝溃败"
        state.act_id = "act2"
        state.phase = "皇统裂变"
        state.ended = True
        state.chapter_transition = {
            "from_act": "act1",
            "to_act": "act2",
            "trigger": "tongguan_fallen",
            "title": "潼关失守，长安与马嵬事件窗开启",
        }
        state.clock.windows.append(EventWindow("capital_evacuation", "长安撤离", state.clock.day, state.clock.day + 4, "错过撤离将使皇统与禁军同时崩裂", "open"))
        headline = "灵宝烟起，诸军相失"
        narrative = "前军入隘后遭伏，烟火遮蔽军旗，后队拥塞。潼关门户洞开，战役转入长安撤离与马嵬军变。"
        reasons = [f"实际投入 {engaged:,} 人受限于狭道正面", "侦察置信度过低", "凝聚力不足导致溃退级联"]
    return headline, narrative, reasons


def _clamp_state(state: GameState) -> None:
    state.attention = _clamp(state.attention, 0, 10)
    state.central_prestige = _clamp(state.central_prestige)
    state.military_power = _clamp(state.military_power)
    state.popular_support = _clamp(state.popular_support)
    state.intel_confidence = _clamp(state.intel_confidence)
    state.army.morale = _clamp(state.army.morale)
    state.army.cohesion = _clamp(state.army.cohesion)
    state.army.supply_ratio = max(0.0, min(1.0, state.army.supply_ratio))
    state.crises.tongguan = _clamp(state.crises.tongguan)
    state.crises.court_conflict = _clamp(state.crises.court_conflict)
    state.crises.false_intel = _clamp(state.crises.false_intel)


def _diff(before: dict, after: dict) -> list[dict]:
    paths = [
        ("central_prestige", "皇威"),
        ("military_power", "军势"),
        ("popular_support", "民心"),
        ("intel_confidence", "情报可信"),
        ("attention", "注意力"),
    ]
    changes = []
    for key, label in paths:
        delta = after[key] - before[key]
        if delta:
            changes.append({"key": key, "label": label, "before": before[key], "after": after[key], "delta": delta})
    return changes
