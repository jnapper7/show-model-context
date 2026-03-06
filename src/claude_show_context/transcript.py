"""JSONL transcript parsing and per-content-block categorization."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from claude_show_context.models import AppConfig, CategoryTokens
from claude_show_context.tokens import estimate_tokens

SKIP_TYPES = {"progress", "file-history-snapshot"}

JsonDict = dict[str, Any]


def _serialize_block(block: object) -> str:
    """Serialize a content block to text for token estimation."""
    if isinstance(block, str):
        return block
    if isinstance(block, dict):
        d = cast(JsonDict, block)
        text: object = d.get("text")
        if isinstance(text, str):
            return text
        tool_input: object = d.get("input")
        if tool_input is not None:
            return json.dumps(tool_input)
        return json.dumps(d)
    return str(block)


def _get_tool_use_id(block: object) -> str | None:
    """Extract tool_use_id from a tool_result block."""
    if not isinstance(block, dict):
        return None
    d = cast(JsonDict, block)
    if d.get("type") != "tool_result":
        return None
    tid: object = d.get("tool_use_id")
    return str(tid) if tid is not None else None


def _get_tool_name_from_block(block: object, tool_id_map: dict[str, str] | None = None) -> str | None:
    """Extract tool name from a tool_use or tool_result block.

    For tool_result blocks, looks up the name via tool_use_id in the provided map.
    """
    if not isinstance(block, dict):
        return None
    d = cast(JsonDict, block)
    block_type: object = d.get("type")
    if block_type == "tool_use":
        name: object = d.get("name")
        return str(name) if name is not None else None
    if block_type == "tool_result":
        # Try direct name field first (rare but possible)
        name = d.get("name")
        if name is not None:
            return str(name)
        # Look up via tool_use_id map
        if tool_id_map is not None:
            tid = _get_tool_use_id(cast(object, block))
            if tid is not None and tid in tool_id_map:
                return tool_id_map[tid]
        return None
    return None


def _get_block_content_type(block: object) -> str | None:
    """Get the content type of a block (text, thinking, tool_use, etc.)."""
    if isinstance(block, str):
        return "text"
    if isinstance(block, dict):
        d = cast(JsonDict, block)
        block_type: object = d.get("type")
        return str(block_type) if block_type is not None else None
    return None


def _match_category(
    block: object,
    entry_type: str,
    serialized: str,
    config: AppConfig,
    tool_name_context: str | None,
    tool_id_map: dict[str, str] | None = None,
) -> tuple[str, str]:
    """Match a content block to a category. Returns (name, color)."""
    block_content_type = _get_block_content_type(block)
    block_tool_name = _get_tool_name_from_block(block, tool_id_map)

    for cat in config.categories:
        if cat.match_type is not None and cat.match_type != entry_type:
            continue

        if cat.match_tools:
            effective_tool = block_tool_name or tool_name_context
            if "*" not in cat.match_tools and effective_tool not in cat.match_tools:
                continue

        if cat.match_content_types:
            if "*" not in cat.match_content_types and block_content_type not in cat.match_content_types:
                continue

        if cat.content_contains:
            if "*" not in cat.content_contains and not any(s in serialized for s in cat.content_contains):
                continue

        return cat.name, cat.color

    return "other", "dim"


def parse_transcript(transcript_path: str, config: AppConfig) -> list[CategoryTokens]:
    """Parse a JSONL transcript and categorize content blocks by token usage."""
    category_map: dict[str, CategoryTokens] = {}
    tool_id_map: dict[str, str] = {}

    if not transcript_path:
        return _finalize(category_map, config)

    path = Path(transcript_path)
    if not path.is_file():
        return _finalize(category_map, config)

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                raw: object = json.loads(line)
            except json.JSONDecodeError:
                continue

            if not isinstance(raw, dict):
                continue
            entry = cast(JsonDict, raw)

            entry_type: object = entry.get("type", "")
            if not isinstance(entry_type, str) or entry_type in SKIP_TYPES:
                continue

            msg_raw: object = entry.get("message")
            if not isinstance(msg_raw, dict):
                continue
            message = cast(JsonDict, msg_raw)

            content: object = message.get("content")
            if content is None:
                continue

            blocks: list[object]
            if isinstance(content, str):
                blocks = [content]
            elif isinstance(content, list):
                blocks = cast(list[object], content)
            else:
                continue

            last_tool_name: str | None = None

            for block in blocks:
                tool_name = _get_tool_name_from_block(block, tool_id_map)
                if isinstance(block, dict):
                    bd = cast(JsonDict, block)
                    # Register tool_use id→name for cross-entry lookup
                    if bd.get("type") == "tool_use" and tool_name:
                        last_tool_name = tool_name
                        tool_id: object = bd.get("id")
                        if isinstance(tool_id, str):
                            tool_id_map[tool_id] = tool_name

                is_tool_result = isinstance(block, dict) and cast(JsonDict, block).get("type") == "tool_result"
                tool_context = last_tool_name if is_tool_result else None

                serialized = _serialize_block(cast(object, block))
                tokens = estimate_tokens(serialized)

                cat_name, cat_color = _match_category(
                    cast(object, block), entry_type, serialized, config, tool_context, tool_id_map
                )

                if cat_name not in category_map:
                    category_map[cat_name] = CategoryTokens(name=cat_name, color=cat_color)
                category_map[cat_name].tokens += tokens

    return _finalize(category_map, config)


def _finalize(category_map: dict[str, CategoryTokens], config: AppConfig) -> list[CategoryTokens]:
    """Return categories in config order, with 'other' at the end."""
    result: list[CategoryTokens] = []
    for cat in config.categories:
        if cat.name in category_map:
            result.append(category_map.pop(cat.name))
    for ct in category_map.values():
        result.append(ct)
    return result
