from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy import DateTime, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker


class Base(DeclarativeBase):
    pass


class GameRecord(Base):
    __tablename__ = "game_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    room_id: Mapped[str] = mapped_column(String(64), index=True)
    winner: Mapped[str] = mapped_column(String(16))
    rounds: Mapped[int] = mapped_column(Integer)
    payload_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class SQLiteRepository:
    def __init__(self, db_path: str = "./werewolf.db") -> None:
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.engine = create_engine(f"sqlite:///{db_path}", future=True)
        self.session_factory = sessionmaker(bind=self.engine, class_=Session, expire_on_commit=False)
        Base.metadata.create_all(self.engine)

    def save_finished_game(self, room_id: str, winner: str, rounds: int, payload: dict) -> int:
        with self.session_factory() as session:
            row = GameRecord(
                room_id=room_id,
                winner=winner,
                rounds=rounds,
                payload_json=json.dumps(payload, ensure_ascii=False),
            )
            session.add(row)
            session.commit()
            session.refresh(row)
            return row.id

    def get_game_record(self, record_id: int) -> Optional[dict]:
        with self.session_factory() as session:
            row = session.get(GameRecord, record_id)
            if not row:
                return None
            return {
                "id": row.id,
                "room_id": row.room_id,
                "winner": row.winner,
                "rounds": row.rounds,
                "payload": json.loads(row.payload_json),
                "created_at": row.created_at.isoformat(),
            }
