from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class CreateRoomRequest(BaseModel):
    owner_nickname: str = Field(min_length=1, max_length=30)
    player_count: int = Field(default=12, ge=8, le=12)
    custom_role_config: Optional[Dict[str, Any]] = None
    admin_override: bool = False


class JoinRoomRequest(BaseModel):
    nickname: str = Field(min_length=1, max_length=30)


class ActionRequest(BaseModel):
    player_id: str
    target_id: Optional[str] = None
    save: Optional[bool] = None


class VoteRequest(BaseModel):
    player_id: str
    target_id: Optional[str] = None


class StartGameResponse(BaseModel):
    room_id: str
    phase: str


class RoomPlayerView(BaseModel):
    player_id: str
    nickname: str
    role: Optional[str] = None
    alive: bool
    online: bool
    can_vote: Optional[bool] = None
    fool_revealed: Optional[bool] = None


class RoomStateResponse(BaseModel):
    room_id: str
    owner_id: str
    started: bool
    phase: str
    players: List[RoomPlayerView]
    game_over: bool
    winner: Optional[str]
    game_metadata: Optional[Dict[str, Any]] = None
    round_no: Optional[int] = None


class GenericMessage(BaseModel):
    message: str


class CreateAIRoomRequest(BaseModel):
    owner_nickname: str = Field(default="cat_01", min_length=1, max_length=30)
    player_count: int = Field(default=12, ge=8, le=12)
    custom_role_config: Optional[Dict[str, Any]] = None
    admin_override: bool = False
    ai_god: bool = False
    god_api_url: Optional[str] = None
    god_api_key: Optional[str] = None
    god_model_name: Optional[str] = None
    god_provider: Optional[str] = None
    god_temperature: Optional[float] = None


class RegisterAgentRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    player_id: str
    nickname: Optional[str] = None
    ipc_endpoint: str
    model_type: str
    timeout_sec: int = Field(default=15, ge=3, le=60)
    api_url: Optional[str] = None
    api_key: Optional[str] = None
    model_name: Optional[str] = None
    cli_command: Optional[str] = None
    cli_timeout_sec: int = Field(default=20, ge=3, le=120)
    preflight_check: bool = False


class RegisterAgentGlobalRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    room_id: str
    player_id: str
    nickname: Optional[str] = None
    endpoint: str
    model: str
    timeout_sec: int = Field(default=15, ge=3, le=60)
    api_url: Optional[str] = None
    api_key: Optional[str] = None
    model_name: Optional[str] = None
    cli_command: Optional[str] = None
    cli_timeout_sec: int = Field(default=20, ge=3, le=120)
    preflight_check: bool = False


class HotSwapAgentRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    player_id: str
    ipc_endpoint: str
    model_type: str
    timeout_sec: int = Field(default=15, ge=3, le=60)
    api_url: Optional[str] = None
    api_key: Optional[str] = None
    model_name: Optional[str] = None
    cli_command: Optional[str] = None
    cli_timeout_sec: int = Field(default=20, ge=3, le=120)
    preflight_check: bool = False
    reset_role_runtime_state: bool = True


class BootstrapAgentsRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    host: str = "127.0.0.1"
    start_port: int = Field(default=9101, ge=1, le=65535)
    startup_timeout_sec: float = Field(default=12.0, ge=1.0, le=60.0)
    model_type: str = "cat-agent"
    timeout_sec: int = Field(default=15, ge=3, le=60)
    api_url: Optional[str] = None
    api_key: Optional[str] = None
    model_name: Optional[str] = None
    cli_command: Optional[str] = None
    cli_timeout_sec: int = Field(default=20, ge=3, le=120)


class RunToEndRequest(BaseModel):
    max_steps: int = Field(default=500, ge=1, le=5000)


class AIPhaseRunResponse(BaseModel):
    state: Dict[str, Any]
    metrics: Dict[str, Any]


class AIRunToEndResponse(BaseModel):
    result: Dict[str, Any]
    state: Dict[str, Any]
    metrics: Dict[str, Any]


class AIHealthResponse(BaseModel):
    all_ready: bool
    agents: Dict[str, Any]
    metrics: Dict[str, Any]


class AgentStatusResponse(BaseModel):
    room_id: str
    agents: Dict[str, Any]
    metrics: Dict[str, Any]


class RoomConfigResponse(BaseModel):
    room_id: str
    player_count: int
    role_distribution: Dict[str, int]
    night_order: List[str]
    warnings: List[str]


class ReplayResponse(BaseModel):
    record: Dict[str, Any]


class WSOutboundEvent(BaseModel):
    event: str
    payload: Dict[str, Any]


class FrontendProfileRequest(BaseModel):
    cats: List[Dict[str, Any]] = Field(default_factory=list)
    monitor_config: Dict[str, Any] = Field(default_factory=dict)


class FrontendProfileResponse(BaseModel):
    source: str
    cats: List[Dict[str, Any]]
    monitor_config: Dict[str, Any]
    saved_at: Optional[str] = None
