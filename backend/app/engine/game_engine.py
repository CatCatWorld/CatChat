from __future__ import annotations

import random
import re
from datetime import datetime, timedelta
from typing import Callable, Dict, List, Optional

from app.core.game_config import GameConfig, default_game_config
from app.core.models import (
    DeathCause,
    GameSnapshot,
    Phase,
    PlayerState,
    ROLE_TEAM_MAP,
    Role,
    Winner,
)
from app.engine.phase_orchestrator import PhaseOrchestrator
from app.roles.skills import SKILL_REGISTRY, resolve_wolf_target


SYSTEM_RNG = random.SystemRandom()


def _pick_random_target(candidates: List[str]) -> Optional[str]:
    if not candidates:
        return None
    pool = list(dict.fromkeys(candidates))
    if not pool:
        return None
    return SYSTEM_RNG.choice(pool)


class GameEngine:
    PUBLIC_SPEECH_HISTORY_LIMIT = 120

    def __init__(self, room_id: str, owner_id: str, config: Optional[GameConfig] = None) -> None:
        self.snapshot = GameSnapshot(room_id=room_id, owner_id=owner_id)
        self.config = config or default_game_config()
        self.phase_orchestrator = PhaseOrchestrator(
            night_order=self.config.night_order,
            role_distribution=self.config.role_distribution,
        )
        self.night_phases: List[Phase] = self.phase_orchestrator.generate_night_phases()
        self.hooks: Dict[str, List[Callable[[GameSnapshot], None]]] = {
            "on_phase_start": [],
            "on_player_death": [],
        }

    def register_hook(self, hook_name: str, callback: Callable[[GameSnapshot], None]) -> None:
        if hook_name not in self.hooks:
            self.hooks[hook_name] = []
        self.hooks[hook_name].append(callback)

    def _trigger_hook(self, hook_name: str) -> None:
        for callback in self.hooks.get(hook_name, []):
            callback(self.snapshot)

    def add_player(self, player_id: str, nickname: str) -> None:
        if self.snapshot.started:
            raise ValueError("game already started")
        if player_id in self.snapshot.players:
            raise ValueError("player already in room")
        if len(self.snapshot.players) >= self.config.total_players:
            raise ValueError("room is full")
        self.snapshot.players[player_id] = PlayerState(player_id=player_id, nickname=nickname)

    def mark_online_status(self, player_id: str, online: bool) -> None:
        player = self._must_get_player(player_id)
        player.online = online
        if not online:
            player.entrusted = True

    def start_game(self, operator_id: str) -> None:
        if operator_id != self.snapshot.owner_id:
            raise ValueError("only owner can start game")
        if self.snapshot.started:
            raise ValueError("game already started")

        expected = self.config.total_players
        if len(self.snapshot.players) != expected:
            raise ValueError(f"exactly {expected} players required")

        self._assign_roles()
        self.snapshot.game_metadata = {
            "total_players": self.config.player_count,
            "role_distribution": self.config.role_distribution,
            "special_rules": [
                "guard_no_consecutive",
                "hunter_cannot_shoot_when_poisoned",
                "fool_reveal_immune_once",
            ],
            "night_order": self.config.night_order,
            "warnings": self.config.warnings,
        }
        self.snapshot.started = True
        first_phase = self.night_phases[0] if self.night_phases else Phase.DAY_ANNOUNCE
        self._goto_phase(first_phase)

    def _assign_roles(self) -> None:
        role_pool: List[Role] = []
        for role_name, count in self.config.role_pool.items():
            role_pool.extend([Role(role_name)] * count)
        random.shuffle(role_pool)
        for player, role in zip(self.snapshot.players.values(), role_pool):
            player.role = role

    def submit_night_action(
        self,
        actor_id: str,
        target_id: Optional[str] = None,
        save: Optional[bool] = None,
    ) -> None:
        actor = self._must_get_player(actor_id)
        if not actor.alive:
            raise ValueError("dead player cannot act")

        if self.snapshot.phase == Phase.NIGHT_WOLF and actor.role == Role.WEREWOLF:
            SKILL_REGISTRY[Role.WEREWOLF.value].apply(self.snapshot, actor_id, target_id)
            self._audit("night_action", actor_id, {"phase": self.snapshot.phase.value, "target": target_id})
            return

        if self.snapshot.phase == Phase.NIGHT_GUARD and actor.role == Role.GUARD:
            SKILL_REGISTRY[Role.GUARD.value].apply(self.snapshot, actor_id, target_id)
            self._audit("night_action", actor_id, {"phase": self.snapshot.phase.value, "target": target_id})
            return

        if self.snapshot.phase == Phase.NIGHT_WITCH and actor.role == Role.WITCH:
            SKILL_REGISTRY[Role.WITCH.value].apply(
                self.snapshot,
                actor_id,
                target_id,
                extra={"save": bool(save)},
            )
            self._audit(
                "night_action",
                actor_id,
                {
                    "phase": self.snapshot.phase.value,
                    "save": bool(save),
                    "poison_target": target_id,
                },
            )
            return

        if self.snapshot.phase == Phase.NIGHT_SEER and actor.role == Role.SEER:
            SKILL_REGISTRY[Role.SEER.value].apply(self.snapshot, actor_id, target_id)
            self._audit("night_action", actor_id, {"phase": self.snapshot.phase.value, "target": target_id})
            return

        raise ValueError("action not allowed in current phase or role")

    def submit_vote(self, voter_id: str, target_id: Optional[str]) -> None:
        if self.snapshot.phase != Phase.DAY_VOTE:
            raise ValueError("vote only allowed in day vote phase")

        voter = self._must_get_player(voter_id)
        if not voter.alive:
            raise ValueError("dead player cannot vote")
        if not voter.can_vote:
            raise ValueError("player cannot vote")

        if target_id is not None:
            target = self._must_get_player(target_id)
            if not target.alive:
                raise ValueError("target is not alive")

        self.snapshot.round_context.night_actions.day_votes[voter_id] = target_id or ""
        self._audit("vote", voter_id, {"target": target_id})

    def submit_hunter_shot(self, hunter_id: str, target_id: str) -> None:
        hunter = self._must_get_player(hunter_id)
        if hunter.role != Role.HUNTER:
            raise ValueError("only hunter can shoot")
        if not hunter.can_hunter_shoot:
            raise ValueError("hunter cannot shoot now")

        target = self._must_get_player(target_id)
        if not target.alive:
            raise ValueError("target is not alive")

        self._kill_player(target_id, DeathCause.HUNTER)
        hunter.can_hunter_shoot = False
        self._audit("hunter_shot", hunter_id, {"target": target_id})

    def timeout_autorun_current_phase(self) -> None:
        phase = self.snapshot.phase
        if phase == Phase.NIGHT_WOLF:
            self._autorun_wolf_phase()
        elif phase == Phase.NIGHT_GUARD:
            self._autorun_guard_phase()
        elif phase == Phase.NIGHT_WITCH:
            self._autorun_witch_phase()
        elif phase == Phase.NIGHT_SEER:
            self._autorun_seer_phase()
        elif phase == Phase.DAY_VOTE:
            self._autorun_day_vote_phase()
        self.advance_phase()

    def _autorun_wolf_phase(self) -> None:
        alive_non_wolf = [
            p.player_id
            for p in self.snapshot.players.values()
            if p.alive and p.role != Role.WEREWOLF
        ]
        alive_wolves = [
            p.player_id
            for p in self.snapshot.players.values()
            if p.alive and p.role == Role.WEREWOLF
        ]
        for wolf_id in alive_wolves:
            votes = self.snapshot.round_context.night_actions.wolf_votes
            if wolf_id in votes or not alive_non_wolf:
                continue
            picked = _pick_random_target(alive_non_wolf)
            if not picked:
                continue
            votes[wolf_id] = picked
            self._audit("auto_action", wolf_id, {"phase": "night_wolf"})

    def _autorun_guard_phase(self) -> None:
        guard = self._find_alive_role(Role.GUARD)
        if not guard:
            return
        if self.snapshot.round_context.night_actions.guard_target is not None:
            return

        candidates = [
            p.player_id
            for p in self.snapshot.players.values()
            if p.alive and p.player_id != guard.last_guard_target
        ]
        if not candidates:
            candidates = [p.player_id for p in self.snapshot.players.values() if p.alive]
        picked = _pick_random_target(candidates)
        if not picked:
            return
        self.snapshot.round_context.night_actions.guard_target = picked
        guard.last_guard_target = self.snapshot.round_context.night_actions.guard_target
        self._audit("auto_action", guard.player_id, {"phase": "night_guard"})

    def _autorun_witch_phase(self) -> None:
        witch = self._find_alive_role(Role.WITCH)
        if witch:
            self._audit("auto_action", witch.player_id, {"phase": "night_witch", "action": "skip"})

    def _autorun_seer_phase(self) -> None:
        seer = self._find_alive_role(Role.SEER)
        if not seer:
            return
        if self.snapshot.round_context.night_actions.seer_target is not None:
            return
        candidates = [
            p.player_id
            for p in self.snapshot.players.values()
            if p.alive and p.player_id != seer.player_id and p.player_id != seer.last_seer_target
        ]
        if not candidates:
            candidates = [
                p.player_id
                for p in self.snapshot.players.values()
                if p.alive and p.player_id != seer.player_id
            ]
        if not candidates:
            return
        target_id = _pick_random_target(candidates)
        if not target_id:
            return
        self.snapshot.round_context.night_actions.seer_target = target_id
        seer.last_seer_target = target_id
        self._audit("auto_action", seer.player_id, {"phase": "night_seer"})

    def _autorun_day_vote_phase(self) -> None:
        alive_players = [p.player_id for p in self.snapshot.players.values() if p.alive]
        votes = self.snapshot.round_context.night_actions.day_votes
        for pid in alive_players:
            player = self.snapshot.players[pid]
            if not player.can_vote:
                continue
            if pid in votes:
                continue
            candidates = [x for x in alive_players if x != pid]
            votes[pid] = random.choice(candidates) if candidates else ""
            self._audit("auto_action", pid, {"phase": "day_vote", "action": "random_vote"})

    def advance_phase(self) -> None:
        if self.snapshot.game_over:
            self.snapshot.phase = Phase.GAME_OVER
            return

        phase = self.snapshot.phase
        if phase in self.night_phases:
            self._resolve_night_subphase(phase)
            return

        if phase == Phase.DAY_ANNOUNCE:
            self._goto_phase(Phase.DAY_DISCUSS)
            return

        if phase == Phase.DAY_DISCUSS:
            self._goto_phase(Phase.DAY_VOTE)
            return

        if phase == Phase.DAY_VOTE:
            self._resolve_day_vote()
            self._check_and_finalize_winner()
            if self.snapshot.game_over:
                return
            self._next_round_reset()
            first_phase = self.night_phases[0] if self.night_phases else Phase.DAY_ANNOUNCE
            self._goto_phase(first_phase)

    def _resolve_night_subphase(self, phase: Phase) -> None:
        if phase == Phase.NIGHT_WOLF:
            self._resolve_wolf_target()
        elif phase == Phase.NIGHT_GUARD:
            self._resolve_guard_effect()

        idx = self.night_phases.index(phase)
        if idx + 1 < len(self.night_phases):
            self._goto_phase(self.night_phases[idx + 1])
            return

        self._resolve_night_deaths()
        self._goto_phase(Phase.DAY_ANNOUNCE)
        self._check_and_finalize_winner()

    def get_seer_result(self, seer_id: str) -> Optional[dict]:
        seer = self._must_get_player(seer_id)
        if seer.role != Role.SEER:
            raise ValueError("not a seer")
        target_id = self.snapshot.round_context.night_actions.seer_target
        if not target_id:
            return None
        target = self._must_get_player(target_id)
        return {
            "target_id": target_id,
            "is_wolf": target.role == Role.WEREWOLF,
        }

    def get_witch_hint(self, witch_id: str) -> Optional[str]:
        witch = self._must_get_player(witch_id)
        if witch.role != Role.WITCH:
            raise ValueError("not a witch")
        if self.snapshot.phase != Phase.NIGHT_WITCH:
            return None
        return self.snapshot.round_context.wolf_target

    def _resolve_wolf_target(self) -> None:
        alive_non_wolf = [
            p.player_id
            for p in self.snapshot.players.values()
            if p.alive and p.role != Role.WEREWOLF
        ]
        wolf_target = resolve_wolf_target(
            self.snapshot.round_context.night_actions.wolf_votes,
            alive_non_wolf,
        )
        self.snapshot.round_context.wolf_target = wolf_target

    def _resolve_guard_effect(self) -> None:
        guard_target = self.snapshot.round_context.night_actions.guard_target
        self.snapshot.round_context.protected_players.clear()
        if guard_target:
            self.snapshot.round_context.protected_players.add(guard_target)

    def _resolve_night_deaths(self) -> None:
        ctx = self.snapshot.round_context
        deaths: Dict[str, DeathCause] = {}

        wolf_target = ctx.wolf_target
        if wolf_target:
            guarded = wolf_target in ctx.protected_players
            saved = ctx.night_actions.witch_save
            if not guarded and not saved:
                deaths[wolf_target] = DeathCause.WOLF

        poison_target = ctx.night_actions.witch_poison_target
        if poison_target:
            deaths[poison_target] = DeathCause.POISON

        ctx.deaths_this_round = {}
        for player_id, cause in deaths.items():
            if not self.snapshot.players[player_id].alive:
                continue
            self._kill_player(player_id, cause)
            ctx.deaths_this_round[player_id] = cause

        self._check_hunter_trigger(ctx.deaths_this_round)

    def _resolve_day_vote(self) -> None:
        votes = self.snapshot.round_context.night_actions.day_votes
        alive_voters = {
            p.player_id
            for p in self.snapshot.players.values()
            if p.alive and p.can_vote
        }

        counter: Dict[str, int] = {}
        submitted_count = 0
        for voter_id, target_id in votes.items():
            if voter_id not in alive_voters:
                continue
            submitted_count += 1
            if not target_id:
                continue
            target = self.snapshot.players.get(target_id)
            if not target or not target.alive:
                continue
            counter[target_id] = counter.get(target_id, 0) + 1

        abstain_or_missing = max(0, len(alive_voters) - submitted_count)

        if not counter:
            self.snapshot.round_context.deaths_this_round = {}
            self._audit("vote_result", "system", {"result": "no_valid_vote"})
            self._emit_day_vote_summary(
                result="no_valid_vote",
                counter=counter,
                abstain_or_missing=abstain_or_missing,
            )
            return

        max_votes = max(counter.values())
        tied = [pid for pid, cnt in counter.items() if cnt == max_votes]

        if len(tied) > 1 and self.config.rules.vote_tie_exile_none:
            self.snapshot.round_context.deaths_this_round = {}
            self._audit("vote_result", "system", {"result": "tie_no_exile", "tied": tied})
            self._emit_day_vote_summary(
                result="tie_no_exile",
                counter=counter,
                tied=tied,
                abstain_or_missing=abstain_or_missing,
            )
            return

        exile_target = random.choice(tied)
        exiled_player = self.snapshot.players[exile_target]

        if (
            exiled_player.role == Role.FOOL
            and not exiled_player.fool_revealed
            and self.config.rules.fool_reveal_immune_once
        ):
            exiled_player.fool_revealed = True
            exiled_player.can_vote = False
            self.snapshot.round_context.deaths_this_round = {}
            self._audit(
                "fool_reveal",
                exiled_player.player_id,
                {"result": "immune", "lost_vote_right": True},
            )
            self._emit_day_vote_summary(
                result="fool_reveal_immune",
                counter=counter,
                exile_target=exile_target,
                abstain_or_missing=abstain_or_missing,
            )
            return

        self._kill_player(exile_target, DeathCause.VOTE)
        self.snapshot.round_context.deaths_this_round = {exile_target: DeathCause.VOTE}
        self._audit("vote_result", "system", {"result": "exile", "target": exile_target})
        self._emit_day_vote_summary(
            result="exile",
            counter=counter,
            exile_target=exile_target,
            abstain_or_missing=abstain_or_missing,
        )
        self._check_hunter_trigger(self.snapshot.round_context.deaths_this_round)

    def _emit_day_vote_summary(
        self,
        *,
        result: str,
        counter: Dict[str, int],
        exile_target: Optional[str] = None,
        tied: Optional[List[str]] = None,
        abstain_or_missing: int = 0,
    ) -> None:
        lines: List[str] = ["法官：白天投票结果如下。"]

        if counter:
            items = sorted(counter.items(), key=lambda item: (-item[1], item[0]))
            detail = "、".join(
                f"{self.snapshot.players[pid].nickname or pid}({count}票)"
                for pid, count in items
                if pid in self.snapshot.players
            )
            if detail:
                lines.append("票型统计：" + detail + "。")

        if abstain_or_missing > 0:
            lines.append(f"未形成有效投票：{abstain_or_missing} 人。")

        if result == "exile" and exile_target:
            target_name = self.snapshot.players[exile_target].nickname or exile_target
            lines.append(f"最终放逐：{target_name}。")
        elif result == "tie_no_exile":
            tied_names = []
            for pid in tied or []:
                player = self.snapshot.players.get(pid)
                tied_names.append((player.nickname if player else None) or pid)
            if tied_names:
                lines.append("出现平票（" + "、".join(tied_names) + "），本轮无人出局。")
            else:
                lines.append("出现平票，本轮无人出局。")
        elif result == "fool_reveal_immune" and exile_target:
            target_name = self.snapshot.players[exile_target].nickname or exile_target
            lines.append(f"{target_name} 身份为白痴，翻牌免死，本轮无人出局。")
        elif result == "no_valid_vote":
            lines.append("本轮未形成有效票型，无人出局。")

        self._audit(
            "agent_speech",
            "god",
            {
                "phase": Phase.DAY_VOTE.value,
                "role": "judge",
                "content": " ".join(lines),
                "is_fallback": False,
                "fallback_reason": None,
            },
        )

    def _check_hunter_trigger(self, deaths: Dict[str, DeathCause]) -> None:
        for player_id, cause in deaths.items():
            player = self.snapshot.players[player_id]
            if player.role != Role.HUNTER:
                continue
            if cause == DeathCause.POISON and self.config.rules.hunter_cannot_shoot_if_poisoned:
                player.can_hunter_shoot = False
            elif cause in {DeathCause.WOLF, DeathCause.VOTE}:
                player.can_hunter_shoot = True

    def _kill_player(self, player_id: str, cause: DeathCause) -> None:
        player = self._must_get_player(player_id)
        if not player.alive:
            return
        player.alive = False
        self._audit("death", "system", {"player_id": player_id, "cause": cause.value})
        self._trigger_hook("on_player_death")

    def _check_and_finalize_winner(self) -> Optional[Winner]:
        alive_wolves = 0
        alive_total = 0
        for player in self.snapshot.players.values():
            if not player.alive:
                continue
            alive_total += 1
            if ROLE_TEAM_MAP[player.role] == ROLE_TEAM_MAP[Role.WEREWOLF]:
                alive_wolves += 1

        if alive_wolves == 0:
            self.snapshot.winner = Winner.GOOD
        elif alive_wolves >= (alive_total - alive_wolves):
            self.snapshot.winner = Winner.WOLF
        else:
            return None

        self.snapshot.game_over = True
        self.snapshot.phase = Phase.GAME_OVER
        return self.snapshot.winner

    def _next_round_reset(self) -> None:
        ctx = self.snapshot.round_context
        ctx.round_no += 1
        ctx.first_night = False
        ctx.night_actions.wolf_votes.clear()
        ctx.night_actions.day_votes.clear()
        ctx.night_actions.guard_target = None
        ctx.night_actions.witch_save = False
        ctx.night_actions.witch_poison_target = None
        ctx.night_actions.seer_target = None
        ctx.deaths_this_round.clear()
        ctx.protected_players.clear()
        ctx.wolf_target = None

    def _goto_phase(self, phase: Phase) -> None:
        self.snapshot.phase = phase
        self.snapshot.round_context.phase = phase
        timeout_seconds = (
            self.config.timeout.day_vote_seconds
            if phase == Phase.DAY_VOTE
            else self.config.timeout.night_action_seconds
        )

        timed_phases = set(self.night_phases)
        timed_phases.add(Phase.DAY_VOTE)
        if phase in timed_phases:
            self.snapshot.round_context.deadline_at = datetime.utcnow() + timedelta(seconds=timeout_seconds)
        else:
            self.snapshot.round_context.deadline_at = None

        if phase == Phase.NIGHT_WOLF:
            self.snapshot.round_context.night_actions.wolf_votes.clear()
        if phase == Phase.DAY_VOTE:
            self.snapshot.round_context.night_actions.day_votes.clear()

        self._audit("phase_change", "system", {"phase": phase.value})
        self._trigger_hook("on_phase_start")

    def _audit(self, event_type: str, actor_id: str, payload: dict) -> None:
        if event_type == "agent_speech" and isinstance(payload, dict):
            phase = str(payload.get("phase") or "")
            if phase == Phase.DAY_DISCUSS.value:
                content = str(payload.get("content") or "").strip()
                if content:
                    sanitized_payload = dict(payload)
                    sanitized_payload["content"] = self._sanitize_public_day_discuss_content(content)
                    payload = sanitized_payload

        self.snapshot.action_audit_log.append(
            {
                "ts": datetime.utcnow().isoformat(),
                "event_type": event_type,
                "actor_id": actor_id,
                "payload": payload,
            }
        )

    @staticmethod
    def _sanitize_public_day_discuss_content(text: str) -> str:
        speech = str(text or "").strip()
        if not speech:
            return speech

        replacements = [
            ("暴露狼人身份", "暴露真实身份"),
            ("狼人身份", "真实身份"),
            ("（狼人）", "（疑似狼人）"),
            ("是狼人", "疑似狼人"),
            ("就是狼人", "疑似狼人"),
            ("为狼人", "疑似狼人"),
            ("必是狼人", "疑似狼人"),
        ]
        for src, dst in replacements:
            speech = speech.replace(src, dst)

        speech = re.sub(r"\b狼(?:人)?阵营\b", "对立阵营", speech)
        return speech

    def _find_alive_role(self, role: Role) -> Optional[PlayerState]:
        for player in self.snapshot.players.values():
            if player.alive and player.role == role:
                return player
        return None

    def _must_get_player(self, player_id: str) -> PlayerState:
        player = self.snapshot.players.get(player_id)
        if not player:
            raise ValueError("player not found")
        return player

    def public_state(self) -> dict:
        speech_history = []
        death_cause_by_player: Dict[str, str] = {}
        for row in self.snapshot.action_audit_log:
            event_type = row.get("event_type")
            payload = row.get("payload", {}) or {}

            if event_type == "death":
                dead_player_id = payload.get("player_id")
                cause = payload.get("cause")
                if isinstance(dead_player_id, str) and dead_player_id and isinstance(cause, str) and cause:
                    death_cause_by_player[dead_player_id] = cause
                continue

            if event_type == "agent_speech":
                speech_history.append(
                    {
                        "player_id": row.get("actor_id"),
                        "phase": payload.get("phase"),
                        "role": payload.get("role"),
                        "content": payload.get("content", ""),
                        "thought_content": payload.get("thought_content", ""),
                        "is_fallback": payload.get("is_fallback", False),
                        "fallback_reason": payload.get("fallback_reason"),
                        "timestamp": row.get("ts"),
                        "event": "agent_speech",
                    }
                )
                continue

            if event_type == "god_narration":
                speech_history.append(
                    {
                        "player_id": "god",
                        "phase": payload.get("phase") or self.snapshot.phase.value,
                        "role": "judge",
                        "content": payload.get("content", ""),
                        "is_fallback": payload.get("is_fallback", False),
                        "fallback_reason": payload.get("fallback_reason"),
                        "timestamp": row.get("ts"),
                        "event": "god_narration",
                    }
                )
                continue

            if event_type == "vote_result":
                result = str(payload.get("result") or "")
                if result == "exile":
                    target_id = payload.get("target")
                    target_name = (
                        (self.snapshot.players[target_id].nickname or target_id)
                        if isinstance(target_id, str) and target_id in self.snapshot.players
                        else "未知"
                    )
                    content = f"投票结果：{target_name} 被放逐。"
                elif result == "tie_no_exile":
                    tied = payload.get("tied") or []
                    tied_names = [
                        (self.snapshot.players[pid].nickname or pid)
                        for pid in tied
                        if isinstance(pid, str) and pid in self.snapshot.players
                    ]
                    if tied_names:
                        content = "投票结果：平票（" + "、".join(tied_names) + "），无人出局。"
                    else:
                        content = "投票结果：平票，无人出局。"
                elif result == "no_valid_vote":
                    content = "投票结果：未形成有效票型，无人出局。"
                else:
                    content = "投票结果已结算。"

                speech_history.append(
                    {
                        "player_id": "god",
                        "phase": Phase.DAY_VOTE.value,
                        "role": "judge",
                        "content": content,
                        "is_fallback": False,
                        "fallback_reason": None,
                        "timestamp": row.get("ts"),
                        "event": "vote_result",
                    }
                )
                continue

            if event_type == "fool_reveal":
                player_id = row.get("actor_id")
                player_name = (
                    (self.snapshot.players[player_id].nickname or player_id)
                    if isinstance(player_id, str) and player_id in self.snapshot.players
                    else "该玩家"
                )
                speech_history.append(
                    {
                        "player_id": "god",
                        "phase": Phase.DAY_VOTE.value,
                        "role": "judge",
                        "content": f"投票结果：{player_name} 为白痴并翻牌免死，本轮无人出局。",
                        "is_fallback": False,
                        "fallback_reason": None,
                        "timestamp": row.get("ts"),
                        "event": "fool_reveal",
                    }
                )

        return {
            "room_id": self.snapshot.room_id,
            "owner_id": self.snapshot.owner_id,
            "started": self.snapshot.started,
            "phase": self.snapshot.phase.value,
            "round_no": self.snapshot.round_context.round_no,
            "game_over": self.snapshot.game_over,
            "winner": self.snapshot.winner.value if self.snapshot.winner else None,
            "game_metadata": self.snapshot.game_metadata,
            "night_phases": [p.value for p in self.night_phases],
            "players": [
                {
                    "player_id": p.player_id,
                    "nickname": p.nickname,
                    "role": p.role.value if p.role else None,
                    "alive": p.alive,
                    "death_cause": death_cause_by_player.get(p.player_id),
                    "online": p.online,
                    "can_vote": p.can_vote,
                    "fool_revealed": p.fool_revealed,
                }
                for p in self.snapshot.players.values()
            ],
            "deaths_this_round": {
                pid: cause.value
                for pid, cause in self.snapshot.round_context.deaths_this_round.items()
            },
            "speech_history": speech_history[-self.PUBLIC_SPEECH_HISTORY_LIMIT :],
            "is_peace_night": self.snapshot.phase in {Phase.DAY_ANNOUNCE, Phase.DAY_DISCUSS, Phase.DAY_VOTE}
            and not self.snapshot.round_context.deaths_this_round,
        }
