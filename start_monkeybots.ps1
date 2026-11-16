<#
.SYNOPSIS
    MonkeyBots Desktop Launcher & Process Supervisor (Windows PowerShell)
.DESCRIPTION
    Verifies offline prerequisites, boots the Python simulation server (Port 8765),
    verifies local health status, and launches the Tauri desktop application.
#>

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$Host.UI.RawUI.WindowTitle = "MonkeyBots Robotics Workstation"

Write-Host "===============================================================================" -ForegroundColor Cyan
Write-Host "         MONKEYBOTS: PRECISION ROBOTICS ENGINEERING WORKSTATION" -ForegroundColor White
Write-Host "                 Local-First Desktop Environment v1.0.0" -ForegroundColor Gray
Write-Host "===============================================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Environment & Dependency Validation
Write-Host "[1/4] Verifying Python Runtime & MuJoCo Kernel..." -ForegroundColor Yellow
try {
    $pyVer = python -c "import sys, mujoco; print(f'{sys.version.split()[0]}|{getattr(mujoco, ''__version__'', ''OK'')}')" 2>$null
    if (-not $pyVer) {
        throw "Python or MuJoCo missing."
    }
    $parts = $pyVer.Split('|')
    Write-Host "  -> Python Version: $($parts[0]) (Verified)" -ForegroundColor Green
    Write-Host "  -> MuJoCo Kernel: $($parts[1]) (Operational)" -ForegroundColor Green
} catch {
    Write-Host "  [WARN] MuJoCo or dependencies not fully configured." -ForegroundColor Red
    Write-Host "  Installing required packages via pip..." -ForegroundColor Yellow
    pip install -r requirements.txt
}

# 2. Start Simulation Backend Daemon
Write-Host "[2/4] Starting Local Simulation Backend Engine on 127.0.0.1:8765..." -ForegroundColor Yellow
if (-not (Test-Path "logs")) { New-Item -ItemType Directory -Path "logs" | Out-Null }

$backendJob = Start-Process -FilePath "python" `
    -ArgumentList "-m uvicorn server.monkeybots_server.main:app --host 127.0.0.1 --port 8765 --workers 1" `
    -PassThru -NoNewWindow -RedirectStandardOutput "logs/backend_stdout.log" -RedirectStandardError "logs/backend_stderr.log"

# Wait for healthy response
$maxRetries = 10
$healthy = $false
for ($i = 0; $i -lt $maxRetries; $i++) {
    Start-Sleep -Milliseconds 500
    try {
        $res = Invoke-RestMethod -Uri "http://127.0.0.1:8765/api/v1/system/health" -TimeoutSec 1 -ErrorAction Stop
        if ($res.status -eq "HEALTHY") {
            $healthy = $true
            break
        }
    } catch {
        # Retry
    }
}

if ($healthy) {
    Write-Host "  -> Backend Online: 127.0.0.1:8765 (Healthy)" -ForegroundColor Green
} else {
    Write-Host "  [WARN] Backend startup took longer than expected. Continuing..." -ForegroundColor Yellow
}

# 3. Launch Desktop Interface
Write-Host "[3/4] Launching Desktop User Interface..." -ForegroundColor Yellow
$tauriExeDebug = "app/src-tauri/target/debug/app.exe"
$tauriExeRelease = "app/src-tauri/target/release/app.exe"

if (Test-Path $tauriExeRelease) {
    Write-Host "  -> Launching Native Release Desktop Binary..." -ForegroundColor Green
    Start-Process $tauriExeRelease
} elseif (Test-Path $tauriExeDebug) {
    Write-Host "  -> Launching Native Desktop Binary..." -ForegroundColor Green
    Start-Process $tauriExeDebug
} else {
    Write-Host "  -> Launching Vite Workstation Shell..." -ForegroundColor Yellow
    Set-Location app
    Start-Process -FilePath "npm.cmd" -ArgumentList "run preview -- --port 5173" -NoNewWindow
    Start-Process "http://localhost:5173"
    Set-Location ..
}

Write-Host ""
Write-Host "===============================================================================" -ForegroundColor Cyan
Write-Host " MonkeyBots Workstation is active. Press Ctrl+C in this terminal to shut down." -ForegroundColor White
Write-Host "===============================================================================" -ForegroundColor Cyan

try {
    # Keep script open monitoring backend process
    while (-not $backendJob.HasExited) {
        Start-Sleep -Seconds 1
    }
} finally {
    Write-Host "`nStopping MonkeyBots backend..." -ForegroundColor Yellow
    if ($backendJob -and -not $backendJob.HasExited) {
        Stop-Process -Id $backendJob.Id -Force -ErrorAction SilentlyContinue
    }
    Write-Host "MonkeyBots terminated cleanly." -ForegroundColor Gray
}
