"""Tests for labware MCP tools."""

from __future__ import annotations

from pathlib import Path

import pytest

from ot2_cherrypick_mcp.tools.labware_tools import add_labware_definition
from ot2_cherrypick_mcp.utils.errors import ConfigurationError


def _copy_labware(tmp_path: Path) -> Path:
    repo_root = Path(__file__).resolve().parents[1]
    source = repo_root / "labware_dict.toml"
    destination = tmp_path / "labware_dict.toml"
    destination.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    return destination


def test_add_labware_definition_appends_entry(tmp_path: Path) -> None:
    """Adding labware appends a new table and creates a backup."""

    labware_copy = _copy_labware(tmp_path)
    result = add_labware_definition(
        labware_id="custom_plate_96",
        category="plate",
        well_count=96,
        well_volume=200,
        offset_x=0.1,
        labware_path=str(labware_copy),
    )

    assert result["labware_id"] == "custom_plate_96"

    updated_text = labware_copy.read_text(encoding="utf-8")
    assert 'labware_id = "custom_plate_96"' in updated_text
    assert "offset_x = 0.1" in updated_text

    backup_path = Path(result["backup_file"])
    assert backup_path.exists()


def test_add_labware_definition_duplicate_id_errors(tmp_path: Path) -> None:
    """Duplicate labware IDs raise configuration errors."""

    labware_copy = _copy_labware(tmp_path)
    with pytest.raises(ConfigurationError):
        add_labware_definition(
            labware_id="tip_rack_yellow_100ul",
            category="tip_rack",
            well_count=96,
            well_volume=100,
            labware_path=str(labware_copy),
        )
