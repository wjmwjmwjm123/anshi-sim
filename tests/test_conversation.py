from anshi.conversation import ConversationState, confirm_decree, context_for, draft_freeform, record_exchange


def test_conversation_builds_memory_relationship_and_freeform_decree() -> None:
    state = ConversationState()
    for index in range(3):
        topic = f"朕答应事后酬功，第{index}次密查军心"
        record_exchange(state, "gao_lishi", topic, "臣领密旨。", "密诏", 1)
    context = context_for(state, "gao_lishi")
    assert len(context["近期对话"]) == 6
    assert context["君臣关系"]["trust"] == 53
    assert context["君臣关系"]["promises"]

    candidates = [{"kind": "relief", "target": "changan", "amount": 30, "subject": "", "reason": "文书模型解析"}]
    decree = draft_freeform(state, "命户部开仓赈济长安，发粮三十，另查军报真伪。", 1, candidates)
    assert decree["candidates"] == candidates
    assert confirm_decree(state, decree["id"])["status"] == "已确认"


def test_freeform_decree_keeps_validated_model_candidates() -> None:
    state = ConversationState()
    candidates = [{"kind": "mediate", "target": "court_conflict", "amount": 20, "subject": "", "reason": "模型解析"}]
    decree = draft_freeform(state, "召宰相与主帅当殿释疑，停止彼此攻讦。", 1, candidates)
    assert decree["candidates"] == candidates


def test_freeform_decree_does_not_keyword_parse_actions_without_model_output() -> None:
    decree = draft_freeform(ConversationState(), "命户部开仓赈济长安，发粮三十。", 1)
    assert decree["candidates"] == []
