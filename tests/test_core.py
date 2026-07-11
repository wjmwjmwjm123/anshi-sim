from anshi.core import apply_order, initial_state


def test_verify_reveals_ambush_without_changing_army() -> None:
    state = initial_state()
    result = apply_order(state, "verify")

    assert state.intel_confidence == 52
    assert state.army.present_strength == 178_000
    assert "南山" in state.intel_claims[0].summary
    assert state.intel_claims[0].independent
    assert state.clock.windows[0].status == "resolved"
    assert result["command"]["lifecycle"] == ["draft", "validated", "dispatched", "executing", "completed"]
    assert result["diff"]


def test_sally_is_replayable_and_ends_slice() -> None:
    first = initial_state()
    second = initial_state()

    one = apply_order(first, "sally")
    two = apply_order(second, "sally")

    assert one == two
    assert first.ended
    assert first.act_id == "act2"
    assert first.chapter_transition["trigger"] == "tongguan_fallen"
    assert first.army.present_strength == 71_000
    assert first.army.fit_strength == 28_000


def test_verified_sally_retreats_without_total_collapse() -> None:
    state = initial_state()
    apply_order(state, "verify")
    result = apply_order(state, "sally")

    assert not state.ended
    assert state.army.fit_strength == 77_000
    assert result["headline"] == "伏兵虽发，前军有备而退"


def test_full_preparation_turns_rout_into_orderly_retreat() -> None:
    state = initial_state()
    for order in ("verify", "reconcile", "constrain", "prepare_retreat"):
        apply_order(state, order)

    result = apply_order(state, "sally")

    assert result["headline"] == "伏兵虽发，诸军按旗而退"
    assert state.army.fit_strength >= 88_000
    assert not state.ended


def test_holding_after_deadline_can_be_refused_without_advancing_time() -> None:
    state = initial_state()
    for _ in range(4):
        apply_order(state, "hold")
    day = state.clock.day

    result = apply_order(state, "hold")

    assert not result["accepted"]
    assert result["command"]["status"] == "refused"
    assert state.clock.day == day
