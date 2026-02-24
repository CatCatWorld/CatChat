from __future__ import annotations

import asyncio
import uuid
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from threading import RLock
from typing import Any, Awaitable, Callable, Dict, Optional

import httpx

from app.agent.ai_god_orchestrator import AIGodOrchestrator, GodAgentConfig
from app.agent.child_process_manager import ChildAgentProcessManager
from app.agent.god_orchestrator import GodOrchestrator
from app.config.frontend_profile_env import load_frontend_profile
from app.core.game_config import default_game_config
from app.engine.game_engine import GameEngine
from app.storage.repository import SQLiteRepository

from typing import Union


logger = logging.getLogger("uvicorn.error")


@dataclass(slots=True)
class Room:
    room_id: str
    engine: GameEngine
    orchestrator: Union[GodOrchestrator, AIGodOrchestrator]
    sockets: Dict[str, object] = field(default_factory=dict)
    ai_god_enabled: bool = False


class RoomManager:
    def __init__(self, repository: Optional[SQLiteRepository] = None) -> None:
        self._rooms: Dict[str, Room] = {}
        self._lock = RLock()
        self.repository = repository or SQLiteRepository("./backend/data/werewolf.db")
        self.child_agents = ChildAgentProcessManager()

    def shutdown_cleanup(self) -> None:
        self.child_agents.stop_all()
        with self._lock:
            self._rooms.clear()

    def create_room(
        self,
        owner_nickname: str,
        player_count: int = 12,
        custom_role_config: Optional[dict] = None,
        admin_override: bool = False,
    ) -> dict:
        with self._lock:
            room_id = self._new_room_id()
            owner_id = self._new_player_id()
            config = default_game_config(
                player_count=player_count,
                custom_role_config=custom_role_config,
                admin_override=admin_override,
            )
            engine = GameEngine(room_id=room_id, owner_id=owner_id, config=config)
            engine.add_player(owner_id, owner_nickname)
            room = Room(room_id=room_id, engine=engine, orchestrator=GodOrchestrator())
            self._rooms[room_id] = room
            return {
                "room_id": room_id,
                "owner_id": owner_id,
                "player_count": config.player_count,
                "role_distribution": config.role_distribution,
            }

    def bootstrap_from_frontend_env(self) -> dict:
        profile = load_frontend_profile()
        cats = profile.get("cats") if isinstance(profile, dict) else []
        monitor_cfg = profile.get("monitor_config") if isinstance(profile, dict) else {}

        if not isinstance(cats, list) or len(cats) < 8:
            raise ValueError("frontend env cats not ready: need at least 8 cats")
        if len(cats) > 12:
            raise ValueError("frontend env cats too many: max 12")
        if not isinstance(monitor_cfg, dict):
            monitor_cfg = {}

        ai_god = bool(monitor_cfg.get("aiGod"))
        god_cat_id = str(monitor_cfg.get("godCatId") or "").strip()
        selected_god_cat: Optional[dict] = None
        if ai_god:
            if god_cat_id:
                selected_god_cat = next(
                    (cat for cat in cats if isinstance(cat, dict) and str(cat.get("id") or "").strip() == god_cat_id),
                    None,
                )
            if selected_god_cat is None and cats:
                selected_god_cat = cats[0]

        participant_cats: list[dict] = []
        judge_cat_id = str((selected_god_cat or {}).get("id") or "").strip()
        for cat in cats:
            if not isinstance(cat, dict):
                continue
            if ai_god and judge_cat_id and str(cat.get("id") or "").strip() == judge_cat_id:
                continue
            participant_cats.append(cat)

        owner_name = str(((participant_cats[0] if participant_cats else (cats[0] if cats else {})) or {}).get("name") or "cat_01")
        player_count = len(participant_cats)

        if ai_god and player_count < 8:
            raise ValueError("启用AI法官时，除法官外至少需要 8 只参赛猫猫（当前不足）")

        stale_room_ids: list[str] = []
        with self._lock:
            active_started = any(
                r.engine.snapshot.started and not r.engine.snapshot.game_over
                for r in self._rooms.values()
            )
            if active_started:
                raise ValueError("游戏已开始，不能再切换/设定 AI 法官模式；请在开局前设置")

            for existing in self._rooms.values():
                existing_players = list(existing.engine.snapshot.players.values())
                if (
                    not existing.engine.snapshot.started
                    and not existing.engine.snapshot.game_over
                    and len(existing_players) == player_count
                    and existing.ai_god_enabled == ai_god
                    and not ai_god
                ):
                    logger.info(
                        "[BootstrapEnv] reuse existing room room_id=%s players=%s ai_god=%s",
                        existing.room_id,
                        len(existing_players),
                        existing.ai_god_enabled,
                    )
                    return {
                        "room_id": existing.room_id,
                        "owner_id": existing.engine.snapshot.owner_id,
                        "players": [p.player_id for p in existing_players],
                        "player_count": len(existing_players),
                        "ai_god": existing.ai_god_enabled,
                        "bootstrap": {
                            "reused": True,
                            "reason": "existing_unstarted_room",
                        },
                        "source": "existing_room",
                    }

            stale_room_ids = [room_id for room_id in self._rooms.keys()]
            self._rooms.clear()

        for room_id in stale_room_ids:
            self.child_agents.stop_room(room_id)

        selected_provider = str((selected_god_cat or {}).get("provider") or "").strip().lower()
        god_api_url = (
            (selected_god_cat or {}).get("apiUrl")
            or monitor_cfg.get("modelApiUrl")
            or monitor_cfg.get("godApiUrl")
        )
        god_api_key = (
            (selected_god_cat or {}).get("apiKey")
            or monitor_cfg.get("modelApiKey")
            or monitor_cfg.get("godApiKey")
        )
        god_model_name = (
            (selected_god_cat or {}).get("model")
            or monitor_cfg.get("modelName")
            or monitor_cfg.get("godModelName")
        )
        god_provider = "claude" if selected_provider == "claude" else "openai"
        god_temperature = monitor_cfg.get("godTemperature")

        if ai_god:
            if selected_god_cat is None:
                raise ValueError("AI法官模式已启用，但未找到可用的法官猫猫")
            if not god_api_url or not god_api_key:
                raise ValueError(
                    "AI法官配置不完整：所选法官猫猫缺少 API URL 或 API Key，"
                    "请先完善该猫猫模型配置后再启动"
                )

        room = self.create_ai_room(
            owner_nickname=owner_name,
            player_count=player_count,
            ai_god=ai_god,
            god_api_url=god_api_url,
            god_api_key=god_api_key,
            god_model_name=god_model_name,
            god_provider=god_provider,
            god_temperature=god_temperature,
        )

        room_id = room["room_id"]
        host_raw = str(monitor_cfg.get("agentHost") or "http://127.0.0.1")
        host = host_raw.replace("https://", "").replace("http://", "")
        start_port = int(monitor_cfg.get("agentStartPort") or 9101)

        bootstrap = self.bootstrap_agents(
            room_id=room_id,
            host=host,
            start_port=start_port,
            startup_timeout_sec=20,
            model_type="cat-agent",
            timeout_sec=45,
            api_url=monitor_cfg.get("modelApiUrl") or None,
            api_key=monitor_cfg.get("modelApiKey") or None,
            model_name=monitor_cfg.get("modelName") or None,
            cli_command=monitor_cfg.get("cliCommand") or None,
            cli_timeout_sec=45,
            cat_configs=participant_cats,
        )

        return {
            "room_id": room_id,
            "owner_id": room.get("owner_id") or "cat_01",
            "players": room.get("players") or [],
            "player_count": player_count,
            "ai_god": room.get("ai_god", False),
            "god_cat_id": judge_cat_id,
            "god_cat_name": str((selected_god_cat or {}).get("name") or ""),
            "bootstrap": bootstrap,
            "source": "frontend_env",
        }

    def create_ai_room(
        self,
        owner_nickname: str = "cat_01",
        player_count: int = 12,
        custom_role_config: Optional[dict] = None,
        admin_override: bool = False,
        ai_god: bool = False,
        god_api_url: Optional[str] = None,
        god_api_key: Optional[str] = None,
        god_model_name: Optional[str] = None,
        god_provider: Optional[str] = None,
        god_temperature: Optional[float] = None,
    ) -> dict:
        with self._lock:
            if ai_god and (not god_api_url or not god_api_key):
                raise ValueError("ai_god enabled but missing god_api_url/god_api_key")

            room_id = self._new_room_id()
            owner_id = "cat_01"
            config = default_game_config(
                player_count=player_count,
                custom_role_config=custom_role_config,
                admin_override=admin_override,
            )
            engine = GameEngine(room_id=room_id, owner_id=owner_id, config=config)

            if ai_god:
                god_cfg = GodAgentConfig(
                    api_url=god_api_url,
                    api_key=god_api_key,
                    model_name=god_model_name or "gpt-4o-mini",
                    provider=god_provider or "openai",
                    temperature=god_temperature if god_temperature is not None else 0.7,
                )
                orchestrator: Union[GodOrchestrator, AIGodOrchestrator] = AIGodOrchestrator(god_config=god_cfg)
            else:
                orchestrator = GodOrchestrator()

            room = Room(
                room_id=room_id,
                engine=engine,
                orchestrator=orchestrator,
                ai_god_enabled=bool(ai_god),
            )
            self._rooms[room_id] = room

            for idx in range(1, config.total_players + 1):
                pid = f"cat_{idx:02d}"
                nickname = owner_nickname if idx == 1 else pid
                engine.add_player(pid, nickname)

            return {
                "room_id": room_id,
                "owner_id": owner_id,
                "player_count": config.player_count,
                "role_distribution": config.role_distribution,
                "players": [p.player_id for p in engine.snapshot.players.values()],
                "ai_god": room.ai_god_enabled,
            }

    def join_room(self, room_id: str, nickname: str) -> dict:
        room = self.get_room(room_id)
        if not room:
            raise ValueError("room not found")

        player_id = self._new_player_id()
        room.engine.add_player(player_id, nickname)
        return {"room_id": room_id, "player_id": player_id}

    def start_game(self, room_id: str, owner_id: str) -> None:
        room = self.must_get_room(room_id)
        room.engine.start_game(owner_id)

    def register_agent(
        self,
        room_id: str,
        player_id: str,
        nickname: Optional[str],
        ipc_endpoint: str,
        model_type: str,
        timeout_sec: int,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        cli_command: Optional[str] = None,
        cli_timeout_sec: int = 20,
        preflight_check: bool = False,
        skip_endpoint_check: bool = False,
    ) -> dict:
        room = self.must_get_room(room_id)
        if player_id not in room.engine.snapshot.players:
            raise ValueError("player not found")
        if not skip_endpoint_check:
            self._assert_agent_endpoint(ipc_endpoint)
        if preflight_check:
            self._assert_agent_model_access(
                ipc_endpoint=ipc_endpoint,
                player_id=player_id,
                api_url=api_url,
                api_key=api_key,
                model_name=model_name,
                cli_command=cli_command,
                cli_timeout_sec=cli_timeout_sec,
            )
        if isinstance(nickname, str) and nickname.strip():
            room.engine.snapshot.players[player_id].nickname = nickname.strip()
        reg = room.orchestrator.scheduler.registry.register(
            player_id=player_id,
            ipc_endpoint=ipc_endpoint,
            model_type=model_type,
            timeout_sec=timeout_sec,
            api_url=api_url,
            api_key=api_key,
            model_name=model_name,
            cli_command=cli_command,
            cli_timeout_sec=cli_timeout_sec,
        )
        invoke_mode = (
            "cli"
            if reg.cli_command
            else ("api" if reg.api_url and reg.api_key else "mock")
        )
        return {
            "player_id": reg.player_id,
            "ipc_endpoint": reg.ipc_endpoint,
            "model_type": reg.model_type,
            "timeout_sec": reg.timeout_sec,
            "model_name": reg.model_name,
            "invoke_mode": invoke_mode,
            "online": reg.online,
        }

    def hot_swap_agent(
        self,
        room_id: str,
        player_id: str,
        ipc_endpoint: str,
        model_type: str,
        timeout_sec: int,
        api_url: Optional[str],
        api_key: Optional[str],
        model_name: Optional[str],
        cli_command: Optional[str],
        cli_timeout_sec: int,
        preflight_check: bool,
        reset_role_runtime_state: bool,
    ) -> dict:
        room = self.must_get_room(room_id)
        player = room.engine.snapshot.players.get(player_id)
        if not player:
            raise ValueError("player not found")
        self._assert_agent_endpoint(ipc_endpoint)
        if preflight_check:
            self._assert_agent_model_access(
                ipc_endpoint=ipc_endpoint,
                player_id=player_id,
                api_url=api_url,
                api_key=api_key,
                model_name=model_name,
                cli_command=cli_command,
                cli_timeout_sec=cli_timeout_sec,
            )

        reg = room.orchestrator.scheduler.registry.register(
            player_id=player_id,
            ipc_endpoint=ipc_endpoint,
            model_type=model_type,
            timeout_sec=timeout_sec,
            api_url=api_url,
            api_key=api_key,
            model_name=model_name,
            cli_command=cli_command,
            cli_timeout_sec=cli_timeout_sec,
        )
        player.online = True
        player.entrusted = False
        if reset_role_runtime_state:
            player.can_hunter_shoot = False

        invoke_mode = (
            "cli"
            if reg.cli_command
            else ("api" if reg.api_url and reg.api_key else "mock")
        )

        return {
            "player_id": reg.player_id,
            "ipc_endpoint": reg.ipc_endpoint,
            "model_type": reg.model_type,
            "timeout_sec": reg.timeout_sec,
            "model_name": reg.model_name,
            "invoke_mode": invoke_mode,
            "online": reg.online,
            "reset_role_runtime_state": reset_role_runtime_state,
        }

    def bootstrap_agents(
        self,
        room_id: str,
        host: str,
        start_port: int,
        startup_timeout_sec: float,
        model_type: str,
        timeout_sec: int,
        api_url: Optional[str],
        api_key: Optional[str],
        model_name: Optional[str],
        cli_command: Optional[str],
        cli_timeout_sec: int,
        cat_configs: Optional[list[dict]] = None,
    ) -> dict:
        room = self.must_get_room(room_id)
        players = list(room.engine.snapshot.players.values())
        player_ids = [p.player_id for p in players]

        existing_child_processes = self.child_agents.status(room_id)
        reusable = len(existing_child_processes) == len(player_ids) and len(player_ids) > 0
        if reusable:
            existing_endpoints: Dict[str, str] = {}
            reused_agents: Dict[str, Any] = {}
            for player_id in player_ids:
                proc_info = existing_child_processes.get(player_id) or {}
                endpoint = str(proc_info.get("endpoint") or "").rstrip("/")
                running = bool(proc_info.get("running"))
                reg = room.orchestrator.scheduler.registry.get(player_id)
                reg_endpoint = (reg.ipc_endpoint if reg else "").rstrip("/")
                if not (running and endpoint and reg and reg.online and reg_endpoint == endpoint):
                    reusable = False
                    break
                existing_endpoints[player_id] = endpoint
                invoke_mode = (
                    "cli"
                    if reg.cli_command
                    else ("api" if reg.api_url and reg.api_key else "mock")
                )
                reused_agents[player_id] = {
                    "player_id": reg.player_id,
                    "ipc_endpoint": reg.ipc_endpoint,
                    "model_type": reg.model_type,
                    "timeout_sec": reg.timeout_sec,
                    "model_name": reg.model_name,
                    "invoke_mode": invoke_mode,
                    "online": reg.online,
                    "attempts": 1,
                    "retries": 0,
                    "last_retry_error": "",
                    "reused": True,
                }

            if reusable:
                logger.info(
                    "[BootstrapAgents] mode=reused room_id=%s players=%s",
                    room_id,
                    len(reused_agents),
                )
                return {
                    "room_id": room_id,
                    "bootstrap_defaults": {
                        "model_type": model_type,
                        "timeout_sec": timeout_sec,
                        "api_url": bool(api_url),
                        "api_key": bool(api_key),
                        "model_name": model_name,
                        "cli_command": bool(cli_command),
                        "cli_timeout_sec": cli_timeout_sec,
                    },
                    "startup_mode": "reused",
                    "endpoints": existing_endpoints,
                    "registered_agents": {
                        "count": len(reused_agents),
                        "mode": "reused",
                        "retries_total": 0,
                        "retried_agents": 0,
                        "agents": reused_agents,
                    },
                    "child_processes": existing_child_processes,
                }

        endpoints = self.child_agents.bootstrap_room(
            room_id=room_id,
            player_ids=player_ids,
            host=host,
            start_port=start_port,
            startup_timeout_sec=startup_timeout_sec,
        )
        registration = self._register_bootstrap_agents_with_retry(
            room_id=room_id,
            player_ids=player_ids,
            endpoints=endpoints,
            model_type=model_type,
            timeout_sec=timeout_sec,
            api_url=api_url,
            api_key=api_key,
            model_name=model_name,
            cli_command=cli_command,
            cli_timeout_sec=cli_timeout_sec,
            cat_configs=cat_configs,
        )

        logger.info(
            "[BootstrapAgents] mode=parallel room_id=%s players=%s retries_total=%s retried_agents=%s",
            room_id,
            len(player_ids),
            registration.get("retries_total", 0),
            registration.get("retried_agents", 0),
        )

        return {
            "room_id": room_id,
            "bootstrap_defaults": {
                "model_type": model_type,
                "timeout_sec": timeout_sec,
                "api_url": bool(api_url),
                "api_key": bool(api_key),
                "model_name": model_name,
                "cli_command": bool(cli_command),
                "cli_timeout_sec": cli_timeout_sec,
            },
            "startup_mode": "parallel",
            "endpoints": endpoints,
            "registered_agents": registration,
            "child_processes": self.child_agents.status(room_id),
        }

    def _register_bootstrap_agents_with_retry(
        self,
        *,
        room_id: str,
        player_ids: list[str],
        endpoints: Dict[str, str],
        model_type: str,
        timeout_sec: int,
        api_url: Optional[str],
        api_key: Optional[str],
        model_name: Optional[str],
        cli_command: Optional[str],
        cli_timeout_sec: int,
        cat_configs: Optional[list[dict]] = None,
    ) -> Dict[str, Any]:
        room = self.must_get_room(room_id)
        cats = cat_configs if isinstance(cat_configs, list) else []
        if not cats:
            profile = load_frontend_profile()
            cats = profile.get("cats") if isinstance(profile, dict) else []
            if not isinstance(cats, list):
                cats = []
            monitor_cfg = profile.get("monitor_config") if isinstance(profile, dict) else {}
            if not isinstance(monitor_cfg, dict):
                monitor_cfg = {}
            if bool(monitor_cfg.get("aiGod")):
                god_cat_id = str(monitor_cfg.get("godCatId") or "").strip()
                if god_cat_id:
                    cats = [
                        cat
                        for cat in cats
                        if not (isinstance(cat, dict) and str(cat.get("id") or "").strip() == god_cat_id)
                    ]

        player_configs: list[dict] = []
        for idx, player_id in enumerate(player_ids):
            endpoint = endpoints.get(player_id)
            if not endpoint:
                raise ValueError(f"bootstrap endpoint missing for player: {player_id}")

            cat_cfg = cats[idx] if idx < len(cats) and isinstance(cats[idx], dict) else {}
            player_configs.append(
                {
                    "player_id": player_id,
                    "endpoint": endpoint,
                    "nickname": str(cat_cfg.get("name") or room.engine.snapshot.players[player_id].nickname),
                    "model_type": str(cat_cfg.get("provider") or model_type),
                    "api_url": cat_cfg.get("apiUrl") or api_url,
                    "api_key": cat_cfg.get("apiKey") or api_key,
                    "model_name": cat_cfg.get("model") or model_name,
                }
            )

        def _register_one(cfg: dict) -> dict:
            player_id_local = cfg["player_id"]
            attempt_local = 0
            last_error_local = ""
            while True:
                attempt_local += 1
                try:
                    reg_local = self.register_agent(
                        room_id=room_id,
                        player_id=player_id_local,
                        nickname=cfg["nickname"],
                        ipc_endpoint=cfg["endpoint"],
                        model_type=cfg["model_type"],
                        timeout_sec=timeout_sec,
                        api_url=cfg["api_url"],
                        api_key=cfg["api_key"],
                        model_name=cfg["model_name"],
                        cli_command=cli_command,
                        cli_timeout_sec=cli_timeout_sec,
                        preflight_check=False,
                        skip_endpoint_check=True,
                    )
                    reg_local["attempts"] = attempt_local
                    reg_local["retries"] = max(0, attempt_local - 1)
                    reg_local["last_retry_error"] = last_error_local
                    return reg_local
                except Exception as exc:  # noqa: BLE001
                    last_error_local = str(exc)
                    time.sleep(retry_interval_sec)

        registered: Dict[str, Any] = {}
        retry_interval_sec = 1.5
        retries_total = 0
        retried_agents = 0

        max_workers = max(1, len(player_configs))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_map = {
                executor.submit(_register_one, cfg): cfg["player_id"]
                for cfg in player_configs
            }
            for future in as_completed(future_map):
                player_id = future_map[future]
                reg = future.result()
                registered[player_id] = reg
                retries_total += int(reg.get("retries") or 0)
                if int(reg.get("attempts") or 1) > 1:
                    retried_agents += 1

        return {
            "count": len(registered),
            "mode": "parallel",
            "retries_total": retries_total,
            "retried_agents": retried_agents,
            "agents": registered,
        }

    def teardown_agents(self, room_id: str) -> dict:
        self.child_agents.stop_room(room_id)
        return {"room_id": room_id, "stopped": True}

    def child_process_status(self, room_id: str) -> dict:
        self.must_get_room(room_id)
        return {
            "room_id": room_id,
            "child_processes": self.child_agents.status(room_id),
        }

    @staticmethod
    def _assert_agent_endpoint(ipc_endpoint: str) -> None:
        base = (ipc_endpoint or "").strip().rstrip("/")
        if not base:
            raise ValueError("ipc_endpoint is required")
        health_url = base + "/health"
        deadline = time.time() + 8.0
        last_error = "unknown"
        while time.time() < deadline:
            try:
                with httpx.Client(timeout=2.5) as client:
                    resp = client.get(health_url)
                if resp.status_code < 400:
                    return
                last_error = f"HTTP {resp.status_code}"
            except Exception as exc:  # noqa: BLE001
                last_error = type(exc).__name__
            time.sleep(0.25)

        if str(last_error).startswith("HTTP"):
            raise ValueError(f"agent endpoint unhealthy: {health_url} -> {last_error}")
        raise ValueError(f"agent endpoint unreachable: {health_url} ({last_error})")

    @staticmethod
    def _assert_agent_model_access(
        *,
        ipc_endpoint: str,
        player_id: str,
        api_url: Optional[str],
        api_key: Optional[str],
        model_name: Optional[str],
        cli_command: Optional[str],
        cli_timeout_sec: int,
    ) -> None:
        if not (cli_command or (api_url and api_key)):
            return

        url = (ipc_endpoint or "").strip().rstrip("/") + "/act"
        payload = {
            "session_id": "bootstrap-preflight",
            "player_id": player_id,
            "role": "villager",
            "phase": "day_discuss",
            "visible_state": {
                "player_id": player_id,
                "player_name": "probe",
                "alive_players": ["probe", "test_target"],
                "alive_player_ids": [player_id, "test_target"],
            },
            "prompt_template": "返回JSON action+reasoning",
            "agent_config": {
                "api_url": api_url,
                "api_key": api_key,
                "model_name": model_name,
                "cli_command": cli_command,
                "cli_timeout_sec": cli_timeout_sec,
            },
        }
        timeout = httpx.Timeout(connect=5.0, read=45.0, write=10.0, pool=5.0)

        def _once() -> None:
            with httpx.Client(timeout=timeout) as client:
                resp = client.post(url, json=payload)
            if resp.status_code >= 400:
                detail = ""
                try:
                    data = resp.json() if resp.content else {}
                    detail = str((data or {}).get("detail") or "")
                except Exception:  # noqa: BLE001
                    detail = resp.text[:200] if resp.text else ""
                msg = f"agent preflight http={resp.status_code}"
                if detail:
                    msg += f" detail={detail}"
                raise ValueError(msg)

            data = resp.json() if resp.content else {}
            reasoning = str((data or {}).get("reasoning") or "")
            if reasoning.startswith("[api-error:"):
                raise ValueError("model api preflight failed: " + reasoning)
            if reasoning.startswith("[cli-error:"):
                raise ValueError("cli preflight failed: " + reasoning)

        try:
            _once()
        except httpx.ReadTimeout:
            _once()
        except ValueError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise ValueError(f"agent preflight unreachable: {type(exc).__name__}") from exc

    async def ai_run_single_phase(
        self,
        room_id: str,
        progress_callback: Optional[Callable[[dict], Awaitable[None]]] = None,
    ) -> dict:
        room = self.must_get_room(room_id)
        engine = room.engine
        original_audit = engine._audit

        def _audit_and_stream(event_type: str, actor_id: str, payload: dict) -> None:
            original_audit(event_type, actor_id, payload)
            if not progress_callback:
                return
            if event_type not in {"agent_speech", "god_narration", "phase_change", "vote_result", "death"}:
                return
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(progress_callback(engine.public_state()))
            except RuntimeError:
                return

        engine._audit = _audit_and_stream
        try:
            await room.orchestrator.run_single_phase(engine)
        finally:
            engine._audit = original_audit

        self.remove_room_if_game_over(room_id)
        return {
            "state": engine.public_state(),
            "metrics": room.orchestrator.scheduler.metrics.to_dict(),
        }

    async def ai_run_to_end(self, room_id: str, max_steps: int = 500) -> dict:
        room = self.must_get_room(room_id)
        result = await room.orchestrator.run_to_game_over(room.engine, max_steps=max_steps)
        self.remove_room_if_game_over(room_id)
        return {
            "result": result,
            "state": room.engine.public_state(),
            "metrics": room.orchestrator.scheduler.metrics.to_dict(),
        }

    def ai_health(self, room_id: str) -> dict:
        room = self.must_get_room(room_id)
        agents = room.orchestrator.scheduler.registry.all()
        result = {
            "all_ready": room.orchestrator.all_agents_ready(room.engine),
            "agents": {
                pid: {
                    "online": agent.online,
                    "entrusted": agent.entrusted,
                    "model_type": agent.model_type,
                    "model_name": agent.model_name,
                    "timeout_sec": agent.timeout_sec,
                    "failed_count": agent.failed_count,
                }
                for pid, agent in agents.items()
            },
            "metrics": room.orchestrator.scheduler.metrics.to_dict(),
            "ai_god": room.ai_god_enabled,
        }
        if room.ai_god_enabled and isinstance(room.orchestrator, AIGodOrchestrator):
            result["god_narration_count"] = len(room.orchestrator.narration_log)
        return result

    def agents_status(self, room_id: str) -> dict:
        room = self.must_get_room(room_id)
        agents = room.orchestrator.scheduler.registry.all()
        return {
            "room_id": room_id,
            "agents": {
                pid: {
                    "online": agent.online,
                    "entrusted": agent.entrusted,
                    "model_type": agent.model_type,
                    "model_name": agent.model_name,
                    "invoke_mode": (
                        "cli"
                        if agent.cli_command
                        else ("api" if agent.api_url and agent.api_key else "mock")
                    ),
                    "timeout_sec": agent.timeout_sec,
                    "failed_count": agent.failed_count,
                    "last_heartbeat": agent.last_heartbeat.isoformat(),
                    "error_msg": agent.last_error,
                }
                for pid, agent in agents.items()
            },
            "metrics": room.orchestrator.scheduler.metrics.to_dict(),
        }

    def room_config(self, room_id: str) -> dict:
        room = self.must_get_room(room_id)
        config = room.engine.config
        return {
            "room_id": room_id,
            "player_count": config.player_count,
            "role_distribution": config.role_distribution,
            "night_order": config.night_order,
            "warnings": config.warnings,
        }

    def health_summary(self) -> dict:
        with self._lock:
            rooms = list(self._rooms.values())

        total_agents = 0
        online_agents = 0
        per_room: dict[str, dict] = {}
        for room in rooms:
            regs = room.orchestrator.scheduler.registry.all()
            total_agents += len(regs)
            online = sum(1 for reg in regs.values() if reg.online)
            online_agents += online
            per_room[room.room_id] = {
                "players": len(room.engine.snapshot.players),
                "agents_registered": len(regs),
                "agents_online": online,
                "phase": room.engine.snapshot.phase.value,
                "game_over": room.engine.snapshot.game_over,
            }

        return {
            "rooms": len(rooms),
            "agents_total": total_agents,
            "agents_online": online_agents,
            "rooms_detail": per_room,
        }

    def replay_record(self, record_id: int) -> dict:
        record = self.repository.get_game_record(record_id)
        if not record:
            raise ValueError("record not found")
        return record

    def get_room(self, room_id: str) -> Optional[Room]:
        with self._lock:
            return self._rooms.get(room_id)

    def must_get_room(self, room_id: str) -> Room:
        room = self.get_room(room_id)
        if not room:
            raise ValueError("room not found")
        return room

    def state(self, room_id: str) -> dict:
        room = self.must_get_room(room_id)
        return room.engine.public_state()

    def remove_room_if_game_over(self, room_id: str) -> None:
        with self._lock:
            room = self._rooms.get(room_id)
            if not room:
                return
            if room.engine.snapshot.game_over:
                self.child_agents.stop_room(room_id)
                snapshot = room.engine.snapshot
                self.repository.save_finished_game(
                    room_id=snapshot.room_id,
                    winner=snapshot.winner.value if snapshot.winner else "unknown",
                    rounds=snapshot.round_context.round_no,
                    payload={
                        "audit": snapshot.action_audit_log,
                        "agent_audit": room.orchestrator.scheduler.audit_logs,
                        "metrics": room.orchestrator.scheduler.metrics.to_dict(),
                        "players": [
                            {
                                "player_id": p.player_id,
                                "nickname": p.nickname,
                                "role": p.role.value if p.role else None,
                                "alive": p.alive,
                            }
                            for p in snapshot.players.values()
                        ],
                    },
                )

    @staticmethod
    def _new_room_id() -> str:
        return uuid.uuid4().hex[:8]

    @staticmethod
    def _new_player_id() -> str:
        return uuid.uuid4().hex
