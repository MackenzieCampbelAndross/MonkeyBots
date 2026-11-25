"""
Unit tests for CLI export command
"""
import pytest
from pathlib import Path
from core.monkeybots.cli.export_cmd import run_export


def test_cli_export_tmp(tmp_path):
    out_file = tmp_path / "test_ur5e.urdf"
    run_export("ur5e", "urdf", str(out_file))
    assert out_file.exists()
    content = out_file.read_text(encoding="utf-8")
    assert "<robot" in content
    assert 'name="ur5e"' in content
