"""设置与诊断路由。"""
from __future__ import annotations

import os

from fastapi import APIRouter
from pydantic import BaseModel

from anshi.ai import load_config
from anshi import token_stats

router = APIRouter()


class ModelConfigRequest(BaseModel):
    role: str = "chat"
    api_key: str = ""
    base_url: str = ""
    model: str = ""


def register(router_: APIRouter, game) -> None:
    SCENARIO = game.scenario

    def model_roles_payload() -> dict:
        roles = {}
        for role in ("chat", "simulation", "utility"):
            config = load_config(role=role)
            roles[role] = {"configured": config is not None, "status": "已配置，调用时验证" if config else "未配置", "base_url": config.base_url if config else "", "model": config.model if config else ""}
        return roles

    @router_.get("/api/token-stats")
    def get_token_stats() -> dict:
        return token_stats.summary()

    @router_.get("/api/health")
    def health() -> dict:
        roles = model_roles_payload()
        configured = sum(item["configured"] for item in roles.values())
        return {"status": "ok", "content_version": SCENARIO.manifest.content_version, "llm": f"已配置 {configured}/3" if configured else "未配置", "model": roles["chat"]["model"] or "中文模板", "models": roles}

    @router_.get("/api/model-config")
    def model_config() -> dict:
        return {"roles": model_roles_payload()}

    @router_.post("/api/model-config")
    def update_model_config(request: ModelConfigRequest) -> dict:
        if request.role not in {"chat", "simulation", "utility"}:
            return {"configured": False, "detail": "未知模型职责。"}
        prefix = request.role.upper()
        if request.api_key.strip():
            os.environ[f"{prefix}_API_KEY"] = request.api_key.strip()
        if request.base_url.strip():
            os.environ[f"{prefix}_BASE_URL"] = request.base_url.strip()
        if request.model.strip():
            os.environ[f"{prefix}_MODEL"] = request.model.strip()
        config = load_config(role=request.role)
        return {"configured": config is not None, "base_url": config.base_url if config else "", "model": config.model if config else "", "detail": "配置仅保存在当前游戏进程，密钥不会返回前端。"}
