import json
from unittest.mock import patch

from anshi.ai import (
    LLMConfig,
    generate_character_reply,
    generate_decree_candidates,
    generate_turn_narration,
    generate_world_proposal,
    load_config,
)


class FakeResponse:
    def __init__(self, text: str):
        self.body = json.dumps({"choices": [{"message": {"content": text}}]}).encode()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def read(self) -> bytes:
        return self.body


def test_longcat_fallback_config() -> None:
    config = load_config({"LONGCAT_API_KEY": "secret"})

    assert config is not None
    assert config.api_key == "secret"
    assert config.base_url == "https://api.longcat.chat/openai/v1"
    assert config.model == "LongCat-2.0"


def test_ark_global_config_can_back_all_model_roles() -> None:
    env = {
        "ARK_API_KEY": "secret",
        "ARK_BASE_URL": "https://ark.example.test/api/v3",
        "ARK_MODEL": "doubao-test",
    }
    for role in ("chat", "simulation", "utility"):
        config = load_config(env, role=role)
        assert config is not None
        assert config.base_url == "https://ark.example.test/api/v3"
        assert config.model == "doubao-test"


def test_ark_key_without_model_is_not_reported_as_ready() -> None:
    assert load_config({"ARK_API_KEY": "secret"}, role="simulation") is None


def test_image_only_ark_key_does_not_hide_longcat_chat_config() -> None:
    config = load_config({"ARK_API_KEY": "image-secret", "LONGCAT_API_KEY": "chat-secret"})
    assert config is not None
    assert config.api_key == "chat-secret"
    assert config.model == "LongCat-2.0"


def test_role_config_overrides_general_model() -> None:
    config = load_config({"OPENAI_API_KEY": "general", "OPENAI_MODEL": "small", "SIMULATION_API_KEY": "strong", "SIMULATION_MODEL": "large"}, role="simulation")
    assert config is not None
    assert config.api_key == "strong"
    assert config.model == "large"


def test_character_scenes_send_distinct_prompts() -> None:
    config = LLMConfig("secret", "https://example.test/v1", "test-model")
    character = {"name": "哥舒翰", "identity": "潼关主帅", "public_stance": "应当固守潼关"}
    requests = []

    def fake_open(request, timeout):
        requests.append((request, timeout))
        return FakeResponse("臣请固守。")

    with patch("anshi.ai.urlopen", side_effect=fake_open):
        replies = [generate_character_reply(character, "是否出关？", scene, config=config) for scene in ("court", "secret", "remote")]

    prompts = [json.loads(item[0].data)["messages"][0]["content"] for item in requests]
    assert replies == ["臣请固守。"] * 3
    assert "公开奏对" in prompts[0]
    assert "密诏召对" in prompts[1]
    assert "递交远奏" in prompts[2]
    assert all(item[0].get_header("Authorization") == "Bearer secret" for item in requests)


def test_turn_narration_sends_read_only_result_without_mutation() -> None:
    config = LLMConfig("secret", "https://example.test/v1/chat/completions", "test-model")
    result = {"turn": 3, "reports": [{"accepted": True, "headline": "开仓赈济"}], "diff": [{"path": "finance.grain", "delta": -30}]}
    original = json.loads(json.dumps(result))
    captured = {}

    def fake_open(request, timeout):
        captured.update(json.loads(request.data))
        return FakeResponse("本月开仓赈济，储粮减少三十。")

    with patch("anshi.ai.urlopen", side_effect=fake_open):
        narration = generate_turn_narration(result, config)

    assert narration == "本月开仓赈济，储粮减少三十。"
    assert result == original
    assert "不得修改" in captured["messages"][0]["content"]
    assert '"delta":-30' in captured["messages"][1]["content"]


def test_missing_config_and_network_failure_use_chinese_fallbacks() -> None:
    character = {"name": "郭子仪", "public_stance": "先保朔方军心"}
    with patch.dict("os.environ", {}, clear=True):
        assert "当殿奏道" in generate_character_reply(character, "如何用兵？", "court")
        assert "低声奏道" in generate_character_reply(character, "太子何在？", "secret")
        assert "远奏" in generate_character_reply(character, "军粮如何？", "remote")

    config = LLMConfig("secret", "https://example.test/v1", "test-model")
    with patch("anshi.ai.urlopen", side_effect=OSError("offline")):
        text = generate_turn_narration(
            {"turn": 2, "reports": [{"accepted": True}, {"accepted": False}], "diff": []},
            config,
        )
    assert text == "第2回合结算完毕：施行诏令1道，留中或未行1道。钱粮、军务与地方变化均已依规则写入实录。"


def test_invalid_scene_is_rejected_before_network() -> None:
    try:
        generate_character_reply({"name": "高力士"}, "当前局势", "hall")  # type: ignore[arg-type]
    except ValueError as error:
        assert "未知奏对场景" in str(error)
    else:
        raise AssertionError("invalid scene should fail")


def test_world_proposal_extracts_structured_json() -> None:
    config = LLMConfig("secret", "https://example.test/v1", "simulation-model")
    body = '{"assessment":"军心动摇","proposals":[],"npc_actions":[],"event_seeds":["撤离争论"]}'
    with patch("anshi.ai.urlopen", return_value=FakeResponse(body)):
        proposal, used = generate_world_proposal({"turn": 2}, config)

    assert used is True
    assert proposal["assessment"] == "军心动摇"
    assert proposal["event_seeds"] == ["撤离争论"]


def test_decree_candidates_extract_structured_actions() -> None:
    config = LLMConfig("secret", "https://example.test/v1", "utility-model")
    body = '{"candidates":[{"kind":"supply","target":"tang_tongguan","amount":30,"subject":"","reason":"转运军粮"}]}'
    with patch("anshi.ai.urlopen", return_value=FakeResponse(body)):
        candidates, used = generate_decree_candidates("向潼关转运军粮三十", {"armies": {"tang_tongguan": "潼关军"}}, config)

    assert used is True
    assert candidates[0]["target"] == "tang_tongguan"
