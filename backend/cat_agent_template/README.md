# Cat Agent Template

这是猫猫子Agent参考实现（独立进程）。

## 启动

```bash
pip install -r requirements.txt
uvicorn main:app --host 127.0.0.1 --port 9001
```

可通过环境变量配置模型标识：

```bash
MODEL_TYPE=qwen-max uvicorn main:app --host 127.0.0.1 --port 9001
```

## 调用模式说明

- 默认：API 调用模式（由后端在注册 Agent 时透传 `api_url/api_key/model_name`）
- 可选：CLI 调用模式（仅在透传 `cli_command` 时启用）

也就是说，CLI 不是全局开关，而是每个 Agent 的可选参数。

### 期望的 CLI I/O 协议

- stdin：一段 JSON，字段包含 `session_id/player_id/role/phase/visible_state/prompt_template/model_type`
- stdout：一段 JSON，至少包含：

```json
{
  "action": {"type": "vote", "target": "cat_03"},
  "reasoning": "..."
}
```

### CLI 模式参数（由后端透传）

- `cli_command`: 例如 `python cli_worker.py`
- `cli_timeout_sec`: 超时秒数（默认 20）

## 通信协议

- `POST /act`
  - 入参：`session_id/player_id/role/phase/visible_state/prompt_template/agent_config`
  - 出参：`action/reasoning/timestamp`

`agent_config` 关键字段：

- API 默认模式：`api_url/api_key/model_name`
- CLI 可选模式：`cli_command/cli_timeout_sec`

当 API 或 CLI 调用失败时，模板会自动回退到内置 mock 动作，避免整局阻塞。
