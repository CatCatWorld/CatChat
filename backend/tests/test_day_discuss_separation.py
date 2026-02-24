from app.agent.ai_god_orchestrator import AIGodOrchestrator
from app.agent.god_orchestrator import GodOrchestrator
from types import SimpleNamespace


def test_day_discuss_split_uses_speech_and_thinking_fields() -> None:
    result = {
        "speech": "我怀疑2号昨夜发言矛盾。",
        "thinking": "2号更像狼人，先试探票型。",
        "reasoning": "这段不应直接公开",
    }

    speech_1, thinking_1 = GodOrchestrator._split_day_discuss_texts(result, default_speech="默认发言")
    speech_2, thinking_2 = AIGodOrchestrator._split_day_discuss_texts(result, default_speech="默认发言")

    assert speech_1 == "我怀疑2号昨夜发言矛盾。"
    assert thinking_1 == "2号更像狼人，先试探票型。"
    assert speech_2 == "我怀疑2号昨夜发言矛盾。"
    assert thinking_2 == "2号更像狼人，先试探票型。"


def test_day_discuss_split_falls_back_to_default_public_speech() -> None:
    result = {
        "reasoning": "我真实想法是3号嫌疑最大，但这属于内部推理。",
    }

    speech_1, thinking_1 = GodOrchestrator._split_day_discuss_texts(result, default_speech="我先听听大家的意见。")
    speech_2, thinking_2 = AIGodOrchestrator._split_day_discuss_texts(result, default_speech="我先听听大家的意见。")

    assert speech_1 == "我先听听大家的意见。"
    assert thinking_1 == "我真实想法是3号嫌疑最大，但这属于内部推理。"
    assert speech_2 == "我先听听大家的意见。"
    assert thinking_2 == "我真实想法是3号嫌疑最大，但这属于内部推理。"


def test_day_discuss_split_uses_reasoning_as_public_speech_when_safe() -> None:
    result = {
        "reasoning": "[api:cat-agent] 我倾向先观察2号和5号的发言矛盾，再决定投票目标。",
    }

    speech_1, thinking_1 = GodOrchestrator._split_day_discuss_texts(result, default_speech="我先听听大家的意见。")
    speech_2, thinking_2 = AIGodOrchestrator._split_day_discuss_texts(result, default_speech="我先听听大家的意见。")

    assert speech_1.startswith("我倾向先观察2号")
    assert thinking_1 == ""
    assert speech_2.startswith("我倾向先观察2号")
    assert thinking_2 == ""


def test_day_vote_split_does_not_promote_reasoning_to_public_speech() -> None:
    result = {
        "reasoning": "[api:cat-agent] 我会先跟票压制高嫌疑位，本轮投票给3号。",
    }

    speech_1, thinking_1 = GodOrchestrator._split_day_vote_texts(result, default_speech="我选择弃票。")
    speech_2, thinking_2 = AIGodOrchestrator._split_day_vote_texts(result, default_speech="我选择弃票。")

    assert speech_1 == "我选择弃票。"
    assert "本轮投票给3号" in thinking_1
    assert speech_2 == "我选择弃票。"
    assert "本轮投票给3号" in thinking_2


def test_day_vote_split_keeps_private_reasoning_as_thinking() -> None:
    result = {
        "reasoning": "真实想法：2号更像狼，但这段不要公开。",
    }

    speech_1, thinking_1 = GodOrchestrator._split_day_vote_texts(result, default_speech="我选择弃票。")
    speech_2, thinking_2 = AIGodOrchestrator._split_day_vote_texts(result, default_speech="我选择弃票。")

    assert speech_1 == "我选择弃票。"
    assert "真实想法" in thinking_1
    assert speech_2 == "我选择弃票。"
    assert "真实想法" in thinking_2


def test_day_discuss_split_prefix_only_reasoning_falls_back_to_default() -> None:
    result = {
        "reasoning": "[api:cat-agent]",
    }

    speech_1, thinking_1 = GodOrchestrator._split_day_discuss_texts(result, default_speech="我先听听大家的意见。")
    speech_2, thinking_2 = AIGodOrchestrator._split_day_discuss_texts(result, default_speech="我先听听大家的意见。")

    assert speech_1 == "我先听听大家的意见。"
    assert thinking_1 == ""
    assert speech_2 == "我先听听大家的意见。"
    assert thinking_2 == ""


def test_day_vote_split_prefix_only_reasoning_falls_back_to_default() -> None:
    result = {
        "reasoning": "[api:cat-agent]",
    }

    speech_1, thinking_1 = GodOrchestrator._split_day_vote_texts(result, default_speech="我选择弃票。")
    speech_2, thinking_2 = AIGodOrchestrator._split_day_vote_texts(result, default_speech="我选择弃票。")

    assert speech_1 == "我选择弃票。"
    assert thinking_1 == ""
    assert speech_2 == "我选择弃票。"
    assert thinking_2 == ""


def test_vote_speech_text_removes_abstain_conflict_when_target_exists() -> None:
    engine = SimpleNamespace(snapshot=SimpleNamespace(players={"p1": SimpleNamespace(nickname="蓝猫")}))
    base = "我投票给 蓝猫。我选择弃票。"

    s1 = GodOrchestrator()._vote_speech_text(engine, "p1", base)
    s2 = AIGodOrchestrator()._vote_speech_text(engine, "p1", base)

    assert "投票给" in s1
    assert "弃票" not in s1
    assert "投票给" in s2
    assert "弃票" not in s2


def test_vote_speech_text_removes_target_conflict_when_abstain() -> None:
    engine = SimpleNamespace(snapshot=SimpleNamespace(players={"p1": SimpleNamespace(nickname="蓝猫")}))
    base = "我投票给 蓝猫。"

    s1 = GodOrchestrator()._vote_speech_text(engine, None, base)
    s2 = AIGodOrchestrator()._vote_speech_text(engine, None, base)

    assert "弃票" in s1
    assert "投票给" not in s1
    assert "弃票" in s2
    assert "投票给" not in s2


def test_witch_speech_text_keeps_action_conclusion_consistent() -> None:
    engine = SimpleNamespace(
        snapshot=SimpleNamespace(
            players={
                "p2": SimpleNamespace(nickname="波斯猫"),
                "p3": SimpleNamespace(nickname="奶牛猫"),
            },
            round_context=SimpleNamespace(wolf_target="p2"),
        )
    )
    result = {
        "speech": "今晚局势很乱，我先稳住节奏。我不使用解药，也不使用毒药。",
    }

    s1 = GodOrchestrator()._witch_speech_text(engine, result, target_id="p3", save=True)
    s2 = AIGodOrchestrator()._witch_speech_text(engine, result, target_id="p3", save=True)

    assert "使用解药：是（救助目标：波斯猫）。" in s1
    assert "使用毒药：是（毒杀目标：奶牛猫）。" in s1
    assert "不使用解药" not in s1
    assert "不使用毒药" not in s1

    assert "使用解药：是（救助目标：波斯猫）。" in s2
    assert "使用毒药：是（毒杀目标：奶牛猫）。" in s2
    assert "不使用解药" not in s2
    assert "不使用毒药" not in s2
