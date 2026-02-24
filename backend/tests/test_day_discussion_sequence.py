import asyncio
from dataclasses import dataclass

from app.agent.ai_god_orchestrator import AIGodOrchestrator, GodNarration
from app.agent.god_orchestrator import GodOrchestrator
from app.engine.game_engine import GameEngine


@dataclass
class _CallRecord:
    player_id: str
    history_len: int


class _FakeScheduler:
    def __init__(self) -> None:
        self.calls: list[_CallRecord] = []

    async def trigger_agent_action(self, **kwargs):
        player_id = kwargs.get("player_id")
        visible_state = kwargs.get("visible_state") or {}
        history = visible_state.get("day_discussion_so_far") or []
        self.calls.append(_CallRecord(player_id=str(player_id), history_len=len(history)))
        return {
            "action": {"type": "speak"},
            "speech": f"day discuss from {player_id}",
            "thinking": "internal",
        }


def _make_engine_three_alive() -> GameEngine:
    engine = GameEngine(room_id="r_day_seq", owner_id="owner")
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

    for pid, player in engine.snapshot.players.items():
        if pid not in {"owner", "p2", "p3"}:
            player.alive = False
    return engine


def test_god_orchestrator_day_discussion_is_sequential() -> None:
    engine = _make_engine_three_alive()
    fake = _FakeScheduler()
    orchestrator = GodOrchestrator(scheduler=fake)

    asyncio.run(orchestrator._run_day_discuss(engine))

    assert len(fake.calls) == 3
    assert fake.calls[0].history_len == 0
    assert fake.calls[1].history_len == 1
    assert fake.calls[2].history_len == 2


def test_ai_god_orchestrator_day_discussion_is_sequential() -> None:
    engine = _make_engine_three_alive()
    fake = _FakeScheduler()
    orchestrator = AIGodOrchestrator(scheduler=fake)
    god_result = GodNarration(phase="day_discuss", narration="", reasoning="")

    asyncio.run(orchestrator._run_day_discuss(engine, god_result))

    assert len(fake.calls) == 3
    assert fake.calls[0].history_len == 0
    assert fake.calls[1].history_len == 1
    assert fake.calls[2].history_len == 2
