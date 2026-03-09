"""Token estimation and human-readable formatting."""

from __future__ import annotations


def estimate_tokens(text: str) -> int:
    """Estimate token count as len(text) / 4."""
    return len(text) // 4


def format_tokens(count: int) -> str:
    """Format a token count for human display (e.g. 1.5K, 200K, 1.2M)."""
    if count >= 1_000_000:
        value = count / 1_000_000
        if value == int(value):
            return f"{int(value)}M"
        return f"{value:.1f}M"
    if count >= 1_000:
        value = count / 1_000
        if value == int(value):
            return f"{int(value)}K"
        return f"{value:.1f}K"
    return str(count)
