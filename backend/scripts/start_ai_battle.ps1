param(
    [string]$BackendBase = "http://127.0.0.1:8000",
    [int]$AgentStartPort = 9101,
    [ValidateRange(8, 12)]
    [int]$PlayerCount = 12
)

$ErrorActionPreference = "Stop"

Write-Host "[1/5] 启动$PlayerCount个猫猫子Agent..."
$modelPool = @("qwen-max", "glm-4", "deepseek-v3", "claude-haiku")

for ($i = 1; $i -le $PlayerCount; $i++) {
    $port = $AgentStartPort + $i - 1
    $model = $modelPool[($i - 1) % $modelPool.Count]
    Start-Process powershell -ArgumentList @(
        "-NoExit",
        "-Command",
        "cd '$PSScriptRoot\..\cat_agent_template'; `$env:MODEL_TYPE='$model'; uvicorn main:app --host 127.0.0.1 --port $port"
    ) | Out-Null
}

Write-Host "等待子Agent健康检查..."
$healthDeadline = (Get-Date).AddSeconds(30)
for ($i = 1; $i -le $PlayerCount; $i++) {
    $port = $AgentStartPort + $i - 1
    $url = "http://127.0.0.1:$port/health"
    $ready = $false
    while ((Get-Date) -lt $healthDeadline) {
        try {
            $resp = Invoke-WebRequest -Method Get -Uri $url -TimeoutSec 2
            if ($resp.StatusCode -lt 400) {
                $ready = $true
                break
            }
        } catch {
            Start-Sleep -Milliseconds 250
        }
    }
    if (-not $ready) {
        throw "子Agent健康检查超时: $url"
    }
}

Write-Host "[2/5] 创建AI房间..."
$roomResp = Invoke-RestMethod -Method Post -Uri "$BackendBase/api/ai/rooms" -ContentType "application/json" -Body (@{ owner_nickname = "cat_01"; player_count = $PlayerCount } | ConvertTo-Json)
$roomId = $roomResp.room_id
Write-Host "Room: $roomId"

Write-Host "[3/5] 注册$PlayerCount个猫猫Agent..."
for ($i = 1; $i -le $PlayerCount; $i++) {
    $player = "cat_{0:d2}" -f $i
    $port = $AgentStartPort + $i - 1
    $model = $modelPool[($i - 1) % $modelPool.Count]
    $body = @{ player_id = $player; ipc_endpoint = "http://127.0.0.1:$port"; model_type = $model; timeout_sec = 15 } | ConvertTo-Json
    Invoke-RestMethod -Method Post -Uri "$BackendBase/api/ai/rooms/$roomId/agents/register" -ContentType "application/json" -Body $body | Out-Null
}

Write-Host "[4/5] 开始游戏..."
Invoke-RestMethod -Method Post -Uri "$BackendBase/api/rooms/$roomId/start?owner_id=cat_01" | Out-Null

Write-Host "[5/5] 上帝Agent自动跑到结算..."
$runResult = Invoke-RestMethod -Method Post -Uri "$BackendBase/api/ai/rooms/$roomId/run-to-end" -ContentType "application/json" -Body (@{ max_steps = 500 } | ConvertTo-Json)
$winner = $runResult.state.winner
$roundNo = $runResult.state.round_no
Write-Host "✅ 游戏结束，胜者: $winner, 回合: $roundNo"
Write-Host "调度指标:"
$runResult.metrics | ConvertTo-Json -Depth 8 | Write-Host
