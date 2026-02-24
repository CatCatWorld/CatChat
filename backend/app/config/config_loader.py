from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from app.config.config_validator import ConfigValidator


def load_role_template(
    player_count: int,
    custom_role_config: Optional[Dict[str, Any]] = None,
    admin_override: bool = False,
) -> Dict[str, Any]:
    template = _load_builtin_template(player_count)
    if custom_role_config:
        if not admin_override:
            raise ValueError("custom_role_config requires admin_override=true")
        merged = {
            "player_count": player_count,
            "distribution": ConfigValidator.normalize_distribution(custom_role_config),
            "night_order": custom_role_config.get("night_order", template["night_order"]),
        }
        result = ConfigValidator.validate_template(
            player_count=player_count,
            distribution=merged["distribution"],
            night_order=merged["night_order"],
        )
        merged["warnings"] = result.warnings
        return merged

    result = ConfigValidator.validate_template(
        player_count=player_count,
        distribution=template["distribution"],
        night_order=template["night_order"],
    )
    template["warnings"] = result.warnings
    return template


def _load_builtin_template(player_count: int) -> Dict[str, Any]:
    config_path = Path(__file__).resolve().parents[2] / "config" / "role_balance.yaml"
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    templates = raw.get("role_templates", {})
    node = templates.get(player_count) or templates.get(str(player_count))
    if not node:
        raise ValueError(f"role template for player_count={player_count} not found")

    distribution = ConfigValidator.normalize_distribution(
        {
            "werewolf": node.get("wolves", 0),
            "villager": node.get("villagers", 0),
            "seer": node.get("seer", 0),
            "witch": node.get("witch", 0),
            "hunter": node.get("hunter", 0),
            "guard": node.get("guardian", 0),
            "fool": node.get("fool", 0),
        }
    )
    night_order = [str(x) for x in node.get("night_order", [])]

    return {
        "player_count": int(player_count),
        "distribution": distribution,
        "night_order": night_order,
    }
