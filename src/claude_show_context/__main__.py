"""Allow running as python -m claude_show_context."""

from claude_show_context.cli import main

main(standalone_mode=True)  # pyright: ignore[reportCallIssue]
