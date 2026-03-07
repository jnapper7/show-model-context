"""ANSI color bar rendering for terminal status line."""

from __future__ import annotations

import re
import shutil

from claude_show_context.models import AppConfig, CategoryTokens
from claude_show_context.tokens import format_tokens

_ANSI_RE = re.compile(r"\033\[[0-9;]*m")

# ANSI 16-color codes
COLOR_CODES: dict[str, str] = {
    "black": "\033[30m",
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "magenta": "\033[35m",
    "cyan": "\033[36m",
    "white": "\033[37m",
    "bright_black": "\033[90m",
    "bright_red": "\033[91m",
    "bright_green": "\033[92m",
    "bright_yellow": "\033[93m",
    "bright_blue": "\033[94m",
    "bright_magenta": "\033[95m",
    "bright_cyan": "\033[96m",
    "bright_white": "\033[97m",
    "dim": "\033[2m",
}

RESET = "\033[0m"


def _color(text: str, color_name: str) -> str:
    """Wrap text in ANSI color codes."""
    code = COLOR_CODES.get(color_name, "")
    if not code:
        return text
    return f"{code}{text}{RESET}"


def render_bar(
    categories: list[CategoryTokens],
    total_tokens: int,
    context_window_size: int,
    config: AppConfig,
    mode: str,
) -> str:
    """Render a colored bar showing token usage by category.

    Args:
        categories: Token counts per category.
        total_tokens: Total tokens used (from context_window data).
        context_window_size: Maximum context window size.
        config: Application configuration.
        mode: "total" (100% = context window) or "current" (100% = tokens used).

    Returns:
        A single-line string with ANSI colors for the status bar.
    """
    filled_char = config.filled_char
    empty_char = config.empty_char

    estimated_total = sum(c.tokens for c in categories)

    if mode == "current":
        display_total = total_tokens if total_tokens > 0 else estimated_total
        display_max = display_total
    else:
        display_total = total_tokens if total_tokens > 0 else estimated_total
        display_max = context_window_size

    # Build the label first so we can auto-size the bar
    label = _build_label(categories, display_total, display_max, config)

    # Resolve bar width: 0 means auto-detect from terminal
    bar_width = config.bar_width
    if bar_width <= 0:
        terminal_width = shutil.get_terminal_size().columns
        visible_label_len = _visible_len(label)
        bar_width = max(10, terminal_width - visible_label_len - 1)

    if mode == "current":
        denominator = total_tokens if total_tokens > 0 else (estimated_total if estimated_total > 0 else 1)
        filled_width = bar_width
    else:
        denominator = context_window_size if context_window_size > 0 else 1
        used = total_tokens if total_tokens > 0 else estimated_total
        filled_width = min(bar_width, round(used / denominator * bar_width))

    # Compute per-category widths within the filled portion
    segments: list[tuple[int, str]] = []
    remaining_width = filled_width

    if estimated_total > 0 and total_tokens > 0:
        scale = total_tokens / estimated_total
    else:
        scale = 1.0

    for i, cat in enumerate(categories):
        if cat.tokens == 0:
            continue
        scaled_tokens = cat.tokens * scale
        if i == len(categories) - 1 or remaining_width <= 0:
            width = remaining_width
        else:
            width = round(scaled_tokens / denominator * bar_width)
            width = min(width, remaining_width)
        if width > 0:
            segments.append((width, cat.color))
            remaining_width -= width

    # Build the bar
    bar_parts: list[str] = []
    for width, color in segments:
        bar_parts.append(_color(filled_char * width, color))

    empty_width = bar_width - filled_width
    if empty_width > 0:
        bar_parts.append(_color(empty_char * empty_width, "bright_black"))

    bar = "".join(bar_parts)

    if config.label_position == "right":
        return f"{bar} {label}"
    return f"{label} {bar}"


def _visible_len(text: str) -> int:
    """Return the visible length of a string after stripping ANSI escape codes."""
    return len(_ANSI_RE.sub("", text))


def _build_label(
    categories: list[CategoryTokens],
    display_total: int,
    display_max: int,
    config: AppConfig,
) -> str:
    """Build the label string based on the configured format.

    Args:
        categories: Token counts per category.
        display_total: Total tokens to display.
        display_max: Maximum tokens to display.
        config: Application configuration.

    Returns:
        Formatted label string.
    """
    if config.label_format == "percentage":
        if display_max == 0:
            return "0%"
        return f"{round(display_total / display_max * 100)}%"

    if config.label_format == "legend":
        parts: list[str] = []
        for cat in categories:
            if cat.tokens > 0:
                parts.append(f"{_color(config.filled_char, cat.color)}{cat.name[0].upper()}")
        return " ".join(parts)

    return f"{format_tokens(display_total)} / {format_tokens(display_max)}"
