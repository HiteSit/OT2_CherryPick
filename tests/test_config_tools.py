"""Tests for configuration MCP tools."""

from __future__ import annotations

from pathlib import Path

import pytest

from ot2_cherrypick_mcp.tools.config_tools import (
    apply_liquid_preset,
    batch_update_settings,
    list_settings_values,
    update_settings_value,
)
from ot2_cherrypick_mcp.utils.errors import ConfigurationError


def _copy_settings(tmp_path: Path) -> Path:
    repo_root = Path(__file__).resolve().parents[1]
    source = repo_root / "settings.toml"
    destination = tmp_path / "settings.toml"
    destination.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    return destination


def test_update_settings_value_overrides_scalar(tmp_path: Path) -> None:
    """Updating an existing scalar value writes the new content and backup."""

    settings_copy = _copy_settings(tmp_path)
    result = update_settings_value(
        path="settings.general.mode",
        value='"single_X1"',
        settings_path=str(settings_copy),
    )

    assert result["old_value"] == "multi"
    assert result["new_value"] == "single_X1"

    updated_text = settings_copy.read_text(encoding="utf-8")
    assert 'mode = "single_X1"' in updated_text

    backup_path = Path(result["backup_file"])
    assert backup_path.exists()


def test_update_settings_autocreates_missing_aliased_key(tmp_path: Path) -> None:
    """Known alias targets are auto-created when missing from the TOML file."""

    settings_copy = _copy_settings(tmp_path)
    # protocol_name exists in the template settings.toml with an empty default
    result = update_settings_value(
        path="settings.general.protocol_name",
        value='"MyProtocol"',
        settings_path=str(settings_copy),
    )

    assert result["old_value"] == ""
    assert result["new_value"] == "MyProtocol"
    assert result["path"] == "settings.general.protocol_name"

    updated_text = settings_copy.read_text(encoding="utf-8")
    assert 'protocol_name = "MyProtocol"' in updated_text


def test_update_settings_shorthand_alias(tmp_path: Path) -> None:
    """Shorthand aliases resolve to their full dotted path."""

    settings_copy = _copy_settings(tmp_path)
    result = update_settings_value(
        path="mode",
        value='"multi"',
        settings_path=str(settings_copy),
    )

    assert result["path"] == "settings.general.mode"
    assert result["new_value"] == "multi"

    updated_text = settings_copy.read_text(encoding="utf-8")
    assert 'mode = "multi"' in updated_text


def test_update_settings_value_handles_numbers(tmp_path: Path) -> None:
    """Numeric literals are parsed correctly."""

    settings_copy = _copy_settings(tmp_path)
    result = update_settings_value(
        path="settings.general.head_speed.speed",
        value="450",
        settings_path=str(settings_copy),
    )

    assert result["old_value"] == 400
    assert result["new_value"] == 450

    updated_text = settings_copy.read_text(encoding="utf-8")
    assert "speed = 450" in updated_text


def test_update_settings_invalid_path_errors(tmp_path: Path) -> None:
    """Invalid dotted paths raise configuration errors."""

    settings_copy = _copy_settings(tmp_path)
    with pytest.raises(ConfigurationError):
        update_settings_value(
            path="settings.missing.section",
            value="false",
            settings_path=str(settings_copy),
        )


def test_update_settings_position_rack_coerces_to_string(tmp_path: Path) -> None:
    """Working plate position_rack values are always stored as strings."""

    settings_copy = _copy_settings(tmp_path)

    result = update_settings_value(
        path="settings.working_plate[0].position_rack",
        value="4",
        settings_path=str(settings_copy),
    )

    assert result["new_value"] == "4"

    text = settings_copy.read_text(encoding="utf-8")
    assert 'position_rack = "4"' in text


def test_list_settings_values_returns_flattened_entries(tmp_path: Path) -> None:
    """Listing settings returns both nested data and flattened paths."""

    settings_copy = _copy_settings(tmp_path)
    result = list_settings_values(settings_path=str(settings_copy))

    assert result["settings_file"] == str(settings_copy)
    assert result["total_entries"] > 0

    entries = {entry["path"]: entry["value"] for entry in result["entries"]}
    assert entries["settings.general.mode"] == "multi"
    assert entries["settings.liquid_handling.push_out.enabled"] is True

    data = result["data"]
    assert data["settings"]["general"]["head_speed"]["speed"] == 400


def test_batch_update_settings_applies_multiple_changes(tmp_path: Path) -> None:
    """Batch update applies all changes in a single atomic write."""

    settings_copy = _copy_settings(tmp_path)
    result = batch_update_settings(
        updates=[
            {"path": "mode", "value": '"single_X1"'},
            {"path": "speed", "value": "250"},
            {"path": "push_out", "value": "false"},
        ],
        settings_path=str(settings_copy),
    )

    assert result["count"] == 3
    updates = result["updates"]

    assert updates[0]["path"] == "settings.general.mode"
    assert updates[0]["old_value"] == "multi"
    assert updates[0]["new_value"] == "single_X1"

    assert updates[1]["path"] == "settings.general.head_speed.speed"
    assert updates[1]["old_value"] == 400
    assert updates[1]["new_value"] == 250

    assert updates[2]["path"] == "settings.liquid_handling.push_out.enabled"
    assert updates[2]["old_value"] is True
    assert updates[2]["new_value"] is False

    # Verify single backup file was created
    backup_path = Path(result["backup_file"])
    assert backup_path.exists()

    # Verify all changes are in the file
    text = settings_copy.read_text(encoding="utf-8")
    assert 'mode = "single_X1"' in text
    assert "speed = 250" in text
    assert "enabled = false" in text or "push_out" in text


def test_batch_update_settings_atomic_on_error(tmp_path: Path) -> None:
    """If any path fails, no changes are written."""

    settings_copy = _copy_settings(tmp_path)
    original_text = settings_copy.read_text(encoding="utf-8")

    with pytest.raises(ConfigurationError):
        batch_update_settings(
            updates=[
                {"path": "mode", "value": '"single_X1"'},
                {"path": "totally.bogus.path", "value": "42"},
            ],
            settings_path=str(settings_copy),
        )

    # File should be unchanged
    assert settings_copy.read_text(encoding="utf-8") == original_text


def test_batch_update_settings_position_rack_string(tmp_path: Path) -> None:
    """Working plate position_rack values stay as strings in batch mode."""

    settings_copy = _copy_settings(tmp_path)
    result = batch_update_settings(
        updates=[
            {"path": "settings.working_plate[0].position_rack", "value": "7"},
        ],
        settings_path=str(settings_copy),
    )

    assert result["updates"][0]["new_value"] == "7"
    text = settings_copy.read_text(encoding="utf-8")
    assert 'position_rack = "7"' in text


def test_apply_liquid_preset_updates_multiple_sections(tmp_path: Path) -> None:
    """Applying a preset copies all preset values into active configuration."""

    settings_copy = _copy_settings(tmp_path)

    result = apply_liquid_preset(
        preset_name="viscous",
        settings_path=str(settings_copy),
    )

    change_paths = {change["path"] for change in result["changes"]}
    assert "settings.liquid_handling.pre_aspirate_contact" in change_paths
    assert "settings.liquid_handling.delays" in change_paths

    updated_text = settings_copy.read_text(encoding="utf-8")
    assert 'post_aspirate = 2.0' in updated_text
    assert '{ enabled = true, volume_ul = 5 }' in updated_text

    backup_path = Path(result["backup_file"])
    assert backup_path.exists()
    backup_content = backup_path.read_text(encoding="utf-8")
    assert 'post_aspirate = 0' in backup_content


def test_apply_liquid_preset_missing_name_errors(tmp_path: Path) -> None:
    """Unknown preset names raise configuration errors."""

    settings_copy = _copy_settings(tmp_path)
    with pytest.raises(ConfigurationError):
        apply_liquid_preset(
            preset_name="does_not_exist",
            settings_path=str(settings_copy),
        )
