from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Literal

DirectiveKind = Literal[
    "relief", "tax", "supply", "mobilize", "fortify", "investigate", "appoint", "mediate"
]


@dataclass
class QueuedDirective:
    id: int
    kind: DirectiveKind
    target: str
    amount: int = 10
    subject: str = ""


@dataclass
class FinanceState:
    cash: int = 1_000
    grain: int = 800
    monthly_income: int = 160
    monthly_expenses: int = 120
    monthly_grain: int = 100


@dataclass
class RegionState:
    name: str
    support: int
    unrest: int
    tax_rate: int
    fortification: int = 0


@dataclass
class ArmyState:
    name: str
    region: str
    strength: int
    fit_strength: int
    supply: int
    morale: int


@dataclass
class IssueState:
    title: str
    tension: int
    progress: int = 0
    status: Literal["active", "resolved"] = "active"
    assignee: str = ""


@dataclass
class CharacterState:
    name: str
    office: str
    loyalty: int
    ability: int
    status: Literal["active", "offstage"] = "active"


def _regions() -> dict[str, RegionState]:
    return {
        "guanzhong": RegionState("关中", 38, 45, 18, 35),
        "henan": RegionState("河南", 32, 58, 20, 15),
    }


def _armies() -> dict[str, ArmyState]:
    return {
        "tongguan": ArmyState("潼关军", "guanzhong", 178_000, 150_000, 72, 43),
        "shuofang": ArmyState("朔方军", "guanzhong", 55_000, 46_000, 64, 58),
    }


def _issues() -> dict[str, IssueState]:
    return {
        "refugees": IssueState("关中流民", 65, 20),
        "court_conflict": IssueState("将相不和", 80, 10),
    }


def _characters() -> dict[str, CharacterState]:
    return {
        "geshu_han": CharacterState("哥舒翰", "河西陇右节度使", 62, 78),
        "yang_guozhong": CharacterState("杨国忠", "宰相", 48, 55),
    }


@dataclass
class ManagementState:
    turn: int = 1
    finance: FinanceState = field(default_factory=FinanceState)
    regions: dict[str, RegionState] = field(default_factory=_regions)
    armies: dict[str, ArmyState] = field(default_factory=_armies)
    issues: dict[str, IssueState] = field(default_factory=_issues)
    characters: dict[str, CharacterState] = field(default_factory=_characters)
    directives: list[QueuedDirective] = field(default_factory=list)
    next_directive_id: int = 1


@dataclass
class DirectiveReport:
    directive_id: int
    kind: DirectiveKind
    accepted: bool
    headline: str
    effects: list[str] = field(default_factory=list)
    reason: str = ""


@dataclass
class Change:
    path: str
    before: int | str
    after: int | str
    delta: int | None = None


@dataclass
class ResolutionResult:
    turn: int
    reports: list[DirectiveReport]
    diff: list[Change]
    world_events: list[str] = field(default_factory=list)

    def payload(self) -> dict:
        return asdict(self)


def initial_state() -> ManagementState:
    return ManagementState()


def draft(
    state: ManagementState,
    kind: DirectiveKind,
    target: str,
    amount: int = 10,
    subject: str = "",
) -> QueuedDirective:
    if kind not in {"relief", "tax", "supply", "mobilize", "fortify", "investigate", "appoint", "mediate"}:
        raise ValueError(f"未知诏令类型：{kind}")
    if amount <= 0:
        raise ValueError("投入规模必须大于零")
    directive = QueuedDirective(state.next_directive_id, kind, target, amount, subject)
    state.next_directive_id += 1
    state.directives.append(directive)
    return directive


def remove(state: ManagementState, directive_id: int) -> bool:
    for index, directive in enumerate(state.directives):
        if directive.id == directive_id:
            state.directives.pop(index)
            return True
    return False


def resolve(state: ManagementState, act: int = 1) -> ResolutionResult:
    before = _snapshot(state)
    resolved_turn = state.turn
    state.finance.cash += state.finance.monthly_income - state.finance.monthly_expenses
    state.finance.grain += state.finance.monthly_grain - sum(army.strength // 5_000 for army in state.armies.values())

    world_events = _world_tick(state, act)
    reports = [_apply(state, directive) for directive in sorted(state.directives, key=lambda item: item.id)]
    state.directives.clear()
    state.turn += 1
    _clamp(state)
    return ResolutionResult(resolved_turn, reports, _diff(before, _snapshot(state)), world_events)


def _world_tick(state: ManagementState, act: int) -> list[str]:
    events: list[str] = []
    for army in state.armies.values():
        consumption = max(1, army.strength // 50_000)
        army.supply -= consumption
        if army.supply < 50:
            army.morale -= 2
            events.append(f"{army.name}补给不足，士气下降")
    for region in state.regions.values():
        if region.tax_rate >= 25:
            region.support -= 1
            region.unrest += 1
        if region.unrest >= 70:
            region.support -= 1
            events.append(f"{region.name}动乱高企，民心继续下滑")
    for issue in state.issues.values():
        if issue.status == "resolved":
            continue
        if issue.assignee and issue.assignee in state.characters:
            official = state.characters[issue.assignee]
            gain = max(1, official.ability // 25)
            issue.progress += gain
            issue.tension -= max(1, gain // 2)
            events.append(f"{official.name}承办“{issue.title}”，进度增加{gain}")
        else:
            issue.tension += min(3, max(1, act))
        if issue.progress >= 100 or issue.tension <= 0:
            issue.status = "resolved"
            events.append(f"“{issue.title}”已经办结")
    return events


def _apply(state: ManagementState, directive: QueuedDirective) -> DirectiveReport:
    kind, target, amount, subject = directive.kind, directive.target, directive.amount, directive.subject

    if kind in {"relief", "tax", "fortify"} and target not in state.regions:
        return _reject(directive, f"未知地区：{target}")
    if kind in {"supply", "mobilize"} and target not in state.armies:
        return _reject(directive, f"未知军队：{target}")
    if kind in {"investigate", "mediate"} and target not in state.issues:
        return _reject(directive, f"未知事项：{target}")
    if kind == "appoint" and target not in state.characters:
        return _reject(directive, f"未知人物：{target}")

    if kind == "relief":
        if not _spend(state, amount * 2, amount * 3):
            return _reject(directive, "现银或粮储不足")
        region = state.regions[target]
        region.support += amount // 2
        region.unrest -= amount // 2
        refugee_issue = "refugees" if "refugees" in state.issues else "succession_dual_court"
        if target in {"guanzhong", "changan"} and refugee_issue in state.issues:
            state.issues[refugee_issue].tension -= amount
        return _accept(directive, "开仓赈济", [f"{region.name}民心回升", "库银与储粮下降"])

    if kind == "tax":
        region = state.regions[target]
        state.finance.cash += amount * 4
        region.tax_rate += max(1, amount // 5)
        region.support -= amount // 2
        region.unrest += amount // 3
        return _accept(directive, "加征赋税", [f"增征现银 {amount * 4}", f"{region.name}民心受损"])

    if kind == "supply":
        if not _spend(state, amount * 2, amount * 4):
            return _reject(directive, "现银或粮储不足")
        army = state.armies[target]
        army.supply += amount
        army.morale += amount // 4
        return _accept(directive, "转运军粮", [f"{army.name}补给提升", "国库承担转运开支"])

    if kind == "mobilize":
        source = subject or state.armies[target].region
        if source not in state.regions:
            return _reject(directive, f"未知征发地区：{source}")
        if not _spend(state, amount * 3, amount * 2):
            return _reject(directive, "现银或粮储不足")
        army, region = state.armies[target], state.regions[source]
        raised = amount * 1_000
        army.strength += raised
        army.fit_strength += raised * 3 // 4
        region.support -= amount // 3
        region.unrest += amount // 4
        return _accept(directive, "征发兵员", [f"{army.name}增员 {raised}", f"{region.name}承受征发"])

    if kind == "fortify":
        if not _spend(state, amount * 3, 0):
            return _reject(directive, "现银不足")
        region = state.regions[target]
        region.fortification += amount
        return _accept(directive, "修筑城防", [f"{region.name}城防提升", f"支出现银 {amount * 3}"])

    if kind == "investigate":
        if subject and subject not in state.characters:
            return _reject(directive, f"未知承办人物：{subject}")
        issue = state.issues[target]
        issue.progress += amount
        issue.tension -= amount // 2
        if subject:
            issue.assignee = subject
        if issue.progress >= 100:
            issue.status = "resolved"
        return _accept(directive, "查明情形", [f"{issue.title}调查进度提升"])

    if kind == "appoint":
        if not subject:
            return _reject(directive, "必须填写授予官职")
        character = state.characters[target]
        previous = character.office
        character.office = subject
        character.loyalty += 5
        return _accept(directive, "授官任职", [f"{character.name}：{previous} -> {subject}"])

    issue = state.issues[target]  # mediate
    if subject:
        if subject not in state.characters:
            return _reject(directive, f"未知承办人物：{subject}")
        issue.assignee = subject
        state.characters[subject].loyalty += 2
    issue.tension -= amount
    issue.progress += amount // 2
    if issue.tension <= 0:
        issue.status = "resolved"
    return _accept(directive, "调停争端", [f"{issue.title}紧张度下降"])


def _spend(state: ManagementState, cash: int, grain: int) -> bool:
    if state.finance.cash < cash or state.finance.grain < grain:
        return False
    state.finance.cash -= cash
    state.finance.grain -= grain
    return True


def _accept(directive: QueuedDirective, headline: str, effects: list[str]) -> DirectiveReport:
    return DirectiveReport(directive.id, directive.kind, True, headline, effects)


def _reject(directive: QueuedDirective, reason: str) -> DirectiveReport:
    return DirectiveReport(directive.id, directive.kind, False, "旨意未行", reason=reason)


def _clamp(state: ManagementState) -> None:
    state.finance.cash = max(0, state.finance.cash)
    state.finance.grain = max(0, state.finance.grain)
    for region in state.regions.values():
        region.support = _percent(region.support)
        region.unrest = _percent(region.unrest)
        region.tax_rate = _percent(region.tax_rate)
        region.fortification = _percent(region.fortification)
    for army in state.armies.values():
        army.strength = max(0, army.strength)
        army.fit_strength = max(0, min(army.strength, army.fit_strength))
        army.supply = _percent(army.supply)
        army.morale = _percent(army.morale)
    for issue in state.issues.values():
        issue.tension = _percent(issue.tension)
        issue.progress = _percent(issue.progress)
    for character in state.characters.values():
        character.loyalty = _percent(character.loyalty)
        character.ability = _percent(character.ability)


def _percent(value: int) -> int:
    return max(0, min(100, value))


def _snapshot(state: ManagementState) -> dict:
    data = asdict(state)
    data.pop("directives")
    data.pop("next_directive_id")
    return data


def _diff(before: dict, after: dict, prefix: str = "") -> list[Change]:
    changes: list[Change] = []
    for key in before.keys() | after.keys():
        path = f"{prefix}.{key}" if prefix else key
        old, new = before.get(key), after.get(key)
        if isinstance(old, dict) and isinstance(new, dict):
            changes.extend(_diff(old, new, path))
        elif old != new:
            delta = new - old if isinstance(old, int) and isinstance(new, int) else None
            changes.append(Change(path, old, new, delta))
    return sorted(changes, key=lambda change: change.path)
