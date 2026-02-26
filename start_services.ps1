#!/usr/bin/env powershell

# 启动前后端服务的脚本
# 作者: AI Assistant
# 日期: 2026-02-26

Write-Host "========================================" -ForegroundColor Green
Write-Host "        AI 测试用例生成平台启动脚本        " -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

# 切换到项目根目录
Set-Location "$PSScriptRoot"

# 启动后端服务
Write-Host "[1/2] 启动后端服务..." -ForegroundColor Cyan

# 创建后端服务终端
$backendTerminal = New-Object System.Diagnostics.Process
$backendTerminal.StartInfo.FileName = "powershell.exe"
$backendTerminal.StartInfo.Arguments = "-NoExit -Command `$env:PYTHONPATH = `"`$pwd`"; venv_backend\Scripts\python.exe -m backend.main"
$backendTerminal.StartInfo.WorkingDirectory = "$PSScriptRoot"
$backendTerminal.StartInfo.UseShellExecute = $false
$backendTerminal.Start()

# 等待后端服务初始化
Write-Host "正在初始化后端服务..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# 启动前端服务
Write-Host "[2/2] 启动前端服务..." -ForegroundColor Cyan

# 创建前端服务终端
$frontendTerminal = New-Object System.Diagnostics.Process
$frontendTerminal.StartInfo.FileName = "powershell.exe"
$frontendTerminal.StartInfo.Arguments = "-NoExit -Command cd frontend; npm run dev"
$frontendTerminal.StartInfo.WorkingDirectory = "$PSScriptRoot"
$frontendTerminal.StartInfo.UseShellExecute = $false
$frontendTerminal.Start()

Write-Host "========================================" -ForegroundColor Green
Write-Host "服务启动完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "后端服务: http://localhost:8888" -ForegroundColor Blue
Write-Host "前端服务: http://localhost:5173" -ForegroundColor Blue
Write-Host "========================================" -ForegroundColor Green

# 提示用户如何停止服务
Write-Host "按任意键关闭此窗口..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')

# 停止服务
$backendTerminal.Kill()
$frontendTerminal.Kill()

Write-Host "服务已停止。" -ForegroundColor Red
