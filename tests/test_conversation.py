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

    decree = draft_freeform(state, "命户部开仓赈济长安，发粮三十，另查军报真伪。", 1)
    assert {item["kind"] for item in decree["candidates"]} == {"relief", "supply", "investigate"}
    assert confirm_decree(state, decree["id"])["status"] == "已确认"
