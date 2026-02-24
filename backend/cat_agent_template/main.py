from __future__ import annotations

import json
import logging
import os
import re
import subprocess
import time
from typing import Any, Dict

import httpx
from fastapi import FastAPI
from pydantic import BaseModel


class ActRequest(BaseModel):
    session_id: str
    player_id: str
    role: str
    phase: str
    visible_state: Dict[str, Any]
    prompt_template: str
    agent_config: Dict[str, Any] = {}


class ActResponse(BaseModel):
    action: Dict[str, Any]
    reasoning: str = ""
    speech: str = ""
    thinking: str = ""
    timestamp: int


app = FastAPI(title="Cat Agent Template", version="0.1.0")
logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.INFO)

MODEL_TYPE = os.getenv("MODEL_TYPE", "cat-agent")
DEFAULT_API_TIMEOUT_SEC = int(os.getenv("CAT_AGENT_API_TIMEOUT", "30"))
LLM_LOG_MAX_CHARS = max(100, int(os.getenv("CAT_LLM_LOG_MAX_CHARS", "1024")))


def _clip_text(text: str, limit: int = LLM_LOG_MAX_CHARS) -> str:
    if text is None:
        return ""
    if len(text) <= limit:
        return text
    return text[:limit] + f" ...[truncated {len(text) - limit} chars]"


def _mock_action(req: ActRequest) -> Dict[str, Any]:
    alive = req.visible_state.get("alive_players", [])
    me = req.player_id
    candidates = [pid for pid in alive if pid != me]

    target = candidates[0] if candidates else None
    action_type = "vote"

    if req.phase == "night_wolf":
        action_type = "kill"
    elif req.phase == "night_guard":
        action_type = "guard"
    elif req.phase == "night_witch":
        action_type = "save"
        wolf_target = req.visible_state.get("wolf_target")
        target = wolf_target
    elif req.phase == "night_seer":
        action_type = "check"
    elif req.phase == "hunter_shot":
        action_type = "shoot"
    elif req.phase == "day_discuss":
        action_type = "speak"
        target = None

    return {
        "action": {
            "type": action_type,
            "target": target,
            "save": req.phase == "night_witch" and bool(target),
        },
        "reasoning": (
            f"[{MODEL_TYPE}] phase={req.phase} "
            f"role={req.role} target={target}"
        ),
    }


def _parse_json_from_text(text: str) -> Dict[str, Any]:
    raw = (text or "").strip()
    if not raw:
        raise RuntimeError("模型未返回文本")

    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            return parsed
    except Exception:  # noqa: BLE001
        pass

    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", raw, re.DOTALL)
    if fenced:
        parsed = json.loads(fenced.group(1))
        if isinstance(parsed, dict):
            return parsed

    brace = re.search(r"\{.*\}", raw, re.DOTALL)
    if brace:
        parsed = json.loads(brace.group(0))
        if isinstance(parsed, dict):
            return parsed

    raise RuntimeError("无法从模型输出解析JSON")


def _run_cli_action(req: ActRequest, cfg: Dict[str, Any]) -> Dict[str, Any]:
    cli_cmd = str(cfg.get("cli_command") or "").strip()
    if not cli_cmd:
        raise RuntimeError("cli_command 未传入")

    cli_timeout_sec = int(cfg.get("cli_timeout_sec") or 20)

    payload = {
        "session_id": req.session_id,
        "player_id": req.player_id,
        "role": req.role,
        "phase": req.phase,
        "visible_state": req.visible_state,
        "prompt_template": req.prompt_template,
        "model_type": MODEL_TYPE,
        "agent_config": cfg,
    }

    proc = subprocess.run(
        cli_cmd,
        input=json.dumps(payload, ensure_ascii=False),
        capture_output=True,
        text=True,
        timeout=cli_timeout_sec,
        shell=True,
        check=False,
    )

    if proc.returncode != 0:
        stderr = (proc.stderr or "").strip()
        raise RuntimeError(f"CLI 返回非0退出码: {proc.returncode}; {stderr}")

    raw = (proc.stdout or "").strip()
    if not raw:
        raise RuntimeError("CLI 未返回内容")

    data = json.loads(raw)
    if not isinstance(data, dict):
        raise RuntimeError("CLI 输出必须是 JSON 对象")
    if not isinstance(data.get("action"), dict):
        raise RuntimeError("CLI 输出缺少 action 对象")

    reasoning = data.get("reasoning", "")
    if not isinstance(reasoning, str):
        reasoning = str(reasoning)
    speech = data.get("speech", "")
    if not isinstance(speech, str):
        speech = str(speech)
    thinking = data.get("thinking", "")
    if not isinstance(thinking, str):
        thinking = str(thinking)

    return {
        "action": data["action"],
        "reasoning": reasoning,
        "speech": speech,
        "thinking": thinking,
    }


def _detect_provider(cfg: Dict[str, Any]) -> str:
    """Detect the API provider from agent_config fields."""
    provider = str(cfg.get("provider") or "").strip().lower()
    if provider:
        return provider
    api_url = str(cfg.get("api_url") or "").strip().lower()
    if "anthropic" in api_url:
        return "claude"
    if "siliconflow" in api_url:
        return "siliconflow"
    if "bigmodel.cn" in api_url:
        return "glm"
    return "openai"


def _build_prompt(req: ActRequest) -> str:
    return (
        "你是狼人杀子Agent。请只返回JSON，不要输出多余文本。"
        "格式: {\"action\": {\"type\": "
        "\"vote|kill|guard|save|check|shoot|speak\", "
        "\"target\": \"player_id或null\", \"save\": true或false}, "
        "\"reasoning\": \"简短说明\"}.\n"
        f"phase={req.phase}, role={req.role}.\n"
        f"rules_prompt={req.prompt_template}\n"
        f"visible_state={json.dumps(req.visible_state, ensure_ascii=False)}"
    )


def _call_openai_compatible(api_url: str, api_key: str, model_name: str,
                            prompt: str, timeout_sec: int) -> str:
    """Call OpenAI-compatible API (OpenAI / GLM / SiliconFlow)."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": "你是狼人杀策略决策助手。"},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.3,
        "max_tokens": 800,
    }
    with httpx.Client(timeout=timeout_sec) as client:
        resp = client.post(api_url, headers=headers, json=body)
    resp.raise_for_status()
    data = resp.json()
    choices = data.get("choices")
    if isinstance(choices, list) and choices:
        msg = choices[0].get("message") or {}
        return str(msg.get("content") or "")
    return ""


def _call_claude(api_url: str, api_key: str, model_name: str,
                 prompt: str, timeout_sec: int) -> str:
    """Call Anthropic Claude Messages API."""
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }
    body = {
        "model": model_name,
        "max_tokens": 800,
        "system": "你是狼人杀策略决策助手。",
        "messages": [
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.3,
    }
    with httpx.Client(timeout=timeout_sec) as client:
        resp = client.post(api_url, headers=headers, json=body)
    resp.raise_for_status()
    data = resp.json()
    content_blocks = data.get("content")
    if isinstance(content_blocks, list):
        texts = [b.get("text", "") for b in content_blocks if b.get("type") == "text"]
        return "\n".join(texts)
    return ""


def _run_api_action(req: ActRequest, cfg: Dict[str, Any]) -> Dict[str, Any]:
    api_url = str(cfg.get("api_url") or "").strip()
    api_key = str(cfg.get("api_key") or "").strip()
    model_name = str(cfg.get("model_name") or MODEL_TYPE).strip()
    timeout_sec = int(cfg.get("api_timeout_sec") or DEFAULT_API_TIMEOUT_SEC)

    if not api_url or not api_key:
        raise RuntimeError("api_url/api_key 未传入")

    provider = _detect_provider(cfg)
    prompt = _build_prompt(req)
    logger.info(
        "[LLM][request] provider=%s model=%s player=%s phase=%s prompt=%s",
        provider,
        model_name,
        req.player_id,
        req.phase,
        _clip_text(prompt),
    )
    retry_max = max(
        0,
        int(
            cfg.get("api_retry_max")
            or os.getenv("CAT_AGENT_API_RETRY_MAX", "2")
        ),
    )
    retry_backoff_sec = max(
        0.1,
        float(
            cfg.get("api_retry_backoff_sec")
            or os.getenv("CAT_AGENT_API_RETRY_BACKOFF_SEC", "0.8")
        ),
    )

    def _call_once() -> str:
        if provider == "claude":
            return _call_claude(api_url, api_key, model_name, prompt, timeout_sec)
        return _call_openai_compatible(api_url, api_key, model_name, prompt, timeout_sec)

    content = ""
    last_error: Exception | None = None
    for attempt in range(retry_max + 1):
        try:
            content = _call_once()
            last_error = None
            break
        except httpx.ReadTimeout as exc:
            last_error = RuntimeError(f"model api timeout (attempt={attempt + 1})")
            if attempt < retry_max:
                time.sleep(retry_backoff_sec * (2 ** attempt))
                continue
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code if exc.response is not None else 0
            transient = status in {429, 500, 502, 503, 504}
            last_error = RuntimeError(f"model api http={status} (attempt={attempt + 1})")
            if transient and attempt < retry_max:
                time.sleep(retry_backoff_sec * (2 ** attempt))
                continue
        except Exception as exc:  # noqa: BLE001
            last_error = exc
        break

    if last_error is not None:
        raise last_error

    logger.info(
        "[LLM][response] provider=%s model=%s player=%s phase=%s content=%s",
        provider,
        model_name,
        req.player_id,
        req.phase,
        _clip_text(content),
    )

    parsed = _parse_json_from_text(content)
    action = parsed.get("action")
    if not isinstance(action, dict):
        raise RuntimeError("模型输出缺少 action 对象")
    reasoning = parsed.get("reasoning", "")
    if not isinstance(reasoning, str):
        reasoning = str(reasoning)
    speech = parsed.get("speech", "")
    if not isinstance(speech, str):
        speech = str(speech)
    thinking = parsed.get("thinking", "")
    if not isinstance(thinking, str):
        thinking = str(thinking)

    return {
        "action": action,
        "reasoning": reasoning,
        "speech": speech,
        "thinking": thinking,
    }


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "model_type": MODEL_TYPE,
        "invoke_strategy": "api-default-cli-optional",
    }


@app.post("/act", response_model=ActResponse)
def act(req: ActRequest) -> ActResponse:
    cfg = req.agent_config or {}
    cli_command = str(cfg.get("cli_command") or "").strip()

    if cli_command:
        try:
            decision = _run_cli_action(req, cfg)
            action = decision["action"]
            raw_reasoning = str(decision.get("reasoning") or "").strip()
            reasoning = (f"[cli:{MODEL_TYPE}] {raw_reasoning}").strip() if raw_reasoning else ""
            speech = str(decision.get("speech") or "").strip()
            thinking = str(decision.get("thinking") or "").strip()
        except Exception as exc:  # noqa: BLE001
            fallback = _mock_action(req)
            action = fallback["action"]
            reasoning = (
                f"[cli-error:{MODEL_TYPE}] {exc}; "
                f"fallback={fallback.get('reasoning', '')}"
            )
            speech = ""
            thinking = ""
    else:
        try:
            decision = _run_api_action(req, cfg)
            action = decision["action"]
            raw_reasoning = str(decision.get("reasoning") or "").strip()
            reasoning = (f"[api:{MODEL_TYPE}] {raw_reasoning}").strip() if raw_reasoning else ""
            speech = str(decision.get("speech") or "").strip()
            thinking = str(decision.get("thinking") or "").strip()
        except Exception as exc:  # noqa: BLE001
            fallback = _mock_action(req)
            action = fallback["action"]
            reasoning = (
                f"[api-error:{MODEL_TYPE}] {exc}; "
                f"fallback={fallback.get('reasoning', '')}"
            )
            speech = ""
            thinking = ""

    return ActResponse(
        action=action,
        reasoning=reasoning,
        speech=speech,
        thinking=thinking,
        timestamp=int(time.time()),
    )
