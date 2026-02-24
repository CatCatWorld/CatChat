from app.core.models import Role
from app.engine.game_engine import GameEngine
from app.websocket.handler import WSConnectionManager


def _started_engine() -> GameEngine:
    engine = GameEngine(room_id="r_visibility", owner_id="cat_01")
    for i in range(1, 13):
        pid = f"cat_{i:02d}"
        engine.add_player(pid, pid)
    engine.start_game("cat_01")
    for pid in engine.snapshot.players:
        engine.snapshot.players[pid].role = Role.VILLAGER
    return engine


def test_public_state_keeps_longer_speech_history_window() -> None:
    engine = _started_engine()
    for i in range(50):
        engine._audit(
            "agent_speech",
            "cat_01",
            {
                "phase": "day_vote",
                "role": Role.VILLAGER.value,
                "content": f"vote speech {i:02d}",
            },
        )

    state = engine.public_state()
    rows = state.get("speech_history") or []

    assert len(rows) == 50
    assert any(str(item.get("content") or "") == "vote speech 00" for item in rows)
    assert any(str(item.get("content") or "") == "vote speech 49" for item in rows)


def test_player_view_hides_judge_settlement_and_thoughts() -> None:
    state = {
        "room_id": "r_visibility",
        "players": [
            {
                "player_id": "cat_01",
                "nickname": "cat_01",
                "role": "villager",
                "alive": True,
                "online": True,
            }
        ],
        "speech_history": [
            {
                "player_id": "god",
                "event": "agent_speech",
                "phase": "night_wolf",
                "role": "judge",
                "content": "狼人已讨论并达成一致：今晚目标为 cat_09。",
                "thought_content": "internal",
            },
            {
                "player_id": "god",
                "event": "god_narration",
                "phase": "day_announce",
                "role": "judge",
                "content": "天亮了，现在公布昨夜结果。",
            },
            {
                "player_id": "cat_02",
                "event": "agent_speech",
                "phase": "day_vote",
                "role": "villager",
                "content": "我投 cat_03",
                "thought_content": "仅法官可见",
            },
        ],
    }

    filtered = WSConnectionManager._filter_state_for_view(state, "player:cat_09", "cat_09")
    rows = filtered.get("speech_history") or []

    assert filtered.get("watch_player") == "cat_09"
    assert len(rows) == 2
    assert all(str(item.get("event") or "") != "agent_speech" or str(item.get("player_id") or "") != "god" for item in rows)
    assert any(str(item.get("event") or "") == "god_narration" for item in rows)
    assert all("thought_content" not in item for item in rows if isinstance(item, dict))
