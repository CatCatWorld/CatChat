from app.core.game_config import default_game_config
from app.core.models import Phase, Role
from app.engine.game_engine import GameEngine
from app.room.room_manager import RoomManager


def _started_game_with_fool() -> GameEngine:
    config = default_game_config(player_count=11)
    engine = GameEngine(room_id="r_fool", owner_id="owner", config=config)

    players = {
        "owner": "P1",
        "p2": "P2",
        "p3": "P3",
        "p4": "P4",
        "p5": "P5",
        "p6": "P6",
        "p7": "P7",
        "p8": "P8",
        "p9": "P9",
        "p10": "P10",
        "p11": "P11",
    }
    for pid, nick in players.items():
        engine.add_player(pid, nick)

    engine.start_game("owner")

    role_map = {
        "owner": Role.WEREWOLF,
        "p2": Role.WEREWOLF,
        "p3": Role.WEREWOLF,
        "p4": Role.VILLAGER,
        "p5": Role.GUARD,
        "p6": Role.WITCH,
        "p7": Role.SEER,
        "p8": Role.HUNTER,
        "p9": Role.VILLAGER,
        "p10": Role.VILLAGER,
        "p11": Role.FOOL,
    }
    for pid, role in role_map.items():
        engine.snapshot.players[pid].role = role

    return engine


def _goto_day_vote(engine: GameEngine) -> None:
    # night_wolf -> night_guard -> night_witch -> night_seer -> day_announce -> day_discuss -> day_vote
    while engine.snapshot.phase != Phase.DAY_VOTE:
        engine.timeout_autorun_current_phase()


def test_fool_reveal_immune_and_loses_vote() -> None:
    engine = _started_game_with_fool()
    _goto_day_vote(engine)

    # all alive voters vote fool
    for pid, p in engine.snapshot.players.items():
        if p.alive and p.player_id != "p11":
            engine.submit_vote(pid, "p11")

    engine.advance_phase()

    fool = engine.snapshot.players["p11"]
    assert fool.alive is True
    assert fool.fool_revealed is True
    assert fool.can_vote is False


def test_create_ai_room_respects_player_count() -> None:
    manager = RoomManager()
    result = manager.create_ai_room(player_count=8)
    room = manager.must_get_room(result["room_id"])

    assert len(room.engine.snapshot.players) == 8
    assert room.engine.config.player_count == 8
