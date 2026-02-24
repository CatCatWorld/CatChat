from app.agent.ai_god_orchestrator import AIGodOrchestrator
from app.agent.god_orchestrator import GodOrchestrator
from app.engine.game_engine import GameEngine


def test_day_discuss_public_speech_sanitizes_definitive_wolf_claims() -> None:
    raw = "上一轮投票里，蓝猫（狼人）跳得太高，他就是狼人。"

    s1 = GodOrchestrator._sanitize_day_discuss_public_speech(raw)
    s2 = AIGodOrchestrator._sanitize_day_discuss_public_speech(raw)

    assert "（疑似狼人）" in s1
    assert "就是狼人" not in s1
    assert "（疑似狼人）" in s2
    assert "就是狼人" not in s2


def test_day_discuss_public_speech_keeps_definitive_claim_for_seer_check_result() -> None:
    raw = "昨晚我查验了折耳，他就是狼人。我是预言家，信息可靠。"

    s1 = GodOrchestrator._sanitize_day_discuss_public_speech(raw)
    s2 = AIGodOrchestrator._sanitize_day_discuss_public_speech(raw)

    assert "就是狼人" in s1
    assert "疑似狼人" not in s1
    assert "就是狼人" in s2
    assert "疑似狼人" not in s2


def test_day_discuss_public_speech_still_sanitizes_without_explicit_target() -> None:
    raw = "昨晚我查验了，他就是狼人。我是预言家，信息可靠。"

    s1 = GodOrchestrator._sanitize_day_discuss_public_speech(raw)
    s2 = AIGodOrchestrator._sanitize_day_discuss_public_speech(raw)

    assert "就是狼人" not in s1
    assert "疑似狼人" in s1
    assert "就是狼人" not in s2
    assert "疑似狼人" in s2


def test_day_discuss_public_speech_still_sanitizes_without_round_time_hint() -> None:
    raw = "我查验了折耳，他就是狼人。我是预言家，信息可靠。"

    s1 = GodOrchestrator._sanitize_day_discuss_public_speech(raw)
    s2 = AIGodOrchestrator._sanitize_day_discuss_public_speech(raw)

    assert "就是狼人" not in s1
    assert "疑似狼人" in s1
    assert "就是狼人" not in s2
    assert "疑似狼人" in s2


def test_day_discuss_public_speech_sanitizes_wolf_identity_exposure_phrase() -> None:
    raw = "伪装好人，支持女巫信息，呼吁预言家起跳，避免暴露狼人身份。"

    s1 = GodOrchestrator._sanitize_day_discuss_public_speech(raw)
    s2 = AIGodOrchestrator._sanitize_day_discuss_public_speech(raw)

    assert "狼人身份" not in s1
    assert "暴露真实身份" in s1
    assert "狼人身份" not in s2
    assert "暴露真实身份" in s2


def test_engine_audit_applies_day_discuss_identity_sanitize() -> None:
    engine = GameEngine(room_id="r_day_sanitize", owner_id="owner")
    engine._audit(
        "agent_speech",
        "p1",
        {
            "phase": "day_discuss",
            "role": "werewolf",
            "content": "伪装好人并避免暴露狼人身份。他就是狼人。",
        },
    )

    payload = (engine.snapshot.action_audit_log[-1].get("payload") or {})
    content = str(payload.get("content") or "")
    assert "狼人身份" not in content
    assert "暴露真实身份" in content
    assert "就是狼人" not in content
