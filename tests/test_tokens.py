"""Tests for token estimation and formatting."""

from __future__ import annotations

from show_model_context.tokens import estimate_tokens, format_tokens


def test_estimate_tokens_empty() -> None:
    assert estimate_tokens("") == 0


def test_estimate_tokens_short() -> None:
    assert estimate_tokens("abcd") == 1


def test_estimate_tokens_remainder() -> None:
    assert estimate_tokens("abc") == 0


def test_estimate_tokens_longer() -> None:
    assert estimate_tokens("a" * 100) == 25


def test_format_tokens_small() -> None:
    assert format_tokens(500) == "500"


def test_format_tokens_zero() -> None:
    assert format_tokens(0) == "0"


def test_format_tokens_exact_k() -> None:
    assert format_tokens(1000) == "1K"


def test_format_tokens_fractional_k() -> None:
    assert format_tokens(1500) == "1.5K"


def test_format_tokens_large_k() -> None:
    assert format_tokens(200000) == "200K"


def test_format_tokens_exact_m() -> None:
    assert format_tokens(1000000) == "1M"


def test_format_tokens_fractional_m() -> None:
    assert format_tokens(1500000) == "1.5M"
