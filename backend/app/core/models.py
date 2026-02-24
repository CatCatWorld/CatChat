from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set


class Role(str, Enum):
    WEREWOLF = "werewolf"
    VILLAGER = "villager"
    SEER = "seer"
    WITCH = "witch"
    HUNTER = "hunter"
    GUARD = "guard"
    FOOL = "fool"


class Team(str, Enum):
    WOLF = "wolf"
    GOOD = "good"


class DeathCause(str, Enum):
    WOLF = "wolf"
    POISON = "poison"
    VOTE = "vote"
    HUNTER = "hunter"


class Phase(str, Enum):
    PREPARE = "prepare"
    NIGHT_WOLF = "night_wolf"
    NIGHT_GUARD = "night_guard"
    NIGHT_WITCH = "night_witch"
    NIGHT_SEER = "night_seer"
    DAY_ANNOUNCE = "day_announce"
    DAY_DISCUSS = "day_discuss"
    DAY_VOTE = "day_vote"
    GAME_OVER = "game_over"


class Winner(str, Enum):
    WOLF = "wolf"
    GOOD = "good"


@dataclass(slots=True)
class PlayerState:
    player_id: str
    nickname: str
    role: Optional[Role] = None
    alive: bool = True
    online: bool = True
    entrusted: bool = False
    can_hunter_shoot: bool = False
    can_vote: bool = True
    fool_revealed: bool = False
    last_guard_target: Optional[str] = None
    last_seer_target: Optional[str] = None
    used_antidote: bool = False
    used_poison: bool = False


@dataclass(slots=True)
class NightActions:
    wolf_votes: Dict[str, str] = field(default_factory=dict)
    day_votes: Dict[str, str] = field(default_factory=dict)
    guard_target: Optional[str] = None
    witch_save: bool = False
    witch_poison_target: Optional[str] = None
    seer_target: Optional[str] = None


@dataclass(slots=True)
class RoundContext:
    round_no: int = 1
    first_night: bool = True
    phase: Phase = Phase.PREPARE
    started_at: datetime = field(default_factory=datetime.utcnow)
    deadline_at: Optional[datetime] = None
    night_actions: NightActions = field(default_factory=NightActions)
    deaths_this_round: Dict[str, DeathCause] = field(default_factory=dict)
    protected_players: Set[str] = field(default_factory=set)
    wolf_target: Optional[str] = None


@dataclass(slots=True)
class GameSnapshot:
    room_id: str
    owner_id: str
    started: bool = False
    game_over: bool = False
    winner: Optional[Winner] = None
    players: Dict[str, PlayerState] = field(default_factory=dict)
    phase: Phase = Phase.PREPARE
    game_metadata: Dict[str, Any] = field(default_factory=dict)
    round_context: RoundContext = field(default_factory=RoundContext)
    action_audit_log: List[Dict[str, Any]] = field(default_factory=list)


ROLE_TEAM_MAP: Dict[Role, Team] = {
    Role.WEREWOLF: Team.WOLF,
    Role.VILLAGER: Team.GOOD,
    Role.SEER: Team.GOOD,
    Role.WITCH: Team.GOOD,
    Role.HUNTER: Team.GOOD,
    Role.GUARD: Team.GOOD,
    Role.FOOL: Team.GOOD,
}
