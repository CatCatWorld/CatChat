from __future__ import annotations

from typing import Dict, List

from app.core.models import Phase
from app.engine.phase_orchestrator import PhaseOrchestrator


def generate_night_phases(room_config: Dict[str, object]) -> List[Phase]:
    role_distribution = room_config.get("role_distribution", {})
    night_order = room_config.get("night_order", ["werewolf", "guardian", "witch", "seer"])
    orchestrator = PhaseOrchestrator(
        night_order=[str(x) for x in night_order],
        role_distribution={str(k): int(v) for k, v in dict(role_distribution).items()},
    )
    return orchestrator.generate_night_phases()
