from app.agent.god_orchestrator import GodOrchestrator


def test_strip_agent_prefix_when_reasoning_promoted_to_speech() -> None:
    result = {
        "reasoning": "[api:cat-agent] [model:x] 我建议先从票型分布观察可疑对象。",
    }

    speech, thinking = GodOrchestrator._split_day_discuss_texts(result, default_speech="默认")

    assert speech.startswith("我建议先从票型分布观察可疑对象")
    assert "[api:cat-agent]" not in speech
    assert thinking == ""
