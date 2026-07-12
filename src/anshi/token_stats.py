"""Token 记账（仿照 ming_sim/token_stats.py 模式）。L2。

记录每次 LLM 调用的 prompt/completion tokens，供 API 查询。
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from threading import Lock


@dataclass
class TokenRecord:
    timestamp: float
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    tag: str = ""


_records: list[TokenRecord] = []
_lock = Lock()
_MAX_RECORDS = 500


def record(model: str, prompt_tokens: int, completion_tokens: int, tag: str = "") -> None:
    """记录一次 LLM 调用的 token 用量。"""
    rec = TokenRecord(
        timestamp=time.time(),
        model=model,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens,
        tag=tag,
    )
    with _lock:
        _records.append(rec)
        if len(_records) > _MAX_RECORDS:
            _records[:] = _records[-_MAX_RECORDS:]


def summary() -> dict:
    """返回 token 用量汇总。"""
    with _lock:
        total_prompt = sum(r.prompt_tokens for r in _records)
        total_completion = sum(r.completion_tokens for r in _records)
        return {
            "total_calls": len(_records),
            "total_prompt_tokens": total_prompt,
            "total_completion_tokens": total_completion,
            "total_tokens": total_prompt + total_completion,
            "recent": [
                {"model": r.model, "prompt": r.prompt_tokens, "completion": r.completion_tokens, "tag": r.tag}
                for r in _records[-10:]
            ],
        }


def clear() -> None:
    """清空记录。"""
    with _lock:
        _records.clear()
