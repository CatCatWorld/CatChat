from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass(slots=True)
class ValidationResult:
    ok: bool
    warnings: List[str]


class ConfigValidator:
    ALLOWED_COUNTS = {8, 9, 10, 11, 12}
    ALLOWED_NIGHT_ROLES = {"werewolf", "guardian", "witch", "seer"}

    @staticmethod
    def normalize_distribution(distribution: Dict[str, int]) -> Dict[str, int]:
        mapped = {
            "werewolf": int(distribution.get("werewolf", distribution.get("wolf", distribution.get("wolves", 0)))),
            "villager": int(distribution.get("villager", distribution.get("villagers", 0))),
            "seer": int(distribution.get("seer", 0)),
            "witch": int(distribution.get("witch", 0)),
            "hunter": int(distribution.get("hunter", 0)),
            "guard": int(distribution.get("guard", distribution.get("guardian", 0))),
            "fool": int(distribution.get("fool", 0)),
        }
        return mapped

    @classmethod
    def validate_template(cls, player_count: int, distribution: Dict[str, int], night_order: List[str]) -> ValidationResult:
        if player_count not in cls.ALLOWED_COUNTS:
            raise ValueError("player_count must be between 8 and 12")

        normalized = cls.normalize_distribution(distribution)
        total = sum(normalized.values())
        if total != player_count:
            raise ValueError(f"role sum mismatch: expected {player_count}, got {total}")

        if normalized["werewolf"] < 1:
            raise ValueError("werewolf count must be >= 1")

        gods = normalized["seer"] + normalized["witch"] + normalized["hunter"] + normalized["guard"] + normalized["fool"]
        if gods > player_count * 0.5:
            raise ValueError("special roles must be <= 50% of total players")

        ratio = normalized["werewolf"] / player_count
        if not (0.15 <= ratio <= 0.40):
            raise ValueError("werewolf ratio must be between 15% and 40%")

        unknown = [r for r in night_order if r not in cls.ALLOWED_NIGHT_ROLES]
        if unknown:
            raise ValueError(f"invalid night roles in night_order: {unknown}")

        warnings: List[str] = []
        if normalized["fool"] > 1:
            warnings.append("fool count > 1 may heavily bias village side")
        if normalized["werewolf"] == normalized["villager"]:
            warnings.append("wolf and villager counts are equal; game may end quickly")

        return ValidationResult(ok=True, warnings=warnings)
