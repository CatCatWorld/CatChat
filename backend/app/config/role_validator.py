from __future__ import annotations

from typing import Dict, List

from app.config.config_validator import ConfigValidator, ValidationResult


class RoleValidator:
    @staticmethod
    def validate(player_count: int, distribution: Dict[str, int], night_order: List[str]) -> ValidationResult:
        return ConfigValidator.validate_template(
            player_count=player_count,
            distribution=distribution,
            night_order=night_order,
        )
