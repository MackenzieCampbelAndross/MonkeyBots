@echo off
REM MonkeyBots Manual / On-Demand Daily Commit Runner
cd /d "D:\Mac\project\MonkeyBots"
echo ========================================================
echo   MonkeyBots 5-Day Automated Commit Runner
echo ========================================================
python scripts\automation\runner.py %*
pause
