from anshi.management import initial_state
from anshi.world_simulation import apply_world_proposal


def test_world_proposal_applies_only_allowlisted_bounded_changes() -> None:
    state = initial_state()
    result = apply_world_proposal(
        {
            "assessment": "败报引发关中震动",
            "proposals": [
                {"path": "regions.guanzhong.support", "operation": "add", "value": -20, "reason": "败报", "confidence": 0.9},
                {"path": "armies.tongguan.morale", "operation": "add", "value": 4, "reason": "整军", "confidence": 0.8},
                {"path": "finance.cash", "operation": "add", "value": 999, "reason": "幻觉", "confidence": 1},
                {"path": "issues.court_conflict.tension", "operation": "set", "value": 1, "reason": "非法操作", "confidence": 1},
                {"path": "characters.geshu_han.loyalty", "operation": "add", "value": -2, "reason": "受疑", "confidence": 0.2},
            ],
            "event_seeds": ["长安撤离争论"],
        },
        state,
    )

    assert state.regions["guanzhong"].support == 34  # requested -20, bounded to -4
    assert state.armies["tongguan"].morale == 47
    assert state.finance.cash == 1_000
    assert state.issues["court_conflict"].tension == 80
    assert state.characters["geshu_han"].loyalty == 62
    assert len(result["accepted"]) == 2
    assert len(result["rejected"]) == 3
    assert result["event_seeds"] == ["长安撤离争论"]
