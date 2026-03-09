"""Allow running as python -m show_model_context."""

from show_model_context.cli import main

main(standalone_mode=True)  # pyright: ignore[reportCallIssue]
