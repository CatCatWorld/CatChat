from app.agent.perspective_engine import PerspectiveEngine
from app.core.models import Phase, Role
from app.engine.game_engine import GameEngine


def _started_engine() -> GameEngine:
    engine = GameEngine(room_id="r_p", owner_id="cat_01")
    for i in range(1, 13):
        pid = f"cat_{i:02d}"
        engine.add_player(pid, pid)
    engine.start_game("cat_01")

    role_map = {
        "cat_01": Role.WEREWOLF,
        "cat_02": Role.WEREWOLF,
        "cat_03": Role.WEREWOLF,
        "cat_04": Role.WEREWOLF,
        "cat_05": Role.GUARD,
        "cat_06": Role.WITCH,
        "cat_07": Role.SEER,
        "cat_08": Role.HUNTER,
        "cat_09": Role.VILLAGER,
        "cat_10": Role.VILLAGER,
        "cat_11": Role.VILLAGER,
        "cat_12": Role.VILLAGER,
    }
    for pid, role in role_map.items():
        engine.snapshot.players[pid].role = role
    return engine


def test_werewolf_can_see_wolf_team() -> None:
    engine = _started_engine()
    visible = PerspectiveEngine.build_visible_state(engine, "cat_01")
    assert "wolf_team" in visible
    assert set(visible["wolf_team"]) == {"cat_01", "cat_02", "cat_03", "cat_04"}


def test_villager_cannot_see_wolf_team() -> None:
    engine = _started_engine()
    visible = PerspectiveEngine.build_visible_state(engine, "cat_09")
    assert "wolf_team" not in visible


def test_witch_only_gets_wolf_target_in_witch_phase() -> None:
    engine = _started_engine()

    # wolf phase action
    engine.submit_night_action("cat_01", "cat_09")
    engine.submit_night_action("cat_02", "cat_09")
    engine.submit_night_action("cat_03", "cat_09")
    engine.submit_night_action("cat_04", "cat_09")
    engine.advance_phase()  # guard
    engine.advance_phase()  # witch

    assert engine.snapshot.phase == Phase.NIGHT_WITCH
    visible = PerspectiveEngine.build_visible_state(engine, "cat_06")
    assert visible["wolf_target"] == "cat_09"

    engine.advance_phase()  # seer
    visible2 = PerspectiveEngine.build_visible_state(engine, "cat_06")
    assert "wolf_target" not in visible2


def test_seer_can_read_own_result() -> None:
    engine = _started_engine()
    engine.submit_night_action("cat_01", "cat_09")
    engine.submit_night_action("cat_02", "cat_09")
    engine.submit_night_action("cat_03", "cat_09")
    engine.submit_night_action("cat_04", "cat_09")
    engine.advance_phase()  # guard
    engine.submit_night_action("cat_05", "cat_10")
    engine.advance_phase()  # witch
    engine.advance_phase()  # seer
    engine.submit_night_action("cat_07", "cat_01")

    visible = PerspectiveEngine.build_visible_state(engine, "cat_07")
    assert visible["seer_result"]["target_id"] == "cat_01"
    assert visible["seer_result"]["is_wolf"] is True


def test_public_vote_log_contains_only_vote_events() -> None:
    engine = _started_engine()
    engine.snapshot.phase = Phase.DAY_VOTE
    engine.submit_vote("cat_01", "cat_09")
    engine.submit_vote("cat_02", "cat_09")

    visible = PerspectiveEngine.build_visible_state(engine, "cat_09")
    assert "public_vote_log" in visible
    assert len(visible["public_vote_log"]) >= 2
    assert all(item["event_type"] in {"vote", "vote_result"} for item in visible["public_vote_log"])


def test_memory_context_contains_public_history() -> None:
    engine = _started_engine()
    engine._audit(
        "agent_speech",
        "cat_09",
        {
            "phase": Phase.DAY_DISCUSS.value,
            "role": Role.VILLAGER.value,
            "content": "我怀疑2号昨夜发言矛盾。",
        },
    )
    engine._audit(
        "vote_result",
        "system",
        {
            "result": "tie_no_exile",
        },
    )

    visible = PerspectiveEngine.build_visible_state(engine, "cat_10")
    memory = visible.get("memory_context") or {}
    public_memory = memory.get("public_memory") or []
    game_facts = memory.get("game_facts") or {}
    summary = str(memory.get("summary") or "")
    round_summaries = memory.get("round_summaries") or []
    rolling_summary = str(memory.get("rolling_summary") or "")

    assert public_memory
    assert any("我怀疑2号" in str(item.get("content") or "") for item in public_memory)
    assert any("平票" in str(item.get("content") or "") for item in public_memory)
    assert isinstance(game_facts.get("recent_highlights"), list)
    assert any("平票" in str(item) for item in game_facts.get("recent_highlights") or [])
    assert "当前第" in summary
    assert "近期关键记忆" in summary
    assert isinstance(round_summaries, list)
    assert round_summaries
    assert "round_no" in round_summaries[-1]
    assert isinstance(game_facts.get("round_summaries"), list)
    assert "第" in rolling_summary


def test_memory_context_hides_wolf_night_discussion_from_villager() -> None:
    engine = _started_engine()
    engine._audit(
        "agent_speech",
        "cat_01",
        {
            "phase": "night_wolf_discuss",
            "role": Role.WEREWOLF.value,
            "content": "今晚先刀9号。",
        },
    )

    villager_visible = PerspectiveEngine.build_visible_state(engine, "cat_09")
    villager_memory = (villager_visible.get("memory_context") or {}).get("public_memory") or []
    assert all("今晚先刀9号" not in str(item.get("content") or "") for item in villager_memory)

    wolf_visible = PerspectiveEngine.build_visible_state(engine, "cat_02")
    wolf_team_memory = (wolf_visible.get("memory_context") or {}).get("wolf_team_memory") or []
    assert any("今晚先刀9号" in str(item.get("content") or "") for item in wolf_team_memory)


def test_memory_context_hides_night_judge_settlement_from_guard() -> None:
    engine = _started_engine()
    engine._audit(
        "agent_speech",
        "god",
        {
            "phase": "night_wolf",
            "role": "judge",
            "content": "狼人已讨论并达成一致：今晚目标为 cat_09。",
        },
    )

    guard_visible = PerspectiveEngine.build_visible_state(engine, "cat_05")
    memory = guard_visible.get("memory_context") or {}
    public_memory = memory.get("public_memory") or []
    self_memory = memory.get("self_memory") or []
    highlights = ((memory.get("game_facts") or {}).get("recent_highlights") or [])
    summary = str(memory.get("summary") or "")

    assert all("今晚目标为" not in str(item.get("content") or "") for item in public_memory)
    assert all("今晚目标为" not in str(item.get("content") or "") for item in self_memory)
    assert all("今晚目标为" not in str(item) for item in highlights)
    assert "今晚目标为" not in summary


def test_memory_context_blocks_sensitive_marker_even_in_day_phase() -> None:
    engine = _started_engine()
    engine._audit(
        "god_narration",
        "god",
        {
            "phase": "day_discuss",
            "content": "（调试）今晚目标为 cat_09。",
        },
    )

    villager_visible = PerspectiveEngine.build_visible_state(engine, "cat_09")
    public_memory = (villager_visible.get("memory_context") or {}).get("public_memory") or []
    assert all("今晚目标为" not in str(item.get("content") or "") for item in public_memory)


def test_memory_context_role_aware_marker_filtering_for_seer_debug_leak() -> None:
    engine = _started_engine()
    engine._audit(
        "god_narration",
        "god",
        {
            "phase": "day_discuss",
            "content": "debug: seer_result={\"target_id\":\"cat_01\",\"is_wolf\":true}",
        },
    )

    villager_visible = PerspectiveEngine.build_visible_state(engine, "cat_09")
    villager_public_memory = (villager_visible.get("memory_context") or {}).get("public_memory") or []
    assert all("seer_result" not in str(item.get("content") or "") for item in villager_public_memory)

    seer_visible = PerspectiveEngine.build_visible_state(engine, "cat_07")
    seer_public_memory = (seer_visible.get("memory_context") or {}).get("public_memory") or []
    assert any("seer_result" in str(item.get("content") or "") for item in seer_public_memory)
