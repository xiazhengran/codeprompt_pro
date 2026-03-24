# CodePrompt Pro - 启动脚本
# 使用方法: .\start.ps1

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  CodePrompt Pro 启动脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 获取脚本所在目录
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Split-Path -Parent $ScriptDir

# 检查环境变量文件
$EnvFile = Join-Path $RootDir ".env"
if (-Not (Test-Path $EnvFile)) {
    Write-Host "[警告] .env 文件不存在，复制 .env.example 为 .env" -ForegroundColor Yellow
    $EnvExampleFile = Join-Path $RootDir ".env.example"
    if (Test-Path $EnvExampleFile) {
        Copy-Item $EnvExampleFile $EnvFile
        Write-Host "[提示] 请编辑 .env 文件配置 LLM API" -ForegroundColor Yellow
    }
}

# 检查前端依赖
$FrontendNodeModules = Join-Path $RootDir "frontend\node_modules"
if (-Not (Test-Path $FrontendNodeModules)) {
    Write-Host "[安装] 前端依赖..." -ForegroundColor Yellow
    Push-Location (Join-Path $RootDir "frontend")
    npm install
    Pop-Location
}

# 启动后端
Write-Host "[启动] 后端服务 (FastAPI)..." -ForegroundColor Green
$BackendProcess = Start-Process -FilePath "uvicorn" -ArgumentList "src.api.main:app","--reload","--host","0.0.0.0","--port","8000" -WorkingDirectory $RootDir -PassThru -NoNewWindow

# 等待后端启动
Start-Sleep -Seconds 3

# 启动前端
Write-Host "[启动] 前端服务 (Next.js)..." -ForegroundColor Green
$FrontendProcess = Start-Process -FilePath "npm" -ArgumentList "run","dev" -WorkingDirectory (Join-Path $RootDir "frontend") -PassThru -NoNewWindow

# 保存进程 ID
$ProcessFile = Join-Path $ScriptDir "processes.txt"
"$BackendProcess.Id`n$FrontendProcess.Id" | Out-File -FilePath $ProcessFile -Encoding UTF8

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  服务已启动!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  后端: http://localhost:8000" -ForegroundColor White
Write-Host "  前端: http://localhost:3000" -ForegroundColor White
Write-Host "  API文档: http://localhost:8000/docs" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "按 Ctrl+C 停止服务，或运行 .\stop.ps1" -ForegroundColor Yellow
