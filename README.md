# claude-show-context

A CLI tool that displays a colored terminal bar showing Claude Code context window usage, broken down by configurable categories.

```
45K / 200K ██████████████░░░░░░░░░░░░░░░░░░░░░░░░░░
```

The filled portion is multi-colored, with each color representing a category of context usage (system prompts, files, tools, skills, Claude responses).

## How It Works

`claude-show-context` integrates with Claude Code's [statusLine](https://docs.anthropic.com/en/docs/claude-code) setting. After each assistant message, Claude Code sends a JSON payload on stdin containing the transcript path and token usage. This tool:

1. Reads the session transcript (JSONL) and categorizes each content block
2. Estimates token usage per category (chars / 4)
3. Scales proportionally to match the actual token counts from Claude Code
4. Renders a colored ANSI bar to stdout, which Claude Code displays in its status area

## Installation

Requires Python 3.11+.

```bash
# Clone the repository
git clone https://github.com/your-org/claude-show-context.git
cd claude-show-context

# Install with uv
uv sync
```

Or install directly:

```bash
uv tool install git+https://github.com/your-org/claude-show-context.git
```

## Claude Code Setup

Add the following to your Claude Code settings (`.claude/settings.json` or `~/.claude/settings.json`):

```json
{
  "statusLine": {
    "type": "command",
    "command": "uv tool run claude-show-context --mode total"
  }
}
```

## Usage

```
claude-show-context [--config PATH] [--mode total|current]
```

| Flag | Description |
|---|---|
| `--config PATH` | Path to a TOML config file (default: `~/.config/claude-show-context/config.toml`) |
| `--mode total` | 100% = model's max context window (e.g. 200K). Shows how full the window is. |
| `--mode current` | 100% = current tokens used. Shows category proportions only. |

The tool reads JSON from stdin and writes a single line to stdout.

## Display Modes

**Total mode** (default) -- shows usage relative to the full context window:

```
45K / 200K ██████████████░░░░░░░░░░░░░░░░░░░░░░░░░░
           ^^^^^^^^^^^^^ ^^^^^^^^^^^^^^^^^^^^^^^^^
           filled (used)  empty (remaining)
```

**Current mode** -- shows category proportions within the used portion:

```
45K / 45K ████████████████████████████████████████
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
          all filled, colored by category
```

## Default Categories

| Category | Color | What it matches |
|---|---|---|
| system | gray | User messages containing `<system-reminder>`, `CLAUDE.md`, `<local-command-` |
| files | blue | Tool calls to `Read`, `Write`, `Edit` |
| tools | yellow | Tool calls to `Bash`, `Glob`, `Grep`, `WebFetch`, `WebSearch` |
| skills | magenta | Tool calls to `Task`, `Skill` |
| claude | green | Assistant `text` and `thinking` blocks |
| other | dim | Anything that doesn't match the above |

Categories are checked in order; first match wins.

## Configuration

Optionally create `~/.config/claude-show-context/config.toml` (or pass `--config`). See [`config.example.toml`](config.example.toml) for all options.

```toml
[general]
bar_width = 0             # 0 = auto-detect from terminal width; >0 = fixed character count
empty_char = "░"      # character for unfilled portion
filled_char = "█"     # character for filled portion
label_position = "left"   # "left" or "right"
label_format = "ratio"    # "ratio", "percentage", or "legend"

[[categories]]
name = "system"
color = "bright_black"
match_type = "user"                    # match transcript entry type
content_contains = ["<system-reminder>", "CLAUDE.md"]  # substring match

[[categories]]
name = "files"
color = "blue"
match_tools = ["Read", "Write", "Edit"]  # match tool_use/tool_result by name

[[categories]]
name = "claude"
color = "green"
match_type = "assistant"
match_content_types = ["text", "thinking"]  # match content block type
```

### Category Matching Rules

Each category can use one or more of these matchers (all specified matchers must pass):

| Matcher | Description |
|---|---|
| `match_type` | Match the transcript entry's `type` field (`user` or `assistant`) |
| `match_tools` | Match `tool_use` blocks by tool name, or `tool_result` blocks paired with a preceding `tool_use` |
| `match_content_types` | Match content block `type` (`text`, `thinking`, `tool_use`, etc.) |
| `content_contains` | Match if serialized content contains any of the listed substrings |

### Wildcards

Any list matcher (`match_tools`, `match_content_types`, `content_contains`) supports `"*"` as a wildcard that matches anything. This is useful for catch-all categories at the end of the list:

```toml
# Catch any tool not matched by earlier categories
[[categories]]
name = "tools"
color = "yellow"
match_tools = ["*"]

# Match all assistant output regardless of content block type
[[categories]]
name = "claude"
color = "green"
match_type = "assistant"
match_content_types = ["*"]
```

The wildcard only applies to the field it's in — other matchers on the same category still apply normally. For example, `match_type = "assistant"` with `match_tools = ["*"]` will only match assistant entries that contain tool blocks.

### Available Colors

`black`, `red`, `green`, `yellow`, `blue`, `magenta`, `cyan`, `white`, and bright variants (`bright_black`, `bright_red`, etc.), plus `dim`.

## Development

```bash
# Install dependencies
uv sync

# Run tests (100% branch coverage required)
uv run --frozen pytest -x

# Type checking
uv tool run pyright

# Linting
uv tool run ruff check --fix
```

## License

MIT
