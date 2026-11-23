"""
Unit Tests for MonkeyBots CLI
"""

import subprocess
import sys


def test_cli_help():
    res = subprocess.run([sys.executable, "-m", "core.monkeybots.cli.main", "--help"], capture_output=True, text=True)
    assert res.returncode == 0
    assert "MonkeyBots" in res.stdout
