from anshi.core import apply_order, initial_state
from anshi.storage import GameStore


def test_state_and_turn_survive_reopen(tmp_path) -> None:
    path = tmp_path / "game.db"
    store = GameStore(path)
    state = store.load()
    result = apply_order(state, "verify")
    store.record_turn("verify", result)
    store.save(state)
    store.close()

    reopened = GameStore(path)
    loaded = reopened.load()
    assert loaded.intel_confidence == 52
    assert loaded.clock.day == 3
    assert loaded.intel_claims[0].id == "south_mountain_movement"
    assert reopened.revision() == 2
    assert reopened.conn.execute("SELECT COUNT(*) FROM turn_log").fetchone()[0] == 1
    reopened.close()


def test_legacy_payload_is_upgraded() -> None:
    from anshi.storage import state_from_payload

    payload = initial_state().payload()
    payload.pop("clock")
    payload.pop("intel_claims")
    payload["day"] = 5
    payload["date_label"] = "天宝十五载 六月初五"
    payload["known_intel"] = ["旧军报"]

    upgraded = state_from_payload(payload)

    assert upgraded.clock.day == 5
    assert upgraded.intel_claims[0].summary == "旧军报"
