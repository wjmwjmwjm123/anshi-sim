"""共享状态：所有 router 通过闭包捕获这些对象。"""
from __future__ import annotations

from threading import Lock


class GameState:
    """运行时游戏状态容器，由 create_app 初始化后注入各 router。"""

    def __init__(self):
        self.lock = Lock()
        self.store = None
        self.campaign = None
        self.management = None
        self.progress = None
        self.conversation = None
        self.strategy = None

    def unified_payload(self) -> dict:
        from dataclasses import asdict
        return {
            "state": self.campaign["state"].payload(),
            "management": asdict(self.management),
            "progress": asdict(self.progress),
            "conversation": asdict(self.conversation),
            "strategy": asdict(self.strategy),
        }

    def persist_all(self) -> None:
        self.store.save(self.campaign["state"])
        self.store.save_management(self.management)
        self.store.save_progress(self.progress)
        self.store.save_conversation(self.conversation)
        self.store.save_strategy(self.strategy)
