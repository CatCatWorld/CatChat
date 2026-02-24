from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from app.core.models import Phase


ROLE_PHASE_MAP: Dict[str, Phase] = {
    "werewolf": Phase.NIGHT_WOLF,
    "guard": Phase.NIGHT_GUARD,
    "guardian": Phase.NIGHT_GUARD,
    "witch": Phase.NIGHT_WITCH,
    "seer": Phase.NIGHT_SEER,
}


@dataclass(slots=True)
class PhaseOrchestrator:
    night_order: List[str]
    role_distribution: Dict[str, int]

    def generate_night_phases(self) -> List[Phase]:
        active: List[Phase] = []
        for role_name in self.night_order:
            phase = ROLE_PHASE_MAP.get(role_name)
            if not phase:
                continue
            normalized = "guard" if role_name == "guardian" else role_name
            if self.role_distribution.get(normalized, 0) > 0:
                active.append(phase)
        return active
