"""Shared test fixtures."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from claude_show_context.config import DEFAULT_CATEGORIES
from claude_show_context.models import AppConfig


@pytest.fixture
def default_config() -> AppConfig:
    """Default app configuration."""
    return AppConfig(categories=list(DEFAULT_CATEGORIES))


@pytest.fixture
def tmp_transcript(tmp_path: Path) -> Path:
    """Path to a temp transcript file."""
    return tmp_path / "transcript.jsonl"


def write_transcript(path: Path, entries: list[dict[str, Any]]) -> None:
    """Write transcript entries as JSONL."""
    with path.open("w") as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")


def make_status_input(
    transcript_path: str = "",
    context_window_size: int = 200000,
    input_tokens: int = 8500,
    cache_creation: int = 5000,
    cache_read: int = 2000,
) -> str:
    """Create a JSON string mimicking Claude Code statusLine input."""
    return json.dumps({
        "transcript_path": transcript_path,
        "context_window": {
            "context_window_size": context_window_size,
            "current_usage": {
                "input_tokens": input_tokens,
                "cache_creation_input_tokens": cache_creation,
                "cache_read_input_tokens": cache_read,
            },
        },
    })
