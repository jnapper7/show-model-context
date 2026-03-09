"""Data models for show-model-context."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CategoryConfig:
    """Configuration for a single content category."""

    name: str
    color: str = "white"
    label: str = ""
    match_type: str | None = None
    match_tools: list[str] = field(default_factory=lambda: list[str]())
    match_content_types: list[str] = field(default_factory=lambda: list[str]())
    content_contains: list[str] = field(default_factory=lambda: list[str]())


@dataclass
class AppConfig:
    """Full application configuration."""

    bar_width: int = 0
    empty_char: str = "░"
    filled_char: str = "█"
    label_position: str = "left"
    label_format: str = "ratio"
    categories: list[CategoryConfig] = field(default_factory=lambda: list[CategoryConfig]())


@dataclass
class CurrentUsage:
    """Token usage from the context window payload."""

    input_tokens: int = 0
    cache_creation_input_tokens: int = 0
    cache_read_input_tokens: int = 0


@dataclass
class ContextWindow:
    """Context window information from Claude Code."""

    context_window_size: int = 200000
    current_usage: CurrentUsage = field(default_factory=CurrentUsage)


@dataclass
class StatusInput:
    """Top-level JSON input from Claude Code's statusLine."""

    transcript_path: str = ""
    context_window: ContextWindow = field(default_factory=ContextWindow)


@dataclass
class CategoryTokens:
    """Token count for a single category."""

    name: str
    color: str
    label: str = ""
    tokens: int = 0
