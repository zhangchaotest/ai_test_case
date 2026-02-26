#!/usr/bin/env powershell

# 启动前后端服务的脚本
# 作者: AI Assistant
# 日期: 2026-02-26

Write-Host "========================================" -ForegroundColor Green
Write-Host "        AI 测试用例生成平台启动脚本        " -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

# 切换到项目根目录
Set-Location "$PSScriptRoot"

# 定义服务端口
$backendPort = 8888
$frontendPort = 5173

# 检查并停止已运行的服务
Write-Host "检查服务运行状态..." -ForegroundColor Yellow

# 检查后端服务
try {
    $backendListener = [System.Net.Sockets.TcpListener]$backendPort
    $backendListener.Start()
    $backendListener.Stop()
    Write-Host "后端服务端口 $backendPort 可用" -ForegroundColor Green
} catch {
    Write-Host "后端服务端口 $backendPort 已被占用，正在停止..." -ForegroundColor Yellow
    # 查找并停止占用端口的进程
    $processes = netstat -ano | Select-String ":$backendPort"
    foreach ($process in $processes) {
        $parts = $process.ToString().Split()
        $pid = $parts[-1]
        Write-Host "停止进程 (PID: $pid)..." -ForegroundColor Yellow
        Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
    }
    # 等待端口释放
    Start-Sleep -Seconds 2
}

# 检查前端服务
try {
    $frontendListener = [System.Net.Sockets.TcpListener]$frontendPort
    $frontendListener.Start()
    $frontendListener.Stop()
    Write-Host "前端服务端口 $frontendPort 可用" -ForegroundColor Green
} catch {
    Write-Host "前端服务端口 $frontendPort 已被占用，正在停止..." -ForegroundColor Yellow
    # 查找并停止占用端口的进程
    $processes = netstat -ano | Select-String ":$frontendPort"
    foreach ($process in $processes) {
        $parts = $process.ToString().Split()
        $pid = $parts[-1]
        Write-Host "停止进程 (PID: $pid)..." -ForegroundColor Yellow
        Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
    }
    # 等待端口释放
    Start-Sleep -Seconds 2
}

# 启动后端服务
Write-Host "[1/2] 启动后端服务..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "$env:PYTHONPATH = `"$pwd`"; venv_backend\Scripts\python.exe -m backend.main"

# 等待后端服务初始化
Write-Host "正在初始化后端服务..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# 启动前端服务
Write-Host "[2/2] 启动前端服务..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev"

Write-Host "========================================" -ForegroundColor Green
Write-Host "服务启动完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "后端服务: http://localhost:$backendPort" -ForegroundColor Blue
Write-Host "前端服务: http://localhost:$frontendPort" -ForegroundColor Blue
Write-Host "========================================" -ForegroundColor Green

# 提示用户
Write-Host "服务已启动，按任意键退出..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')

Write-Host "脚本执行完成。" -ForegroundColor Green