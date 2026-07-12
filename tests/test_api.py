import os

from fastapi.testclient import TestClient

# ponytail: prevent .env from loading real API keys during tests
os.environ["ANSHI_TESTING"] = "1"

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


def test_complete_management_loop_uses_snapshot_audience_and_directives(tmp_path, monkeypatch) -> None:
    import apps.api.routes.council as _council_mod
    monkeypatch.setattr(_council_mod, "generate_character_reply", lambda character, topic, scene="court", context=None, config=None, with_status=False: (f"{character.get('name', '臣下')}奏道：{topic}之事，钱粮为要。", False))
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
    import apps.api.routes.decree as _decree_mod
    monkeypatch.setattr(_decree_mod, "generate_decree_candidates", lambda text, targets: ([{"kind": "relief", "target": "changan", "amount": 30, "subject": "", "reason": "文书模型解析"}], True))
    monkeypatch.setattr(_decree_mod, "polish_document", lambda text: (f"奉天承运皇帝诏曰：{text}", True))
    app = create_app(tmp_path / "full-loop.db")
    with TestClient(app) as client:
        for topic in ("潼关应守还是战？", "朕答应事后酬功，请再陈利害", "军粮能支几日？"):
            reply = client.post("/api/audience", json={"character_id":"gao_lishi","topic":topic,"scene":"密诏"}).json()
            assert reply["accepted"]
        snapshot = client.get("/api/snapshot").json()
        assert len(snapshot["conversation"]["chats"]["gao_lishi"]) == 6
        assert snapshot["conversation"]["relationships"]["gao_lishi"]["promises"]

        event = snapshot["progress"]["active_event"]
        queued_choice = client.post("/api/events/choice", json={"choice": event["choices"][0]}).json()
        assert queued_choice["accepted"]
        assert client.get("/api/snapshot").json()["progress"]["total_turn"] == 1

        decree = client.post("/api/decrees/freeform", json={"text":"命户部开仓赈济长安，发粮三十，并查军报真伪。"}).json()["decree"]
        assert decree["decision"]["choice"] == event["choices"][0]
        assert decree["model_used"] and decree["parser_model_used"]
        confirmed = client.post(f"/api/decrees/{decree['id']}/confirm").json()
        assert confirmed["directives"]
        movement = client.post("/api/armies/move", json={"army_id":"tang_tongguan","destination":"lingbao"}).json()
        assert movement["movement"]["to"] == "lingbao"
        assert movement["movement"]["queued"]
        assert movement["strategy"]["armies"]["tang_tongguan"]["region"] == "tongguan"
        invalid_movement = client.post("/api/armies/move", json={"army_id":"tang_tongguan","destination":"fanyang"})
        assert invalid_movement.status_code == 400

        resolved = client.post("/api/resolve", json={}).json()
        assert resolved["result"]["world_events"]
        assert client.get("/api/snapshot").json()["strategy"]["armies"]["tang_tongguan"]["region"] == "lingbao"
        assert client.get("/api/snapshot").json()["conversation"]["freeform_decrees"][0]["status"] == "已颁行"
        slots = client.get("/api/saves").json()["slots"]
        assert any(slot["slot_id"] == 0 for slot in slots)
        client.post("/api/saves", json={"slot_id":2,"name":"测试存档"})
        assert app.state.game_store.conn.execute("SELECT payload_json FROM save_slots WHERE slot_id=2").fetchone()[0].find("state_hash") > 0
        loaded = client.post("/api/saves/2/load").json()
        assert loaded["loaded"]
    app.state.game_store.close()
