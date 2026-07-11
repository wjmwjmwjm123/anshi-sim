from anshi.campaign import ACT_LENGTHS, add_secret_edict, advance, initial_progress


def test_five_acts_advance_and_end_deterministically() -> None:
    progress = initial_progress()
    seen = {1}
    for _ in range(sum(ACT_LENGTHS.values()) + 10):
        choice = progress.active_event.choices[0] if progress.active_event else ""
        result = advance(progress, choice)
        seen.add(progress.act)
        if progress.ending:
            break
        if not result["advanced"] and progress.active_event:
            advance(progress, progress.active_event.choices[0])
    assert seen == {1, 2, 3, 4, 5}
    assert progress.ending
    assert progress.year >= 762


def test_event_requires_choice_and_secret_edict_persists() -> None:
    progress = initial_progress()
    assert progress.active_event
    blocked = advance(progress)
    assert blocked["requires_choice"]
    edict = add_secret_edict(progress, "高力士", "暗查禁军军心", "军情")
    assert edict["status"] == "进行中"
    for _ in range(3):
        if progress.active_event:
            advance(progress, progress.active_event.choices[0])
        else:
            advance(progress)
    assert progress.secret_edicts[0]["status"] == "已办结"
