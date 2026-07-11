from pathlib import Path
import json

from anshi.content import load_scenario


def test_tongguan_scenario_is_connected_and_referenced() -> None:
    root = Path(__file__).parents[1] / "content" / "scenarios" / "tongguan_756"
    scenario = load_scenario(root)

    assert scenario.manifest.content_version == "0.5.0"
    assert len(scenario.regions) == 4
    assert len(scenario.armies) == 2
    assert len(scenario.characters) == 8
    assert [act.id for act in scenario.acts] == ["act1", "act2", "act3", "act4", "act5"]


def test_complete_campaign_catalog_has_cross_act_content() -> None:
    root = Path(__file__).parents[1] / "content" / "scenarios" / "tongguan_756"
    catalog = json.loads((root / "campaign.json").read_text(encoding="utf-8"))

    assert len(catalog["regions"]) == 16
    assert len(catalog["armies"]) == 13
    assert len(catalog["characters"]) == 21
    assert len(catalog["acts"]) == 5
    assert sum(len(act["event_candidates"]) for act in catalog["acts"]) == 18
    extra = json.loads((root / "characters_extra.json").read_text(encoding="utf-8"))
    assert len(extra) == 10
    assert all(character["public_stance"] and character["available_from"] for character in extra)
