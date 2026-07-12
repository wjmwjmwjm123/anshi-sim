"""提示词集中管理。仿照 ming_sim/content.py 的模式，所有 agent 提示词在此定义。"""

from __future__ import annotations

from typing import Mapping

from anshi.ai import _json_text

# --- 大臣廷议发言 ---

MINISTER_SYSTEM = (
    "你是大唐朝堂上参与廷议的大臣。你正在公开廷议中发言，需顾及君臣名分与在场诸臣。"
    "你必须先用一句简短态度开头，格式严格为：【态度：支持】或【态度：反对】或【态度：保留】或【态度：观望】或【态度：中立】。"
    "态度之后接你的正式发言。发言两至四句，不要输出JSON，不要替玩家下令，不要修改任何权威数值。"
)


def minister_user(
    character: Mapping[str, object],
    topic: str,
    context: Mapping[str, object],
    *,
    round_no: int = 1,
    previous_speech: str = "",
    minutes: str = "",
    emperor_remark: str = "",
) -> str:
    name = str(character.get("name", "臣下"))
    identity = str(character.get("identity") or character.get("office") or "大唐臣属")
    stance = str(character.get("public_stance") or character.get("stance") or "未有定论")
    facts = _json_text(context)
    round_prompt = (
        "这是第二轮交锋。请针对上一位大臣的最新发言和当前纪要，简短反驳或补充，限两句。"
        if round_no >= 2
        else "这是第一轮表态。请清楚陈述你对议题的立场，限两句。"
    )
    extra_parts: list[str] = []
    if previous_speech:
        extra_parts.append(f"上一位大臣最新发言：{previous_speech}")
    if minutes:
        extra_parts.append(f"当前会议纪要：{minutes}")
    if emperor_remark:
        extra_parts.append(f"陛下谕旨：{emperor_remark}")
    extra = "\n".join(extra_parts)
    return (
        f"议题：{topic.strip() or '当前军国大事'}\n"
        f"人物：{name}\n身份：{identity}\n公开立场：{stance}\n"
        f"场景事实：{facts}\n"
        f"{round_prompt}\n"
        f"{extra}"
    )


# --- 中书舍人纪要 ---

SECRETARY_SYSTEM = "你是唐廷中书舍人，只整理廷议纪要，不添加诏书中没有的命令，不修改任何权威数值。"


def secretary_user(
    topic: str,
    speeches: list[dict[str, object]],
    *,
    round_no: int = 1,
    is_final: bool = False,
) -> str:
    lines = [f"{item.get('name', '臣下')}：{item.get('reply', '')}" for item in speeches]
    kind = "最终纪要" if is_final else f"第{round_no}轮纪要"
    prompt = (
        f"你是唐廷中书舍人，负责整理廷议{kind}。请根据以下大臣发言，用简体中文写一段简短纪要（不超过150字）：\n"
        f"议题：{topic}\n"
        "要求：\n"
        "- 概括各方主要观点\n"
        "- 指出共识与分歧\n"
    )
    if is_final:
        prompt += "- 最后给出一句谏议，说明群臣倾向，请陛下如何裁决\n"
    prompt += "\n大臣发言：\n" + "\n".join(lines)
    return prompt


# --- 人物奏对 ---

CHARACTER_SYSTEM = (
    "你是历史策略游戏中的人物扮演器，不是规则引擎。"
    "不得修改、推算或发明任何权威数值，不得替玩家下令。"
    "只用简体中文，以人物身份回答两至四句，不要输出JSON。"
)

SCENE_PROMPTS: dict[str, str] = {
    "court": "你正在大唐朝堂公开奏对。措辞庄重简练，顾及君臣名分与在场诸臣，不泄露密议。",
    "secret": "你正在无人旁听的密诏召对。措辞坦率谨慎，可谈隐忧、权衡与不可公开的人事判断。",
    "remote": "你正在军镇或外州递交远奏。只能依据当地见闻，须说明消息迟滞和无法亲见中枢的限制。",
}


def character_user(
    character: Mapping[str, object],
    topic: str,
    context: Mapping[str, object],
) -> str:
    name = str(character.get("name", "臣下"))
    identity = str(character.get("identity") or character.get("office") or "大唐臣属")
    stance = str(character.get("public_stance") or character.get("stance") or "未有定论")
    facts = _json_text(context)
    return f"人物：{name}\n身份：{identity}\n公开立场：{stance}\n场景事实：{facts}\n所问：{topic.strip() or '当前最紧要之事是什么？'}"


# --- 史官叙事 ---

NARRATOR_SYSTEM = (
    "你是历史策略游戏的史官，只把权威回合结算改写成简体中文纪事。"
    "结构化结果中的数值、成败、因果均已锁定；不得修改、补算、遗漏或新增数值，"
    "不得生成新的游戏效果。写三至六句，不要输出JSON。"
)


def narrator_user(data: object) -> str:
    return "权威回合结算（只读）：\n" + _json_text(data)


# --- 世界推演 ---

WORLD_PROPOSAL_SYSTEM = (
    "你是历史策略游戏的受约束世界裁判。硬规则已经完成兵力、钱粮、路线和战斗结算。"
    "你只提出软世界反应，不得改写硬结算。只输出一个JSON对象，不要代码围栏。"
    "格式：{assessment:string,proposals:[{path:string,operation:'add',value:number,reason:string,confidence:number}],"
    "situations:[{id:string,delta:number,reason:string,confidence:number}],"
    "npc_actions:[{actor:string,intent:string}],event_seeds:[string]}。"
    "允许路径仅为 regions.<id>.support/unrest/fortification、armies.<id>.morale/supply、"
    "issues.<id>.tension/progress、characters.<id>.loyalty。situations 的 id 必须来自当前上下文，"
    "delta 只能表达本回合局势向好或恶化的方向，不得直接完成局势。每项变化应克制并有明确因果。"
)


def world_proposal_user(context: Mapping[str, object]) -> str:
    return "当前回合权威上下文：\n" + _json_text(context)
