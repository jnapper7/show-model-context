"""CLI entry point for show-model-context."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, cast

import click

from show_model_context.config import load_config
from show_model_context.models import ContextWindow, CurrentUsage, StatusInput
from show_model_context.renderer import render_bar
from show_model_context.transcript import parse_transcript

JsonDict = dict[str, Any]


def _parse_input(raw: str) -> StatusInput:
    """Parse JSON input from stdin into a StatusInput."""
    data: object = json.loads(raw)
    if not isinstance(data, dict):
        return StatusInput()
    top = cast(JsonDict, data)

    transcript_path = str(top.get("transcript_path", ""))

    cw_raw: object = top.get("context_window", {})
    if not isinstance(cw_raw, dict):
        cw_raw = {}
    cw = cast(JsonDict, cw_raw)

    usage_raw: object = cw.get("current_usage", {})
    if not isinstance(usage_raw, dict):
        usage_raw = {}
    usg = cast(JsonDict, usage_raw)

    usage = CurrentUsage(
        input_tokens=int(usg.get("input_tokens", 0)),
        cache_creation_input_tokens=int(usg.get("cache_creation_input_tokens", 0)),
        cache_read_input_tokens=int(usg.get("cache_read_input_tokens", 0)),
    )

    context_window = ContextWindow(
        context_window_size=int(cw.get("context_window_size", 200000)),
        current_usage=usage,
    )

    return StatusInput(
        transcript_path=transcript_path,
        context_window=context_window,
    )


@click.command()
@click.option("--config", "config_path", type=click.Path(exists=False), default=None, help="Path to TOML config file.")
@click.option("--mode", type=click.Choice(["total", "current"]), default="total", help="Bar display mode.")
def main(config_path: str | None, mode: str) -> None:
    """Display Claude Code context window usage as a colored bar."""
    config_p = Path(config_path) if config_path else None
    config = load_config(config_p)

    raw = sys.stdin.read().strip()
    if not raw:
        click.echo("No input provided.", err=True)
        sys.exit(1)

    try:
        status_input = _parse_input(raw)
    except (json.JSONDecodeError, ValueError, TypeError) as e:
        click.echo(f"Invalid input: {e}", err=True)
        sys.exit(1)

    usage = status_input.context_window.current_usage
    total_tokens = usage.input_tokens + usage.cache_creation_input_tokens + usage.cache_read_input_tokens

    categories = parse_transcript(status_input.transcript_path, config)

    output = render_bar(
        categories=categories,
        total_tokens=total_tokens,
        context_window_size=status_input.context_window.context_window_size,
        config=config,
        mode=mode,
    )

    sys.stdout.write(output + "\n")
    sys.stdout.flush()
