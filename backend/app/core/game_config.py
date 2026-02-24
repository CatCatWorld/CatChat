from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.config.config_loader import load_role_template


@dataclass(slots=True)
class TimeoutConfig:
    night_action_seconds: int = 60
    day_vote_seconds: int = 60


@dataclass(slots=True)
class RuleConfig:
    guard_cannot_guard_same_target_consecutively: bool = True
    guard_vs_wolf_same_target_guard_wins: bool = True
    witch_can_self_save_on_first_night_only: bool = True
    witch_antidote_only_for_unprotected_wolf_target: bool = True
    hunter_cannot_shoot_if_poisoned: bool = True
    vote_tie_exile_none: bool = True
    fool_reveal_immune_once: bool = True


@dataclass(slots=True)
class GameConfig:
    player_count: int = 12
    role_distribution: Dict[str, int] = field(
        default_factory=lambda: {
            "werewolf": 4,
            "villager": 4,
            "seer": 1,
            "witch": 1,
            "hunter": 1,
            "guard": 1,
            "fool": 0,
        }
    )
    night_order: List[str] = field(
        default_factory=lambda: ["werewolf", "guardian", "witch", "seer"]
    )
    timeout: TimeoutConfig = field(default_factory=TimeoutConfig)
    rules: RuleConfig = field(default_factory=RuleConfig)
    warnings: List[str] = field(default_factory=list)

    @property
    def total_players(self) -> int:
        return int(sum(self.role_distribution.values()))

    @property
    def role_pool(self) -> Dict[str, int]:
        return {
            "werewolf": self.role_distribution.get("werewolf", 0),
            "villager": self.role_distribution.get("villager", 0),
            "seer": self.role_distribution.get("seer", 0),
            "witch": self.role_distribution.get("witch", 0),
            "hunter": self.role_distribution.get("hunter", 0),
            "guard": self.role_distribution.get("guard", 0),
            "fool": self.role_distribution.get("fool", 0),
        }


    def has_role(self, role_name: str) -> bool:
        normalized = "guard" if role_name == "guardian" else role_name
        return self.role_distribution.get(normalized, 0) > 0


def default_game_config(
    player_count: int = 12,
    custom_role_config: Optional[Dict[str, Any]] = None,
    admin_override: bool = False,
) -> GameConfig:
    loaded = load_role_template(
        player_count=player_count,
        custom_role_config=custom_role_config,
        admin_override=admin_override,
    )
    return GameConfig(
        player_count=loaded["player_count"],
        role_distribution=loaded["distribution"],
        night_order=loaded["night_order"],
        warnings=loaded.get("warnings", []),
    )
