from anshi.campaign import initial_progress
from anshi.core import initial_state
from anshi.management import initial_state as initial_management
from anshi.situations import advance_situations, policy_catalog, resolve_policy, select_policy


def test_model_situation_delta_is_bounded_and_completion_adds_modifier() -> None:
    progress = initial_progress()
    state = initial_state()
    management = initial_management()
    progress.situations[0]["progress"] = 95

    events = advance_situations(
        progress,
        state,
        management,
        [{"id": "tongguan_command", "delta": 99, "reason": "军令已趋统一", "confidence": 0.9}],
    )

    assert progress.situations[0]["status"] == "已完成"
    assert progress.situations[0]["progress"] == 100
    assert any(item["name"] == "军令一体" for item in progress.modifiers)
    assert state.military_power == 63
    assert any("局势完成" in item for item in events)


def test_policy_requires_prerequisite_and_resolves_only_on_turn_settlement() -> None:
    progress = initial_progress()
    state = initial_state()
    management = initial_management()

    try:
        select_policy(progress, "shuofang_recruit")
    except ValueError as error:
        assert "前置" in str(error)
    else:
        raise AssertionError("locked policy should not be selectable")

    select_policy(progress, "reinforce_tongguan")
    assert progress.active_policy == "reinforce_tongguan"
    assert not progress.completed_policies

    events = resolve_policy(progress, state, management)
    assert "reinforce_tongguan" in progress.completed_policies
    assert not progress.active_policy
    assert policy_catalog(progress)[0]["completed"]
    assert any("帝国修正" in item for item in events)
