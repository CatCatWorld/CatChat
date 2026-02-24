from __future__ import annotations

from abc import ABC, abstractmethod

from app.core.models import Phase


class BasePhaseState(ABC):
    phase: Phase

    @abstractmethod
    def next_phase(self) -> Phase:
        pass


class PrepareState(BasePhaseState):
    phase = Phase.PREPARE

    def next_phase(self) -> Phase:
        return Phase.NIGHT_WOLF


class NightWolfState(BasePhaseState):
    phase = Phase.NIGHT_WOLF

    def next_phase(self) -> Phase:
        return Phase.NIGHT_GUARD


class NightGuardState(BasePhaseState):
    phase = Phase.NIGHT_GUARD

    def next_phase(self) -> Phase:
        return Phase.NIGHT_WITCH


class NightWitchState(BasePhaseState):
    phase = Phase.NIGHT_WITCH

    def next_phase(self) -> Phase:
        return Phase.NIGHT_SEER


class NightSeerState(BasePhaseState):
    phase = Phase.NIGHT_SEER

    def next_phase(self) -> Phase:
        return Phase.DAY_ANNOUNCE


class DayAnnounceState(BasePhaseState):
    phase = Phase.DAY_ANNOUNCE

    def next_phase(self) -> Phase:
        return Phase.DAY_DISCUSS


class DayDiscussState(BasePhaseState):
    phase = Phase.DAY_DISCUSS

    def next_phase(self) -> Phase:
        return Phase.DAY_VOTE


class DayVoteState(BasePhaseState):
    phase = Phase.DAY_VOTE

    def next_phase(self) -> Phase:
        return Phase.NIGHT_WOLF


STATE_REGISTRY = {
    Phase.PREPARE: PrepareState(),
    Phase.NIGHT_WOLF: NightWolfState(),
    Phase.NIGHT_GUARD: NightGuardState(),
    Phase.NIGHT_WITCH: NightWitchState(),
    Phase.NIGHT_SEER: NightSeerState(),
    Phase.DAY_ANNOUNCE: DayAnnounceState(),
    Phase.DAY_DISCUSS: DayDiscussState(),
    Phase.DAY_VOTE: DayVoteState(),
}
