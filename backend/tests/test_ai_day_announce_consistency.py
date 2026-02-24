import asyncio

from app.agent.ai_god_orchestrator import AIGodOrchestrator
from app.core.models import DeathCause, Phase, Role
from app.engine.game_engine import GameEngine


def test_ai_day_announce_uses_engine_fact_summary() -> None:
    engine = GameEngine(room_id="r_da", owner_id="owner")
    players = {
        "owner": "折耳",
        "p2": "大橘",
        "p3": "布偶",
        "p4": "蓝猫",
        "p5": "狸花",
        "p6": "孟加拉",
        "p7": "波斯",
        "p8": "退罗",
        "p9": "波斯猫",
        "p10": "缅因",
        "p11": "暹罗",
        "p12": "英短",
    }
    for pid, nick in players.items():
        engine.add_player(pid, nick)
    engine.start_game("owner")

    role_map = {
        "owner": Role.WEREWOLF,
        "p2": Role.VILLAGER,
        "p3": Role.WEREWOLF,
        "p4": Role.WITCH,
        "p5": Role.GUARD,
        "p6": Role.SEER,
        "p7": Role.VILLAGER,
        "p8": Role.VILLAGER,
        "p9": Role.VILLAGER,
        "p10": Role.VILLAGER,
        "p11": Role.VILLAGER,
        "p12": Role.VILLAGER,
    }
    for pid, role in role_map.items():
        engine.snapshot.players[pid].role = role

    ctx = engine.snapshot.round_context
    ctx.wolf_target = "owner"
    ctx.night_actions.guard_target = "owner"
    ctx.night_actions.witch_poison_target = "p2"
    ctx.deaths_this_round = {"p2": DeathCause.POISON}
    ctx.protected_players = {"owner"}
    engine.snapshot.phase = Phase.DAY_ANNOUNCE

    orchestrator = AIGodOrchestrator()
    asyncio.run(orchestrator.run_single_phase(engine))

    speeches = [
        row
        for row in engine.snapshot.action_audit_log
        if row.get("event_type") == "agent_speech"
        and (row.get("payload") or {}).get("phase") == Phase.DAY_ANNOUNCE.value
    ]
    assert speeches, "day_announce should emit deterministic speech"

    text = str((speeches[-1].get("payload") or {}).get("content") or "")
    assert "守卫昨夜守护了" in text and "折耳" in text
    assert "女巫昨夜毒杀了" in text and "大橘" in text
    assert "出局名单" in text and "大橘" in text
