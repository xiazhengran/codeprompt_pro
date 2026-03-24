# CodePrompt Pro - 停止脚本
# 使用方法: .\stop.ps1

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  CodePrompt Pro 停止脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 获取脚本所在目录
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# 读取进程 ID
$ProcessFile = Join-Path $ScriptDir "processes.txt"

if (Test-Path $ProcessFile) {
    $ProcessIds = Get-Content -Path $ProcessFile
    
    foreach ($pid in $ProcessIds) {
        $pid = $pid.Trim()
        if ($pid -and $pid -ne "") {
            try {
                $process = Get-Process -Id $pid -ErrorAction SilentlyContinue
                if ($process) {
                    Write-Host "[停止] 进程 ID: $pid ($( $process.ProcessName ))" -ForegroundColor Yellow
                    Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
                }
            } catch {
                Write-Host "[提示] 进程 $pid 可能已经停止" -ForegroundColor Gray
            }
        }
    }
    
    # 删除进程文件
    Remove-Item -Path $ProcessFile -Force -ErrorAction SilentlyContinue
}

# 额外清理：停止相关进程
$RelatedProcesses = @("uvicorn", "node", "next")
foreach ($procName in $RelatedProcesses) {
    $processes = Get-Process -Name $procName -ErrorAction SilentlyContinue
    if ($processes) {
        foreach ($process in $processes) {
            # 检查是否是 CodePrompt Pro 相关的进程
            $commandLine = (Get-CimInstance Win32_Process -Filter "ProcessId=$($process.Id)").CommandLine
            if ($commandLine -match "src.api.main|localhost:3000|localhost:8000") {
                Write-Host "[停止] 相关进程: $procName (ID: $($process.Id))" -ForegroundColor Yellow
                Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
            }
        }
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  所有服务已停止!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
