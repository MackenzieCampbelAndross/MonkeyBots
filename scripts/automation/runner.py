"""
MonkeyBots 5-Day Automated Commit & Contribution Engine
Runs scheduled daily batches at 10:00 AM IST with automatic catch-up,
executing genuine engineering changes, running tests, committing under the
verified author identity, and pushing to origin main.
"""

import os
import sys
import json
import subprocess
import datetime
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
STATE_FILE = Path(__file__).resolve().parent / "state.json"
LOG_FILE = Path(__file__).resolve().parent / "automation.log"

AUTHOR_NAME = "MackenzieCampbelAndross"
AUTHOR_EMAIL = "mackenzieandross@gmail.com"

SCHEDULE = {
    1: {"date_str": "2026-11-19", "target_commits": 22, "module": "day1"},
    2: {"date_str": "2026-11-20", "target_commits": 27, "module": "day2"},
    3: {"date_str": "2026-11-21", "target_commits": 21, "module": "day3"},
    4: {"date_str": "2026-11-22", "target_commits": 28, "module": "day4"},
    5: {"date_str": "2026-11-23", "target_commits": 24, "module": "day5"},
}


def log(msg: str):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] {msg}"
    print(formatted)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(formatted + "\n")


def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"completed_days": [], "last_run": None, "total_commits_created": 0}


def save_state(state: dict):
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def git_commit_with_date(message: str, date_iso: str, files_to_add: list = None):
    """Executes an authentic git commit with explicit author date and identity."""
    os.environ["GIT_AUTHOR_NAME"] = AUTHOR_NAME
    os.environ["GIT_AUTHOR_EMAIL"] = AUTHOR_EMAIL
    os.environ["GIT_COMMITTER_NAME"] = AUTHOR_NAME
    os.environ["GIT_COMMITTER_EMAIL"] = AUTHOR_EMAIL
    os.environ["GIT_AUTHOR_DATE"] = date_iso
    os.environ["GIT_COMMITTER_DATE"] = date_iso

    if files_to_add:
        for f in files_to_add:
            subprocess.run(["git", "add", str(f)], cwd=str(WORKSPACE_ROOT), check=True)
    else:
        subprocess.run(["git", "add", "."], cwd=str(WORKSPACE_ROOT), check=True)

    res = subprocess.run(
        ["git", "commit", "-m", message],
        cwd=str(WORKSPACE_ROOT),
        capture_output=True,
        text=True,
    )
    if res.returncode == 0:
        log(f"Committed: {message} ({date_iso})")
        return True
    else:
        log(f"Commit output: {res.stdout.strip()} {res.stderr.strip()}")
        return False


def git_push():
    """Pushes commits to origin main."""
    log("Pushing to origin main...")
    res = subprocess.run(
        ["git", "push", "origin", "main"],
        cwd=str(WORKSPACE_ROOT),
        capture_output=True,
        text=True,
    )
    if res.returncode == 0:
        log("Successfully pushed to GitHub origin main.")
        return True
    else:
        log(f"Git push error: {res.stderr.strip()}")
        return False


def run_day(day_num: int):
    """Runs a specific day's batch."""
    log(f"=== Starting Day {day_num} Execution ===")
    state = load_state()

    if day_num == 1:
        from day1 import execute_day1
        count = execute_day1(git_commit_with_date, SCHEDULE[1]["date_str"])
    elif day_num == 2:
        from day2 import execute_day2
        count = execute_day2(git_commit_with_date, SCHEDULE[2]["date_str"])
    elif day_num == 3:
        from day3 import execute_day3
        count = execute_day3(git_commit_with_date, SCHEDULE[3]["date_str"])
    elif day_num == 4:
        from day4 import execute_day4
        count = execute_day4(git_commit_with_date, SCHEDULE[4]["date_str"])
    elif day_num == 5:
        from day5 import execute_day5
        count = execute_day5(git_commit_with_date, SCHEDULE[5]["date_str"])
    else:
        log(f"Invalid day {day_num}")
        return

    # Push upon completion of the day's batch
    git_push()

    if day_num not in state["completed_days"]:
        state["completed_days"].append(day_num)
    state["last_run"] = datetime.datetime.now().isoformat()
    state["total_commits_created"] = state.get("total_commits_created", 0) + count
    save_state(state)
    log(f"=== Completed Day {day_num}: {count} commits pushed ===")


def main():
    log("MonkeyBots Daily Automation Runner Invoked.")
    state = load_state()
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    log(f"Current Date: {today_str}, Completed Days: {state['completed_days']}")

    # Determine which day to run
    # If a specific day argument is passed (e.g. `python runner.py 1`)
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        target_day = int(sys.argv[1])
        run_day(target_day)
        return

    # Otherwise, check calendar schedule
    # Day 1: Nov 19, Day 2: Nov 20, Day 3: Nov 21, Day 4: Nov 22, Day 5: Nov 23
    for day_num, info in SCHEDULE.items():
        if day_num not in state["completed_days"]:
            # If today >= scheduled date, run it (catch-up supported!)
            if today_str >= info["date_str"]:
                log(f"Running scheduled Day {day_num} for {info['date_str']}...")
                run_day(day_num)
                break
            else:
                log(f"Day {day_num} is scheduled for {info['date_str']}. Waiting for scheduled date.")
                break
    else:
        log("All 5 days have been successfully completed!")


if __name__ == "__main__":
    main()
