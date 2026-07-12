from __future__ import annotations

import json
import os
from pathlib import Path
from threading import Lock

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from anshi.content import load_scenario
from anshi.agents import create_minister_agent, create_secretary_agent, run_agent  # noqa: F401 — kept for tests
from anshi.storage import GameStore
from anshi.strategy import FieldArmy, Siege, initial_strategy
from anshi.management import (
    ArmyState as ManagedArmyState,
    CharacterState,
    IssueState,
    RegionState as ManagedRegionState,
)
from anshi.campaign import CampaignProgress

from apps.api.routes import council, decree, game, settings

ROOT = Path(__file__).parents[2]
SCENARIO = load_scenario(ROOT / "content" / "scenarios" / "tongguan_756")
CAMPAIGN = json.loads((ROOT / "content" / "scenarios" / "tongguan_756" / "campaign.json").read_text(encoding="utf-8"))
CAMPAIGN["characters"].extend(json.loads((ROOT / "content" / "scenarios" / "tongguan_756" / "characters_extra.json").read_text(encoding="utf-8")))


def _load_dotenv() -> None:
    if os.environ.get("ANSHI_TESTING"):
        return
    env_file = Path(__file__).resolve().parent.parent.parent / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _hydrate_management(management) -> None:
    aliases = {
        "regions": {"guanzhong", "henan"},
        "armies": {"tongguan", "shuofang"},
        "characters": {"geshu_han", "yang_guozhong"},
        "issues": {"refugees", "court_conflict"},
    }
    for domain, keys in aliases.items():
        values = getattr(management, domain)
        for key in keys:
            values.pop(key, None)
    management.directives = [item for item in management.directives if item.target not in set().union(*aliases.values())]
    for region in CAMPAIGN["regions"]:
        management.regions.setdefault(region["id"], ManagedRegionState(
            region["name"], region["support"], region["unrest"], min(100, region["tax"]["cp_per_30_days"] // 100),
            70 if "fort" in region["status"] else 20,
        ))
    for army in CAMPAIGN["armies"]:
        if army["act_from"] == 1:
            management.armies.setdefault(army["id"], ManagedArmyState(
                army["name"], army["region"], army["present_strength"], army["fit_strength"], army["supply"], army["morale"],
            ))
    for character in CAMPAIGN["characters"]:
        status = "active" if character["audience_status"] in {"available", "remote_only", "player_character"} else "offstage"
        management.characters.setdefault(character["id"], CharacterState(
            character["name"], character["identity"], character["attributes"]["loyalty"],
            max(character["attributes"]["administration"], character["attributes"]["military"]), status,
        ))
    for issue in CAMPAIGN["ongoing_issues"]:
        management.issues.setdefault(issue["id"], IssueState(issue["name"], issue["pressure"], 100 - issue["progress"]))


def _activate_content(management, act: int) -> None:
    for army in CAMPAIGN["armies"]:
        if army["act_from"] <= act and army["id"] not in management.armies:
            management.armies[army["id"]] = ManagedArmyState(
                army["name"], army["region"], army["present_strength"], army["fit_strength"], army["supply"], army["morale"]
            )
    for character in CAMPAIGN["characters"]:
        if character["id"] not in management.characters:
            continue
        available_act = 1
        if character["audience_status"].startswith("future"):
            available_act = 2 if character["available_from"] < "0757-01-01" else 3
            if character["available_from"] >= "0758-01-01":
                available_act = 4
            if character["available_from"] >= "0761-01-01":
                available_act = 5
        if act >= available_act and character["audience_status"] not in {"enemy_only", "future_enemy", "player_character"}:
            management.characters[character["id"]].status = "active"


class _GameState:
    """运行时游戏状态，注入各 router。"""

    def __init__(self, store, campaign, management, progress, conversation, strategy):
        self.lock = Lock()
        self.store = store
        self.campaign = campaign
        self.management = management
        self.progress = progress
        self.conversation = conversation
        self.strategy = strategy
        self.campaign_data = CAMPAIGN
        self.scenario = SCENARIO

    def hydrate_management(self, management):
        _hydrate_management(management)

    def activate_content(self):
        _activate_content(self.management, self.progress.act)

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


def create_app(db_path: str | Path | None = None) -> FastAPI:
    _load_dotenv()
    os.environ.setdefault("OPENAI_BASE_URL", "https://api.xiaomimimo.com/v1")
    os.environ.setdefault("OPENAI_MODEL", "mimo-v2.5")

    app = FastAPI(title="Anshi Sim", version="0.5.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["*"],
    )

    store = GameStore(db_path or os.environ.get("ANSHI_DB", ROOT / "data" / "anshi.db"))
    campaign = {"state": store.load()}
    management = store.load_management()
    progress = store.load_progress()
    conversation = store.load_conversation()
    strategy = store.load_strategy() or initial_strategy(CAMPAIGN)

    game_state = _GameState(store, campaign, management, progress, conversation, strategy)
    _hydrate_management(management)
    game_state.activate_content()
    store.save_management(management)
    app.state.game_store = store

    # Register routers
    council.register(council.router, game_state)
    decree.register(decree.router, game_state)
    game.register(game.router, game_state)
    settings.register(settings.router, game_state)

    app.include_router(council.router)
    app.include_router(decree.router)
    app.include_router(game.router)
    app.include_router(settings.router)

    app.mount("/", StaticFiles(directory=ROOT / "apps" / "web" / "dist", html=True), name="static")
    return app


app = create_app()
