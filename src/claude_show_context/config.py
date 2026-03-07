"""Configuration loading with TOML support and built-in defaults."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any, cast

from claude_show_context.models import AppConfig, CategoryConfig

DEFAULT_CONFIG_PATH = Path.home() / ".config" / "claude-show-context" / "config.toml"

JsonDict = dict[str, Any]

DEFAULT_CATEGORIES: list[CategoryConfig] = [
    CategoryConfig(
        name="system",
        color="bright_black",
        match_type="user",
        content_contains=["<system-reminder>", "CLAUDE.md", "<local-command-"],
    ),
    CategoryConfig(
        name="files",
        color="blue",
        match_tools=["Read", "Write", "Edit"],
    ),
    CategoryConfig(
        name="tools",
        color="yellow",
        match_tools=["Bash", "Glob", "Grep", "WebFetch", "WebSearch"],
    ),
    CategoryConfig(
        name="skills",
        color="magenta",
        match_tools=["Task", "Skill"],
    ),
    CategoryConfig(
        name="claude",
        color="green",
        match_type="assistant",
        match_content_types=["text", "thinking"],
    ),
]


def _parse_category(raw: JsonDict) -> CategoryConfig:
    """Parse a single category from TOML dict."""
    name = str(raw.get("name", "unknown"))
    color = str(raw.get("color", "white"))
    match_type_val: object = raw.get("match_type")
    match_type = str(match_type_val) if match_type_val is not None else None

    match_tools_raw: object = raw.get("match_tools", [])
    match_tools: list[str] = (
        [str(t) for t in cast(list[object], match_tools_raw)] if isinstance(match_tools_raw, list) else []
    )

    match_content_types_raw: object = raw.get("match_content_types", [])
    match_content_types: list[str] = (
        [str(t) for t in cast(list[object], match_content_types_raw)]
        if isinstance(match_content_types_raw, list)
        else []
    )

    content_contains_raw: object = raw.get("content_contains", [])
    content_contains: list[str] = (
        [str(s) for s in cast(list[object], content_contains_raw)]
        if isinstance(content_contains_raw, list)
        else []
    )

    return CategoryConfig(
        name=name,
        color=color,
        match_type=match_type,
        match_tools=match_tools,
        match_content_types=match_content_types,
        content_contains=content_contains,
    )


def load_config(config_path: Path | None = None) -> AppConfig:
    """Load configuration from TOML file, falling back to defaults."""
    path = config_path or DEFAULT_CONFIG_PATH

    if not path.exists():
        return AppConfig(categories=list(DEFAULT_CATEGORIES))

    with path.open("rb") as f:
        data = tomllib.load(f)

    general_raw: object = data.get("general", {})
    if not isinstance(general_raw, dict):
        general_raw = {}
    general = cast(JsonDict, general_raw)

    bar_width = int(general.get("bar_width", 40))
    empty_char = str(general.get("empty_char", "░"))
    filled_char = str(general.get("filled_char", "█"))
    label_position = str(general.get("label_position", "left"))
    label_format = str(general.get("label_format", "ratio"))

    raw_categories_val: object = data.get("categories", [])
    raw_categories: list[object] = (
        cast(list[object], raw_categories_val) if isinstance(raw_categories_val, list) else []
    )

    categories = [_parse_category(cast(JsonDict, c)) for c in raw_categories if isinstance(c, dict)]

    if not categories:
        categories = list(DEFAULT_CATEGORIES)

    return AppConfig(
        bar_width=bar_width,
        empty_char=empty_char,
        filled_char=filled_char,
        label_position=label_position,
        label_format=label_format,
        categories=categories,
    )
