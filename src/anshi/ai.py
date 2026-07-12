from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, is_dataclass
from typing import Literal, Mapping
from urllib.request import Request, urlopen

Scene = Literal["court", "secret", "remote"]

_SCENE_PROMPTS: dict[Scene, str] = {
    "court": "你正在大唐朝堂公开奏对。措辞庄重简练，顾及君臣名分与在场诸臣，不泄露密议。",
    "secret": "你正在无人旁听的密诏召对。措辞坦率谨慎，可谈隐忧、权衡与不可公开的人事判断。",
    "remote": "你正在军镇或外州递交远奏。只能依据当地见闻，须说明消息迟滞和无法亲见中枢的限制。",
}


@dataclass(frozen=True)
class LLMConfig:
    api_key: str
    base_url: str
    model: str
    timeout: float = 20.0


def load_config(environ: Mapping[str, str] | None = None, role: str = "chat") -> LLMConfig | None:
    env = os.environ if environ is None else environ
    prefix = role.upper()
    role_key = env.get(f"{prefix}_API_KEY", "").strip()
    ark_key = env.get("ARK_API_KEY", "").strip()
    ark_model = env.get(f"{prefix}_MODEL", "").strip() or env.get("ARK_MODEL", "").strip()
    openai_key = env.get("OPENAI_API_KEY", "").strip()
    longcat_key = env.get("LONGCAT_API_KEY", "").strip()
    api_key = role_key or (ark_key if ark_model else "") or openai_key or longcat_key
    if not api_key:
        return None
    role_base = env.get(f"{prefix}_BASE_URL", "").strip()
    role_model = env.get(f"{prefix}_MODEL", "").strip()
    if role_key:
        is_ark_role = role_key.startswith("ark-")
        base_url = role_base or (env.get("ARK_BASE_URL", "").strip() if is_ark_role else env.get("OPENAI_BASE_URL", "").strip()) or (
            "https://ark.cn-beijing.volces.com/api/v3" if is_ark_role else "https://api.openai.com/v1"
        )
        model = role_model or (env.get("ARK_MODEL", "").strip() if is_ark_role else env.get("OPENAI_MODEL", "").strip()) or (
            "" if is_ark_role else "gpt-4o-mini"
        )
        if not model:
            return None
    elif ark_key and ark_model:
        base_url = role_base or env.get("ARK_BASE_URL", "").strip() or "https://ark.cn-beijing.volces.com/api/v3"
        model = ark_model
    elif openai_key:
        base_url = role_base or env.get("OPENAI_BASE_URL", "").strip() or "https://api.openai.com/v1"
        model = role_model or env.get("OPENAI_MODEL", "").strip() or "gpt-4o-mini"
    else:
        base_url = role_base or "https://api.longcat.chat/openai/v1"
        model = role_model or "LongCat-2.0"
    return LLMConfig(api_key, base_url, model)


def is_available(environ: Mapping[str, str] | None = None) -> bool:
    return load_config(environ) is not None


def chat_completion(
    messages: list[dict[str, str]],
    config: LLMConfig | None = None,
    *,
    temperature: float = 0.7,
) -> str:
    cfg = config or load_config()
    if cfg is None:
        raise RuntimeError("未配置联网模型")
    endpoint = cfg.base_url.rstrip("/")
    if not endpoint.endswith("/chat/completions"):
        endpoint += "/chat/completions"
    body = json.dumps(
        {"model": cfg.model, "messages": messages, "temperature": temperature},
        ensure_ascii=False,
    ).encode("utf-8")
    request = Request(
        endpoint,
        data=body,
        headers={"Authorization": f"Bearer {cfg.api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=cfg.timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    content = payload["choices"][0]["message"]["content"]
    if not isinstance(content, str) or not content.strip():
        raise ValueError("模型返回了空内容")
    return content.strip()


def generate_character_reply(
    character: Mapping[str, object],
    topic: str,
    scene: Scene = "court",
    context: Mapping[str, object] | None = None,
    config: LLMConfig | None = None,
    with_status: bool = False,
) -> str | tuple[str, bool]:
    if scene not in _SCENE_PROMPTS:
        raise ValueError(f"未知奏对场景：{scene}")
    fallback = _character_fallback(character, topic, scene)
    if config is None and load_config(role="chat") is None:
        return (fallback, False) if with_status else fallback
    name = str(character.get("name", "臣下"))
    identity = str(character.get("identity") or character.get("office") or "大唐臣属")
    stance = str(character.get("public_stance") or character.get("stance") or "未有定论")
    facts = _json_text(context or {})
    messages = [
        {
            "role": "system",
            "content": (
                "你是历史策略游戏中的人物扮演器，不是规则引擎。"
                "不得修改、推算或发明任何权威数值，不得替玩家下令。"
                "只用简体中文，以人物身份回答两至四句，不要输出JSON。"
                + _SCENE_PROMPTS[scene]
            ),
        },
        {
            "role": "user",
            "content": f"人物：{name}\n身份：{identity}\n公开立场：{stance}\n场景事实：{facts}\n所问：{topic.strip() or '当前最紧要之事是什么？'}",
        },
    ]
    try:
        text = chat_completion(messages, config or load_config(role="chat"))
        return (text, True) if with_status else text
    except (OSError, TimeoutError, KeyError, IndexError, TypeError, ValueError, RuntimeError, json.JSONDecodeError):
        return (fallback, False) if with_status else fallback


def generate_turn_narration(result: object, config: LLMConfig | None = None, *, with_status: bool = False) -> str | tuple[str, bool]:
    data = _plain_data(result)
    fallback = _turn_fallback(data)
    if config is None and load_config(role="simulation") is None:
        return (fallback, False) if with_status else fallback
    messages = [
        {
            "role": "system",
            "content": (
                "你是历史策略游戏的史官，只把权威回合结算改写成简体中文纪事。"
                "结构化结果中的数值、成败、因果均已锁定；不得修改、补算、遗漏或新增数值，"
                "不得生成新的游戏效果。写三至六句，不要输出JSON。"
            ),
        },
        {"role": "user", "content": "权威回合结算（只读）：\n" + _json_text(data)},
    ]
    try:
        text = chat_completion(messages, config or load_config(role="simulation"), temperature=0.4)
        return (text, True) if with_status else text
    except (OSError, TimeoutError, KeyError, IndexError, TypeError, ValueError, RuntimeError, json.JSONDecodeError):
        return (fallback, False) if with_status else fallback


def polish_document(text: str, config: LLMConfig | None = None) -> tuple[str, bool]:
    source = text.strip()
    if not source:
        return "", False
    cfg = config or load_config(role="utility")
    if cfg is None:
        return source, False
    messages = [
        {"role": "system", "content": "你是唐廷中书舍人。将皇帝口谕润色为简体中文诏书，保留所有人名、数值、对象与行动，不添加新命令，不输出解释。限一百五十字。"},
        {"role": "user", "content": source},
    ]
    try:
        return chat_completion(messages, cfg, temperature=0.3), True
    except (OSError, TimeoutError, KeyError, IndexError, TypeError, ValueError, RuntimeError, json.JSONDecodeError):
        return source, False


def generate_decree_candidates(text: str, targets: Mapping[str, object], config: LLMConfig | None = None) -> tuple[list[dict[str, object]], bool]:
    cfg = config or load_config(role="utility")
    if cfg is None:
        return [], False
    messages = [
        {
            "role": "system",
            "content": (
                "你是唐廷中书省的诏令结构化助手。把皇帝自由诏书拆成可执行事项，只输出JSON对象："
                "{candidates:[{kind,target,amount,subject,reason}]}。kind只能是 relief、tax、supply、mobilize、"
                "fortify、investigate、appoint、mediate；target必须从用户提供的对应目标ID中选择；amount为1到100。"
                "不得发明目标，不得添加诏书中没有的命令。无法执行的句子不要强行映射。"
            ),
        },
        {"role": "user", "content": "可用目标：" + _json_text(targets) + "\n诏书：" + text.strip()},
    ]
    try:
        raw = chat_completion(messages, cfg, temperature=0.2)
        start, end = raw.find("{"), raw.rfind("}")
        payload = json.loads(raw[start : end + 1]) if start >= 0 and end > start else {}
        candidates = payload.get("candidates", []) if isinstance(payload, dict) else []
        return (candidates, True) if isinstance(candidates, list) else ([], False)
    except (OSError, TimeoutError, KeyError, IndexError, TypeError, ValueError, RuntimeError, json.JSONDecodeError):
        return [], False
def generate_world_proposal(context: Mapping[str, object], config: LLMConfig | None = None) -> tuple[dict[str, object], bool]:
    cfg = config or load_config(role="simulation")
    empty = {"assessment": "", "proposals": [], "situations": [], "npc_actions": [], "event_seeds": []}
    if cfg is None:
        return empty, False
    messages = [
        {
            "role": "system",
            "content": (
                "你是历史策略游戏的受约束世界裁判。硬规则已经完成兵力、钱粮、路线和战斗结算。"
                "你只提出软世界反应，不得改写硬结算。只输出一个JSON对象，不要代码围栏。"
                "格式：{assessment:string,proposals:[{path:string,operation:'add',value:number,reason:string,confidence:number}],"
                "situations:[{id:string,delta:number,reason:string,confidence:number}],"
                "npc_actions:[{actor:string,intent:string}],event_seeds:[string]}。"
                "允许路径仅为 regions.<id>.support/unrest/fortification、armies.<id>.morale/supply、"
                "issues.<id>.tension/progress、characters.<id>.loyalty。situations 的 id 必须来自当前上下文，"
                "delta 只能表达本回合局势向好或恶化的方向，不得直接完成局势。每项变化应克制并有明确因果。"
            ),
        },
        {"role": "user", "content": "当前回合权威上下文：\n" + _json_text(context)},
    ]
    try:
        text = chat_completion(messages, cfg, temperature=0.45)
        start, end = text.find("{"), text.rfind("}")
        if start < 0 or end <= start:
            return empty, False
        payload = json.loads(text[start : end + 1])
        return (payload, True) if isinstance(payload, dict) else (empty, False)
    except (OSError, TimeoutError, KeyError, IndexError, TypeError, ValueError, RuntimeError, json.JSONDecodeError):
        return empty, False
def _plain_data(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return asdict(value)
    if hasattr(value, "payload") and callable(value.payload):
        return value.payload()
    return value


def _json_text(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), default=str)


def _character_fallback(character: Mapping[str, object], topic: str, scene: Scene) -> str:
    name = str(character.get("name", "臣下"))
    stance = str(character.get("public_stance") or character.get("stance") or "此事尚须细察")
    question = topic.strip() or "当前局势"
    if scene == "secret":
        return f"{name}低声奏道：此事不可只看明面。臣以为{stance}，还请陛下就“{question}”密定底线与追责之期。"
    if scene == "remote":
        return f"{name}远奏：臣身在外镇，所得消息恐有迟滞。就“{question}”而言，臣所见是{stance}，请中枢另以驿报复核。"
    return f"{name}当殿奏道：臣以为{stance}。至于“{question}”，请先明军令、钱粮与承办之责，再议施行。"


def _turn_fallback(data: object) -> str:
    if not isinstance(data, Mapping):
        return "本回合已依既定规则结算，史官将结果录入实录。"
    turn = data.get("turn")
    reports = data.get("reports")
    if isinstance(reports, list):
        accepted = sum(bool(item.get("accepted")) for item in reports if isinstance(item, Mapping))
        rejected = sum(not bool(item.get("accepted")) for item in reports if isinstance(item, Mapping))
        prefix = f"第{turn}回合" if turn is not None else "本回合"
        return f"{prefix}结算完毕：施行诏令{accepted}道，留中或未行{rejected}道。钱粮、军务与地方变化均已依规则写入实录。"
    headline = data.get("headline", "本回合结算完毕")
    narrative = data.get("narrative", "结果已依既定规则写入实录。")
    return f"{headline}。{narrative}"
