"""Tests for configuration MCP tools."""

from __future__ import annotations

from pathlib import Path

import pytest

from ot2_cherrypick_mcp.tools.config_tools import (
    apply_liquid_preset,
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
    """Updating a scalar value writes the new content and backup."""

    settings_copy = _copy_settings(tmp_path)
    result = update_settings_value(
        path="settings.general.tip_reuse",
        value='"never"',
        settings_path=str(settings_copy),
    )

    assert result["old_value"] == "always"
    assert result["new_value"] == "never"

    updated_text = settings_copy.read_text(encoding="utf-8")
    assert 'tip_reuse = "never"' in updated_text

    backup_path = Path(result["backup_file"])
    assert backup_path.exists()


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


def test_list_settings_values_returns_flattened_entries(tmp_path: Path) -> None:
    """Listing settings returns both nested data and flattened paths."""

    settings_copy = _copy_settings(tmp_path)
    result = list_settings_values(settings_path=str(settings_copy))

    assert result["settings_file"] == str(settings_copy)
    assert result["total_entries"] > 0

    entries = {entry["path"]: entry["value"] for entry in result["entries"]}
    assert entries["settings.general.tip_reuse"] == "always"
    assert entries["settings.liquid_handling.push_out.enabled"] is True

    data = result["data"]
    assert data["settings"]["general"]["head_speed"]["speed"] == 400


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
    assert 'push_out = { enabled = true, volume_ul = 5 }' in updated_text

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
