from __future__ import annotations

import subprocess
import sys
import time
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from threading import RLock
from typing import Dict, List

import httpx


@dataclass(slots=True)
class ChildAgentProcess:
    room_id: str
    player_id: str
    host: str
    port: int
    process: subprocess.Popen

    @property
    def endpoint(self) -> str:
        return f"http://{self.host}:{self.port}"


class ChildAgentProcessManager:
    """Manage child cat-agent processes under god-agent parent process."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._by_room: Dict[str, List[ChildAgentProcess]] = {}
        self._backend_dir = Path(__file__).resolve().parents[2]

    def bootstrap_room(
        self,
        *,
        room_id: str,
        player_ids: List[str],
        host: str = "127.0.0.1",
        start_port: int = 9101,
        startup_timeout_sec: float = 12.0,
    ) -> Dict[str, str]:
        self.stop_room(room_id)
        created: List[ChildAgentProcess] = []
        reserved_ports: set[int] = set()
        try:
            for idx, player_id in enumerate(player_ids):
                preferred_port = start_port + idx
                port = self._next_available_port(host, preferred_port, reserved_ports)
                reserved_ports.add(port)
                cmd = [
                    sys.executable,
                    "-m",
                    "uvicorn",
                    "cat_agent_template.main:app",
                    "--app-dir",
                    str(self._backend_dir),
                    "--host",
                    host,
                    "--port",
                    str(port),
                ]
                proc = subprocess.Popen(cmd, cwd=str(self._backend_dir))
                child = ChildAgentProcess(
                    room_id=room_id,
                    player_id=player_id,
                    host=host,
                    port=port,
                    process=proc,
                )
                created.append(child)

            max_workers = max(1, len(created))
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_map = {
                    executor.submit(self._wait_health, child.endpoint, startup_timeout_sec): child
                    for child in created
                }
                for future in as_completed(future_map):
                    future.result()

            with self._lock:
                self._by_room[room_id] = created

            return {item.player_id: item.endpoint for item in created}
        except Exception:
            for item in created:
                self._stop_process(item.process)
            raise

    @staticmethod
    def _is_port_available(host: str, port: int) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind((host, port))
                return True
            except OSError:
                return False

    @classmethod
    def _next_available_port(
        cls,
        host: str,
        start_port: int,
        reserved_ports: set[int],
        max_scan: int = 200,
    ) -> int:
        port = start_port
        for _ in range(max_scan):
            if port not in reserved_ports and cls._is_port_available(host, port):
                return port
            port += 1
            if port > 65535:
                port = 1024
        raise ValueError(f"no available port found from {start_port} within scan window={max_scan}")

    def stop_room(self, room_id: str) -> None:
        with self._lock:
            items = self._by_room.pop(room_id, [])
        for item in items:
            self._stop_process(item.process)

    def stop_all(self) -> None:
        with self._lock:
            all_rooms = list(self._by_room.keys())
        for room_id in all_rooms:
            self.stop_room(room_id)

    def status(self, room_id: str) -> Dict[str, dict]:
        with self._lock:
            items = list(self._by_room.get(room_id, []))
        result: Dict[str, dict] = {}
        for item in items:
            result[item.player_id] = {
                "endpoint": item.endpoint,
                "running": item.process.poll() is None,
                "pid": item.process.pid,
            }
        return result

    @staticmethod
    def _wait_health(endpoint: str, timeout_sec: float) -> None:
        url = endpoint.rstrip("/") + "/health"
        deadline = time.time() + timeout_sec
        last_error = "unknown"
        while time.time() < deadline:
            try:
                with httpx.Client(timeout=1.5) as client:
                    resp = client.get(url)
                if resp.status_code < 400:
                    return
                last_error = f"HTTP {resp.status_code}"
            except Exception as exc:  # noqa: BLE001
                last_error = type(exc).__name__
            time.sleep(0.25)
        raise ValueError(f"child agent not healthy: {url} ({last_error})")

    @staticmethod
    def _stop_process(proc: subprocess.Popen) -> None:
        if proc.poll() is not None:
            return
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:  # noqa: BLE001
            proc.kill()
