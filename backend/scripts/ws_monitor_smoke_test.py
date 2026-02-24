from __future__ import annotations

import argparse
import asyncio
import json
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

import httpx

try:
    import websockets
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "缺少依赖 websockets，请先执行: pip install websockets==13.1"
    ) from exc


@dataclass(slots=True)
class SmokeResult:
    room_id: str
    owner_id: str
    subscribe_events: list[str]
    change_view_events: list[str]
    advance_events: list[str]


def to_ws_base(http_base: str) -> str:
    parsed = urlparse(http_base)
    if parsed.scheme == "https":
        scheme = "wss"
    elif parsed.scheme == "http":
        scheme = "ws"
    else:
        raise ValueError(f"不支持的地址协议: {parsed.scheme}")
    return f"{scheme}://{parsed.netloc}"


async def recv_events(ws: Any, duration_sec: float) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    loop = asyncio.get_running_loop()
    end_at = loop.time() + duration_sec
    while True:
        remain = end_at - loop.time()
        if remain <= 0:
            break
        try:
            raw = await asyncio.wait_for(ws.recv(), timeout=remain)
        except TimeoutError:
            break
        events.append(json.loads(raw))
    return events


def event_names(events: list[dict[str, Any]]) -> list[str]:
    names = [item.get("event", "") for item in events]
    return sorted({name for name in names if name})


def ensure_contains(
    actual: list[str],
    expected: list[str],
    stage: str,
) -> None:
    missing = [name for name in expected if name not in actual]
    if missing:
        raise RuntimeError(f"{stage} 缺少事件: {missing}; 实际: {actual}")


async def run_smoke(
    base_url: str,
    player_count: int,
    window_sec: float,
) -> SmokeResult:
    base_url = base_url.rstrip("/")

    async with httpx.AsyncClient(base_url=base_url, timeout=20) as client:
        create_resp = await client.post(
            "/api/ai/rooms",
            json={"owner_nickname": "cat_01", "player_count": player_count},
        )
        create_resp.raise_for_status()
        created = create_resp.json()

        room_id = created["room_id"]
        owner_id = created.get("owner_id", "cat_01")
        players = created.get("players", [])
        watch_player = players[1] if len(players) > 1 else owner_id

        ws_url = f"{to_ws_base(base_url)}/ws/{room_id}/{owner_id}"
        async with websockets.connect(ws_url) as ws:
            await ws.send(
                json.dumps(
                    {
                        "type": "subscribe",
                        "room_id": room_id,
                        "view_mode": "god",
                    }
                )
            )
            subscribe_events = event_names(await recv_events(ws, window_sec))
            ensure_contains(
                subscribe_events,
                ["subscribed", "room_state"],
                "subscribe",
            )

            await ws.send(
                json.dumps(
                    {
                        "type": "change_view",
                        "mode": f"player:{watch_player}",
                    }
                )
            )
            change_view_events = event_names(await recv_events(ws, window_sec))
            ensure_contains(
                change_view_events,
                ["view_changed", "room_state"],
                "change_view",
            )

            start_resp = await client.post(
                f"/api/rooms/{room_id}/start",
                params={"owner_id": owner_id},
            )
            start_resp.raise_for_status()

            await ws.send(json.dumps({"event": "advance", "payload": {}}))

            advance_events = event_names(await recv_events(ws, window_sec))
            ensure_contains(
                advance_events,
                ["room_state", "phase_changed"],
                "advance",
            )

    return SmokeResult(
        room_id=room_id,
        owner_id=owner_id,
        subscribe_events=subscribe_events,
        change_view_events=change_view_events,
        advance_events=advance_events,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="狼人杀监控模式 WS 烟测脚本")
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:8000",
        help="后端地址",
    )
    parser.add_argument(
        "--player-count",
        type=int,
        default=11,
        help="创建房间人数(8~12)",
    )
    parser.add_argument(
        "--window-sec",
        type=float,
        default=1.2,
        help="每次动作后收集事件窗口(秒)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = asyncio.run(
        run_smoke(
            args.base_url,
            args.player_count,
            args.window_sec,
        )
    )
    print(
        json.dumps(
            {
                "room_id": result.room_id,
                "owner_id": result.owner_id,
                "subscribe": result.subscribe_events,
                "change_view": result.change_view_events,
                "advance": result.advance_events,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
