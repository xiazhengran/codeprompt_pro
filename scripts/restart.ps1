# CodePrompt Pro - 重启脚本
# 使用方法: .\restart.ps1

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  CodePrompt Pro 重启脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 获取脚本所在目录
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# 调用停止脚本
Write-Host "[步骤1] 停止现有服务..." -ForegroundColor Yellow
& (Join-Path $ScriptDir "stop.ps1")

Start-Sleep -Seconds 2

# 调用启动脚本
Write-Host "[步骤2] 启动新服务..." -ForegroundColor Yellow
& (Join-Path $ScriptDir "start.ps1")
