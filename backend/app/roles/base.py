from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from app.core.models import GameSnapshot


class SkillStrategy(ABC):
    role_name: str

    @abstractmethod
    def validate(self, snapshot: GameSnapshot, actor_id: str, target_id: Optional[str]) -> None:
        pass

    @abstractmethod
    def apply(self, snapshot: GameSnapshot, actor_id: str, target_id: Optional[str], extra: Optional[dict] = None) -> None:
        pass
