@echo off
setlocal enabledelayedexpansion

title MonkeyBots Professional Robotics Workstation
echo ===============================================================================
echo            MONKEYBOTS: PRECISION ROBOTICS ENGINEERING WORKSTATION
echo                       Local-First Architecture v1.0.0
echo ===============================================================================
echo.

:: 1. Verify Python Environment
echo [1/4] Verifying Python runtime...
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python not found in system PATH.
    echo Please install Python 3.10+ from https://www.python.org/
    pause
    exit /b 1
)

:: 2. Verify MuJoCo Physics Kernel
echo [2/4] Verifying MuJoCo physics engine...
python -c "import mujoco; print('  -> MuJoCo version:', getattr(mujoco, '__version__', 'Available'))" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] MuJoCo Python SDK is not detected in active environment.
    echo Installing required simulation dependencies...
    pip install -r requirements.txt
)

:: 3. Launch Simulation Backend Daemon
echo [3/4] Launching MonkeyBots Python Simulation Engine (Port 8765)...
start /b "" python -m uvicorn server.monkeybots_server.main:app --host 127.0.0.1 --port 8765 --workers 1 > logs\backend.log 2>&1

:: Wait 2 seconds for server loopback port binding
timeout /t 2 /nobreak >nul

:: 4. Launch Desktop Frontend / Tauri Container
echo [4/4] Launching MonkeyBots Workstation Interface...
cd app
if exist "src-tauri\target\debug\app.exe" (
    echo Starting native Windows desktop application...
    start "" "src-tauri\target\debug\app.exe"
) else if exist "src-tauri\target\release\app.exe" (
    echo Starting native Windows desktop release...
    start "" "src-tauri\target\release\app.exe"
) else (
    echo Launching high-speed development workstation shell...
    start "" npm run preview -- --port 5173
    start http://localhost:5173
)

echo.
echo ===============================================================================
echo MonkeyBots is now active!
echo Backend Gateway: http://127.0.0.1:8765
echo WebSocket Stream: ws://127.0.0.1:8765/ws/simulation
echo Close this window or terminate backend process to stop.
echo ===============================================================================
