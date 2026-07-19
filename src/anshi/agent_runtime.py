"""轻量 Agent 运行时。L6。

提供带有对话历史累积、工具注册和多轮推理的 AgentSession。
无第三方框架依赖，兼容现有 ai.py / agents.py。
"""

from __future__ import annotations

from collections.abc import Callable, Generator
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolDefinition:
    """OpenAI function-calling 格式的工具定义。"""
    name: str
    description: str
    parameters: dict  # JSON Schema
    executor: Callable[..., str]  # Python 实现


@dataclass
class ToolRegistry:
    """工具注册中心：所有 agent 共享同一套游戏盘面查询工具。"""
    tools: dict[str, ToolDefinition] = field(default_factory=dict)

    def register(self, tool: ToolDefinition) -> None:
        self.tools[tool.name] = tool

    def openai_specs(self) -> list[dict[str, Any]]:
        """返回 OpenAI function calling 格式的工具列表。"""
        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                },
            }
            for t in self.tools.values()
        ]

    def executor_map(self) -> dict[str, Callable[..., str]]:
        return {t.name: t.executor for t in self.tools.values()}

    @classmethod
    def from_pairs(cls, specs: list[dict], executors: dict[str, Callable]) -> ToolRegistry:
        """从 build_game_tools 的输出构造 ToolRegistry。"""
        registry = cls()
        for spec in specs:
            fn = spec.get("function", {})
            name = fn.get("name", "")
            if name and name in executors:
                registry.register(ToolDefinition(
                    name=name,
                    description=fn.get("description", ""),
                    parameters=fn.get("parameters", {"type": "object", "properties": {}, "required": []}),
                    executor=executors[name],
                ))
        return registry


@dataclass
class AgentSession:
    """保持跨调用对话历史的有状态 session。

    Usage:
        session = AgentSession()
        session.add_user("What's the state of Tongguan?")
        # ... LLM responds ...
        session.add_assistant("Tongguan is under siege...")
    """
    messages: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_user(self, content: str) -> None:
        self.messages.append({"role": "user", "content": content})

    def add_assistant(self, content: str, tool_calls: list[dict] | None = None) -> None:
        msg: dict[str, Any] = {"role": "assistant", "content": content}
        if tool_calls:
            msg["tool_calls"] = tool_calls
        self.messages.append(msg)

    def add_tool_result(self, call_id: str, content: str) -> None:
        self.messages.append({
            "role": "tool",
            "tool_call_id": call_id,
            "content": content,
        })

    def to_messages(self, system_prompt: str) -> list[dict[str, Any]]:
        return [{"role": "system", "content": system_prompt}] + self.messages

    def clear(self) -> None:
        self.messages.clear()

    def recent_summary(self, n: int = 4) -> str:
        """返回最近 N 轮对话摘要，用于注入新 agent 的上下文。"""
        recent = self.messages[-n * 2:]
        lines = []
        for msg in recent:
            role = msg.get("role", "?")
            content = str(msg.get("content", ""))[:100]
            if role == "user":
                lines.append(f"皇帝：{content}")
            elif role == "assistant":
                lines.append(f"臣：{content}")
        return "\n".join(lines)


def run_agent_loop(
    system_prompt: str,
    user_input: str,
    config,
    tools: ToolRegistry | None = None,
    *,
    temperature: float = 0.7,
    max_rounds: int = 5,
    tag: str = "",
) -> str:
    """执行一次 agent 调用（无 session 历史，兼容旧接口）。

    若提供 tools，启用 function calling 循环。
    返回最终文本回复。
    """
    from anshi.ai import chat_completion

    messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_input}]
    tool_specs = tools.openai_specs() if tools else None
    executors = tools.executor_map() if tools else None
    if tool_specs and executors:
        return chat_completion(
            messages, config, temperature=temperature,
            tools=tool_specs, tool_executors=executors,
            max_tool_rounds=max_rounds, tag=tag,
        )
    return chat_completion(messages, config, temperature=temperature, tag=tag)


def run_session_loop(
    session: AgentSession,
    system_prompt: str,
    config,
    tools: ToolRegistry | None = None,
    *,
    temperature: float = 0.7,
    max_rounds: int = 5,
    tag: str = "",
) -> str:
    """执行一次带 session 历史的 agent 调用。

    session 中的历史消息会被包含在请求中。LLM 回复会自动写入 session。
    用于连续对话场景（人物奏对 / 密诏）。
    """
    from anshi.ai import chat_completion

    messages = session.to_messages(system_prompt)
    tool_specs = tools.openai_specs() if tools else None
    executors = tools.executor_map() if tools else None
    if tool_specs and executors:
        text = chat_completion(
            messages, config, temperature=temperature,
            tools=tool_specs, tool_executors=executors,
            max_tool_rounds=max_rounds, tag=tag,
        )
    else:
        text = chat_completion(messages, config, temperature=temperature, tag=tag)
    session.add_assistant(text)
    return text


def run_agent_stream_with_session(
    session: AgentSession,
    system_prompt: str,
    config,
    *,
    temperature: float = 0.7,
    tag: str = "",
) -> Generator[str, None, None]:
    """流式执行带 session 历史的 agent 调用。yield 每个 delta。"""
    from anshi.ai import stream_chat_completion

    messages = session.to_messages(system_prompt)
    full = ""
    for chunk in stream_chat_completion(
        messages, config, temperature=temperature, tag=tag,
    ):
        if isinstance(chunk, str):
            full += chunk
            yield chunk
    if full.strip():
        session.add_assistant(full)
