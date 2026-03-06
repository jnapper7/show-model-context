"""Tests for transcript parsing and categorization."""

from __future__ import annotations

import json
from pathlib import Path

from claude_show_context.models import AppConfig, CategoryConfig
from claude_show_context.transcript import _get_tool_name_from_block, _get_tool_use_id, parse_transcript
from tests.conftest import write_transcript


def _simple_config() -> AppConfig:
    return AppConfig(categories=[
        CategoryConfig(name="files", color="blue", match_tools=["Read"]),
        CategoryConfig(name="claude", color="green", match_type="assistant", match_content_types=["text"]),
        CategoryConfig(name="system", color="bright_black", match_type="user", content_contains=["<system-reminder>"]),
    ])


def test_parse_empty_transcript(tmp_path: Path) -> None:
    """Empty transcript returns no token counts."""
    path = tmp_path / "empty.jsonl"
    path.write_text("")
    result = parse_transcript(str(path), _simple_config())
    assert all(c.tokens == 0 for c in result)


def test_parse_nonexistent_transcript(tmp_path: Path) -> None:
    """Nonexistent file returns empty categories."""
    result = parse_transcript(str(tmp_path / "missing.jsonl"), _simple_config())
    assert len(result) == 0


def test_parse_assistant_text(tmp_path: Path) -> None:
    """Assistant text blocks are categorized as 'claude'."""
    path = tmp_path / "t.jsonl"
    write_transcript(path, [
        {"type": "assistant", "message": {"content": [{"type": "text", "text": "Hello world! This is a test."}]}},
    ])
    result = parse_transcript(str(path), _simple_config())
    claude_cats = [c for c in result if c.name == "claude"]
    assert len(claude_cats) == 1
    assert claude_cats[0].tokens > 0


def test_parse_tool_use(tmp_path: Path) -> None:
    """Tool use blocks are categorized by tool name."""
    path = tmp_path / "t.jsonl"
    write_transcript(path, [
        {
            "type": "assistant",
            "message": {
                "content": [
                    {"type": "tool_use", "name": "Read", "input": {"path": "/foo/bar.py"}},
                ],
            },
        },
    ])
    config = _simple_config()
    result = parse_transcript(str(path), config)
    files_cats = [c for c in result if c.name == "files"]
    assert len(files_cats) == 1
    assert files_cats[0].tokens > 0


def test_parse_tool_result_paired_with_use(tmp_path: Path) -> None:
    """Tool result in a separate entry is matched via tool_use_id (real transcript format)."""
    path = tmp_path / "t.jsonl"
    # Real Claude Code transcripts have tool_use in assistant entries
    # and tool_result in separate user entries, linked by tool_use_id
    write_transcript(path, [
        {
            "type": "assistant",
            "message": {
                "content": [
                    {"type": "tool_use", "id": "toolu_abc", "name": "Read", "input": {"path": "/foo"}},
                ],
            },
        },
        {
            "type": "user",
            "message": {
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_abc",
                        "content": "file contents here which is some text",
                    },
                ],
            },
        },
    ])
    config = _simple_config()
    result = parse_transcript(str(path), config)
    files_cats = [c for c in result if c.name == "files"]
    assert len(files_cats) == 1
    # Both the tool_use input AND the tool_result content should be counted as "files"
    assert files_cats[0].tokens > 0


def test_parse_tool_result_cross_entry_via_tool_use_id(tmp_path: Path) -> None:
    """Tool result in a separate entry is matched via tool_use_id from a prior tool_use entry."""
    path = tmp_path / "t.jsonl"
    write_transcript(path, [
        {
            "type": "assistant",
            "message": {
                "content": [
                    {"type": "tool_use", "id": "toolu_123", "name": "Read", "input": {"path": "/foo/bar.py"}},
                ],
            },
        },
        {
            "type": "user",
            "message": {
                "content": [
                    {"type": "tool_result", "tool_use_id": "toolu_123", "content": "file contents " * 20},
                ],
            },
        },
    ])
    config = _simple_config()
    result = parse_transcript(str(path), config)
    files_cats = [c for c in result if c.name == "files"]
    assert len(files_cats) == 1
    assert files_cats[0].tokens > 0


def test_parse_tool_result_cross_entry_bash(tmp_path: Path) -> None:
    """Bash tool_result in a separate entry is categorized as 'tools' via tool_use_id."""
    path = tmp_path / "t.jsonl"
    config = AppConfig(categories=[
        CategoryConfig(name="tools", color="yellow", match_tools=["Bash"]),
    ])
    write_transcript(path, [
        {
            "type": "assistant",
            "message": {
                "content": [
                    {"type": "tool_use", "id": "toolu_bash_1", "name": "Bash", "input": {"command": "ls"}},
                ],
            },
        },
        {
            "type": "user",
            "message": {
                "content": [
                    {"type": "tool_result", "tool_use_id": "toolu_bash_1", "content": "file1.py\nfile2.py\n"},
                ],
            },
        },
    ])
    result = parse_transcript(str(path), config)
    tools_cats = [c for c in result if c.name == "tools"]
    assert len(tools_cats) == 1
    assert tools_cats[0].tokens > 0


def test_parse_tool_result_unknown_id(tmp_path: Path) -> None:
    """Tool result with unrecognized tool_use_id falls through to other."""
    path = tmp_path / "t.jsonl"
    write_transcript(path, [
        {
            "type": "user",
            "message": {
                "content": [
                    {"type": "tool_result", "tool_use_id": "toolu_unknown", "content": "some result data"},
                ],
            },
        },
    ])
    config = AppConfig(categories=[
        CategoryConfig(name="files", color="blue", match_tools=["Read"]),
    ])
    result = parse_transcript(str(path), config)
    other = [c for c in result if c.name == "other"]
    assert len(other) == 1


def test_parse_system_reminder(tmp_path: Path) -> None:
    """Content containing system-reminder markers is categorized as system."""
    path = tmp_path / "t.jsonl"
    write_transcript(path, [
        {
            "type": "user",
            "message": {
                "content": [{"type": "text", "text": "Here is a <system-reminder>important</system-reminder> note."}],
            },
        },
    ])
    result = parse_transcript(str(path), _simple_config())
    system_cats = [c for c in result if c.name == "system"]
    assert len(system_cats) == 1
    assert system_cats[0].tokens > 0


def test_parse_skips_progress(tmp_path: Path) -> None:
    """Progress entries are skipped."""
    path = tmp_path / "t.jsonl"
    write_transcript(path, [
        {"type": "progress", "message": {"content": "loading..."}},
    ])
    result = parse_transcript(str(path), _simple_config())
    assert all(c.tokens == 0 for c in result)


def test_parse_skips_file_history_snapshot(tmp_path: Path) -> None:
    """file-history-snapshot entries are skipped."""
    path = tmp_path / "t.jsonl"
    write_transcript(path, [
        {"type": "file-history-snapshot", "message": {"content": "snapshot data"}},
    ])
    result = parse_transcript(str(path), _simple_config())
    assert all(c.tokens == 0 for c in result)


def test_parse_unmatched_goes_to_other(tmp_path: Path) -> None:
    """Entries that don't match any category go to 'other'."""
    path = tmp_path / "t.jsonl"
    write_transcript(path, [
        {
            "type": "user",
            "message": {
                "content": [{"type": "text", "text": "plain user message without system markers"}],
            },
        },
    ])
    config = AppConfig(categories=[
        CategoryConfig(name="claude", color="green", match_type="assistant"),
    ])
    result = parse_transcript(str(path), config)
    other_cats = [c for c in result if c.name == "other"]
    assert len(other_cats) == 1
    assert other_cats[0].tokens > 0


def test_parse_string_content(tmp_path: Path) -> None:
    """Content that is a plain string (not list) is handled."""
    path = tmp_path / "t.jsonl"
    write_transcript(path, [
        {"type": "assistant", "message": {"content": "just a string response text here"}},
    ])
    result = parse_transcript(str(path), _simple_config())
    claude_cats = [c for c in result if c.name == "claude"]
    assert len(claude_cats) == 1
    assert claude_cats[0].tokens > 0


def test_parse_invalid_json_lines(tmp_path: Path) -> None:
    """Invalid JSON lines are skipped."""
    path = tmp_path / "t.jsonl"
    path.write_text("not json\n{bad json}\n")
    result = parse_transcript(str(path), _simple_config())
    assert all(c.tokens == 0 for c in result)


def test_parse_non_dict_entry(tmp_path: Path) -> None:
    """Non-dict JSON lines are skipped."""
    path = tmp_path / "t.jsonl"
    path.write_text(json.dumps([1, 2, 3]) + "\n")
    result = parse_transcript(str(path), _simple_config())
    assert all(c.tokens == 0 for c in result)


def test_parse_entry_no_message(tmp_path: Path) -> None:
    """Entries without a message field are skipped."""
    path = tmp_path / "t.jsonl"
    write_transcript(path, [{"type": "user"}])
    result = parse_transcript(str(path), _simple_config())
    assert all(c.tokens == 0 for c in result)


def test_parse_message_no_content(tmp_path: Path) -> None:
    """Messages without content are skipped."""
    path = tmp_path / "t.jsonl"
    write_transcript(path, [{"type": "user", "message": {"role": "user"}}])
    result = parse_transcript(str(path), _simple_config())
    assert all(c.tokens == 0 for c in result)


def test_parse_message_non_dict(tmp_path: Path) -> None:
    """Entries with non-dict message are skipped."""
    path = tmp_path / "t.jsonl"
    write_transcript(path, [{"type": "user", "message": "not a dict"}])
    result = parse_transcript(str(path), _simple_config())
    assert all(c.tokens == 0 for c in result)


def test_parse_content_non_string_non_list(tmp_path: Path) -> None:
    """Entries with content that is neither string nor list are skipped."""
    path = tmp_path / "t.jsonl"
    write_transcript(path, [{"type": "user", "message": {"content": 42}}])
    result = parse_transcript(str(path), _simple_config())
    assert all(c.tokens == 0 for c in result)


def test_parse_entry_no_type(tmp_path: Path) -> None:
    """Entries without type field are handled (empty string type, not skipped)."""
    path = tmp_path / "t.jsonl"
    write_transcript(path, [{"message": {"content": "text"}}])
    result = parse_transcript(str(path), _simple_config())
    # Empty type doesn't match any skip types, so it gets processed
    # but likely doesn't match any category
    other = [c for c in result if c.name == "other"]
    assert len(other) == 1


def test_parse_blank_lines_skipped(tmp_path: Path) -> None:
    """Blank lines in JSONL are skipped."""
    path = tmp_path / "t.jsonl"
    path.write_text("\n\n\n")
    result = parse_transcript(str(path), _simple_config())
    assert all(c.tokens == 0 for c in result)


def test_parse_tool_result_without_preceding_tool_use(tmp_path: Path) -> None:
    """Tool result without a preceding tool_use has no tool context."""
    path = tmp_path / "t.jsonl"
    write_transcript(path, [
        {
            "type": "user",
            "message": {
                "content": [
                    {"type": "tool_result", "content": "result text content here"},
                ],
            },
        },
    ])
    config = AppConfig(categories=[
        CategoryConfig(name="files", color="blue", match_tools=["Read"]),
    ])
    result = parse_transcript(str(path), config)
    # No tool context, won't match "files", goes to "other"
    other = [c for c in result if c.name == "other"]
    assert len(other) == 1


def test_parse_entry_type_non_string(tmp_path: Path) -> None:
    """Entry with non-string type is skipped."""
    path = tmp_path / "t.jsonl"
    path.write_text(json.dumps({"type": 42, "message": {"content": "text"}}) + "\n")
    result = parse_transcript(str(path), _simple_config())
    assert all(c.tokens == 0 for c in result)


def test_parse_non_dict_non_str_block(tmp_path: Path) -> None:
    """Non-dict, non-str block in content list hits fallback serialization."""
    path = tmp_path / "t.jsonl"
    # Manually write a line with a list block containing a number
    entry = {"type": "user", "message": {"content": [42]}}
    path.write_text(json.dumps(entry) + "\n")
    config = AppConfig(categories=[])
    result = parse_transcript(str(path), config)
    other = [c for c in result if c.name == "other"]
    assert len(other) == 1


def test_parse_content_type_mismatch_continues(tmp_path: Path) -> None:
    """Category with match_content_types skips blocks that don't match type."""
    path = tmp_path / "t.jsonl"
    write_transcript(path, [
        {
            "type": "assistant",
            "message": {
                "content": [{"type": "thinking", "text": "I am thinking about this"}],
            },
        },
    ])
    # Category requires "text" content type, but block is "thinking"
    config = AppConfig(categories=[
        CategoryConfig(name="text_only", color="green", match_type="assistant", match_content_types=["text"]),
    ])
    result = parse_transcript(str(path), config)
    # "thinking" doesn't match "text", so it goes to "other"
    other = [c for c in result if c.name == "other"]
    assert len(other) == 1
    assert other[0].tokens > 0


def test_parse_content_contains_no_match(tmp_path: Path) -> None:
    """Category with content_contains skips blocks that don't contain any substring."""
    path = tmp_path / "t.jsonl"
    write_transcript(path, [
        {
            "type": "user",
            "message": {
                "content": [{"type": "text", "text": "normal user text without any special markers"}],
            },
        },
    ])
    config = AppConfig(categories=[
        CategoryConfig(name="system", color="bright_black", match_type="user", content_contains=["<system-reminder>"]),
    ])
    result = parse_transcript(str(path), config)
    # Doesn't contain "<system-reminder>", so goes to other
    other = [c for c in result if c.name == "other"]
    assert len(other) == 1
    assert other[0].tokens > 0


def test_parse_dict_block_no_text_no_input(tmp_path: Path) -> None:
    """Dict block without text or input field falls back to json.dumps of the block."""
    path = tmp_path / "t.jsonl"
    write_transcript(path, [
        {
            "type": "assistant",
            "message": {
                "content": [{"type": "unknown_type", "data": "some data here"}],
            },
        },
    ])
    config = AppConfig(categories=[])
    result = parse_transcript(str(path), config)
    other = [c for c in result if c.name == "other"]
    assert len(other) == 1
    assert other[0].tokens > 0


def test_parse_dict_block_no_type(tmp_path: Path) -> None:
    """Dict block without a type field returns None for content type."""
    path = tmp_path / "t.jsonl"
    write_transcript(path, [
        {
            "type": "user",
            "message": {
                "content": [{"text": "text without type field on the block"}],
            },
        },
    ])
    config = AppConfig(categories=[
        CategoryConfig(name="needs_type", color="green", match_content_types=["text"]),
    ])
    result = parse_transcript(str(path), config)
    # Block has no type, so match_content_types check fails
    other = [c for c in result if c.name == "other"]
    assert len(other) == 1


def test_parse_empty_path() -> None:
    """Empty transcript path returns empty."""
    config = AppConfig(categories=[])
    result = parse_transcript("", config)
    assert result == []


def test_parse_directory_path(tmp_path: Path) -> None:
    """Path that is a directory (not a file) returns empty."""
    config = AppConfig(categories=[])
    result = parse_transcript(str(tmp_path), config)
    assert result == []


def test_get_tool_use_id_non_dict() -> None:
    """_get_tool_use_id returns None for non-dict blocks."""
    assert _get_tool_use_id("not a dict") is None


def test_get_tool_use_id_non_tool_result() -> None:
    """_get_tool_use_id returns None for non-tool_result blocks."""
    assert _get_tool_use_id({"type": "tool_use", "id": "123"}) is None


def test_get_tool_name_tool_result_with_direct_name() -> None:
    """tool_result with a direct name field uses it."""
    block = {"type": "tool_result", "name": "Read", "content": "data"}
    assert _get_tool_name_from_block(block) == "Read"


def test_get_tool_name_tool_result_no_map() -> None:
    """tool_result without name and no map returns None."""
    block = {"type": "tool_result", "tool_use_id": "toolu_1", "content": "data"}
    assert _get_tool_name_from_block(block, None) is None


def test_parse_tool_result_with_direct_name(tmp_path: Path) -> None:
    """tool_result with a direct name field is categorized correctly."""
    path = tmp_path / "t.jsonl"
    write_transcript(path, [
        {
            "type": "user",
            "message": {
                "content": [
                    {"type": "tool_result", "name": "Read", "content": "file contents here for testing"},
                ],
            },
        },
    ])
    config = _simple_config()
    result = parse_transcript(str(path), config)
    files_cats = [c for c in result if c.name == "files"]
    assert len(files_cats) == 1
    assert files_cats[0].tokens > 0


def test_wildcard_match_tools(tmp_path: Path) -> None:
    """match_tools with '*' matches any tool."""
    path = tmp_path / "t.jsonl"
    write_transcript(path, [
        {
            "type": "assistant",
            "message": {
                "content": [
                    {"type": "tool_use", "id": "t1", "name": "SomeRandomTool", "input": {"x": 1}},
                ],
            },
        },
    ])
    config = AppConfig(categories=[
        CategoryConfig(name="all_tools", color="yellow", match_tools=["*"]),
    ])
    result = parse_transcript(str(path), config)
    matched = [c for c in result if c.name == "all_tools"]
    assert len(matched) == 1
    assert matched[0].tokens > 0


def test_wildcard_match_content_types(tmp_path: Path) -> None:
    """match_content_types with '*' matches any content block type."""
    path = tmp_path / "t.jsonl"
    write_transcript(path, [
        {
            "type": "assistant",
            "message": {
                "content": [{"type": "thinking", "text": "deep thoughts about the universe"}],
            },
        },
    ])
    config = AppConfig(categories=[
        CategoryConfig(name="everything", color="cyan", match_type="assistant", match_content_types=["*"]),
    ])
    result = parse_transcript(str(path), config)
    matched = [c for c in result if c.name == "everything"]
    assert len(matched) == 1
    assert matched[0].tokens > 0


def test_wildcard_content_contains(tmp_path: Path) -> None:
    """content_contains with '*' matches any content."""
    path = tmp_path / "t.jsonl"
    write_transcript(path, [
        {
            "type": "user",
            "message": {
                "content": [{"type": "text", "text": "just a normal message"}],
            },
        },
    ])
    config = AppConfig(categories=[
        CategoryConfig(name="catch_all", color="white", match_type="user", content_contains=["*"]),
    ])
    result = parse_transcript(str(path), config)
    matched = [c for c in result if c.name == "catch_all"]
    assert len(matched) == 1
    assert matched[0].tokens > 0


def test_wildcard_does_not_bypass_other_matchers(tmp_path: Path) -> None:
    """Wildcard in one field doesn't bypass other field checks."""
    path = tmp_path / "t.jsonl"
    write_transcript(path, [
        {
            "type": "user",
            "message": {
                "content": [{"type": "text", "text": "user message"}],
            },
        },
    ])
    # match_tools=["*"] but match_type="assistant" — won't match a user entry
    config = AppConfig(categories=[
        CategoryConfig(name="nope", color="red", match_type="assistant", match_tools=["*"]),
    ])
    result = parse_transcript(str(path), config)
    other = [c for c in result if c.name == "other"]
    assert len(other) == 1
