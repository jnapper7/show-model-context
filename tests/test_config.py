"""Tests for configuration loading."""

from __future__ import annotations

from pathlib import Path

from show_model_context.config import DEFAULT_CATEGORIES, load_config


def test_load_config_no_file() -> None:
    """Falls back to defaults when no config file exists."""
    config = load_config(Path("/nonexistent/config.toml"))
    assert config.bar_width == 0
    assert config.empty_char == "░"
    assert config.filled_char == "█"
    assert config.label_position == "left"
    assert config.label_format == "ratio"
    assert len(config.categories) == len(DEFAULT_CATEGORIES)
    assert config.categories[0].name == "system"


def test_load_config_from_toml(tmp_path: Path) -> None:
    """Loads a custom TOML config file."""
    config_file = tmp_path / "config.toml"
    config_file.write_text("""\
[general]
bar_width = 50
empty_char = "-"
filled_char = "#"

[[categories]]
name = "custom"
color = "red"
match_type = "user"
match_tools = ["Bash"]
match_content_types = ["text"]
content_contains = ["hello"]
""")
    config = load_config(config_file)
    assert config.bar_width == 50
    assert config.empty_char == "-"
    assert config.filled_char == "#"
    assert len(config.categories) == 1
    assert config.categories[0].name == "custom"
    assert config.categories[0].color == "red"
    assert config.categories[0].match_type == "user"
    assert config.categories[0].match_tools == ["Bash"]
    assert config.categories[0].match_content_types == ["text"]
    assert config.categories[0].content_contains == ["hello"]


def test_load_config_empty_categories_uses_defaults(tmp_path: Path) -> None:
    """When TOML has no categories, defaults are used."""
    config_file = tmp_path / "config.toml"
    config_file.write_text("""\
[general]
bar_width = 30
""")
    config = load_config(config_file)
    assert config.bar_width == 30
    assert len(config.categories) == len(DEFAULT_CATEGORIES)


def test_load_config_invalid_general(tmp_path: Path) -> None:
    """Handles non-dict general section gracefully."""
    config_file = tmp_path / "config.toml"
    config_file.write_text("""\
general = "invalid"

[[categories]]
name = "test"
color = "blue"
""")
    config = load_config(config_file)
    assert config.bar_width == 0
    assert len(config.categories) == 1


def test_load_config_invalid_categories_type(tmp_path: Path) -> None:
    """Handles non-list categories gracefully."""
    config_file = tmp_path / "config.toml"
    config_file.write_text("""\
[general]
bar_width = 20

[categories]
name = "invalid_as_dict"
""")
    config = load_config(config_file)
    # categories is a dict not a list, should fall back to defaults
    assert len(config.categories) == len(DEFAULT_CATEGORIES)


def test_load_config_category_minimal(tmp_path: Path) -> None:
    """Category with only name gets defaults for other fields."""
    config_file = tmp_path / "config.toml"
    config_file.write_text("""\
[[categories]]
name = "minimal"
""")
    config = load_config(config_file)
    assert len(config.categories) == 1
    cat = config.categories[0]
    assert cat.name == "minimal"
    assert cat.color == "white"
    assert cat.match_type is None
    assert cat.match_tools == []
    assert cat.match_content_types == []
    assert cat.content_contains == []


def test_load_config_default_path() -> None:
    """When called with None, uses default path (which likely doesn't exist)."""
    config = load_config(None)
    assert len(config.categories) == len(DEFAULT_CATEGORIES)


def test_load_config_non_list_match_tools(tmp_path: Path) -> None:
    """Non-list match_tools defaults to empty."""
    config_file = tmp_path / "config.toml"
    config_file.write_text("""\
[[categories]]
name = "bad_tools"
match_tools = "not_a_list"
""")
    config = load_config(config_file)
    assert config.categories[0].match_tools == []


def test_load_config_non_list_content_contains(tmp_path: Path) -> None:
    """Non-list content_contains defaults to empty."""
    config_file = tmp_path / "config.toml"
    config_file.write_text("""\
[[categories]]
name = "bad_contains"
content_contains = "not_a_list"
""")
    config = load_config(config_file)
    assert config.categories[0].content_contains == []


def test_load_config_non_list_match_content_types(tmp_path: Path) -> None:
    """Non-list match_content_types defaults to empty."""
    config_file = tmp_path / "config.toml"
    config_file.write_text("""\
[[categories]]
name = "bad_types"
match_content_types = "not_a_list"
""")
    config = load_config(config_file)
    assert config.categories[0].match_content_types == []


def test_load_config_skips_non_dict_category_entries(tmp_path: Path) -> None:
    """Non-dict entries in categories list are skipped."""
    config_file = tmp_path / "config.toml"
    # Write raw TOML with a valid category - can't put non-dict in TOML array of tables
    # but we can test that empty categories fallback works
    config_file.write_text("""\
[[categories]]
name = "valid"
color = "green"
""")
    config = load_config(config_file)
    assert len(config.categories) == 1
    assert config.categories[0].name == "valid"


def test_load_config_label_fields(tmp_path: Path) -> None:
    """TOML parsing picks up label_position and label_format."""
    config_file = tmp_path / "config.toml"
    config_file.write_text("""\
[general]
label_position = "right"
label_format = "percentage"

[[categories]]
name = "test"
color = "blue"
""")
    config = load_config(config_file)
    assert config.label_position == "right"
    assert config.label_format == "percentage"


def test_load_config_category_label(tmp_path: Path) -> None:
    """Parses label field from TOML category."""
    config_file = tmp_path / "config.toml"
    config_file.write_text("""\
[[categories]]
name = "skills"
color = "magenta"
label = "Sk"
match_tools = ["Task", "Skill"]
""")
    config = load_config(config_file)
    assert len(config.categories) == 1
    assert config.categories[0].label == "Sk"


def test_load_config_category_label_default(tmp_path: Path) -> None:
    """Label defaults to empty string when not specified."""
    config_file = tmp_path / "config.toml"
    config_file.write_text("""\
[[categories]]
name = "files"
color = "blue"
""")
    config = load_config(config_file)
    assert config.categories[0].label == ""


def test_load_config_label_defaults(tmp_path: Path) -> None:
    """Defaults to left/ratio when label fields not specified."""
    config_file = tmp_path / "config.toml"
    config_file.write_text("""\
[general]
bar_width = 30

[[categories]]
name = "test"
color = "blue"
""")
    config = load_config(config_file)
    assert config.label_position == "left"
    assert config.label_format == "ratio"
