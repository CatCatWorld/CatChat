from app.engine.game_engine import GameEngine
from app.core.models import DeathCause, Phase, Role


def _make_started_game() -> tuple[GameEngine, dict[str, str]]:
    engine = GameEngine(room_id="r1", owner_id="owner")
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
        "p12": "P12",
    }
    for pid, nick in players.items():
        engine.add_player(pid, nick)
    engine.start_game("owner")

    # force deterministic roles for test readability
    role_map = {
        "owner": Role.WEREWOLF,
        "p2": Role.WEREWOLF,
        "p3": Role.WEREWOLF,
        "p4": Role.WEREWOLF,
        "p5": Role.GUARD,
        "p6": Role.WITCH,
        "p7": Role.SEER,
        "p8": Role.HUNTER,
        "p9": Role.VILLAGER,
        "p10": Role.VILLAGER,
        "p11": Role.VILLAGER,
        "p12": Role.VILLAGER,
    }
    for pid, role in role_map.items():
        engine.snapshot.players[pid].role = role

    return engine, players


def test_guard_beats_wolf_same_target() -> None:
    engine, _ = _make_started_game()

    # NIGHT_WOLF
    assert engine.snapshot.phase == Phase.NIGHT_WOLF
    engine.submit_night_action("owner", "p9")
    engine.submit_night_action("p2", "p9")
    engine.submit_night_action("p3", "p9")
    engine.submit_night_action("p4", "p9")
    engine.advance_phase()

    # NIGHT_GUARD
    assert engine.snapshot.phase == Phase.NIGHT_GUARD
    engine.submit_night_action("p5", "p9")
    engine.advance_phase()

    # NIGHT_WITCH (no action)
    assert engine.snapshot.phase == Phase.NIGHT_WITCH
    engine.advance_phase()

    # NIGHT_SEER (no action)
    assert engine.snapshot.phase == Phase.NIGHT_SEER
    engine.advance_phase()

    # DAY_ANNOUNCE: p9 should survive due to guard
    assert engine.snapshot.phase == Phase.DAY_ANNOUNCE
    assert engine.snapshot.players["p9"].alive is True
    assert "p9" not in engine.snapshot.round_context.deaths_this_round


def test_witch_poison_ignores_guard() -> None:
    engine, _ = _make_started_game()

    # NIGHT_WOLF target p9
    engine.submit_night_action("owner", "p9")
    engine.submit_night_action("p2", "p9")
    engine.submit_night_action("p3", "p9")
    engine.submit_night_action("p4", "p9")
    engine.advance_phase()

    # NIGHT_GUARD protect p9
    engine.submit_night_action("p5", "p9")
    engine.advance_phase()

    # NIGHT_WITCH poison p10, no save
    engine.submit_night_action("p6", target_id="p10", save=False)
    engine.advance_phase()

    # NIGHT_SEER skip
    engine.advance_phase()

    deaths = engine.snapshot.round_context.deaths_this_round
    assert engine.snapshot.players["p9"].alive is True  # guarded
    assert engine.snapshot.players["p10"].alive is False  # poisoned
    assert deaths["p10"] == DeathCause.POISON


def test_seer_cannot_check_same_target_in_consecutive_nights() -> None:
    engine, _ = _make_started_game()

    # Round 1 -> NIGHT_SEER
    engine.advance_phase()  # NIGHT_GUARD
    engine.advance_phase()  # NIGHT_WITCH
    engine.advance_phase()  # NIGHT_SEER
    assert engine.snapshot.phase == Phase.NIGHT_SEER

    engine.submit_night_action("p7", "p9")
    engine.advance_phase()  # DAY_ANNOUNCE
    engine.advance_phase()  # DAY_DISCUSS
    engine.advance_phase()  # DAY_VOTE
    engine.timeout_autorun_current_phase()  # resolve vote and next round NIGHT_WOLF

    # Round 2 -> NIGHT_SEER
    engine.advance_phase()  # NIGHT_GUARD
    engine.advance_phase()  # NIGHT_WITCH
    engine.advance_phase()  # NIGHT_SEER
    assert engine.snapshot.phase == Phase.NIGHT_SEER

    try:
        engine.submit_night_action("p7", "p9")
        raised = False
    except ValueError as exc:
        raised = True
        assert "consecutive" in str(exc)

    assert raised is True
