from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Callable, Dict

from app.core.models import Role


class FallbackStrategies:
    """Fallback strategy plugin registry.

    Supports dynamic loading from JSON file and built-in defaults.
    """

    def __init__(self) -> None:
        self._strategies: Dict[str, Callable[[dict], dict]] = {
            "default": self._default_action,
            "night_wolf": self._night_wolf_action,
            "night_guard": self._night_guard_action,
            "night_witch": self._night_witch_action,
            "night_seer": self._night_seer_action,
            "day_vote": self._day_vote_action,
            "day_discuss": self._day_discuss_action,
            "hunter_shot": self._hunter_shot_action,
        }
        self._templates: Dict[str, dict] = {}
        self._rng = random.SystemRandom()

    def _pick_random(self, candidates: list):
        if not candidates:
            return None
        pool = list(dict.fromkeys(candidates))
        if not pool:
            return None
        return self._rng.choice(pool)

    def load_templates(self, file_path: str) -> None:
        path = Path(file_path)
        if not path.exists():
            return
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            self._templates = data

    def get_action(self, strategy_name: str, context: dict) -> dict:
        if strategy_name in self._templates:
            return self._render_template(strategy_name, self._templates[strategy_name], context)
        fn = self._strategies.get(strategy_name, self._strategies["default"])
        return fn(context)

    def _render_template(self, strategy_name: str, template: dict, context: dict) -> dict:
        result = dict(template)
        alive = context.get("alive_players", [])
        if result.get("action", {}).get("target") == "__RANDOM_ALIVE__" and alive:
            result["action"]["target"] = self._pick_random(alive)
        if strategy_name == "day_vote":
            action = result.get("action") or {}
            target = action.get("target") if isinstance(action, dict) else None
            reasoning = str(result.get("reasoning") or "").strip()
            speech = str(result.get("speech") or "").strip()
            thinking = str(result.get("thinking") or "").strip()
            if target:
                if not reasoning or (target not in reasoning and "投票给" not in reasoning):
                    result["reasoning"] = f"信息有限，我投票给 {target}。"
                if not speech:
                    result["speech"] = f"当前信息有限，我投票给 {target}。"
            else:
                if not reasoning or ("弃票" not in reasoning and "不投票" not in reasoning):
                    result["reasoning"] = "当前没有可投目标，我选择弃票。"
                if not speech:
                    result["speech"] = "当前没有可投目标，我选择弃票。"
            if not thinking:
                result["thinking"] = str(result.get("reasoning") or "")
        if strategy_name == "night_seer":
            action = result.get("action") or {}
            target = action.get("target") if isinstance(action, dict) else None
            reasoning = str(result.get("reasoning") or "").strip()
            if target:
                if not reasoning or (target not in reasoning and "查验" not in reasoning):
                    result["reasoning"] = f"第一夜信息有限，我查验了 {target} 以获取身份线索。"
            else:
                if not reasoning or ("未查验" not in reasoning and "没查验" not in reasoning):
                    result["reasoning"] = "当前没有可查验目标，我本轮未完成查验。"
        if strategy_name == "night_wolf":
            action = result.get("action") or {}
            target = action.get("target") if isinstance(action, dict) else None
            reasoning = str(result.get("reasoning") or "").strip()
            if target:
                if not reasoning or (target not in reasoning and "击杀" not in reasoning and "目标" not in reasoning):
                    result["reasoning"] = f"我建议今晚击杀 {target}。"
            else:
                if not reasoning or ("无可击杀目标" not in reasoning and "没有可击杀目标" not in reasoning):
                    result["reasoning"] = "当前无可击杀目标。"
        if strategy_name == "night_guard":
            action = result.get("action") or {}
            target = action.get("target") if isinstance(action, dict) else None
            reasoning = str(result.get("reasoning") or "").strip()
            if target:
                if not reasoning or (target not in reasoning and "守护" not in reasoning):
                    result["reasoning"] = f"我决定守护 {target}。"
            else:
                if not reasoning or ("未守护" not in reasoning and "不守护" not in reasoning):
                    result["reasoning"] = "当前没有可守护目标，我本轮未守护。"
        if strategy_name == "hunter_shot":
            action = result.get("action") or {}
            target = action.get("target") if isinstance(action, dict) else None
            reasoning = str(result.get("reasoning") or "").strip()
            if target:
                if not reasoning or (target not in reasoning and "带走" not in reasoning and "开枪" not in reasoning):
                    result["reasoning"] = f"我决定开枪带走 {target}。"
            else:
                if not reasoning or ("不开枪" not in reasoning and "未开枪" not in reasoning):
                    result["reasoning"] = "当前没有合适目标，我本轮不开枪。"
        return result

    @staticmethod
    def _default_action(context: dict) -> dict:
        return {
            "action": {"type": "skip", "target": None},
            "reasoning": "fallback/default",
        }

    def _night_wolf_action(self, context: dict) -> dict:
        alive = context.get("alive_player_ids") or context.get("alive_players", [])
        wolf_team = context.get("wolf_team_ids") or context.get("wolf_team", [])
        non_wolf = [pid for pid in alive if pid not in wolf_team]
        target = self._pick_random(non_wolf)
        if target:
            reasoning = f"我建议今晚击杀 {target}。"
        else:
            reasoning = "当前无可击杀目标。"
        return {
            "action": {"type": "kill", "target": target},
            "reasoning": reasoning,
        }

    def _night_guard_action(self, context: dict) -> dict:
        alive = context.get("alive_player_ids") or context.get("alive_players", [])
        last_guard_target = context.get("last_guard_target_id") or context.get("last_guard_target")
        candidates = [pid for pid in alive if pid != last_guard_target] or alive
        target = self._pick_random(candidates)
        if target:
            reasoning = f"我决定守护 {target}。"
        else:
            reasoning = "当前没有可守护目标，我本轮未守护。"
        return {
            "action": {"type": "guard", "target": target},
            "reasoning": reasoning,
        }

    def _night_witch_action(self, context: dict) -> dict:
        wolf_target = context.get("wolf_target_id") or context.get("wolf_target")
        role_capability = context.get("role_capability", {})
        if wolf_target and role_capability.get("can_use_antidote", False):
            return {
                "action": {"type": "save", "target": wolf_target, "save": True},
                "reasoning": "fallback/witch_save",
            }
        alive = context.get("alive_player_ids") or context.get("alive_players", [])
        poison_target = self._pick_random(alive) if alive and role_capability.get("can_use_poison", False) else None
        return {
            "action": {"type": "poison", "target": poison_target, "save": False},
            "reasoning": "fallback/witch_skip_or_poison",
        }

    def _night_seer_action(self, context: dict) -> dict:
        alive = context.get("alive_player_ids") or context.get("alive_players", [])
        me = context.get("player_id")
        candidates = [pid for pid in alive if pid != me]
        target = self._pick_random(candidates)
        if target:
            reasoning = f"第一夜信息有限，我查验了 {target} 以获取身份线索。"
        else:
            reasoning = "当前没有可查验目标，我本轮未完成查验。"
        return {
            "action": {"type": "check", "target": target},
            "reasoning": reasoning,
        }

    def _day_vote_action(self, context: dict) -> dict:
        alive = context.get("alive_player_ids") or context.get("alive_players", [])
        me = context.get("player_id")
        candidates = [pid for pid in alive if pid != me]
        target = self._pick_random(candidates)
        if target:
            reasoning = f"信息有限，我投票给 {target}。"
            speech = f"当前信息有限，我投票给 {target}。"
        else:
            reasoning = "当前没有可投目标，我选择弃票。"
            speech = "当前没有可投目标，我选择弃票。"
        return {
            "action": {"type": "vote", "target": target},
            "reasoning": reasoning,
            "speech": speech,
            "thinking": reasoning,
        }

    @staticmethod
    def _day_discuss_action(context: dict) -> dict:
        role = context.get("role", Role.VILLAGER.value)
        return {
            "action": {"type": "speak", "target": None},
            "speech": "我先听听大家的发言，再给出判断。",
            "thinking": f"我是{role}，当前信息有限，先观察发言逻辑。",
            "reasoning": f"我是{role}，当前信息有限，先观察发言逻辑。",
        }

    def _hunter_shot_action(self, context: dict) -> dict:
        alive = context.get("alive_player_ids") or context.get("alive_players", [])
        me = context.get("player_id")
        candidates = [pid for pid in alive if pid != me]
        target = self._pick_random(candidates)
        if target:
            reasoning = f"我决定开枪带走 {target}。"
        else:
            reasoning = "当前没有合适目标，我本轮不开枪。"
        return {
            "action": {"type": "shoot", "target": target},
            "reasoning": reasoning,
        }
