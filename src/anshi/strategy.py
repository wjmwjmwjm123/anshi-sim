from __future__ import annotations

from dataclasses import asdict, dataclass, field

REGION_NAMES = {
    "changan": "长安", "tongguan": "潼关", "lingbao": "灵宝", "shanjun": "陕郡",
    "luoyang": "洛阳", "hedong": "河东", "fanyang": "范阳", "changshan": "常山",
    "pingyuan": "平原", "suiyang": "睢阳", "yangzhou": "扬州", "shuofang": "朔方",
    "hexi": "河西", "longyou": "陇右", "jiannan": "剑南", "mawei": "马嵬",
}


def _cn(region_id: str) -> str:
    return REGION_NAMES.get(region_id, region_id)


@dataclass
class FieldArmy:
    id: str
    name: str
    power: str
    region: str
    strength: int
    supply: int
    morale: int
    objective: str = "据守"


@dataclass
class Siege:
    region: str
    attacker: str
    defender: str
    progress: int = 0
    status: str = "围攻中"


@dataclass
class ArmyMovement:
    army_id: str
    destination: str


@dataclass
class StrategyState:
    armies: dict[str, FieldArmy] = field(default_factory=dict)
    sieges: list[Siege] = field(default_factory=list)
    battle_log: list[str] = field(default_factory=list)
    pending_movements: list[ArmyMovement] = field(default_factory=list)


ROUTES = {
    "changan": ["tongguan", "mawei"], "mawei": ["changan", "jiannan"],
    "tongguan": ["changan", "lingbao"], "lingbao": ["tongguan", "shanjun"],
    "shanjun": ["lingbao", "luoyang"], "luoyang": ["shanjun", "hedong", "suiyang"],
    "hedong": ["luoyang", "fanyang", "shuofang"], "fanyang": ["hedong", "changshan"],
    "changshan": ["fanyang", "pingyuan"], "pingyuan": ["changshan", "suiyang"],
    "suiyang": ["pingyuan", "luoyang", "yangzhou"], "yangzhou": ["suiyang"],
    "shuofang": ["hedong", "hexi"], "hexi": ["shuofang", "longyou"],
    "longyou": ["hexi", "jiannan"], "jiannan": ["longyou", "mawei"],
}


def initial_strategy(catalog: dict) -> StrategyState:
    state = StrategyState()
    for item in catalog["armies"]:
        if item["act_from"] == 1:
            state.armies[item["id"]] = FieldArmy(item["id"], item["name"], item["power"], item["region"], item["present_strength"], item["supply"], item["morale"], item["status"])
    return state


def move(state: StrategyState, army_id: str, destination: str) -> dict:
    army = state.armies.get(army_id)
    if not army:
        raise ValueError("未找到该军队")
    if destination not in ROUTES.get(army.region, []):
        raise ValueError("目的地与当前驻地不相邻")
    origin = army.region
    army.region = destination
    army.supply = max(0, army.supply - 5)
    army.objective = f"进驻{_cn(destination)}"
    return {"army": army_id, "from": _cn(origin), "to": _cn(destination), "supply": -5}


def queue_move(state: StrategyState, army_id: str, destination: str) -> dict:
    army = state.armies.get(army_id)
    if not army:
        raise ValueError("未找到该军队")
    if not army.power.startswith("tang"):
        raise ValueError("不能向敌军下达调动军令")
    if destination not in ROUTES.get(army.region, []):
        raise ValueError("目的地与当前驻地不相邻")
    state.pending_movements = [item for item in state.pending_movements if item.army_id != army_id]
    state.pending_movements.append(ArmyMovement(army_id, destination))
    return {"army": army_id, "from": army.region, "to": destination, "queued": True}


def resolve_movements(state: StrategyState) -> list[str]:
    pending = state.pending_movements
    state.pending_movements = []
    events: list[str] = []
    for order in pending:
        army = state.armies.get(order.army_id)
        name = army.name if army else order.army_id
        try:
            result = move(state, order.army_id, order.destination)
            events.append(f"{name}奉诏由{_cn(result['from'])}调往{_cn(result['to'])}，行军耗粮5")
        except ValueError as error:
            events.append(f"{name}调动军令未能执行：{error}")
    return events


def simulate_month(state: StrategyState, act: int, seed: int) -> list[str]:
    events: list[str] = []
    for army in state.armies.values():
        army.supply = max(0, army.supply - max(1, army.strength // 60_000))
        if army.supply < 35:
            army.morale = max(0, army.morale - 3)
    for army in sorted(state.armies.values(), key=lambda item: item.id):
        if not army.power.startswith("yan"):
            continue
        destination = _enemy_destination(army.region, act, seed + len(events))
        if destination and destination in ROUTES.get(army.region, []):
            origin = army.region
            army.region = destination
            army.supply = max(0, army.supply - 4)
            events.append(f"{army.name}由{_cn(origin)}向{_cn(destination)}推进")
    events.extend(_resolve_battles(state, seed))
    events.extend(_resolve_sieges(state))
    state.battle_log = (events + state.battle_log)[:60]
    return events


def _enemy_destination(region: str, act: int, seed: int) -> str:
    goals = {
        1: {"luoyang": "shanjun", "shanjun": "lingbao", "fanyang": "hedong"},
        2: {"lingbao": "tongguan", "tongguan": "changan", "hedong": "shuofang"},
        3: {"luoyang": "suiyang", "fanyang": "hedong"},
        4: {"fanyang": "hedong", "hedong": "luoyang"},
        5: {"luoyang": "hedong", "hedong": "fanyang"},
    }
    return goals.get(act, {}).get(region, "") if seed % 3 else ""


def _resolve_battles(state: StrategyState, seed: int) -> list[str]:
    events = []
    by_region: dict[str, list[FieldArmy]] = {}
    for army in state.armies.values():
        by_region.setdefault(army.region, []).append(army)
    for region, armies in by_region.items():
        tang = [army for army in armies if army.power.startswith("tang")]
        yan = [army for army in armies if army.power.startswith("yan")]
        if not tang or not yan:
            continue
        tang_power = sum(army.strength * max(20, army.morale) * max(20, army.supply) for army in tang)
        yan_power = sum(army.strength * max(20, army.morale) * max(20, army.supply) for army in yan)
        tang_loss = min(sum(a.strength for a in tang) // 3, max(500, yan_power // 2_000_000))
        yan_loss = min(sum(a.strength for a in yan) // 3, max(500, tang_power // 2_000_000))
        _spread_loss(tang, tang_loss)
        _spread_loss(yan, yan_loss)
        victor = "唐军" if tang_power + seed % 1000 >= yan_power else "燕军"
        events.append(f"{_cn(region)}发生会战：唐军损失{tang_loss}，燕军损失{yan_loss}，{victor}占优")
    return events


def _resolve_sieges(state: StrategyState) -> list[str]:
    events = []
    for siege in state.sieges:
        if siege.status != "围攻中":
            continue
        siege.progress = min(100, siege.progress + 15)
        if siege.progress >= 100:
            siege.status = "城破"
            events.append(f"{_cn(siege.region)}围城结束：守城体系崩溃")
        else:
            events.append(f"{_cn(siege.region)}围城进度达到{siege.progress}%")
    return events


def _spread_loss(armies: list[FieldArmy], loss: int) -> None:
    total = max(1, sum(army.strength for army in armies))
    for army in armies:
        army.strength = max(0, army.strength - loss * army.strength // total)
        army.morale = max(0, army.morale - 4)


def payload(state: StrategyState) -> dict:
    return asdict(state)
