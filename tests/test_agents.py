import json
from unittest.mock import patch

from anshi.ai import LLMConfig
from anshi.agents import (
    CouncilAgent,
    create_character_agent,
    create_court_script_agent,
    create_gazette_agent,
    create_minister_agent,
    create_narrator_agent,
    create_secretary_agent,
    create_simulator_agent,
    run_agent,
)
from anshi.prompts import (
    COURT_SCRIPT_SYSTEM,
    GAZETTE_SYSTEM,
    MINISTER_SYSTEM,
    SECRETARY_SYSTEM,
    court_script_user,
    gazette_user,
    minister_user,
    secretary_user,
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


def test_minister_agent_factory() -> None:
    config = LLMConfig("key", "https://example.test/v1", "test-model")
    character = {"name": "哥舒翰", "identity": "潼关主帅", "public_stance": "固守"}
    agent = create_minister_agent(character, "是否出战", {}, config=config)
    assert agent.name == "廷议大臣-哥舒翰"
    assert agent.role == "minister"
    assert agent.system_prompt == MINISTER_SYSTEM
    assert agent.config.api_key == "key"


def test_secretary_agent_factory() -> None:
    config = LLMConfig("key", "https://example.test/v1", "test-model")
    agent = create_secretary_agent("是否出战", [{"name": "A", "reply": "当守"}], config=config)
    assert agent.name == "中书舍人"
    assert agent.role == "secretary"
    assert agent.system_prompt == SECRETARY_SYSTEM


def test_character_agent_factory() -> None:
    config = LLMConfig("key", "https://example.test/v1", "test-model")
    character = {"name": "郭子仪"}
    agent = create_character_agent(character, "当前局势", scene="secret", config=config)
    assert agent.name == "奏对-郭子仪"
    assert "密诏" in agent.system_prompt


def test_narrator_agent_factory() -> None:
    config = LLMConfig("key", "https://example.test/v1", "test-model")
    agent = create_narrator_agent(config=config)
    assert agent.name == "史官"
    assert agent.role == "narrator"


def test_simulator_agent_factory() -> None:
    config = LLMConfig("key", "https://example.test/v1", "test-model")
    agent = create_simulator_agent(config=config)
    assert agent.name == "世界推演官"
    assert agent.role == "simulator"


def test_run_agent_calls_chat_completion() -> None:
    config = LLMConfig("secret", "https://example.test/v1", "test-model")
    agent = CouncilAgent("test", "minister", MINISTER_SYSTEM, config, temperature=0.5)
    captured = {}

    def fake_open(request, timeout):
        captured.update(json.loads(request.data))
        return FakeResponse("【态度：支持】臣以为当出击。")

    with patch("anshi.ai.urlopen", side_effect=fake_open):
        text, used = run_agent(agent, "是否出战", fallback="fallback", with_status=True)

    assert used is True
    assert "【态度：支持】" in text
    assert captured["messages"][0]["content"] == MINISTER_SYSTEM
    assert captured["messages"][1]["content"] == "是否出战"


def test_run_agent_fallback_on_no_config() -> None:
    agent = CouncilAgent("test", "minister", MINISTER_SYSTEM, LLMConfig("", "", ""), temperature=0.5)
    with patch.dict("os.environ", {}, clear=True):
        text, used = run_agent(agent, "test", fallback="fallback text", with_status=True)
    assert used is False
    assert text == "fallback text"


def test_run_agent_fallback_on_network_error() -> None:
    config = LLMConfig("secret", "https://example.test/v1", "test-model")
    agent = CouncilAgent("test", "minister", MINISTER_SYSTEM, config, temperature=0.5)
    with patch("anshi.ai.urlopen", side_effect=OSError("offline")):
        text, used = run_agent(agent, "test", fallback="offline fallback", with_status=True)
    assert used is False
    assert text == "offline fallback"


def test_minister_user_prompt_contains_context() -> None:
    character = {"name": "哥舒翰", "identity": "潼关主帅", "public_stance": "固守"}
    context = {"章节": "潼关对峙", "年月": "756年6月"}
    prompt = minister_user(character, "是否出战", context, round_no=1)
    assert "哥舒翰" in prompt
    assert "潼关主帅" in prompt
    assert "固守" in prompt
    assert "第一轮表态" in prompt


def test_minister_user_prompt_round2_includes_minutes() -> None:
    character = {"name": "李光弼"}
    prompt = minister_user(character, "是否出战", {}, round_no=2, previous_speech="郭子仪：当出击", minutes="群臣分歧")
    assert "第二轮交锋" in prompt
    assert "郭子仪：当出击" in prompt
    assert "群臣分歧" in prompt


def test_secretary_user_prompt_final_includes_recommendation() -> None:
    speeches = [{"name": "A", "reply": "当守"}, {"name": "B", "reply": "当出"}]
    prompt = secretary_user("是否出战", speeches, is_final=True)
    assert "最终纪要" in prompt
    assert "谏议" in prompt


def test_for_role_returns_advanced_for_simulator() -> None:
    cfg = LLMConfig("key", "https://main.test/v1", "main-model", advanced_model="adv-model", advanced_base_url="https://adv.test/v1", advanced_api_key="adv-key")
    from anshi.ai import for_role
    result = for_role(cfg, "simulator")
    assert result.model == "adv-model"
    assert result.base_url == "https://adv.test/v1"
    assert result.api_key == "adv-key"


def test_for_role_returns_main_for_unknown_role() -> None:
    cfg = LLMConfig("key", "https://main.test/v1", "main-model", advanced_model="adv-model")
    from anshi.ai import for_role
    result = for_role(cfg, "minister")
    assert result.model == "main-model"
    assert result.api_key == "key"


def test_for_role_fallback_when_no_advanced() -> None:
    cfg = LLMConfig("key", "https://main.test/v1", "main-model")
    from anshi.ai import for_role
    result = for_role(cfg, "simulator")
    assert result.model == "main-model"


def test_court_script_agent_factory() -> None:
    config = LLMConfig("key", "https://example.test/v1", "test-model")
    agent = create_court_script_agent(config=config)
    assert agent.name == "朝会编剧"
    assert agent.role == "court_script"
    assert agent.system_prompt == COURT_SCRIPT_SYSTEM


def test_gazette_agent_factory() -> None:
    config = LLMConfig("key", "https://example.test/v1", "test-model")
    agent = create_gazette_agent(config=config)
    assert agent.name == "邸报官"
    assert agent.role == "gazette"
    assert agent.system_prompt == GAZETTE_SYSTEM


def test_court_script_user_prompt() -> None:
    characters = [
        {"name": "哥舒翰", "identity": "潼关主帅", "public_stance": "固守", "attributes": {"loyalty": 70, "administration": 60, "military": 80}},
        {"name": "杨国忠", "identity": "宰相", "public_stance": "出击", "attributes": {"loyalty": 30, "administration": 70, "military": 20}},
    ]
    prompt = court_script_user("潼关应当固守还是出击", characters, {}, round_no=1)
    assert "哥舒翰" in prompt
    assert "杨国忠" in prompt
    assert "第一轮表态" in prompt
    assert "潼关" in prompt


def test_court_script_user_prompt_round2() -> None:
    characters = [{"name": "A", "identity": "臣", "public_stance": "守", "attributes": {"loyalty": 50, "administration": 50, "military": 50}}]
    prompt = court_script_user("议题", characters, {}, round_no=2, previous_minutes="前轮纪要")
    assert "第二轮交锋" in prompt
    assert "前轮纪要" in prompt


def test_gazette_user_prompt() -> None:
    data = {"日期": "756年6月", "纪事": "潼关固守", "天下演化": ["事件1"], "财务": {"现银": 100}}
    prompt = gazette_user(data)
    assert "756年6月" in prompt
    assert "潼关固守" in prompt
