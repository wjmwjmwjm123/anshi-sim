"""Agent 工厂与执行（仿照 ming_sim/agents.py 模式）。L5。

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
    MINISTER_SYSTEM,
    NARRATOR_SYSTEM,
    SECRETARY_SYSTEM,
    WORLD_PROPOSAL_SYSTEM,
    SCENE_PROMPTS,
    character_user,
    minister_user,
    narrator_user,
    secretary_user,
    world_proposal_user,
)


@dataclass
class CouncilAgent:
    """廷议 agent 配置（仿照 ming_sim Agent，但不依赖 agno）。"""
    name: str
    role: str  # "minister" | "secretary" | "character" | "narrator" | "simulator"
    system_prompt: str
    config: LLMConfig
    temperature: float = 0.7


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
    return CouncilAgent(
        name=f"廷议大臣-{name}",
        role="minister",
        system_prompt=MINISTER_SYSTEM,
        config=for_role(cfg, "minister"),
        temperature=0.65,
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
    return CouncilAgent(
        name="中书舍人",
        role="secretary",
        system_prompt=SECRETARY_SYSTEM,
        config=for_role(cfg, "secretary"),
        temperature=0.4,
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
    return CouncilAgent(
        name=f"奏对-{name}",
        role="character",
        system_prompt=CHARACTER_SYSTEM + scene_prompt,
        config=for_role(cfg, "character"),
        temperature=0.7,
    )


def create_narrator_agent(config: LLMConfig | None = None) -> CouncilAgent:
    """史官 agent：回合叙事。"""
    cfg = config or load_config(role="simulation") or LLMConfig("", "", "")
    return CouncilAgent(
        name="史官",
        role="narrator",
        system_prompt=NARRATOR_SYSTEM,
        config=for_role(cfg, "narrator"),
        temperature=0.4,
    )


def create_simulator_agent(config: LLMConfig | None = None) -> CouncilAgent:
    """世界推演 agent：软世界反应。"""
    cfg = config or load_config(role="simulation") or LLMConfig("", "", "")
    return CouncilAgent(
        name="世界推演官",
        role="simulator",
        system_prompt=WORLD_PROPOSAL_SYSTEM,
        config=for_role(cfg, "simulator"),
        temperature=0.45,
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
    """执行 agent（非流式），返回文本。仿照 ming_sim run_agent_text。"""
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
    """执行 agent（真流式），yield 每个 delta 片段。仿照 ming_sim run_agent_stream_text。

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
    """执行 agent 并解析 JSON 输出。仿照 ming_sim parse_agent_json + sanitizer 兜底。

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
