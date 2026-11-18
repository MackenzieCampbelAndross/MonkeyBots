# MonkeyBots Automated Daily Commit Runner (PowerShell)
# Executed daily at 10:00 AM IST via Windows Task Scheduler
# Automatically runs that day's scheduled engineering commits and pushes to origin main.

$ErrorActionPreference = "Continue"
$WorkspaceRoot = "D:\Mac\project\MonkeyBots"
Set-Location $WorkspaceRoot

$LogFile = "$WorkspaceRoot\scripts\automation\scheduler_trigger.log"
$Timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
"[$Timestamp] Windows Scheduled Task triggered Daily Runner" | Out-File -FilePath $LogFile -Append

# Run the python automation runner
python "$WorkspaceRoot\scripts\automation\runner.py" 2>&1 | Out-File -FilePath $LogFile -Append
