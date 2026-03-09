# Development guidelines

This document contains critical information about working with this codebase. Follow these guidelines precisely.

**Note this repo uses Python for coding, and uv as the package manager.**

## Core Development Rules For Generating Code

1. Package Management
   - ONLY use uv, NEVER pip
   - Installation: `uv add <package>`
   - Running tools: `uv run <tool>`
   - Upgrading: `uv lock --upgrade-package <package>`
   - FORBIDDEN: `uv pip install`, `@latest` syntax

2. Code Quality
   - Type hints required for all code
   - Public APIs must have docstrings
   - Functions must be focused and small
   - Follow existing patterns exactly
   - Line length: 120 chars maximum
   - FORBIDDEN: imports inside functions. THEY SHOULD BE AT THE TOP OF THE FILE.

3. Testing Requirements
   - Framework: `uv run --frozen pytest`
   - Do not use `Test` prefixed classes, use functions
   - Coverage: test edge cases and errors
   - New features require tests
   - Bug fixes require regression tests
   - IMPORTANT: Be minimal, and focus on E2E tests
   - IMPORTANT: Before pushing, verify 100% branch coverage on changed files by running
     `uv run --frozen pytest -x` (coverage is configured in `pyproject.toml` with `fail_under = 100`
     and `branch = true`). If any branch is uncovered, add a test for it before pushing.

- NEVER ever mention a `co-authored-by` or similar aspects. In particular, never
  mention the tool used to create the commit message or PR.

## Development Workflow When Updating the Repo *After* Generating Code

1. Make changes
  * Prefer using async functions when performing input/output to files or making network connections
  * Use the "aiofiles" package for async file interactions
2. Use pyright to check for any python type errors
```sh
uv tool run pyright
```
3. Always lint before committing
```sh
uv tool run ruff check --fix
```
