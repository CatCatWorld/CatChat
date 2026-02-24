from __future__ import annotations

import base64
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

_CATS_KEY = "CATCHAT_CATS_B64"
_MONITOR_KEY = "CATCHAT_MONITOR_CONFIG_B64"
_SAVED_AT_KEY = "CATCHAT_PROFILE_SAVED_AT"
_ENV_PATH = Path(__file__).resolve().parents[2] / ".env"


def _decode_b64_json(raw: str | None, default: Any) -> Any:
    if not raw:
        return default
    try:
        text = base64.b64decode(raw.encode("utf-8")).decode("utf-8")
        return json.loads(text)
    except Exception:  # noqa: BLE001
        return default


def _encode_b64_json(data: Any) -> str:
    text = json.dumps(data, ensure_ascii=False)
    return base64.b64encode(text.encode("utf-8")).decode("utf-8")


def _parse_env_file() -> Dict[str, str]:
    if not _ENV_PATH.exists():
        return {}
    result: Dict[str, str] = {}
    for line in _ENV_PATH.read_text(encoding="utf-8").splitlines():
        row = line.strip()
        if not row or row.startswith("#") or "=" not in row:
            continue
        key, value = row.split("=", 1)
        result[key.strip()] = value.strip()
    return result


def _upsert_env_file(values: Dict[str, str]) -> None:
    existing = _parse_env_file()
    existing.update(values)
    lines = [f"{k}={v}" for k, v in sorted(existing.items())]
    _ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def load_frontend_profile() -> Dict[str, Any]:
    file_env = _parse_env_file()
    cats_raw = os.getenv(_CATS_KEY) or file_env.get(_CATS_KEY)
    monitor_raw = os.getenv(_MONITOR_KEY) or file_env.get(_MONITOR_KEY)
    saved_at = os.getenv(_SAVED_AT_KEY) or file_env.get(_SAVED_AT_KEY)

    cats = _decode_b64_json(cats_raw, [])
    monitor = _decode_b64_json(monitor_raw, {})

    if not isinstance(cats, list):
        cats = []
    if not isinstance(monitor, dict):
        monitor = {}

    source = "none"
    if cats_raw or monitor_raw or saved_at:
        source = "env"

    return {
        "source": source,
        "cats": cats,
        "monitor_config": monitor,
        "saved_at": saved_at,
    }


def save_frontend_profile(*, cats: list[dict], monitor_config: dict[str, Any] | None = None) -> Dict[str, Any]:
    monitor_config = monitor_config or {}
    saved_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    cats_b64 = _encode_b64_json(cats)
    monitor_b64 = _encode_b64_json(monitor_config)

    os.environ[_CATS_KEY] = cats_b64
    os.environ[_MONITOR_KEY] = monitor_b64
    os.environ[_SAVED_AT_KEY] = saved_at

    _upsert_env_file(
        {
            _CATS_KEY: cats_b64,
            _MONITOR_KEY: monitor_b64,
            _SAVED_AT_KEY: saved_at,
        }
    )

    return {
        "saved": True,
        "saved_at": saved_at,
        "cats_count": len(cats),
        "env_file": str(_ENV_PATH),
        "keys": [_CATS_KEY, _MONITOR_KEY, _SAVED_AT_KEY],
    }
