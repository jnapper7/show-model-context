"""Tests for ANSI bar rendering."""

from __future__ import annotations

from claude_show_context.models import AppConfig, CategoryTokens
from claude_show_context.renderer import RESET, render_bar


def _config(bar_width: int = 20) -> AppConfig:
    return AppConfig(bar_width=bar_width)


def test_render_total_mode_basic() -> None:
    """Basic total mode rendering."""
    categories = [
        CategoryTokens(name="claude", color="green", tokens=500),
        CategoryTokens(name="files", color="blue", tokens=500),
    ]
    result = render_bar(categories, 10000, 200000, _config(), "total")
    assert "10K / 200K" in result
    # Should have some filled and some empty
    assert RESET in result


def test_render_current_mode() -> None:
    """Current mode uses total tokens as denominator."""
    categories = [
        CategoryTokens(name="claude", color="green", tokens=300),
        CategoryTokens(name="files", color="blue", tokens=700),
    ]
    result = render_bar(categories, 10000, 200000, _config(), "current")
    assert "10K / 10K" in result


def test_render_empty_categories() -> None:
    """No categories means empty bar."""
    result = render_bar([], 0, 200000, _config(), "total")
    assert "0 / 200K" in result


def test_render_zero_context_window() -> None:
    """Zero context window size doesn't crash."""
    categories = [CategoryTokens(name="a", color="green", tokens=100)]
    result = render_bar(categories, 100, 0, _config(), "total")
    assert RESET in result


def test_render_total_mode_no_actual_tokens() -> None:
    """When total_tokens is 0, use estimated total."""
    categories = [CategoryTokens(name="a", color="green", tokens=1000)]
    result = render_bar(categories, 0, 200000, _config(), "total")
    assert "1K / 200K" in result


def test_render_current_mode_no_actual_tokens() -> None:
    """When total_tokens is 0 in current mode, use estimated."""
    categories = [
        CategoryTokens(name="a", color="green", tokens=500),
        CategoryTokens(name="b", color="blue", tokens=500),
    ]
    result = render_bar(categories, 0, 200000, _config(), "current")
    assert "1K / 1K" in result


def test_render_zero_estimated_zero_actual_current_mode() -> None:
    """Both totals zero in current mode."""
    result = render_bar([], 0, 200000, _config(), "current")
    assert "0 / 0" in result


def test_render_filled_exceeds_bar_width() -> None:
    """Filled portion capped at bar_width."""
    categories = [CategoryTokens(name="a", color="green", tokens=300000)]
    result = render_bar(categories, 300000, 200000, _config(bar_width=10), "total")
    assert "300K / 200K" in result


def test_render_unknown_color() -> None:
    """Unknown color name renders without ANSI codes (plain text)."""
    categories = [CategoryTokens(name="a", color="nonexistent", tokens=100)]
    # Use current mode so the bar is fully filled, exercising the _color fallback
    result = render_bar(categories, 100, 200000, _config(), "current")
    assert "100 / 100" in result
    # The filled chars should be present without ANSI escape codes
    assert "█" in result


def test_render_zero_token_categories_skipped() -> None:
    """Categories with 0 tokens don't get segments."""
    categories = [
        CategoryTokens(name="a", color="green", tokens=0),
        CategoryTokens(name="b", color="blue", tokens=500),
    ]
    result = render_bar(categories, 500, 200000, _config(), "total")
    assert "500 / 200K" in result


def test_render_dim_color() -> None:
    """Dim color code works in current mode (fills full bar)."""
    categories = [CategoryTokens(name="other", color="dim", tokens=100)]
    result = render_bar(categories, 100, 200000, _config(), "current")
    assert "\033[2m" in result
