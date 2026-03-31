"""Tests for configuration MCP tools."""

from __future__ import annotations

from pathlib import Path

import pytest

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore[no-redef]

from ot2_cherrypick_mcp.tools.config_tools import (
    _is_default_deck,
    add_deck_entry,
    apply_liquid_preset,
    batch_update_settings,
    clear_deck,
    list_settings_values,
    remove_deck_entry,
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


# ── Deck manipulation tests ─────────────────────────────────────────────


def test_add_deck_entry_basic(tmp_path: Path) -> None:
    settings = _copy_settings(tmp_path)
    result = add_deck_entry(
        entry_type="reservoir",
        labware_id="my_plate_96",
        position_rack="6",
        settings_path=str(settings),
    )
    assert result["status"] == "success"
    assert result["added"]["labware_id"] == "my_plate_96"
    with open(settings, "rb") as f:
        doc = tomllib.load(f)
    slots = [p["position_rack"] for p in doc["settings"]["working_plate"]]
    assert "6" in slots


def test_add_deck_entry_auto_clears_default(tmp_path: Path) -> None:
    settings = _copy_settings(tmp_path)
    with open(settings, "rb") as f:
        before = tomllib.load(f)
    assert len(before["settings"]["working_plate"]) == 7

    result = add_deck_entry(
        entry_type="reservoir",
        labware_id="my_plate_96",
        position_rack="2",
        settings_path=str(settings),
    )
    assert result["auto_cleared_default"] is True

    with open(settings, "rb") as f:
        after = tomllib.load(f)
    assert len(after["settings"]["working_plate"]) == 1
    assert after["settings"]["working_plate"][0]["labware_id"] == "my_plate_96"


def test_add_deck_entry_no_auto_clear_after_first_edit(tmp_path: Path) -> None:
    settings = _copy_settings(tmp_path)
    add_deck_entry(
        entry_type="reservoir", labware_id="plate_a", position_rack="2",
        settings_path=str(settings),
    )
    result = add_deck_entry(
        entry_type="tip", labware_id="tiprack_300", position_rack="1",
        connection="Pipette_8", mode="multi_X1",
        settings_path=str(settings),
    )
    assert result["auto_cleared_default"] is False
    with open(settings, "rb") as f:
        doc = tomllib.load(f)
    assert len(doc["settings"]["working_plate"]) == 2


def test_add_deck_entry_rejects_occupied_slot(tmp_path: Path) -> None:
    settings = _copy_settings(tmp_path)
    add_deck_entry(
        entry_type="reservoir", labware_id="plate_a", position_rack="2",
        settings_path=str(settings),
    )
    with pytest.raises(ConfigurationError, match="already occupied"):
        add_deck_entry(
            entry_type="reservoir", labware_id="plate_b", position_rack="2",
            settings_path=str(settings),
        )


def test_add_deck_entry_tip_fields(tmp_path: Path) -> None:
    settings = _copy_settings(tmp_path)
    add_deck_entry(
        entry_type="tip", labware_id="tiprack_300", position_rack="1",
        connection="Pipette_8", mode="multi",
        settings_path=str(settings),
    )
    with open(settings, "rb") as f:
        doc = tomllib.load(f)
    tip_entry = doc["settings"]["working_plate"][-1]
    assert tip_entry["connection"] == "Pipette_8"
    assert tip_entry["mode"] == "multi"


def test_add_deck_entry_offset_fields(tmp_path: Path) -> None:
    settings = _copy_settings(tmp_path)
    add_deck_entry(
        entry_type="reservoir", labware_id="plate_a", position_rack="2",
        offset_x=-0.5, offset_y=0.8, offset_z=-0.3,
        settings_path=str(settings),
    )
    with open(settings, "rb") as f:
        doc = tomllib.load(f)
    entry = doc["settings"]["working_plate"][-1]
    assert entry["offset_x"] == -0.5
    assert entry["offset_y"] == 0.8
    assert entry["offset_z"] == -0.3


def test_remove_deck_entry_by_slot(tmp_path: Path) -> None:
    settings = _copy_settings(tmp_path)
    result = remove_deck_entry(position_rack="2", settings_path=str(settings))
    assert result["status"] == "success"
    assert result["removed"]["labware_id"] == "384_ppv_55ul"
    with open(settings, "rb") as f:
        doc = tomllib.load(f)
    slots = [p["position_rack"] for p in doc["settings"]["working_plate"]]
    assert "2" not in slots


def test_remove_deck_entry_missing_slot(tmp_path: Path) -> None:
    settings = _copy_settings(tmp_path)
    with pytest.raises(ConfigurationError, match="No working_plate entry"):
        remove_deck_entry(position_rack="99", settings_path=str(settings))


def test_clear_deck(tmp_path: Path) -> None:
    settings = _copy_settings(tmp_path)
    result = clear_deck(settings_path=str(settings))
    assert result["entries_removed"] == 7
    with open(settings, "rb") as f:
        doc = tomllib.load(f)
    # tomlkit removes the key entirely when array is emptied
    assert doc["settings"].get("working_plate", []) == []


def test_clear_deck_already_empty(tmp_path: Path) -> None:
    settings = _copy_settings(tmp_path)
    clear_deck(settings_path=str(settings))
    result = clear_deck(settings_path=str(settings))
    assert result["entries_removed"] == 0


def test_is_default_deck_true_on_template(tmp_path: Path) -> None:
    settings = _copy_settings(tmp_path)
    assert _is_default_deck(settings) is True


def test_is_default_deck_false_after_edit(tmp_path: Path) -> None:
    settings = _copy_settings(tmp_path)
    remove_deck_entry(position_rack="2", settings_path=str(settings))
    assert _is_default_deck(settings) is False
