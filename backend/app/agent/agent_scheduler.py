from __future__ import annotations

import asyncio
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional
from urllib.parse import urlparse

import httpx

from app.agent.fallback_strategies import FallbackStrategies


@dataclass(slots=True)
class AgentRegistration:
    player_id: str
    ipc_endpoint: str
    model_type: str
    timeout_sec: int = 15
    api_url: Optional[str] = None
    api_key: Optional[str] = None
    model_name: Optional[str] = None
    cli_command: Optional[str] = None
    cli_timeout_sec: int = 20
    online: bool = True
    failed_count: int = 0
    entrusted: bool = False
    registered_at: datetime = field(default_factory=datetime.utcnow)
    last_heartbeat: datetime = field(default_factory=datetime.utcnow)
    last_error: Optional[str] = None


@dataclass(slots=True)
class SchedulerMetrics:
    total_calls: int = 0
    timeout_calls: int = 0
    error_calls: int = 0
    total_latency_ms: float = 0.0
    by_error_type: Dict[str, int] = field(default_factory=dict)

    def observe_success(self, latency_ms: float) -> None:
        self.total_calls += 1
        self.total_latency_ms += latency_ms

    def observe_timeout(self) -> None:
        self.total_calls += 1
        self.timeout_calls += 1
        self.by_error_type["timeout"] = self.by_error_type.get("timeout", 0) + 1

    def observe_error(self, error_name: str) -> None:
        self.total_calls += 1
        self.error_calls += 1
        self.by_error_type[error_name] = self.by_error_type.get(error_name, 0) + 1

    def to_dict(self) -> dict:
        avg = 0.0 if self.total_calls == 0 else self.total_latency_ms / self.total_calls
        timeout_rate = 0.0 if self.total_calls == 0 else self.timeout_calls / self.total_calls
        return {
            "total_calls": self.total_calls,
            "timeout_calls": self.timeout_calls,
            "error_calls": self.error_calls,
            "avg_latency_ms": round(avg, 2),
            "timeout_rate": round(timeout_rate, 4),
            "by_error_type": self.by_error_type,
        }


class AgentRegistry:
    def __init__(self) -> None:
        self._agents: Dict[str, AgentRegistration] = {}

    def register(
        self,
        player_id: str,
        ipc_endpoint: str,
        model_type: str,
        timeout_sec: int = 15,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        cli_command: Optional[str] = None,
        cli_timeout_sec: int = 20,
    ) -> AgentRegistration:
        reg = AgentRegistration(
            player_id=player_id,
            ipc_endpoint=ipc_endpoint.rstrip("/"),
            model_type=model_type,
            timeout_sec=timeout_sec,
            api_url=api_url,
            api_key=api_key,
            model_name=model_name,
            cli_command=cli_command,
            cli_timeout_sec=cli_timeout_sec,
            online=True,
            failed_count=0,
            entrusted=False,
        )
        self._agents[player_id] = reg
        return reg

    def get(self, player_id: str) -> Optional[AgentRegistration]:
        return self._agents.get(player_id)

    def all(self) -> Dict[str, AgentRegistration]:
        return self._agents

    def mark_offline(self, player_id: str) -> None:
        agent = self._agents.get(player_id)
        if not agent:
            return
        agent.online = False
        agent.entrusted = True


class AgentScheduler:
    """God-agent scheduling core with timeout/circuit-breaker/fallback."""

    def __init__(self, fallback: Optional[FallbackStrategies] = None, debug_mode: bool = False) -> None:
        self.registry = AgentRegistry()
        self.fallback = fallback or FallbackStrategies()
        self.metrics = SchedulerMetrics()
        self.audit_logs: list[dict] = []
        self.debug_mode = debug_mode
        self.provider_max_concurrency = max(1, int(os.getenv("CAT_PROVIDER_MAX_CONCURRENCY", "8")))
        self.same_provider_max_concurrency = max(1, int(os.getenv("CAT_SAME_PROVIDER_MAX_CONCURRENCY", "1")))
        self.day_discuss_same_provider_concurrency = max(
            1,
            int(os.getenv("CAT_DAY_DISCUSS_SAME_PROVIDER_CONCURRENCY", "2")),
        )
        self.day_vote_same_provider_concurrency = max(
            1,
            int(os.getenv("CAT_DAY_VOTE_SAME_PROVIDER_CONCURRENCY", "1")),
        )
        self.max_timeout_retries = max(0, int(os.getenv("CAT_AGENT_TIMEOUT_RETRIES", "2")))
        self.max_transient_retries = max(0, int(os.getenv("CAT_AGENT_TRANSIENT_RETRIES", "2")))
        self.retry_backoff_sec = max(0.1, float(os.getenv("CAT_AGENT_RETRY_BACKOFF_SEC", "0.8")))
        self._provider_semaphores: Dict[str, asyncio.Semaphore] = {}
        self._provider_limits: Dict[str, int] = {}

    @staticmethod
    def _api_timeout_budget(agent: AgentRegistration, phase: str) -> int:
        if phase in {"day_discuss", "day_vote"}:
            return max(agent.timeout_sec - 1, 20)
        if phase.startswith("night_"):
            return max(agent.timeout_sec - 2, 15)
        return max(agent.timeout_sec - 2, 15)

    @staticmethod
    def _transport_timeout_budget(agent: AgentRegistration, phase: str) -> int:
        if phase in {"day_discuss", "day_vote"}:
            return max(agent.timeout_sec + 10, 35)
        return max(agent.timeout_sec + 5, 25)

    def _provider_key(self, agent: AgentRegistration) -> str:
        if agent.cli_command:
            return "cli"
        url = (agent.api_url or "").strip().lower()
        if url:
            parsed = urlparse(url)
            netloc = parsed.netloc or parsed.path
            model_name = (agent.model_name or "").strip().lower() or "unknown-model"
            return f"api:{netloc}|model:{model_name}"
        return f"model:{(agent.model_type or 'unknown').lower()}"

    def _provider_limit(self, agent: AgentRegistration, phase: str) -> int:
        if agent.cli_command:
            return self.provider_max_concurrency
        if (agent.api_url or "").strip():
            phase_key = (phase or "").strip().lower()
            if phase_key == "day_vote":
                return min(self.provider_max_concurrency, self.day_vote_same_provider_concurrency)
            if phase_key == "day_discuss":
                return min(self.provider_max_concurrency, self.day_discuss_same_provider_concurrency)
            return min(self.provider_max_concurrency, self.same_provider_max_concurrency)
        return self.provider_max_concurrency

    def _provider_semaphore(self, agent: AgentRegistration, phase: str) -> asyncio.Semaphore:
        key = self._provider_key(agent)
        sem = self._provider_semaphores.get(key)
        limit = self._provider_limit(agent, phase)
        if sem is None:
            sem = asyncio.Semaphore(limit)
            self._provider_semaphores[key] = sem
            self._provider_limits[key] = limit
            return sem
        old_limit = self._provider_limits.get(key)
        if old_limit != limit:
            sem = asyncio.Semaphore(limit)
            self._provider_semaphores[key] = sem
            self._provider_limits[key] = limit
        return sem

    async def trigger_agent_action(
        self,
        *,
        player_id: str,
        session_id: str,
        role: str,
        phase: str,
        visible_state: dict,
        prompt_template: str,
        strategy_name: str,
    ) -> dict:
        agent = self.registry.get(player_id)
        if not agent or not agent.online:
            return self._fallback_action(strategy_name, visible_state, "offline")

        payload = {
            "session_id": session_id,
            "player_id": player_id,
            "role": role,
            "phase": phase,
            "visible_state": visible_state,
            "prompt_template": prompt_template,
            "agent_config": {
                "provider": agent.model_type,
                "api_url": agent.api_url,
                "api_key": agent.api_key,
                "model_name": agent.model_name or agent.model_type,
                "api_timeout_sec": self._api_timeout_budget(agent, phase),
                "cli_command": agent.cli_command,
                "cli_timeout_sec": agent.cli_timeout_sec,
            },
        }

        if self.debug_mode:
            self.audit_logs.append(
                {
                    "event": "god_visible_state",
                    "player_id": player_id,
                    "phase": phase,
                    "visible_state": visible_state,
                    "ts": datetime.utcnow().isoformat(),
                }
            )

        start = time.perf_counter()
        try:
            transport_timeout = self._transport_timeout_budget(agent, phase)
            timeout_reason: Optional[str] = None
            async with self._provider_semaphore(agent, phase):
                max_attempts = max(self.max_timeout_retries, self.max_transient_retries) + 1
                for attempt in range(max_attempts):
                    try:
                        async with httpx.AsyncClient(timeout=transport_timeout) as client:
                            resp = await client.post(f"{agent.ipc_endpoint}/act", json=payload)

                        if resp.status_code >= 400:
                            transient = resp.status_code in {429, 500, 502, 503, 504}
                            if transient and attempt < self.max_transient_retries:
                                await asyncio.sleep(self.retry_backoff_sec * (2 ** attempt))
                                continue
                            self.metrics.observe_error(f"http_{resp.status_code}")
                            return self._handle_failure(agent, strategy_name, visible_state, f"http_{resp.status_code}")

                        data = self._validate_and_parse(resp.json())
                        latency_ms = (time.perf_counter() - start) * 1000
                        self.metrics.observe_success(latency_ms)
                        agent.failed_count = 0
                        agent.last_heartbeat = datetime.utcnow()
                        agent.last_error = None

                        self.audit_logs.append(
                            {
                                "event": "agent_response",
                                "player_id": player_id,
                                "phase": phase,
                                "model_type": agent.model_type,
                                "latency_ms": round(latency_ms, 2),
                                "request": self._desensitize_payload(payload),
                                "response": self._desensitize_payload(data),
                                "ts": datetime.utcnow().isoformat(),
                            }
                        )
                        return data
                    except httpx.TimeoutException:
                        timeout_reason = f"timeout(retry={attempt})"
                        if attempt < self.max_timeout_retries:
                            await asyncio.sleep(self.retry_backoff_sec * (2 ** attempt))
                            continue
                        break

            self.metrics.observe_timeout()
            return self._handle_failure(agent, strategy_name, visible_state, timeout_reason or "timeout")
        except httpx.TimeoutException:
            self.metrics.observe_timeout()
            return self._handle_failure(agent, strategy_name, visible_state, "timeout")
        except Exception as exc:  # noqa: BLE001
            self.metrics.observe_error(type(exc).__name__)
            return self._handle_failure(agent, strategy_name, visible_state, type(exc).__name__)

    def _handle_failure(self, agent: AgentRegistration, strategy_name: str, context: dict, reason: str) -> dict:
        agent.failed_count += 1
        agent.last_error = reason
        if agent.failed_count >= 4:
            agent.online = False
            agent.entrusted = True
        return self._fallback_action(strategy_name, context, reason)

    def _fallback_action(self, strategy_name: str, context: dict, reason: str) -> dict:
        action = self.fallback.get_action(strategy_name, context)
        action["fallback_reason"] = reason
        self.audit_logs.append(
            {
                "event": "fallback_action",
                "strategy": strategy_name,
                "reason": reason,
                "response": self._desensitize_payload(action),
                "ts": datetime.utcnow().isoformat(),
            }
        )
        return action

    @staticmethod
    def _validate_and_parse(data: dict) -> dict:
        if not isinstance(data, dict):
            raise ValueError("invalid response format")
        action = data.get("action")
        if not isinstance(action, dict):
            raise ValueError("missing action")
        target = action.get("target")
        if target is not None and not isinstance(target, str):
            raise ValueError("action.target must be string or null")

        reasoning = data.get("reasoning", "")
        if isinstance(reasoning, str) and len(reasoning) > 300:
            data["reasoning"] = reasoning[:300]
        if isinstance(data.get("reasoning"), str):
            data["reasoning"] = AgentScheduler._sanitize_text(data["reasoning"])
        return data

    @staticmethod
    def _sanitize_text(text: str) -> str:
        banned = ["api_key", "password", "secret", "token"]
        cleaned = text
        for word in banned:
            cleaned = cleaned.replace(word, "***")
            cleaned = cleaned.replace(word.upper(), "***")
        return cleaned[:300]

    @staticmethod
    def _desensitize_payload(payload: dict) -> dict:
        def _mask(obj: object) -> object:
            if isinstance(obj, dict):
                masked: dict = {}
                for key, value in obj.items():
                    key_str = str(key).lower()
                    if key_str in {"api_key", "password", "secret", "token"}:
                        masked[key] = "***"
                    else:
                        masked[key] = _mask(value)
                return masked
            if isinstance(obj, list):
                return [_mask(item) for item in obj]
            return obj

        cleaned = _mask(payload)
        text = str(cleaned)
        if len(text) > 1000:
            return {"truncated": text[:1000] + "..."}
        if isinstance(cleaned, dict):
            return cleaned
        return {"value": text[:1000]}
