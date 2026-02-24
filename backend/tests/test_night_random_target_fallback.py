import asyncio

from app.agent.ai_god_orchestrator import AIGodOrchestrator, GodNarration
from app.agent.god_orchestrator import GodOrchestrator
from app.core.models import Phase, Role
from app.engine.game_engine import GameEngine


def _make_engine() -> GameEngine:
    engine = GameEngine(room_id="r_random_fallback", owner_id="owner")
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


class _InvalidTargetScheduler:
    async def trigger_agent_action(self, **kwargs):
        phase = kwargs.get("phase")
        if phase == "night_wolf_discuss":
            return {"action": {"target": ""}, "reasoning": "信息不足，先观察。"}
        if phase == Phase.NIGHT_GUARD.value:
            return {"action": {"target": ""}, "reasoning": "信息不足，先观察。"}
        if phase == Phase.NIGHT_SEER.value:
            return {"action": {"target": ""}, "reasoning": "信息不足，先观察。"}
        return {"action": {"target": ""}, "reasoning": ""}


class _InvalidRuleTargetScheduler:
    async def trigger_agent_action(self, **kwargs):
        phase = kwargs.get("phase")
        if phase == Phase.NIGHT_GUARD.value:
            return {"action": {"target": "p5"}, "reasoning": "继续守护上轮目标。"}
        if phase == Phase.NIGHT_SEER.value:
            return {"action": {"target": "p9"}, "reasoning": "继续查验上轮目标。"}
        return {"action": {"target": ""}, "reasoning": ""}


def test_god_orchestrator_night_roles_use_random_fallback_when_target_invalid() -> None:
    scheduler = _InvalidTargetScheduler()
    orchestrator = GodOrchestrator(scheduler=scheduler)

    engine_wolf = _make_engine()
    asyncio.run(orchestrator._run_wolf_phase(engine_wolf))
    wolf_votes = engine_wolf.snapshot.round_context.night_actions.wolf_votes
    assert set(wolf_votes.keys()) == {"owner", "p2"}
    assert all(vote and engine_wolf.snapshot.players[vote].role != Role.WEREWOLF for vote in wolf_votes.values())

    engine_guard = _make_engine()
    engine_guard.snapshot.phase = Phase.NIGHT_GUARD
    asyncio.run(orchestrator._run_guard_phase(engine_guard))
    guard_target = engine_guard.snapshot.round_context.night_actions.guard_target
    assert guard_target is not None
    assert engine_guard.snapshot.players[guard_target].alive

    engine_seer = _make_engine()
    engine_seer.snapshot.phase = Phase.NIGHT_SEER
    asyncio.run(orchestrator._run_seer_phase(engine_seer))
    seer_target = engine_seer.snapshot.round_context.night_actions.seer_target
    assert seer_target is not None
    assert seer_target != "p7"


def test_ai_god_orchestrator_night_roles_use_random_fallback_when_target_invalid() -> None:
    scheduler = _InvalidTargetScheduler()
    orchestrator = AIGodOrchestrator(scheduler=scheduler)
    god_result = GodNarration(phase="night", narration="", reasoning="")

    engine_wolf = _make_engine()
    asyncio.run(orchestrator._run_wolf_phase(engine_wolf, god_result))
    wolf_votes = engine_wolf.snapshot.round_context.night_actions.wolf_votes
    assert set(wolf_votes.keys()) == {"owner", "p2"}
    assert all(vote and engine_wolf.snapshot.players[vote].role != Role.WEREWOLF for vote in wolf_votes.values())

    engine_guard = _make_engine()
    engine_guard.snapshot.phase = Phase.NIGHT_GUARD
    asyncio.run(orchestrator._run_guard_phase(engine_guard, god_result))
    guard_target = engine_guard.snapshot.round_context.night_actions.guard_target
    assert guard_target is not None
    assert engine_guard.snapshot.players[guard_target].alive

    engine_seer = _make_engine()
    engine_seer.snapshot.phase = Phase.NIGHT_SEER
    asyncio.run(orchestrator._run_seer_phase(engine_seer, god_result))
    seer_target = engine_seer.snapshot.round_context.night_actions.seer_target
    assert seer_target is not None
    assert seer_target != "p7"


def test_god_orchestrator_guard_and_seer_retry_when_target_rule_invalid() -> None:
    scheduler = _InvalidRuleTargetScheduler()
    orchestrator = GodOrchestrator(scheduler=scheduler)

    engine_guard = _make_engine()
    engine_guard.snapshot.phase = Phase.NIGHT_GUARD
    engine_guard.snapshot.players["p5"].last_guard_target = "p5"
    asyncio.run(orchestrator._run_guard_phase(engine_guard))
    guard_target = engine_guard.snapshot.round_context.night_actions.guard_target
    assert guard_target is not None
    assert guard_target != "p5"

    engine_seer = _make_engine()
    engine_seer.snapshot.phase = Phase.NIGHT_SEER
    engine_seer.snapshot.players["p7"].last_seer_target = "p9"
    asyncio.run(orchestrator._run_seer_phase(engine_seer))
    seer_target = engine_seer.snapshot.round_context.night_actions.seer_target
    assert seer_target is not None
    assert seer_target != "p9"


def test_ai_god_orchestrator_guard_and_seer_retry_when_target_rule_invalid() -> None:
    scheduler = _InvalidRuleTargetScheduler()
    orchestrator = AIGodOrchestrator(scheduler=scheduler)
    god_result = GodNarration(phase="night", narration="", reasoning="")

    engine_guard = _make_engine()
    engine_guard.snapshot.phase = Phase.NIGHT_GUARD
    engine_guard.snapshot.players["p5"].last_guard_target = "p5"
    asyncio.run(orchestrator._run_guard_phase(engine_guard, god_result))
    guard_target = engine_guard.snapshot.round_context.night_actions.guard_target
    assert guard_target is not None
    assert guard_target != "p5"

    engine_seer = _make_engine()
    engine_seer.snapshot.phase = Phase.NIGHT_SEER
    engine_seer.snapshot.players["p7"].last_seer_target = "p9"
    asyncio.run(orchestrator._run_seer_phase(engine_seer, god_result))
    seer_target = engine_seer.snapshot.round_context.night_actions.seer_target
    assert seer_target is not None
    assert seer_target != "p9"
