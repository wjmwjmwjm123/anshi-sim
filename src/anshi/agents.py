"""Agent 工厂与执行。L5。

每个 agent 角色有：
- 工厂函数：返回 CouncilAgent（system prompt + config + role）
- run_agent / run_agent_stream：执行 agent，返回文本
- 提示词从 prompts.py 集中管理，不硬编码在本模块。
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Callable, Generator, Mapping

from anshi.ai import LLMConfig, chat_completion, for_role, load_config, sanitize_json, stream_chat_completion
from anshi.prompts import (
    CHARACTER_SYSTEM,
    COURT_SCRIPT_SYSTEM,
    GAZETTE_SYSTEM,
    MINISTER_SYSTEM,
    NARRATOR_SYSTEM,
    SECRETARY_SYSTEM,
    WORLD_PROPOSAL_SYSTEM,
    SCENE_PROMPTS,
    character_user,
    court_script_user,
    gazette_user,
    minister_user,
    narrator_user,
    secretary_user,
    world_proposal_user,
)


# 角色默认采样参数（可被 GAME_SETTINGS 覆盖）
_ROLE_SAMPLING: dict[str, tuple[float, float]] = {
    "minister": (0.65, 0.9),
    "secretary": (0.4, 0.5),
    "character": (0.7, 0.9),
    "narrator": (0.4, 0.5),
    "simulator": (0.5, 0.5),
    "court_script": (0.75, 0.9),
    "gazette": (0.4, 0.5),
}


def _sampling_for(role: str, temperature: float | None = None, top_p: float | None = None) -> tuple[float, float | None]:
    """返回 (temperature, top_p)。显式传入优先，否则用角色默认。"""
    default_t, default_p = _ROLE_SAMPLING.get(role, (0.7, None))
    return (temperature if temperature is not None else default_t, top_p if top_p is not None else default_p)


@dataclass
class CouncilAgent:
    """廷议 agent 配置（纯 Python dataclass，无第三方依赖）。"""
    name: str
    role: str  # "minister" | "secretary" | "character" | "narrator" | "simulator" | "court_script" | "gazette"
    system_prompt: str
    config: LLMConfig
    temperature: float = 0.7
    top_p: float | None = None


# --- 工厂函数 ---


def create_minister_agent(
    character: Mapping[str, object],
    topic: str,
    context: Mapping[str, object],
    *,
    round_no: int = 1,
    previous_speech: str = "",
    minutes: str = "",
    emperor_remark: str = "",
    config: LLMConfig | None = None,
) -> CouncilAgent:
    """廷议大臣 agent：生成发言，带态度标签。"""
    cfg = config or load_config(role="chat") or LLMConfig("", "", "")
    name = str(character.get("name", "臣下"))
    t, p = _sampling_for("minister")
    return CouncilAgent(
        name=f"廷议大臣-{name}",
        role="minister",
        system_prompt=MINISTER_SYSTEM,
        config=for_role(cfg, "minister"),
        temperature=t, top_p=p,
    )


def create_secretary_agent(
    topic: str,
    speeches: list[dict[str, object]],
    *,
    round_no: int = 1,
    is_final: bool = False,
    config: LLMConfig | None = None,
) -> CouncilAgent:
    """中书舍人 agent：整理廷议纪要。"""
    cfg = config or load_config(role="utility") or LLMConfig("", "", "")
    t, p = _sampling_for("secretary")
    return CouncilAgent(
        name="中书舍人",
        role="secretary",
        system_prompt=SECRETARY_SYSTEM,
        config=for_role(cfg, "secretary"),
        temperature=t, top_p=p,
    )


def create_character_agent(
    character: Mapping[str, object],
    topic: str,
    scene: str = "court",
    config: LLMConfig | None = None,
) -> CouncilAgent:
    """人物奏对 agent：朝堂/密诏/远奏。"""
    cfg = config or load_config(role="chat") or LLMConfig("", "", "")
    name = str(character.get("name", "臣下"))
    scene_prompt = SCENE_PROMPTS.get(scene, SCENE_PROMPTS["court"])
    t, p = _sampling_for("character")
    return CouncilAgent(
        name=f"奏对-{name}",
        role="character",
        system_prompt=CHARACTER_SYSTEM + scene_prompt,
        config=for_role(cfg, "character"),
        temperature=t, top_p=p,
    )


def create_narrator_agent(config: LLMConfig | None = None) -> CouncilAgent:
    """史官 agent：回合叙事。"""
    cfg = config or load_config(role="simulation") or LLMConfig("", "", "")
    t, p = _sampling_for("narrator")
    return CouncilAgent(
        name="史官",
        role="narrator",
        system_prompt=NARRATOR_SYSTEM,
        config=for_role(cfg, "narrator"),
        temperature=t, top_p=p,
    )


def create_simulator_agent(config: LLMConfig | None = None) -> CouncilAgent:
    """世界推演 agent：软世界反应。"""
    cfg = config or load_config(role="simulation") or LLMConfig("", "", "")
    t, p = _sampling_for("simulator")
    return CouncilAgent(
        name="世界推演官",
        role="simulator",
        system_prompt=WORLD_PROPOSAL_SYSTEM,
        config=for_role(cfg, "simulator"),
        temperature=t, top_p=p,
    )


def create_court_script_agent(config: LLMConfig | None = None) -> CouncilAgent:
    """廷议剧本 agent：一次调用生成整场廷议对话。"""
    cfg = config or load_config(role="chat") or LLMConfig("", "", "")
    t, p = _sampling_for("court_script")
    return CouncilAgent(
        name="朝会编剧",
        role="court_script",
        system_prompt=COURT_SCRIPT_SYSTEM,
        config=for_role(cfg, "chat"),
        temperature=t, top_p=p,
    )


def create_gazette_agent(config: LLMConfig | None = None) -> CouncilAgent:
    """邸报 agent：生成回合邸报。"""
    cfg = config or load_config(role="utility") or LLMConfig("", "", "")
    t, p = _sampling_for("gazette")
    return CouncilAgent(
        name="邸报官",
        role="gazette",
        system_prompt=GAZETTE_SYSTEM,
        config=for_role(cfg, "utility"),
        temperature=t, top_p=p,
    )


# --- 执行函数 ---


def _messages(agent: CouncilAgent, user_prompt: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": agent.system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def run_agent(
    agent: CouncilAgent,
    user_prompt: str,
    *,
    fallback: str = "",
    with_status: bool = False,
    tag: str = "",
) -> str | tuple[str, bool]:
    """执行 agent（非流式），返回文本。非流式执行。"""
    if not agent.config.api_key:
        return (fallback, False) if with_status else fallback
    try:
        text = chat_completion(
            _messages(agent, user_prompt), agent.config,
            temperature=agent.temperature, tag=tag or agent.name,
        )
        return (text, True) if with_status else text
    except (OSError, TimeoutError, KeyError, IndexError, TypeError, ValueError, RuntimeError, json.JSONDecodeError):
        return (fallback, False) if with_status else fallback


def run_agent_stream(
    agent: CouncilAgent,
    user_prompt: str,
    on_chunk: Callable[[str], None] | None = None,
    tag: str = "",
) -> Generator[str, None, None]:
    """执行 agent（真流式），yield 每个 delta 片段。真流式执行。

    用法：
        for chunk in run_agent_stream(agent, prompt):
            send_sse(chunk)
    """
    if not agent.config.api_key:
        return
    try:
        for chunk in stream_chat_completion(
            _messages(agent, user_prompt), agent.config,
            temperature=agent.temperature, tag=tag or agent.name,
        ):
            if isinstance(chunk, str):
                if on_chunk:
                    on_chunk(chunk)
                yield chunk
    except (OSError, TimeoutError, KeyError, IndexError, TypeError, ValueError, RuntimeError, json.JSONDecodeError):
        return


def run_agent_json(
    agent: CouncilAgent,
    user_prompt: str,
    *,
    fallback: dict | list | None = None,
    with_status: bool = False,
    tag: str = "",
) -> tuple[dict | list | None, bool]:
    """执行 agent 并解析 JSON 输出。带 JSON 修复兜底。

    1. 调用 LLM
    2. sanitize_json 提取 JSON
    3. 失败则返回 fallback
    """
    if not agent.config.api_key:
        return fallback, False
    try:
        text = chat_completion(
            _messages(agent, user_prompt), agent.config,
            temperature=agent.temperature, tag=tag or agent.name,
        )
    except (OSError, TimeoutError, KeyError, IndexError, TypeError, ValueError, RuntimeError, json.JSONDecodeError):
        return fallback, False
    parsed = sanitize_json(text)
    if parsed is not None:
        return parsed, True
    return fallback, False


def run_agent_with_tools(
    agent: CouncilAgent,
    user_prompt: str,
    tools: list[dict],
    tool_executors: dict,
    *,
    fallback: str = "",
    with_status: bool = False,
    tag: str = "",
    max_tool_rounds: int = 5,
) -> str | tuple[str, bool]:
    """执行 agent 并支持 tool-use 循环。

    模型可以请求查询工具（查地区、军队、国库等），工具结果回传后模型继续生成。
    直到模型不再请求工具，返回最终文本。

    Args:
        agent: Agent 配置
        user_prompt: 用户提示
        tools: OpenAI function calling 格式的工具定义
        tool_executors: {工具名: 执行函数} 映射
        fallback: 无 API key 时的回退文本
        with_status: 是否返回 (text, model_used) 元组
        tag: 日志标签
        max_tool_rounds: 最大工具调用轮次
    """
    if not agent.config.api_key:
        return (fallback, False) if with_status else fallback
    try:
        text = chat_completion(
            _messages(agent, user_prompt), agent.config,
            temperature=agent.temperature, tag=tag or agent.name,
            tools=tools, tool_executors=tool_executors,
            max_tool_rounds=max_tool_rounds,
        )
        return (text, True) if with_status else text
    except (OSError, TimeoutError, KeyError, IndexError, TypeError, ValueError, RuntimeError, json.JSONDecodeError):
        return (fallback, False) if with_status else fallback
