from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.integration
def test_monitor_ws_smoke_script() -> None:
    if os.getenv("RUN_MONITOR_INTEGRATION") != "1":
        pytest.skip("set RUN_MONITOR_INTEGRATION=1 to run integration tests")

    base_url = os.getenv("MONITOR_BASE_URL", "http://127.0.0.1:8000")
    player_count = os.getenv("MONITOR_PLAYER_COUNT", "11")

    backend_dir = Path(__file__).resolve().parents[1]
    script = backend_dir / "scripts" / "ws_monitor_smoke_test.py"

    proc = subprocess.run(
        [
            sys.executable,
            str(script),
            "--base-url",
            base_url,
            "--player-count",
            player_count,
        ],
        cwd=str(backend_dir),
        check=False,
        capture_output=True,
        text=True,
    )

    assert proc.returncode == 0, proc.stderr or proc.stdout

    payload = json.loads(proc.stdout)
    assert "subscribed" in payload["subscribe"]
    assert "room_state" in payload["subscribe"]
    assert "view_changed" in payload["change_view"]
    assert "phase_changed" in payload["advance"]
