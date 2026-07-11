from anshi.strategy import initial_strategy, move, simulate_month


def test_movement_enemy_ai_and_battle_are_deterministic() -> None:
    catalog = {"armies": [
        {"id":"t","name":"唐军","power":"tang_xuanzong","region":"tongguan","present_strength":50000,"supply":70,"morale":70,"status":"据守","act_from":1},
        {"id":"y","name":"燕军","power":"yan_an","region":"shanjun","present_strength":40000,"supply":70,"morale":70,"status":"进攻","act_from":1},
    ]}
    state = initial_strategy(catalog)
    move(state, "t", "lingbao")
    events = simulate_month(state, 1, 1)
    assert state.armies["y"].region == "lingbao"
    assert any("会战" in event for event in events)
