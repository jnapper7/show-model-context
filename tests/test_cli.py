"""E2E tests for the CLI."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from click.testing import CliRunner

from show_model_context.cli import main
from tests.conftest import make_status_input, write_transcript


def test_cli_total_mode_with_transcript(tmp_path: Path) -> None:
    """E2E: total mode with a real transcript file."""
    transcript = tmp_path / "t.jsonl"
    write_transcript(transcript, [
        {"type": "assistant", "message": {"content": [{"type": "text", "text": "Hello " * 100}]}},
        {"type": "user", "message": {"content": [{"type": "text", "text": "<system-reminder>test</system-reminder>"}]}},
    ])
    stdin = make_status_input(str(transcript))
    runner = CliRunner()
    result = runner.invoke(main, ["--mode", "total"], input=stdin)
    assert result.exit_code == 0
    assert "/ 200K" in result.output


def test_cli_current_mode(tmp_path: Path) -> None:
    """E2E: current mode."""
    transcript = tmp_path / "t.jsonl"
    write_transcript(transcript, [
        {"type": "assistant", "message": {"content": [{"type": "text", "text": "Some text here."}]}},
    ])
    stdin = make_status_input(str(transcript))
    runner = CliRunner()
    result = runner.invoke(main, ["--mode", "current"], input=stdin)
    assert result.exit_code == 0
    assert "/" in result.output


def test_cli_no_input() -> None:
    """E2E: no stdin input gives error."""
    runner = CliRunner()
    result = runner.invoke(main, [], input="")
    assert result.exit_code == 1
    assert "No input" in result.output


def test_cli_invalid_json() -> None:
    """E2E: invalid JSON gives error."""
    runner = CliRunner()
    result = runner.invoke(main, [], input="not json")
    assert result.exit_code == 1
    assert "Invalid input" in result.output


def test_cli_with_config(tmp_path: Path) -> None:
    """E2E: custom config file."""
    config_file = tmp_path / "config.toml"
    config_file.write_text("""\
[general]
bar_width = 10

[[categories]]
name = "claude"
color = "green"
match_type = "assistant"
match_content_types = ["text"]
""")
    transcript = tmp_path / "t.jsonl"
    write_transcript(transcript, [
        {"type": "assistant", "message": {"content": [{"type": "text", "text": "Test response"}]}},
    ])
    stdin = make_status_input(str(transcript))
    runner = CliRunner()
    result = runner.invoke(main, ["--config", str(config_file), "--mode", "total"], input=stdin)
    assert result.exit_code == 0
    assert "/" in result.output


def test_cli_nonexistent_transcript() -> None:
    """E2E: nonexistent transcript is handled gracefully."""
    stdin = make_status_input("/nonexistent/transcript.jsonl")
    runner = CliRunner()
    result = runner.invoke(main, ["--mode", "total"], input=stdin)
    assert result.exit_code == 0
    assert "/ 200K" in result.output


def test_cli_subprocess(tmp_path: Path) -> None:
    """E2E: run as subprocess to test the actual entry point."""
    transcript = tmp_path / "t.jsonl"
    write_transcript(transcript, [
        {"type": "assistant", "message": {"content": [{"type": "text", "text": "Hello world test!"}]}},
    ])
    stdin = make_status_input(str(transcript))
    result = subprocess.run(
        [sys.executable, "-m", "show_model_context", "--mode", "total"],
        input=stdin,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "/" in result.stdout


def test_cli_missing_context_window_fields() -> None:
    """E2E: missing fields in context_window use defaults."""
    stdin = json.dumps({"transcript_path": "", "context_window": {}})
    runner = CliRunner()
    result = runner.invoke(main, ["--mode", "total"], input=stdin)
    assert result.exit_code == 0


def test_cli_missing_usage_fields() -> None:
    """E2E: missing fields in current_usage use defaults."""
    stdin = json.dumps({
        "transcript_path": "",
        "context_window": {"context_window_size": 100000, "current_usage": {}},
    })
    runner = CliRunner()
    result = runner.invoke(main, ["--mode", "total"], input=stdin)
    assert result.exit_code == 0


def test_cli_non_dict_context_window() -> None:
    """E2E: non-dict context_window handled."""
    stdin = json.dumps({"transcript_path": "", "context_window": "invalid"})
    runner = CliRunner()
    result = runner.invoke(main, ["--mode", "total"], input=stdin)
    assert result.exit_code == 0


def test_cli_non_dict_usage() -> None:
    """E2E: non-dict current_usage handled."""
    stdin = json.dumps({
        "transcript_path": "",
        "context_window": {"context_window_size": 200000, "current_usage": "invalid"},
    })
    runner = CliRunner()
    result = runner.invoke(main, ["--mode", "total"], input=stdin)
    assert result.exit_code == 0


def test_cli_non_dict_input() -> None:
    """E2E: non-dict top-level JSON returns empty StatusInput."""
    stdin = json.dumps([1, 2, 3])
    runner = CliRunner()
    result = runner.invoke(main, ["--mode", "total"], input=stdin)
    assert result.exit_code == 0
