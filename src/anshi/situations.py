"""Bounded situation progress and empire modifiers.

The simulation model may suggest a direction, but this module owns the final
clamp, completion/failure transition, and reward/penalty application.
"""
from __future__ import annotations

from typing import Any


SITUATION_IDS = {"tongguan_command", "guanzhong_supply", "hebei_resistance"}

POLICIES: list[dict[str, Any]] = [
    # ── 中枢整饬 ──
    {"id": "unify_command", "branch": "中枢整饬", "title": "整饬军令体系", "requires": [], "effects": {"command": 10, "prestige": 3}},
    {"id": "repair_post_roads", "branch": "中枢整饬", "title": "重建驿传", "requires": [], "effects": {"command": 6, "intel": 5}},
    {"id": "restrain_eunuchs", "branch": "中枢整饬", "title": "裁抑近习干政", "requires": ["unify_command"], "effects": {"command": 8, "prestige": 5}},
    {"id": "rebuild_censorate", "branch": "中枢整饬", "title": "重整御史台", "requires": ["restrain_eunuchs"], "effects": {"prestige": 8, "command": 4}},
    {"id": "court_reform", "branch": "中枢整饬", "title": "三省合议改制", "requires": ["rebuild_censorate"], "effects": {"prestige": 10, "income": 5}},
    # ── 军镇经略 ──
    {"id": "reinforce_tongguan", "branch": "军镇经略", "title": "加强潼关防务", "requires": [], "effects": {"fortification": 8, "morale": 3}},
    {"id": "shuofang_recruit", "branch": "军镇经略", "title": "朔方整军募骑", "requires": ["reinforce_tongguan"], "effects": {"mobilize": 12}},
    {"id": "hexi_defense", "branch": "军镇经略", "title": "河西走廊防务", "requires": ["shuofang_recruit"], "effects": {"western": -12, "prestige": 3}},
    {"id": "naval_jianghuai", "branch": "军镇经略", "title": "江淮水师操练", "requires": [], "effects": {"grain_safety": 15, "income": 4}},
    {"id": "imperial_guard", "branch": "军镇经略", "title": "重建禁军六军", "requires": ["shuofang_recruit", "naval_jianghuai"], "effects": {"prestige": 12, "morale": 5}},
    # ── 河朔联络 ──
    {"id": "contact_resistance", "branch": "河朔联络", "title": "联络河北义军", "requires": [], "effects": {"resistance": 12, "support": 3}},
    {"id": "divide_yan", "branch": "河朔联络", "title": "离间燕廷诸将", "requires": ["contact_resistance"], "effects": {"resistance": 16}},
    {"id": "recruit_hebei", "branch": "河朔联络", "title": "河北招抚流亡", "requires": ["contact_resistance"], "effects": {"support": 8, "recruit": 3000}},
    {"id": "heshuo_negotiate", "branch": "河朔联络", "title": "藩镇羁縻之策", "requires": ["divide_yan"], "effects": {"autonomy": 15, "income": 8}},
    {"id": "rebellion_pardon", "branch": "河朔联络", "title": "颁诏赦降纳顺", "requires": ["heshuo_negotiate"], "effects": {"resistance": 20, "support": 5}},
    # ── 财赋民生 ──
    {"id": "secure_grain_route", "branch": "财赋民生", "title": "保全江淮漕运", "requires": [], "effects": {"grain": 14}},
    {"id": "relieve_guanzhong", "branch": "财赋民生", "title": "关中军民赈济", "requires": ["secure_grain_route"], "effects": {"grain": 10, "support": 5}},
    {"id": "land_survey", "branch": "财赋民生", "title": "清丈关陇田亩", "requires": ["relieve_guanzhong"], "effects": {"income": 12, "gentry_resistance": 10}},
    {"id": "salt_tax_reform", "branch": "财赋民生", "title": "盐铁专卖整顿", "requires": [], "effects": {"income": 18}},
    {"id": "trade_silk_road", "branch": "财赋民生", "title": "重开丝路商道", "requires": ["hexi_defense", "salt_tax_reform"], "effects": {"income": 25}},
]


def policy_catalog(progress: Any) -> list[dict[str, Any]]:
    completed = set(progress.completed_policies)
    return [{**item, "completed": item["id"] in completed, "available": all(req in completed for req in item["requires"]), "selected": progress.active_policy == item["id"]} for item in POLICIES]


def select_policy(progress: Any, policy_id: str) -> dict[str, Any]:
    item = next((item for item in POLICIES if item["id"] == policy_id), None)
    if item is None:
        raise ValueError("未知国策")
    if item["id"] in progress.completed_policies:
        raise ValueError("该国策已经完成")
    if not all(req in progress.completed_policies for req in item["requires"]):
        raise ValueError("前置国策尚未完成")
    if progress.active_policy:
        raise ValueError("本回合已有一项国策在施行")
    if progress.policy_last_turn == progress.total_turn:
        raise ValueError("本回合已经选择过国策")
    progress.active_policy = policy_id
    progress.policy_last_turn = progress.total_turn
    return item


def resolve_policy(progress: Any, state: Any, management: Any) -> list[str]:
    if not progress.active_policy:
        return []
    item = next((item for item in POLICIES if item["id"] == progress.active_policy), None)
    progress.active_policy = ""
    if item is None:
        return []
    effects = item["effects"]
    events: list[str] = []
    pid = item["id"]

    # ── 中枢效果 ──
    if effects.get("command"):
        state.central_prestige = min(100, state.central_prestige + 1 + effects["command"] // 10)
        issue = management.issues.get("court_conflict") or management.issues.get("succession_dual_court")
        if issue:
            issue.tension = max(0, issue.tension - effects["command"] // 2)
        _advance(progress, "tongguan_command", effects["command"], f"国策[{item['title']}]整肃军令体系")
    if effects.get("prestige"):
        state.central_prestige = min(100, state.central_prestige + effects["prestige"])
    if effects.get("intel"):
        state.intel_confidence = min(100, state.intel_confidence + effects["intel"])

    # ── 军镇效果 ──
    if effects.get("fortification"):
        region = management.regions.get("tongguan") or next(iter(management.regions.values()), None)
        if region:
            region.fortification += effects["fortification"]
        if management.finance.cash >= 60:
            management.finance.cash -= 60
        events.append("国策生效：潼关城防加固")
    if effects.get("morale"):
        for army in management.armies.values():
            army.morale += effects["morale"]
        state.military_power = min(100, state.military_power + 3)
    if effects.get("mobilize"):
        army = management.armies.get("tang_shuofang") or management.armies.get("shuofang")
        if army:
            raised = effects["mobilize"] * 500
            army.strength += raised
            army.fit_strength += raised
        management.finance.cash = max(0, management.finance.cash - 80)
        state.military_power = min(100, state.military_power + 4)
        events.append("国策生效：朔方募骑完成")
    if effects.get("western"):
        progress.obligations["西陲空虚"] = max(0, progress.obligations.get("西陲空虚", 30) + effects["western"])
        events.append("国策生效：西陲防线得到巩固")
    if effects.get("grain_safety"):
        management.finance.monthly_grain += 5

    # ── 河朔效果 ──
    if effects.get("resistance"):
        for key in ("pingyuan", "changshan"):
            region = management.regions.get(key)
            if region:
                region.support += min(3, effects["resistance"] // 5)
        issue = management.issues.get("frontier_autonomy_debt")
        if issue:
            issue.tension = max(0, issue.tension - effects["resistance"] // 3)
        _advance(progress, "hebei_resistance", effects["resistance"], f"国策[{item['title']}]联络河北")
        events.append("国策生效：河朔抵抗态势改善")
    if effects.get("support"):
        state.popular_support = min(100, state.popular_support + effects["support"])
        for region in management.regions.values():
            region.support = min(100, region.support + 1)
    if effects.get("recruit"):
        army = next(iter(management.armies.values()), None)
        if army:
            army.strength += effects["recruit"]
            army.fit_strength += effects["recruit"]
    if effects.get("autonomy"):
        progress.obligations["藩镇自主"] = progress.obligations.get("藩镇自主", 20) + effects["autonomy"]

    # ── 财赋效果 ──
    if effects.get("grain"):
        if pid == "secure_grain_route":
            management.finance.monthly_grain += 15
            management.finance.monthly_income += 8
            management.finance.cash = max(0, management.finance.cash - 70)
        elif pid == "relieve_guanzhong":
            management.finance.grain = max(0, management.finance.grain - 80)
        _advance(progress, "guanzhong_supply", effects["grain"], f"国策[{item['title']}]维系粮道")
        events.append("国策生效：粮道得到加强")
    if effects.get("income"):
        management.finance.monthly_income += effects["income"]
    if effects.get("gentry_resistance"):
        for region in management.regions.values():
            region.unrest = min(100, region.unrest + 2)

    progress.completed_policies.append(item["id"])
    progress.modifiers.append({
        "id": item["id"], "name": item["title"],
        "description": f"国策[{item['title']}]写入帝国修正", "effects": effects,
        "source": "国策", "applied_turn": progress.total_turn,
    })
    events.append(f"帝国修正生效：{item['title']}")
    return events


def advance_situations(progress: Any, state: Any, management: Any, updates: list[dict[str, Any]] | None = None) -> list[str]:
    updates_by_id = {str(item.get("id")): item for item in (updates or []) if isinstance(item, dict)}
    events: list[str] = []
    for situation in progress.situations:
        if situation.get("status") != "进行中":
            continue
        item = updates_by_id.get(situation["id"])
        if item is not None:
            try:
                delta = max(-12, min(12, int(round(float(item.get("delta", 0))))))
                confidence = float(item.get("confidence", 0))
            except (TypeError, ValueError):
                delta = 0
                confidence = 0
            if confidence < 0.35:
                delta = 0
            reason = str(item.get("reason", "推演模型综合判断"))[:120]
        else:
            delta, reason = _fallback_delta(situation["id"], state, management)
        before = situation["progress"]
        situation["progress"] = max(0, min(100, before + delta))
        situation["trend"] = "向好" if delta > 2 else "恶化" if delta < -2 else "摇摆"
        situation["last_reason"] = reason
        if delta:
            events.append(f"局势推进：{situation['title']} {before}→{situation['progress']}（{reason}）")
        if situation["progress"] >= 100:
            situation["status"] = "已完成"
            modifier = _outcome_modifier(situation["id"], True, progress.total_turn)
            progress.modifiers.append(modifier)
            _apply_outcome(modifier, state, management)
            events.append(f"局势完成：{situation['title']}；{modifier['name']}生效")
        elif situation["progress"] <= 0:
            situation["status"] = "已崩坏"
            modifier = _outcome_modifier(situation["id"], False, progress.total_turn)
            progress.modifiers.append(modifier)
            _apply_outcome(modifier, state, management)
            events.append(f"局势崩坏：{situation['title']}；{modifier['name']}生效")
    return events


def _advance(progress: Any, situation_id: str, delta: int, reason: str) -> None:
    for item in progress.situations:
        if item["id"] == situation_id and item.get("status") == "进行中":
            item["progress"] = max(0, min(100, item["progress"] + delta))
            item["trend"] = "向好" if delta > 0 else "恶化"
            item["last_reason"] = reason


def _fallback_delta(situation_id: str, state: Any, management: Any) -> tuple[int, str]:
    if situation_id == "tongguan_command":
        score = (100 - state.crises.court_conflict) + state.army.cohesion + state.intel_confidence
        return (2 if score >= 130 else -2 if score < 80 else 0, "军令冲突、凝聚力与情报可信度综合判断")
    if situation_id == "guanzhong_supply":
        finance = management.finance
        return (2 if finance.grain >= 700 else -2 if finance.grain < 350 else 0, "中央粮储与月度粮入综合判断")
    support = sum(region.support for region in management.regions.values()) // max(1, len(management.regions))
    return (2 if support >= 60 else -2 if support < 35 else 0, "河朔与关东地区民心综合判断")


def _outcome_modifier(situation_id: str, success: bool, turn: int) -> dict[str, Any]:
    names = {
        ("tongguan_command", True): ("军令一体", "军令完成整肃，军势与皇威上升"),
        ("tongguan_command", False): ("军令崩坏", "中枢与行营互不相从，军势下降"),
        ("guanzhong_supply", True): ("漕运畅通", "粮道稳定，民心与月度粮入上升"),
        ("guanzhong_supply", False): ("粮道断裂", "关中粮运告急，民心与财政收入下降"),
        ("hebei_resistance", True): ("河朔响应", "义军与州郡愿意继续抗燕"),
        ("hebei_resistance", False): ("河朔离心", "河北州郡转向观望或自保"),
    }
    name, description = names[(situation_id, success)]
    return {"id": f"situation:{situation_id}:{'success' if success else 'failure'}", "name": name, "description": description, "effects": {"situation": situation_id, "success": success}, "source": "局势进度", "applied_turn": turn}


def _apply_outcome(modifier: dict[str, Any], state: Any, management: Any) -> None:
    situation = modifier["effects"]["situation"]
    success = modifier["effects"]["success"]
    sign = 1 if success else -1
    if situation == "tongguan_command":
        state.central_prestige = max(0, min(100, state.central_prestige + 5 * sign))
        state.military_power = max(0, min(100, state.military_power + 8 * sign))
        for army in management.armies.values():
            army.morale += 4 * sign
    elif situation == "guanzhong_supply":
        state.popular_support = max(0, min(100, state.popular_support + 5 * sign))
        management.finance.monthly_grain = max(0, management.finance.monthly_grain + 20 * sign)
        management.finance.monthly_income = max(0, management.finance.monthly_income + 10 * sign)
    else:
        state.popular_support = max(0, min(100, state.popular_support + 4 * sign))
        issue = management.issues.get("frontier_autonomy_debt")
        if issue:
            issue.tension = max(0, min(100, issue.tension - 10 * sign))
