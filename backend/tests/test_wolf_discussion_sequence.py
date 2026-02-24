import asyncio
from dataclasses import dataclass

from app.agent.ai_god_orchestrator import AIGodOrchestrator, GodNarration
from app.agent.god_orchestrator import GodOrchestrator
from app.core.models import Role
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
        history = visible_state.get("wolf_discussion_so_far") or []
        self.calls.append(_CallRecord(player_id=str(player_id), history_len=len(history)))
        return {
            "action": {"target": None},
            "reasoning": f"wolf discuss from {player_id}，我建议今晚击杀 P3。",
        }


class _TwoRoundConsensusScheduler:
    def __init__(self) -> None:
        self.calls = 0

    async def trigger_agent_action(self, **kwargs):
        self.calls += 1
        if self.calls == 1:
            return {"action": {"target": "p8"}, "reasoning": "第一轮我建议先刀 P8。"}
        if self.calls == 2:
            return {"action": {"target": "p9"}, "reasoning": "第一轮我建议刀 P9。"}
        return {"action": {"target": "p8"}, "reasoning": "第二轮统一目标，今晚刀 P8。"}


def _make_engine_two_wolves() -> GameEngine:
    engine = GameEngine(room_id="r_seq", owner_id="owner")
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

    role_map = {
        "owner": Role.WEREWOLF,
        "p2": Role.WEREWOLF,
        "p3": Role.VILLAGER,
        "p4": Role.VILLAGER,
        "p5": Role.GUARD,
        "p6": Role.WITCH,
        "p7": Role.SEER,
        "p8": Role.VILLAGER,
        "p9": Role.VILLAGER,
        "p10": Role.VILLAGER,
        "p11": Role.VILLAGER,
        "p12": Role.VILLAGER,
    }
    for pid, role in role_map.items():
        engine.snapshot.players[pid].role = role
    return engine


def test_god_orchestrator_wolf_discussion_is_sequential() -> None:
    engine = _make_engine_two_wolves()
    fake = _FakeScheduler()
    orchestrator = GodOrchestrator(scheduler=fake)

    asyncio.run(orchestrator._run_wolf_phase(engine))

    assert len(fake.calls) == 2
    assert fake.calls[0].history_len == 0
    assert fake.calls[1].history_len == 1


def test_ai_god_orchestrator_wolf_discussion_is_sequential() -> None:
    engine = _make_engine_two_wolves()
    fake = _FakeScheduler()
    orchestrator = AIGodOrchestrator(scheduler=fake)
    god_result = GodNarration(phase="night_wolf", narration="", reasoning="")

    asyncio.run(orchestrator._run_wolf_phase(engine, god_result))

    assert len(fake.calls) == 2
    assert fake.calls[0].history_len == 0
    assert fake.calls[1].history_len == 1


def _wolf_discuss_lines(engine: GameEngine) -> list[str]:
    rows = [
        row
        for row in engine.snapshot.action_audit_log
        if row.get("event_type") == "agent_speech"
        and str((row.get("payload") or {}).get("phase") or "") == "night_wolf_discuss"
    ]
    return [str(((row.get("payload") or {}).get("content") or "")).strip() for row in rows]


def test_god_orchestrator_wolf_discussion_requires_explicit_target() -> None:
    engine = _make_engine_two_wolves()
    fake = _FakeScheduler()
    orchestrator = GodOrchestrator(scheduler=fake)

    asyncio.run(orchestrator._run_wolf_phase(engine))

    lines = _wolf_discuss_lines(engine)
    assert len(lines) == 2
    assert all("暂未确定今晚目标" not in line for line in lines)
    assert all("暂无目标" not in line for line in lines)
    assert all("建议今晚击杀" in line for line in lines)


def test_ai_god_orchestrator_wolf_discussion_requires_explicit_target() -> None:
    engine = _make_engine_two_wolves()
    fake = _FakeScheduler()
    orchestrator = AIGodOrchestrator(scheduler=fake)
    god_result = GodNarration(phase="night_wolf", narration="", reasoning="")

    asyncio.run(orchestrator._run_wolf_phase(engine, god_result))

    lines = _wolf_discuss_lines(engine)
    assert len(lines) == 2
    assert all("暂未确定今晚目标" not in line for line in lines)
    assert all("暂无目标" not in line for line in lines)
    assert all("建议今晚击杀" in line for line in lines)


def test_god_orchestrator_wolf_discuss_speech_drops_conflicting_target_text() -> None:
    engine = _make_engine_two_wolves()
    orchestrator = GodOrchestrator(scheduler=_FakeScheduler())

    result = {
        "action": {"target": "p3"},
        "reasoning": "我建议今晚击杀 P4，这样更稳。",
    }
    speech = orchestrator._wolf_discuss_speech_text(engine, result, "p3")

    assert "击杀 P3" in speech
    assert "P4" not in speech


def test_ai_god_orchestrator_wolf_discuss_speech_drops_conflicting_target_text() -> None:
    engine = _make_engine_two_wolves()
    orchestrator = AIGodOrchestrator(scheduler=_FakeScheduler())

    result = {
        "action": {"target": "p3"},
        "reasoning": "我建议今晚击杀 P4，这样更稳。",
    }
    speech = orchestrator._wolf_discuss_speech_text(engine, result, "p3")

    assert "击杀 P3" in speech
    assert "P4" not in speech


def _judge_lines(engine: GameEngine) -> list[str]:
    rows = [
        row
        for row in engine.snapshot.action_audit_log
        if row.get("event_type") == "agent_speech"
        and row.get("actor_id") == "god"
        and str((row.get("payload") or {}).get("phase") or "") == "night_wolf"
    ]
    return [str(((row.get("payload") or {}).get("content") or "")).strip() for row in rows]


def test_god_orchestrator_wolf_discussion_retries_until_consensus() -> None:
    engine = _make_engine_two_wolves()
    fake = _TwoRoundConsensusScheduler()
    orchestrator = GodOrchestrator(scheduler=fake)

    asyncio.run(orchestrator._run_wolf_phase(engine))

    assert fake.calls == 4
    lines = _judge_lines(engine)
    assert any("第1轮讨论未达成一致" in line for line in lines)
    assert any("第2轮讨论达成一致" in line for line in lines)


def test_ai_god_orchestrator_wolf_discussion_retries_until_consensus() -> None:
    engine = _make_engine_two_wolves()
    fake = _TwoRoundConsensusScheduler()
    orchestrator = AIGodOrchestrator(scheduler=fake)
    god_result = GodNarration(phase="night_wolf", narration="", reasoning="")

    asyncio.run(orchestrator._run_wolf_phase(engine, god_result))

    assert fake.calls == 4
    lines = _judge_lines(engine)
    assert any("第1轮讨论未达成一致" in line for line in lines)
    assert any("第2轮讨论达成一致" in line for line in lines)
