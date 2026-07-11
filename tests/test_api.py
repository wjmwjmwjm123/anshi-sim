from fastapi.testclient import TestClient

from apps.api.main import create_app


def test_api_turn_persists_with_temporary_database(tmp_path) -> None:
    app = create_app(tmp_path / "api.db")
    with TestClient(app) as client:
        before = client.get("/api/state").json()
        response = client.post("/api/turn", json={"order": "verify"})
        after = response.json()

        assert response.status_code == 200
        assert after["accepted"]
        assert after["state"]["clock"]["day"] == 3
        assert after["state"]["save_revision"] == before["save_revision"] + 1
        assert client.get("/api/state").json()["intel_confidence"] == 52
    app.state.game_store.close()


def test_complete_management_loop_uses_snapshot_audience_and_directives(tmp_path) -> None:
    app = create_app(tmp_path / "complete.db")
    with TestClient(app) as client:
        snapshot = client.get("/api/snapshot").json()
        assert len(snapshot["catalog"]["regions"]) == 16
        assert len(snapshot["management"]["regions"]) >= 16

        audience = client.post("/api/audience", json={"character_id": "gao_lishi", "topic": "钱粮如何？"}).json()
        assert audience["accepted"]
        assert "钱粮" in audience["reply"]

        queued = client.post("/api/directives", json={"kind": "relief", "target": "changan", "amount": 10}).json()
        assert len(queued["directives"]) == 1
        current_event = snapshot["progress"]["active_event"]
        result = client.post("/api/resolve", json={"event_choice": current_event["choices"][0]}).json()
        assert result["result"]["reports"][0]["accepted"]
        assert not result["management"]["directives"]
        assert result["management"]["turn"] == 2
    app.state.game_store.close()


def test_secret_edict_and_model_config_do_not_echo_key(tmp_path) -> None:
    app = create_app(tmp_path / "secrets.db")
    with TestClient(app) as client:
        configured = client.post("/api/model-config", json={"api_key": "test-secret", "base_url": "https://example.test/v1", "model": "test-model"}).json()
        assert configured["model"] == "test-model"
        assert "test-secret" not in str(configured)
        edict = client.post("/api/secret-edicts", json={"character_id": "gao_lishi", "text": "暗查禁军", "purpose": "军心"}).json()
        assert edict["accepted"]
        assert edict["edict"]["status"] == "进行中"
    app.state.game_store.close()


def test_dialogue_decree_strategy_and_save_loop(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("LONGCAT_API_KEY", raising=False)
    app = create_app(tmp_path / "full-loop.db")
    with TestClient(app) as client:
        for topic in ("潼关应守还是战？", "朕答应事后酬功，请再陈利害", "军粮能支几日？"):
            reply = client.post("/api/audience", json={"character_id":"gao_lishi","topic":topic,"scene":"密诏"}).json()
            assert reply["accepted"]
        snapshot = client.get("/api/snapshot").json()
        assert len(snapshot["conversation"]["chats"]["gao_lishi"]) == 6
        assert snapshot["conversation"]["relationships"]["gao_lishi"]["promises"]

        decree = client.post("/api/decrees/freeform", json={"text":"命户部开仓赈济长安，发粮三十，并查军报真伪。"}).json()["decree"]
        confirmed = client.post(f"/api/decrees/{decree['id']}/confirm").json()
        assert confirmed["directives"]
        movement = client.post("/api/armies/move", json={"army_id":"tang_tongguan","destination":"lingbao"}).json()
        assert movement["movement"]["to"] == "lingbao"

        event = snapshot["progress"]["active_event"]
        resolved = client.post("/api/resolve", json={"event_choice":event["choices"][0]}).json()
        assert resolved["result"]["world_events"]
        slots = client.get("/api/saves").json()["slots"]
        assert any(slot["slot_id"] == 0 for slot in slots)
        client.post("/api/saves", json={"slot_id":2,"name":"测试存档"})
        assert app.state.game_store.conn.execute("SELECT payload_json FROM save_slots WHERE slot_id=2").fetchone()[0].find("state_hash") > 0
        loaded = client.post("/api/saves/2/load").json()
        assert loaded["loaded"]
    app.state.game_store.close()
