from app.agent.fallback_strategies import FallbackStrategies


def test_day_vote_fallback_emits_speech_and_thinking() -> None:
    strategies = FallbackStrategies()
    result = strategies.get_action(
        "day_vote",
        {
            "player_id": "p1",
            "alive_player_ids": ["p1", "p2", "p3"],
        },
    )

    assert isinstance(result.get("speech"), str)
    assert result.get("speech", "").strip()
    assert isinstance(result.get("thinking"), str)
    assert result.get("thinking", "").strip()


def test_day_vote_template_backfills_speech_and_thinking() -> None:
    strategies = FallbackStrategies()
    strategies._templates["day_vote"] = {
        "action": {"type": "vote", "target": "p2"},
        "reasoning": "我倾向先跟票压制高嫌疑位。",
    }

    result = strategies.get_action(
        "day_vote",
        {
            "player_id": "p1",
            "alive_player_ids": ["p1", "p2", "p3"],
        },
    )

    assert result.get("speech", "").strip()
    assert result.get("thinking", "").strip()


def test_night_wolf_fallback_uses_explicit_target_when_available() -> None:
    strategies = FallbackStrategies()
    result = strategies.get_action(
        "night_wolf",
        {
            "player_id": "w1",
            "alive_player_ids": ["w1", "w2", "p3", "p4"],
            "wolf_team_ids": ["w1", "w2"],
        },
    )

    target = ((result.get("action") or {}).get("target") or "").strip()
    reasoning = str(result.get("reasoning") or "")

    assert target in {"p3", "p4"}
    assert "建议今晚击杀" in reasoning
    assert "暂未确定今晚目标" not in reasoning
    assert "暂无目标" not in reasoning


def test_night_wolf_template_backfill_avoids_ambiguous_wording_without_target() -> None:
    strategies = FallbackStrategies()
    strategies._templates["night_wolf"] = {
        "action": {"type": "kill", "target": None},
        "reasoning": "",
    }

    result = strategies.get_action(
        "night_wolf",
        {
            "player_id": "w1",
            "alive_player_ids": ["w1", "w2"],
            "wolf_team_ids": ["w1", "w2"],
        },
    )

    reasoning = str(result.get("reasoning") or "")
    assert reasoning == "当前无可击杀目标。"
    assert "暂未确定今晚目标" not in reasoning
    assert "暂无目标" not in reasoning
