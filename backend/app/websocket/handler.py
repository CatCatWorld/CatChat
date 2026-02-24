from __future__ import annotations

import asyncio
import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import DefaultDict, Dict, Optional, Set

from fastapi import WebSocket


@dataclass(slots=True)
class WSSubscriber:
    room_id: str
    player_id: str
    view_mode: str = "god"
    last_event_id: int = 0


class WSConnectionManager:
    def __init__(self) -> None:
        self._connections: DefaultDict[str, Set[WebSocket]] = defaultdict(set)
        self._subscribers: Dict[WebSocket, WSSubscriber] = {}
        self._event_counter: int = 0
        self._lock = asyncio.Lock()

    async def connect(self, room_id: str, player_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections[room_id].add(websocket)
            self._subscribers[websocket] = WSSubscriber(room_id=room_id, player_id=player_id)

    async def disconnect(self, room_id: str, websocket: WebSocket) -> None:
        async with self._lock:
            if room_id in self._connections and websocket in self._connections[room_id]:
                self._connections[room_id].remove(websocket)
            self._subscribers.pop(websocket, None)

    async def update_view_mode(self, websocket: WebSocket, view_mode: str) -> None:
        async with self._lock:
            sub = self._subscribers.get(websocket)
            if not sub:
                return
            sub.view_mode = view_mode

    async def send_event(self, websocket: WebSocket, event: str, payload: Dict) -> None:
        async with self._lock:
            self._event_counter += 1
            event_id = self._event_counter
            sub = self._subscribers.get(websocket)
            if sub:
                sub.last_event_id = event_id
        message = json.dumps(
            {
                "event_id": event_id,
                "event": event,
                "payload": payload,
                "ts": datetime.utcnow().isoformat(),
            },
            ensure_ascii=False,
        )
        await websocket.send_text(message)

    async def broadcast(self, room_id: str, event: str, payload: Dict) -> None:
        stale = []
        async with self._lock:
            self._event_counter += 1
            event_id = self._event_counter
            conns = list(self._connections.get(room_id, set()))
        for ws in conns:
            try:
                message = json.dumps(
                    {
                        "event_id": event_id,
                        "event": event,
                        "payload": payload,
                        "ts": datetime.utcnow().isoformat(),
                    },
                    ensure_ascii=False,
                )
                await ws.send_text(message)
            except Exception:
                stale.append(ws)
        if stale:
            async with self._lock:
                for ws in stale:
                    self._connections[room_id].discard(ws)
                    self._subscribers.pop(ws, None)

    async def broadcast_room_state(self, room_id: str, state: Dict) -> None:
        stale = []
        async with self._lock:
            self._event_counter += 1
            event_id = self._event_counter
            conns = list(self._connections.get(room_id, set()))
            subscribers = {ws: self._subscribers.get(ws) for ws in conns}

        for ws in conns:
            sub = subscribers.get(ws)
            if not sub:
                continue
            filtered = self._filter_state_for_view(state, sub.view_mode, sub.player_id)
            try:
                message = json.dumps(
                    {
                        "event_id": event_id,
                        "event": "room_state",
                        "payload": filtered,
                        "ts": datetime.utcnow().isoformat(),
                    },
                    ensure_ascii=False,
                )
                await ws.send_text(message)
            except Exception:
                stale.append(ws)

        if stale:
            async with self._lock:
                for ws in stale:
                    self._connections[room_id].discard(ws)
                    self._subscribers.pop(ws, None)

    async def broadcast_phase_changed(
        self,
        room_id: str,
        payload: Dict,
        god_view: Optional[Dict] = None,
    ) -> None:
        stale = []
        async with self._lock:
            self._event_counter += 1
            event_id = self._event_counter
            conns = list(self._connections.get(room_id, set()))
            subscribers = {ws: self._subscribers.get(ws) for ws in conns}

        for ws in conns:
            sub = subscribers.get(ws)
            if not sub:
                continue
            merged = dict(payload)
            if sub.view_mode == "god" and god_view:
                merged["god_view"] = god_view
            try:
                message = json.dumps(
                    {
                        "event_id": event_id,
                        "event": "phase_changed",
                        "payload": merged,
                        "ts": datetime.utcnow().isoformat(),
                    },
                    ensure_ascii=False,
                )
                await ws.send_text(message)
            except Exception:
                stale.append(ws)

        if stale:
            async with self._lock:
                for ws in stale:
                    self._connections[room_id].discard(ws)
                    self._subscribers.pop(ws, None)

    @staticmethod
    def _filter_state_for_view(state: Dict, view_mode: str, player_id: str) -> Dict:
        if view_mode == "god":
            return state

        if view_mode.startswith("player:"):
            watch_player = view_mode.split(":", 1)[1]
        else:
            watch_player = player_id

        filtered = dict(state)
        filtered.pop("game_metadata", None)

        players = filtered.get("players", [])
        filtered["players"] = [
            {
                "player_id": item.get("player_id"),
                "nickname": item.get("nickname"),
                "alive": item.get("alive"),
                "online": item.get("online"),
            }
            for item in players
        ]

        speech_history = filtered.get("speech_history", [])
        if isinstance(speech_history, list):
            sanitized_history = []
            for item in speech_history:
                if not isinstance(item, dict):
                    continue
                if item.get("player_id") == "god" and item.get("event") == "agent_speech":
                    continue
                sanitized = dict(item)
                sanitized.pop("thought_content", None)
                sanitized_history.append(sanitized)
            filtered["speech_history"] = sanitized_history

        filtered["watch_player"] = watch_player
        return filtered

    async def subscriber(self, websocket: WebSocket) -> Optional[WSSubscriber]:
        async with self._lock:
            return self._subscribers.get(websocket)


ws_manager = WSConnectionManager()
