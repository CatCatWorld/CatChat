# CatChat

CatChat 是一个「前端可视化 + Python 后端裁判 + 多 AI 子 Agent」的狼人杀联动项目。

- 前端：`cat_chat.html` + `cat_chat_script.js`
- 本地代理：`cat_chat_cli.js`（解决浏览器 CORS）
- 后端：`backend/`（FastAPI + WebSocket + 规则引擎 + AI 调度）

后端详细设计与完整说明见：`backend/README.md`

## 功能概览

- 多猫聊天与多 Provider（OpenAI / Claude / GLM / 硅基流动）
- 狼人杀流程（8~12 人，规则引擎裁定）
- 监控模式（REST + WebSocket 实时状态/事件）
- AI 子 Agent 注册、热替换、健康检查、自动跑局
- 本地 CLI 代理转发大模型请求

## 仓库结构

```text
.
├─ cat_chat.html                 # 前端页面
├─ cat_chat_script.js            # 前端逻辑（聊天/狼人杀/监控）
├─ cat_chat_cli.js               # Node 本地代理
└─ backend/
	├─ run.py                     # 后端启动入口
	├─ app/
	│  ├─ main.py                 # FastAPI 应用 + /health + /ws
	│  ├─ api/rest.py             # REST API
	│  ├─ engine/                 # 状态机与规则引擎
	│  ├─ agent/                  # 上帝调度/视角过滤/fallback
	│  └─ websocket/handler.py    # WS 事件管理
	├─ scripts/
	│  ├─ start_ai_battle.ps1     # 一键启动 AI 对战
	│  └─ ws_monitor_smoke_test.py# 监控模式 WS 烟测
	└─ tests/                     # 后端测试
```

## 快速开始

### 1) 启动后端

```bash
cd backend
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run.py
```

默认地址：`http://127.0.0.1:8000`

- OpenAPI: `http://127.0.0.1:8000/docs`
- 健康检查: `GET /health`

### 2) 打开前端

直接用浏览器打开根目录的 `cat_chat.html`。

在「🛰️ 监控模式」中将后端地址设置为 `http://127.0.0.1:8000`，然后可执行：

- 创建 AI 房间
- 连接 WebSocket
- 注册 AI 猫猫
- 开始游戏 / 推进阶段

### 3) （可选）启动本地 CLI 代理

```bash
# 默认 3456
node cat_chat_cli.js

# 自定义端口
node cat_chat_cli.js --port 8080
```

前端启用「🖥️ 本地 CLI 代理」后，模型请求会通过 `POST /proxy` 转发。

## 关键接口（后端）

基础前缀：`/api`

- `POST /ai/rooms`：创建 AI 房间
- `POST /rooms/{room_id}/start?owner_id=...`：开局
- `POST /rooms/{room_id}/advance`：推进当前阶段
- `POST /ai/rooms/{room_id}/agents/register`：注册 Agent
- `POST /ai/rooms/{room_id}/agents/hot-swap`：热替换 Agent
- `GET /ai/rooms/{room_id}/agents/health`：AI 健康状态
- `POST /ai/rooms/{room_id}/run-phase`：AI 跑一个阶段
- `POST /ai/rooms/{room_id}/run-to-end`：AI 自动跑到结算
- `GET /replay/{record_id}`：读取复盘记录

WebSocket：`/ws/{room_id}/{player_id}`

常见事件：`subscribe`、`change_view`、`advance`，以及服务端推送 `room_state`、`phase_changed`、`agent_status_update`。

## 一键联调与烟测

### 一键 AI 对战（PowerShell）

```powershell
cd backend
./scripts/start_ai_battle.ps1
# 指定人数（8~12）
./scripts/start_ai_battle.ps1 -PlayerCount 8
```

### 监控模式 WS 烟测

```powershell
cd backend
python scripts/ws_monitor_smoke_test.py --base-url http://127.0.0.1:8000 --player-count 11
```

## 运行测试

```bash
cd backend
pytest -q
```

可选集成测试（需后端运行中）：

```powershell
cd backend
$env:RUN_MONITOR_INTEGRATION="1"
pytest -q -m integration
```

## 常用环境变量

- `CATCHAT_BACKEND_RELOAD=1`：启用 uvicorn 热重载（`run.py`）
- `CATCHAT_AUTO_BOOTSTRAP_ON_STARTUP=0`：关闭启动时自动从前端配置引导房间

更多后端规则、模块细节、复盘说明请查看 `backend/README.md`。

狼人杀效果图示：
<img width="200" height="11294" alt="AI_Agent狼人杀2" src="https://github.com/user-attachments/assets/9a584462-12a2-46b4-8a51-3535a1663396" />
