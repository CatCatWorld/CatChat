from __future__ import annotations

import random
from typing import Dict, Optional

from app.core.models import GameSnapshot, Phase, Role
from app.roles.base import SkillStrategy


def _assert_alive(snapshot: GameSnapshot, player_id: str) -> None:
    player = snapshot.players.get(player_id)
    if not player or not player.alive:
        raise ValueError("player is not alive or not found")


def _assert_target_alive(snapshot: GameSnapshot, target_id: Optional[str]) -> None:
    if not target_id:
        raise ValueError("target_id is required")
    target = snapshot.players.get(target_id)
    if not target or not target.alive:
        raise ValueError("target is not alive or not found")


class WerewolfSkill(SkillStrategy):
    role_name = Role.WEREWOLF.value

    def validate(self, snapshot: GameSnapshot, actor_id: str, target_id: Optional[str]) -> None:
        if snapshot.phase != Phase.NIGHT_WOLF:
            raise ValueError("invalid phase for werewolf action")
        _assert_alive(snapshot, actor_id)
        _assert_target_alive(snapshot, target_id)
        actor = snapshot.players[actor_id]
        if actor.role != Role.WEREWOLF:
            raise ValueError("only werewolf can do this action")

    def apply(self, snapshot: GameSnapshot, actor_id: str, target_id: Optional[str], extra: Optional[dict] = None) -> None:
        self.validate(snapshot, actor_id, target_id)
        snapshot.round_context.night_actions.wolf_votes[actor_id] = target_id or ""


class GuardSkill(SkillStrategy):
    role_name = Role.GUARD.value

    def validate(self, snapshot: GameSnapshot, actor_id: str, target_id: Optional[str]) -> None:
        if snapshot.phase != Phase.NIGHT_GUARD:
            raise ValueError("invalid phase for guard action")
        _assert_alive(snapshot, actor_id)
        _assert_target_alive(snapshot, target_id)
        actor = snapshot.players[actor_id]
        if actor.role != Role.GUARD:
            raise ValueError("only guard can do this action")
        if actor.last_guard_target and actor.last_guard_target == target_id:
            raise ValueError("guard cannot protect same target in consecutive nights")

    def apply(self, snapshot: GameSnapshot, actor_id: str, target_id: Optional[str], extra: Optional[dict] = None) -> None:
        self.validate(snapshot, actor_id, target_id)
        snapshot.round_context.night_actions.guard_target = target_id
        snapshot.players[actor_id].last_guard_target = target_id


class WitchSkill(SkillStrategy):
    role_name = Role.WITCH.value

    def validate(self, snapshot: GameSnapshot, actor_id: str, target_id: Optional[str]) -> None:
        if snapshot.phase != Phase.NIGHT_WITCH:
            raise ValueError("invalid phase for witch action")
        _assert_alive(snapshot, actor_id)
        actor = snapshot.players[actor_id]
        if actor.role != Role.WITCH:
            raise ValueError("only witch can do this action")

    def apply(self, snapshot: GameSnapshot, actor_id: str, target_id: Optional[str], extra: Optional[dict] = None) -> None:
        self.validate(snapshot, actor_id, target_id)
        actor = snapshot.players[actor_id]
        use_save = bool((extra or {}).get("save", False))
        poison_target = target_id

        if use_save:
            if actor.used_antidote:
                raise ValueError("antidote already used")
            wolf_target = snapshot.round_context.wolf_target
            if not wolf_target:
                raise ValueError("no wolf target to save")
            if snapshot.round_context.round_no > 1 and wolf_target == actor_id:
                raise ValueError("witch can self-save only on first night")
            if snapshot.round_context.night_actions.guard_target == wolf_target:
                raise ValueError("cannot use antidote when wolf target is already protected")
            snapshot.round_context.night_actions.witch_save = True
            actor.used_antidote = True

        if poison_target:
            _assert_target_alive(snapshot, poison_target)
            if actor.used_poison:
                raise ValueError("poison already used")
            snapshot.round_context.night_actions.witch_poison_target = poison_target
            actor.used_poison = True


class SeerSkill(SkillStrategy):
    role_name = Role.SEER.value

    def validate(self, snapshot: GameSnapshot, actor_id: str, target_id: Optional[str]) -> None:
        if snapshot.phase != Phase.NIGHT_SEER:
            raise ValueError("invalid phase for seer action")
        _assert_alive(snapshot, actor_id)
        _assert_target_alive(snapshot, target_id)
        actor = snapshot.players[actor_id]
        if actor.role != Role.SEER:
            raise ValueError("only seer can do this action")
        if actor.last_seer_target and actor.last_seer_target == target_id:
            has_alternative = any(
                p.alive and p.player_id not in {actor_id, target_id}
                for p in snapshot.players.values()
            )
            if has_alternative:
                raise ValueError("seer cannot verify same target in consecutive nights")

    def apply(self, snapshot: GameSnapshot, actor_id: str, target_id: Optional[str], extra: Optional[dict] = None) -> None:
        self.validate(snapshot, actor_id, target_id)
        snapshot.round_context.night_actions.seer_target = target_id
        snapshot.players[actor_id].last_seer_target = target_id


def resolve_wolf_target(votes: Dict[str, str], alive_player_ids: list[str]) -> Optional[str]:
    if not alive_player_ids:
        return None
    filtered = [target for target in votes.values() if target in alive_player_ids]
    if not filtered:
        return random.choice(alive_player_ids)

    count: Dict[str, int] = {}
    for target in filtered:
        count[target] = count.get(target, 0) + 1
    max_votes = max(count.values())
    tied = [pid for pid, c in count.items() if c == max_votes]
    return random.choice(tied)


SKILL_REGISTRY: Dict[str, SkillStrategy] = {
    Role.WEREWOLF.value: WerewolfSkill(),
    Role.GUARD.value: GuardSkill(),
    Role.WITCH.value: WitchSkill(),
    Role.SEER.value: SeerSkill(),
}
