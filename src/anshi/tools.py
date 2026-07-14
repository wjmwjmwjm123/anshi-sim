"""游戏盘面查询工具集。供 agent tool-use 调用。

每个工具函数返回格式化文本（不是 JSON），让模型更容易理解。
工具定义遵循 OpenAI function calling 协议。
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Callable


def build_game_tools(management, strategy, progress, campaign_data) -> list[dict[str, Any]]:
    """构建 OpenAI function calling 格式的工具定义 + 执行器。"""

    _regions = {r["id"]: r for r in campaign_data.get("regions", [])}
    _armies = {a["id"]: a for a in campaign_data.get("armies", [])}
    _characters = {c["id"]: c for c in campaign_data.get("characters", [])}

    def list_regions() -> str:
        """查看所有地区概览：名称、控制者、民心、动乱。"""
        lines = []
        for rid, region in _regions.items():
            rt = management.regions.get(rid)
            if not rt:
                continue
            lines.append(f"{region['name']}（{rid}）| 控制：{region.get('controller','?')} | 民心：{rt.support} | 动乱：{rt.unrest} | 城防：{rt.fortification}")
        return "\n".join(lines) if lines else "无地区数据。"

    def inspect_region(region_id: str) -> str:
        """查看某一地区详情。region_id 为地区英文 id（如 tongguan、luoyang）。"""
        region = _regions.get(region_id)
        rt = management.regions.get(region_id)
        if not region or not rt:
            return f"未找到地区 {region_id}。可先调 list_regions 查看可用 id。"
        return (
            f"【{region['name']}】\n"
            f"控制者：{region.get('controller', '?')}\n"
            f"民心：{rt.support}  动乱：{rt.unrest}  城防：{rt.fortification}\n"
            f"税率：{rt.tax_rate}\n"
            f"状态：{region.get('status', '?')}\n"
            f"人口：{region.get('population', {}).get('estimate_range', '?')}\n"
            f"粮储：{region.get('grain', {}).get('stock_glu', '?')}"
        )

    def list_armies() -> str:
        """查看所有军队概览：名称、驻地、兵力、补给、士气。"""
        lines = []
        for army in strategy.armies.values():
            lines.append(f"{army.name}（{army.id}）| 驻地：{army.region} | 兵力：{army.strength} | 补给：{army.supply} | 士气：{army.morale}")
        return "\n".join(lines) if lines else "无军队数据。"

    def inspect_army(army_id: str) -> str:
        """查看某支军队详情。army_id 为军队英文 id（如 tang_tongguan）。"""
        army = strategy.armies.get(army_id)
        if not army:
            return f"未找到军队 {army_id}。可先调 list_armies 查看可用 id。"
        return (
            f"【{army.name}】\n"
            f"驻地：{army.region}\n"
            f"兵力：{army.strength}  补给：{army.supply}  士气：{army.morale}\n"
            f"势力：{army.power}  状态：{army.objective}"
        )

    def check_treasury() -> str:
        """查看国库、粮储与收支状况。"""
        f = management.finance
        return (
            f"【国库】\n"
            f"现银：{f.cash}\n"
            f"粮储：{f.grain}\n"
            f"月入：{f.monthly_income}  月支：{f.monthly_expenses}\n"
            f"粮食月入：{f.monthly_grain}"
        )

    def list_characters() -> str:
        """查看在朝人物名册：姓名、官职、忠诚、能力、状态。"""
        lines = []
        for cid, ch in management.characters.items():
            if ch.status != "active":
                continue
            cdata = _characters.get(cid, {})
            lines.append(f"{ch.name}（{cid}）| {ch.office} | 忠诚：{ch.loyalty} | 能力：{ch.ability} | 状态：{ch.status}")
        return "\n".join(lines) if lines else "无在朝人物。"

    def inspect_character(character_id: str) -> str:
        """查看某人物详情。character_id 为人物英文 id（如 geshu_han）。"""
        ch = management.characters.get(character_id)
        cdata = _characters.get(character_id)
        if not ch:
            return f"未找到人物 {character_id}。可先调 list_characters 查看可用 id。"
        lines = [
            f"【{ch.name}】",
            f"官职：{ch.office}",
            f"忠诚：{ch.loyalty}  能力：{ch.ability}",
            f"状态：{ch.status}",
        ]
        if cdata:
            lines.append(f"身份：{cdata.get('identity', '?')}")
            lines.append(f"立场：{cdata.get('public_stance', '?')}")
        return "\n".join(lines)

    def list_issues() -> str:
        """查看当前在办事项：标题、紧张度、进度、承办人。"""
        lines = []
        for iid, issue in management.issues.items():
            assignee = management.characters.get(issue.assignee, None)
            assignee_name = assignee.name if assignee else "未指派"
            lines.append(f"{issue.title}（{iid}）| 紧张度：{issue.tension} | 进度：{issue.progress} | 承办：{assignee_name}")
        return "\n".join(lines) if lines else "无在办事项。"

    def list_situations() -> str:
        """查看当前局势进度：标题、状态、趋势、进度。"""
        lines = []
        for sit in progress.situations:
            if isinstance(sit, dict):
                lines.append(f"{sit.get('title','')} | {sit.get('status','')} | {sit.get('trend','')} | 进度：{sit.get('progress',0)}/100")
            else:
                lines.append(f"{getattr(sit,'title','')} | {getattr(sit,'status','')} | {getattr(sit,'trend','')} | 进度：{getattr(sit,'progress',0)}/100")
        return "\n".join(lines) if lines else "无局势数据。"

    # 工具定义（OpenAI function calling 格式）
    tool_defs = [
        {
            "type": "function",
            "function": {
                "name": "list_regions",
                "description": "查看所有地区概览：名称、控制者、民心、动乱。用于了解天下大势。",
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "inspect_region",
                "description": "查看某一地区详情。传入地区 id（如 tongguan、luoyang、suiyang）。",
                "parameters": {
                    "type": "object",
                    "properties": {"region_id": {"type": "string", "description": "地区 id，如 tongguan、luoyang"}},
                    "required": ["region_id"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "list_armies",
                "description": "查看所有军队概览：名称、驻地、兵力、补给、士气。",
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "inspect_army",
                "description": "查看某支军队详情。传入军队 id（如 tang_tongguan、tang_shuofang）。",
                "parameters": {
                    "type": "object",
                    "properties": {"army_id": {"type": "string", "description": "军队 id"}},
                    "required": ["army_id"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "check_treasury",
                "description": "查看国库、粮储与收支状况。",
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "list_characters",
                "description": "查看在朝人物名册：姓名、官职、忠诚、能力。",
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "inspect_character",
                "description": "查看某人物详情。传入人物 id（如 geshu_han、guo_ziyi）。",
                "parameters": {
                    "type": "object",
                    "properties": {"character_id": {"type": "string", "description": "人物 id"}},
                    "required": ["character_id"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "list_issues",
                "description": "查看当前在办事项：标题、紧张度、进度、承办人。",
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "list_situations",
                "description": "查看当前局势进度：标题、状态、趋势。",
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
        },
    ]

    # 工具执行器映射
    executors: dict[str, Callable[..., str]] = {
        "list_regions": lambda **_: list_regions(),
        "inspect_region": lambda region_id="", **_: inspect_region(region_id),
        "list_armies": lambda **_: list_armies(),
        "inspect_army": lambda army_id="", **_: inspect_army(army_id),
        "check_treasury": lambda **_: check_treasury(),
        "list_characters": lambda **_: list_characters(),
        "inspect_character": lambda character_id="", **_: inspect_character(character_id),
        "list_issues": lambda **_: list_issues(),
        "list_situations": lambda **_: list_situations(),
    }

    return tool_defs, executors
