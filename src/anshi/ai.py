from __future__ import annotations

import json
import os
import re
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
    advanced_model: str = ""
    advanced_base_url: str = ""
    advanced_api_key: str = ""


# 推演/打分角色走 advanced model，其余走 main model。
_ADVANCED_ROLES = frozenset({"simulator", "extractor"})


def for_role(cfg: LLMConfig, role: str) -> LLMConfig:
    """按 agent 角色派生 LLMConfig：advanced 角色用 advanced_model（若已配），其余用 main model。"""
    if role in _ADVANCED_ROLES and cfg.advanced_model:
        return LLMConfig(
            api_key=cfg.advanced_api_key or cfg.api_key,
            base_url=cfg.advanced_base_url or cfg.base_url,
            model=cfg.advanced_model,
            timeout=cfg.timeout,
            advanced_model=cfg.advanced_model,
            advanced_base_url=cfg.advanced_base_url,
            advanced_api_key=cfg.advanced_api_key,
        )
    return cfg


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
        base_url = role_base or "https://api.xiaomimimo.com/v1"
        model = role_model or "mimo-v2.5"
    adv_model = env.get("ADVANCED_MODEL", "").strip()
    adv_base = env.get("ADVANCED_BASE_URL", "").strip()
    adv_key = env.get("ADVANCED_API_KEY", "").strip()
    return LLMConfig(
        api_key, base_url, model,
        advanced_model=adv_model,
        advanced_base_url=adv_base,
        advanced_api_key=adv_key,
    )


def is_available(environ: Mapping[str, str] | None = None) -> bool:
    return load_config(environ) is not None


def fail_if_llm_error(text: str, stage: str) -> None:
    """检测 LLM 返回中的认证/接口错误，直接报错而非静默 fallback。"""
    lowered = text.lower()
    markers = ("incorrect api key", "invalid_api_key", "error code: 401", "unauthorized", "authentication")
    if any(m in lowered for m in markers):
        raise RuntimeError(f"{stage} 失败：LLM 认证或接口错误。请检查 .env 里的 API_KEY / BASE_URL / MODEL。")


def _endpoint(cfg: LLMConfig) -> str:
    ep = cfg.base_url.rstrip("/")
    if not ep.endswith("/chat/completions"):
        ep += "/chat/completions"
    return ep


# --- 供应商适配 ---

_PROVIDER_EXTRA: dict[str, dict] = {
    "deepseek": {"thinking": {"type": "disabled"}},
    "dashscope": {"enable_thinking": False},
    "aliyuncs": {"enable_thinking": False},
    "minimax": {"thinking": {"type": "disabled"}},
}


def provider_extra_body(base_url: str) -> dict | None:
    """根据 base_url 自动注入供应商特定参数（如关思考模式）。"""
    lowered = base_url.lower()
    for key, extra in _PROVIDER_EXTRA.items():
        if key in lowered:
            return dict(extra)
    return None


def chat_completion(
    messages: list[dict[str, str]],
    config: LLMConfig | None = None,
    *,
    temperature: float = 0.7,
    tag: str = "",
) -> str:
    cfg = config or load_config()
    if cfg is None:
        raise RuntimeError("未配置联网模型")
    payload: dict = {"model": cfg.model, "messages": messages, "temperature": temperature}
    extra = provider_extra_body(cfg.base_url)
    if extra:
        payload["extra_body"] = extra
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = Request(
        _endpoint(cfg),
        data=body,
        headers={"Authorization": f"Bearer {cfg.api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=cfg.timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    content = payload["choices"][0]["message"]["content"]
    if not isinstance(content, str) or not content.strip():
        raise ValueError("模型返回了空内容")
    # token 记账
    usage = payload.get("usage")
    if isinstance(usage, dict):
        from anshi.token_stats import record as record_token
        record_token(cfg.model, usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0), tag=tag)
    return content.strip()


def stream_chat_completion(
    messages: list[dict[str, str]],
    config: LLMConfig | None = None,
    *,
    temperature: float = 0.7,
    tag: str = "",
):
    """流式 chat completion。yield 每个 delta content 片段，最终 yield token usage dict。"""
    import httpx

    cfg = config or load_config()
    if cfg is None:
        raise RuntimeError("未配置联网模型")
    body: dict = {
        "model": cfg.model,
        "messages": messages,
        "temperature": temperature,
        "stream": True,
    }
    extra = provider_extra_body(cfg.base_url)
    if extra:
        body["extra_body"] = extra
    total_content = ""
    with httpx.Client(timeout=httpx.Timeout(cfg.timeout, connect=10.0, read=cfg.timeout)) as client:
        with client.stream("POST", _endpoint(cfg), json=body, headers={"Authorization": f"Bearer {cfg.api_key}"}) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                if not line or not line.startswith("data: "):
                    continue
                data = line[6:]
                if data.strip() == "[DONE]":
                    break
                try:
                    chunk = json.loads(data)
                except json.JSONDecodeError:
                    continue
                delta = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                if delta:
                    total_content += delta
                    yield delta
                # 流式 usage（部分 provider 在最后一个 chunk 返回）
                usage = chunk.get("usage")
                if isinstance(usage, dict):
                    from anshi.token_stats import record as record_token
                    record_token(cfg.model, usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0), tag=tag)
    if not total_content.strip():
        raise ValueError("模型返回了空内容")


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
                "你只提出软世界反应，不得改写硬结算。\n\n"
                "输出分两段，用换行分隔：\n"
                "第一段：一个JSON对象，不要代码围栏。"
                "格式：{assessment:string,proposals:[{path:string,operation:'add',value:number,reason:string,confidence:number}],"
                "situations:[{id:string,delta:number,reason:string,confidence:number}],"
                "npc_actions:[{actor:string,intent:string}],event_seeds:[string]}。"
                "允许路径仅为 regions.<id>.support/unrest/fortification、armies.<id>.morale/supply、"
                "issues.<id>.tension/progress、characters.<id>.loyalty。situations 的 id 必须来自当前上下文，"
                "delta 只能表达本回合局势向好或恶化的方向，不得直接完成局势。每项变化应克制并有明确因果。\n\n"
                "第二段：以 <<<邸报>>> 开头，写一篇邸报（200-350字）。文风仿《资治通鉴》叙事笔法，"
                "以小说般的叙事开篇（场景、气氛、人物动作），用文言与白话相间的笔法，"
                "涵盖诏令施行、军事动向、财政变化、民心态势，以因果叙事串联，结尾留一句余韵暗示天下走向。"
                "不要修改任何数值，不要出现英文。"
            ),
        },
        {"role": "user", "content": "当前回合权威上下文：\n" + _json_text(context)},
    ]
    try:
        text = chat_completion(messages, cfg, temperature=0.45)
        # 解析 JSON 部分
        start, end = text.find("{"), text.rfind("}")
        if start < 0 or end <= start:
            return empty, False
        payload = json.loads(text[start : end + 1])
        # 解析邸报部分
        gazette_marker = text.find("<<<邸报>>>")
        if gazette_marker >= 0:
            payload["_gazette"] = text[gazette_marker + len("<<<邸报>>>"):].strip()
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


def sanitize_json(raw: str) -> dict | list | None:
    """从 LLM 输出中提取合法 JSON。多级降级解析。

    依次尝试：原文解析 → 截取首尾花括号 → 去除控制字符 → 去除 json fence。
    """
    text = raw.strip()
    # 去除 ```json fence
    if text.startswith("```"):
        first_nl = text.find("\n")
        if first_nl > 0:
            text = text[first_nl + 1:]
        if text.endswith("```"):
            text = text[:-3].strip()
    # 试 1：原文直解
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # 试 2：截取最外层 {...}
    start, end = text.find("{"), text.rfind("}")
    if start >= 0 and end > start:
        snippet = text[start : end + 1]
        # 去控制字符
        snippet = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", snippet)
        try:
            return json.loads(snippet)
        except json.JSONDecodeError:
            pass
    # 试 3：截取最外层 [...]
    start, end = text.find("["), text.rfind("]")
    if start >= 0 and end > start:
        snippet = text[start : end + 1]
        snippet = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", snippet)
        try:
            return json.loads(snippet)
        except json.JSONDecodeError:
            pass
    return None


CouncilStance = Literal["支持", "反对", "保留", "观望", "中立"]
_STANCES: set[str] = {"支持", "反对", "保留", "观望", "中立"}


def _council_stance_from_reply(reply: str) -> CouncilStance | None:
    if not reply:
        return None
    head = reply[:30]
    if head.startswith("【态度：") and "】" in head:
        tag = head.split("】", 1)[0].replace("【态度：", "").strip()
        if tag in _STANCES:
            return tag  # type: ignore[return-value]
    return None


def parse_council_stance(reply: str) -> CouncilStance:
    """Extract stance from a council reply, falling back to heuristic keywords."""
    explicit = _council_stance_from_reply(reply)
    if explicit:
        return explicit
    text = reply.lower()
    support = sum(1 for w in ("可", "当", "宜", "应", "赞成", "支持", "可行", "出击", "进兵", "北伐") if w in text)
    oppose = sum(1 for w in ("不可", "不宜", "反对", "暂缓", "守", "固守", "慎重", "再议") if w in text)
    if support > oppose:
        return "支持"
    if oppose > support:
        return "反对"
    return "保留"


def _council_speech_fallback(character: Mapping[str, object], topic: str, round_no: int) -> str:
    name = str(character.get("name", "臣下"))
    stance_text = str(character.get("public_stance") or character.get("stance") or "此事尚须细察")
    if round_no == 2:
        return f"【态度：保留】{name}再奏：臣反复思量，仍以为{stance_text}，还请陛下圣裁。"
    return f"【态度：保留】{name}奏道：关于“{topic.strip() or '此事'}”，臣以为{stance_text}，请陛下与诸公共议。"


def generate_council_speech(
    character: Mapping[str, object],
    topic: str,
    context: Mapping[str, object] | None = None,
    *,
    round_no: int = 1,
    previous_speech: str = "",
    minutes: str = "",
    emperor_remark: str = "",
    config: LLMConfig | None = None,
    with_status: bool = False,
) -> str | tuple[str, bool]:
    """Generate a minister's speech during a council session.

    The model is asked to prefix its reply with a stance tag such as
    【态度：支持】. The returned string always contains the tag; if parsing
    fails the tag is injected from a heuristic fallback.
    """
    fallback = _council_speech_fallback(character, topic, round_no)
    if config is None and load_config(role="chat") is None:
        return (fallback, False) if with_status else fallback
    name = str(character.get("name", "臣下"))
    identity = str(character.get("identity") or character.get("office") or "大唐臣属")
    stance = str(character.get("public_stance") or character.get("stance") or "未有定论")
    facts = _json_text(context or {})
    round_prompt = "这是第二轮交锋。请针对上一位大臣的最新发言和当前纪要，简短反驳或补充，限两句。" if round_no >= 2 else "这是第一轮表态。请清楚陈述你对议题的立场，限两句。"
    extra_parts: list[str] = []
    if previous_speech:
        extra_parts.append(f"上一位大臣最新发言：{previous_speech}")
    if minutes:
        extra_parts.append(f"当前会议纪要：{minutes}")
    if emperor_remark:
        extra_parts.append(f"陛下谕旨：{emperor_remark}")
    extra = "\n".join(extra_parts)
    messages = [
        {
            "role": "system",
            "content": (
                "你是大唐朝堂上参与廷议的大臣。你正在公开廷议中发言，需顾及君臣名分与在场诸臣。"
                "你必须先用一句简短态度开头，格式严格为：【态度：支持】或【态度：反对】或【态度：保留】或【态度：观望】或【态度：中立】。"
                "态度之后接你的正式发言。发言两至四句，不要输出JSON，不要替玩家下令，不要修改任何权威数值。"
            ),
        },
        {
            "role": "user",
            "content": (
                f"议题：{topic.strip() or '当前军国大事'}\n"
                f"人物：{name}\n身份：{identity}\n公开立场：{stance}\n"
                f"场景事实：{facts}\n"
                f"{round_prompt}\n"
                f"{extra}"
            ),
        },
    ]
    try:
        text = chat_completion(messages, config or load_config(role="chat"), temperature=0.65)
        if not _council_stance_from_reply(text):
            stance_guess = parse_council_stance(text)
            text = f"【态度：{stance_guess}】{text}"
        return (text, True) if with_status else text
    except (OSError, TimeoutError, KeyError, IndexError, TypeError, ValueError, RuntimeError, json.JSONDecodeError):
        return (fallback, False) if with_status else fallback


def _council_minutes_fallback(topic: str, speeches: list[dict[str, object]], is_final: bool) -> str:
    if not speeches:
        return "廷议尚未有发言。"
    names = ", ".join(str(item.get("name", "臣下")) for item in speeches)
    if is_final:
        return f"关于“{topic}”，{names} 等人各陈己见，未能立决，请陛下圣裁。"
    return f"关于“{topic}”，{names} 等人已初步表态，尚存分歧，请继续议。"


def generate_council_minutes(
    topic: str,
    speeches: list[dict[str, object]],
    *,
    round_no: int = 1,
    is_final: bool = False,
    config: LLMConfig | None = None,
    with_status: bool = False,
) -> str | tuple[str, bool]:
    """Generate council minutes from a list of minister speeches.

    The minutes summarize positions, consensus, and disagreements. For the
    final round, a concise recommendation is also included.
    """
    fallback = _council_minutes_fallback(topic, speeches, is_final)
    if config is None and load_config(role="utility") is None:
        return (fallback, False) if with_status else fallback
    if not speeches:
        return (fallback, False) if with_status else fallback
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
    messages = [
        {"role": "system", "content": "你是唐廷中书舍人，只整理廷议纪要，不添加诏书中没有的命令，不修改任何权威数值。"},
        {"role": "user", "content": prompt},
    ]
    try:
        text = chat_completion(messages, config or load_config(role="utility"), temperature=0.4)
        return (text, True) if with_status else text
    except (OSError, TimeoutError, KeyError, IndexError, TypeError, ValueError, RuntimeError, json.JSONDecodeError):
        return (fallback, False) if with_status else fallback
