from copy import deepcopy

from anshi.management import draft, initial_state, remove, resolve


def test_queue_remove_and_replay_are_deterministic() -> None:
    first = initial_state()
    removed = draft(first, "tax", "henan", 10)
    assert remove(first, removed.id)
    draft(first, "relief", "guanzhong", 10)
    draft(first, "supply", "tongguan", 8)

    second = deepcopy(first)
    one = resolve(first).payload()
    two = resolve(second).payload()

    assert one == two
    assert not first.directives
    assert all(report["accepted"] for report in one["reports"])
    assert any(change["path"] == "regions.guanzhong.support" for change in one["diff"])


def test_all_directive_kinds_update_their_domain() -> None:
    state = initial_state()
    draft(state, "relief", "guanzhong", 10)
    draft(state, "tax", "henan", 10)
    draft(state, "supply", "tongguan", 5)
    draft(state, "mobilize", "shuofang", 4, "guanzhong")
    draft(state, "fortify", "guanzhong", 6)
    draft(state, "investigate", "refugees", 20, "geshu_han")
    draft(state, "appoint", "geshu_han", 1, "天下兵马副元帅")
    draft(state, "mediate", "court_conflict", 20, "yang_guozhong")

    result = resolve(state)

    assert len(result.reports) == 8
    assert all(report.accepted for report in result.reports)
    assert state.regions["guanzhong"].fortification == 41
    assert state.armies["shuofang"].strength == 59_000
    assert state.issues["refugees"].assignee == "geshu_han"
    assert state.characters["geshu_han"].office == "天下兵马副元帅"
    assert state.issues["court_conflict"].tension == 61


def test_invalid_or_unaffordable_directives_are_reported_without_partial_effects() -> None:
    state = initial_state()
    state.finance.cash = 0
    state.finance.monthly_income = 0
    state.finance.monthly_expenses = 0
    draft(state, "fortify", "guanzhong", 100)
    draft(state, "relief", "missing", 10)
    draft(state, "investigate", "refugees", 10, "missing")

    result = resolve(state)

    assert [report.accepted for report in result.reports] == [False, False, False]
    assert state.regions["guanzhong"].fortification == 35
    assert state.issues["refugees"].progress == 20
    assert result.reports[0].reason == "现银不足"
