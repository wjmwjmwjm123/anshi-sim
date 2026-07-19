from __future__ import annotations

import json
import hashlib
import sqlite3
from dataclasses import asdict
from pathlib import Path

from .core import (
    ArmyState,
    CommandState,
    CrisisState,
    EventClock,
    EventWindow,
    GameState,
    IntelligenceClaim,
    initial_state,
)
from .management import (
    ArmyState as ManagedArmyState,
    CharacterState,
    FinanceState,
    IssueState,
    ManagementState,
    QueuedDirective,
    RegionState as ManagedRegionState,
    initial_state as initial_management_state,
)
from .campaign import CampaignEvent, CampaignProgress, initial_progress
from .conversation import ConversationState, Memory, Message, Relationship
from .strategy import ArmyMovement, FieldArmy, Siege, StrategyState


def state_from_payload(data: dict) -> GameState:
    payload = dict(data)
    legacy_day = payload.pop("day", 1)
    legacy_date = payload.pop("date_label", "天宝十五载 六月初一")
    legacy_intel = payload.pop("known_intel", [])
    payload["army"] = ArmyState(**payload["army"])
    payload["crises"] = CrisisState(**payload["crises"])
    if "clock" in payload:
        clock = dict(payload["clock"])
        clock["windows"] = [EventWindow(**item) for item in clock.get("windows", [])]
        payload["clock"] = EventClock(**clock)
    else:
        payload["clock"] = EventClock(day=legacy_day, date_label=legacy_date)
    if "intel_claims" in payload:
        payload["intel_claims"] = [IntelligenceClaim(**item) for item in payload["intel_claims"]]
    elif legacy_intel:
        payload["intel_claims"] = [
            IntelligenceClaim(f"legacy_{index}", summary, "旧存档奏报", 0, 50, f"legacy_{index}", False)
            for index, summary in enumerate(legacy_intel)
        ]
    if payload.get("last_command"):
        payload["last_command"] = CommandState(**payload["last_command"])
    return GameState(**payload)


def management_from_payload(data: dict) -> ManagementState:
    payload = dict(data)
    payload["finance"] = FinanceState(**payload["finance"])
    payload["regions"] = {key: ManagedRegionState(**value) for key, value in payload["regions"].items()}
    payload["armies"] = {key: ManagedArmyState(**value) for key, value in payload["armies"].items()}
    payload["issues"] = {key: IssueState(**value) for key, value in payload["issues"].items()}
    payload["characters"] = {key: CharacterState(**value) for key, value in payload["characters"].items()}
    payload["directives"] = [QueuedDirective(**value) for value in payload.get("directives", [])]
    return ManagementState(**payload)


class GameStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS campaign (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                state_json TEXT NOT NULL,
                revision INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS turn_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_name TEXT NOT NULL,
                result_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS management (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                state_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS campaign_progress (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                state_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS auxiliary_state (
                state_key TEXT PRIMARY KEY,
                state_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS agent_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kind TEXT NOT NULL,
                model TEXT NOT NULL,
                elapsed_ms INTEGER NOT NULL,
                succeeded INTEGER NOT NULL,
                detail TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS event_memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                character_id TEXT NOT NULL,
                summary TEXT NOT NULL,
                scene TEXT NOT NULL DEFAULT '',
                turn INTEGER NOT NULL,
                importance INTEGER NOT NULL DEFAULT 3,
                tags TEXT NOT NULL DEFAULT '[]',
                year INTEGER NOT NULL DEFAULT 756,
                month INTEGER NOT NULL DEFAULT 6,
                expires_at INTEGER,
                archived INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS save_slots (
                slot_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        self.conn.commit()

    def load(self) -> GameState:
        row = self.conn.execute("SELECT state_json FROM campaign WHERE id=1").fetchone()
        if row:
            return state_from_payload(json.loads(row[0]))
        state = initial_state()
        self.save(state)
        return state

    def save(self, state: GameState) -> None:
        state_json = json.dumps(state.payload(), ensure_ascii=False, separators=(",", ":"))
        with self.conn:
            self.conn.execute(
                """
                INSERT INTO campaign(id,state_json,revision) VALUES(1,?,1)
                ON CONFLICT(id) DO UPDATE SET
                    state_json=excluded.state_json,
                    revision=campaign.revision+1,
                    updated_at=CURRENT_TIMESTAMP
                """,
                (state_json,),
            )

    def load_management(self) -> ManagementState:
        row = self.conn.execute("SELECT state_json FROM management WHERE id=1").fetchone()
        if row:
            return management_from_payload(json.loads(row[0]))
        state = initial_management_state()
        self.save_management(state)
        return state

    def save_management(self, state: ManagementState) -> None:
        state_json = json.dumps(asdict(state), ensure_ascii=False, separators=(",", ":"))
        with self.conn:
            self.conn.execute(
                "INSERT INTO management(id,state_json) VALUES(1,?) ON CONFLICT(id) DO UPDATE SET state_json=excluded.state_json",
                (state_json,),
            )

    def load_progress(self) -> CampaignProgress:
        row = self.conn.execute("SELECT state_json FROM campaign_progress WHERE id=1").fetchone()
        if not row:
            progress = initial_progress()
            self.save_progress(progress)
            return progress
        payload = json.loads(row[0])
        if payload.get("active_event"):
            payload["active_event"] = CampaignEvent(**payload["active_event"])
        return CampaignProgress(**payload)

    def save_progress(self, progress: CampaignProgress) -> None:
        state_json = json.dumps(asdict(progress), ensure_ascii=False, separators=(",", ":"))
        with self.conn:
            self.conn.execute(
                "INSERT INTO campaign_progress(id,state_json) VALUES(1,?) ON CONFLICT(id) DO UPDATE SET state_json=excluded.state_json",
                (state_json,),
            )

    def load_conversation(self) -> ConversationState:
        payload = self._load_aux("conversation")
        if not payload:
            return ConversationState()
        payload["chats"] = {key: [Message(**item) for item in values] for key, values in payload.get("chats", {}).items()}
        payload["memories"] = {key: [Memory(**item) for item in values] for key, values in payload.get("memories", {}).items()}
        payload["relationships"] = {key: Relationship(**value) for key, value in payload.get("relationships", {}).items()}
        return ConversationState(**payload)

    def save_conversation(self, state: ConversationState) -> None:
        self._save_aux("conversation", asdict(state))

    def load_strategy(self) -> StrategyState | None:
        payload = self._load_aux("strategy")
        if not payload:
            return None
        payload["armies"] = {key: FieldArmy(**value) for key, value in payload.get("armies", {}).items()}
        payload["sieges"] = [Siege(**item) for item in payload.get("sieges", [])]
        payload["pending_movements"] = [ArmyMovement(**item) for item in payload.get("pending_movements", [])]
        return StrategyState(**payload)

    def save_strategy(self, state: StrategyState) -> None:
        self._save_aux("strategy", asdict(state))

    def record_agent_run(self, kind: str, model: str, elapsed_ms: int, succeeded: bool, detail: str = "") -> None:
        with self.conn:
            self.conn.execute("INSERT INTO agent_runs(kind,model,elapsed_ms,succeeded,detail) VALUES(?,?,?,?,?)", (kind, model, elapsed_ms, int(succeeded), detail[:500]))

    def agent_runs(self, limit: int = 50) -> list[dict]:
        rows = self.conn.execute("SELECT kind,model,elapsed_ms,succeeded,detail,created_at FROM agent_runs ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [{"kind": row[0], "model": row[1], "elapsed_ms": row[2], "succeeded": bool(row[3]), "detail": row[4], "created_at": row[5]} for row in rows]

    def save_slot(self, slot_id: int, name: str, payload: dict) -> None:
        clean = dict(payload)
        canonical = json.dumps(clean, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        clean["state_hash"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        text = json.dumps(clean, ensure_ascii=False, separators=(",", ":"))
        with self.conn:
            self.conn.execute("INSERT INTO save_slots(slot_id,name,payload_json) VALUES(?,?,?) ON CONFLICT(slot_id) DO UPDATE SET name=excluded.name,payload_json=excluded.payload_json,updated_at=CURRENT_TIMESTAMP", (slot_id, name.strip() or f"存档{slot_id}", text))

    def load_slot(self, slot_id: int) -> dict:
        row = self.conn.execute("SELECT payload_json FROM save_slots WHERE slot_id=?", (slot_id,)).fetchone()
        if not row:
            raise ValueError("存档槽为空")
        payload = json.loads(row[0])
        expected = payload.pop("state_hash", "")
        actual = hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
        if expected and expected != actual:
            raise ValueError("存档校验失败，内容可能已损坏")
        return payload

    def list_slots(self) -> list[dict]:
        rows = self.conn.execute("SELECT slot_id,name,payload_json,updated_at FROM save_slots ORDER BY slot_id").fetchall()
        result = []
        for slot_id, name, payload_json, updated_at in rows:
            payload = json.loads(payload_json)
            result.append({"slot_id": slot_id, "name": name, "updated_at": updated_at, "act": payload.get("progress", {}).get("act", 1), "turn": payload.get("progress", {}).get("total_turn", 1), "year": payload.get("progress", {}).get("year", 756), "month": payload.get("progress", {}).get("month", 6)})
        return result

    def _load_aux(self, key: str) -> dict | None:
        row = self.conn.execute("SELECT state_json FROM auxiliary_state WHERE state_key=?", (key,)).fetchone()
        return json.loads(row[0]) if row else None

    def _save_aux(self, key: str, value: dict) -> None:
        text = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        with self.conn:
            self.conn.execute("INSERT INTO auxiliary_state(state_key,state_json) VALUES(?,?) ON CONFLICT(state_key) DO UPDATE SET state_json=excluded.state_json", (key, text))

    def record_turn(self, order: str, result: dict) -> None:
        with self.conn:
            self.conn.execute(
                "INSERT INTO turn_log(order_name,result_json) VALUES(?,?)",
                (order, json.dumps(result, ensure_ascii=False, separators=(",", ":"))),
            )

    def reset(self) -> GameState:
        state = initial_state()
        with self.conn:
            self.conn.execute("DELETE FROM turn_log")
        self.save(state)
        self.save_management(initial_management_state())
        self.save_progress(initial_progress())
        with self.conn:
            self.conn.execute("DELETE FROM auxiliary_state")
            self.conn.execute("DELETE FROM agent_runs")
        return state

    def save_memories(self, memories: list[dict]) -> None:
        """Batch-insert extracted memories into event_memories table."""
        with self.conn:
            for mem in memories:
                tags = json.dumps(mem.get("tags", []) or [], ensure_ascii=False)
                self.conn.execute(
                    "INSERT INTO event_memories(character_id,summary,scene,turn,importance,tags,year,month,expires_at) VALUES(?,?,?,?,?,?,?,?,?)",
                    (
                        str(mem.get("character_id", "")),
                        str(mem.get("summary", ""))[:200],
                        str(mem.get("scene", "回合记忆")),
                        int(mem.get("turn", 0)),
                        int(mem.get("importance", 3)),
                        tags,
                        int(mem.get("year", 756)),
                        int(mem.get("month", 6)),
                        int(mem["expires_at"]) if mem.get("expires_at") is not None else None,
                    ),
                )

    def expire_memories(self, current_turn: int) -> int:
        """Archive memories past their TTL. Returns count archived."""
        with self.conn:
            cursor = self.conn.execute(
                "UPDATE event_memories SET archived=1 WHERE archived=0 AND expires_at IS NOT NULL AND expires_at <= ?",
                (current_turn,),
            )
            return cursor.rowcount

    def recall_memories(self, character_id: str = "", tags: list[str] | None = None, current_turn: int = 0, limit: int = 10) -> list[dict]:
        """Recall memories for a character or by tags. Returns active (non-archived, non-expired)."""
        params: list = []
        where = ["archived=0", "(expires_at IS NULL OR expires_at > ?)"]
        params.append(current_turn)
        if character_id:
            where.append("character_id = ?")
            params.append(character_id)
        if tags:
            tag_conds = " OR ".join(["tags LIKE ?" for _ in tags])
            where.append(f"({tag_conds})")
            params.extend(f"%{t}%" for t in tags)
        sql = f"SELECT id,character_id,summary,scene,turn,importance,tags,year,month FROM event_memories WHERE {' AND '.join(where)} ORDER BY importance DESC, turn DESC LIMIT ?"
        params.append(limit)
        rows = self.conn.execute(sql, params).fetchall()
        result = []
        for row in rows:
            try:
                tag_list = json.loads(row[6])
            except (json.JSONDecodeError, TypeError):
                tag_list = []
            result.append({"id": row[0], "character_id": row[1], "summary": row[2], "scene": row[3], "turn": row[4], "importance": row[5], "tags": tag_list, "year": row[7], "month": row[8]})
        return result

    def revision(self) -> int:
        row = self.conn.execute("SELECT revision FROM campaign WHERE id=1").fetchone()
        return int(row[0]) if row else 0

    def close(self) -> None:
        self.conn.close()
