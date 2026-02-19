"""Tests for labware MCP tools."""

from __future__ import annotations

from pathlib import Path
from datetime import date

import pytest
import tomlkit

from ot2_cherrypick_mcp.tools.labware_tools import update_labware_offset


def _make_offset_db(tmp_path: Path) -> Path:
    """Create an empty offset_database.toml in tmp_path."""
    db_path = tmp_path / "offset_database.toml"
    db_path.write_text("", encoding="utf-8")
    return db_path


def test_update_labware_offset_creates_new_entry(tmp_path: Path) -> None:
    """update_labware_offset creates a new entry when none exists."""

    db_path = _make_offset_db(tmp_path)
    result = update_labware_offset(
        labware_id="nest_96_wellplate_200ul_flat",
        position_rack="4",
        offset_x=-0.5,
        offset_y=0.8,
        offset_z=-0.3,
        offset_db_path=str(db_path),
    )

    assert result["labware_id"] == "nest_96_wellplate_200ul_flat"
    assert result["position_rack"] == "4"
    assert result["action"] == "created"

    content = db_path.read_text(encoding="utf-8")
    assert 'labware_id = "nest_96_wellplate_200ul_flat"' in content
    assert "offset_x = -0.5" in content
    assert "offset_y = 0.8" in content
    assert "offset_z = -0.3" in content
    assert date.today().isoformat() in content


def test_update_labware_offset_updates_existing_entry(tmp_path: Path) -> None:
    """update_labware_offset updates an existing entry."""

    db_path = _make_offset_db(tmp_path)

    # Create initial entry
    update_labware_offset(
        labware_id="my_plate",
        position_rack="2",
        offset_x=0.1,
        offset_y=0.2,
        offset_z=0.3,
        offset_db_path=str(db_path),
    )

    # Update it
    result = update_labware_offset(
        labware_id="my_plate",
        position_rack="2",
        offset_x=1.0,
        offset_y=2.0,
        offset_z=3.0,
        offset_db_path=str(db_path),
    )

    assert result["action"] == "updated"

    # Verify only one entry exists
    content = db_path.read_text(encoding="utf-8")
    doc = tomlkit.loads(content)
    entries = doc.get("offsets", [])
    matching = [e for e in entries if e["labware_id"] == "my_plate" and str(e["position_rack"]) == "2"]
    assert len(matching) == 1
    assert matching[0]["offset_x"] == 1.0


def test_update_labware_offset_creates_db_file_if_missing(tmp_path: Path) -> None:
    """update_labware_offset creates the database file if it does not exist."""

    db_path = tmp_path / "new_offset_database.toml"
    assert not db_path.exists()

    result = update_labware_offset(
        labware_id="tube_rack",
        position_rack="5",
        offset_x=0.0,
        offset_y=0.0,
        offset_z=0.0,
        offset_db_path=str(db_path),
    )

    assert result["action"] == "created"
    assert db_path.exists()


def test_update_labware_offset_with_notes(tmp_path: Path) -> None:
    """update_labware_offset stores optional notes."""

    db_path = _make_offset_db(tmp_path)
    result = update_labware_offset(
        labware_id="custom_plate",
        position_rack="3",
        offset_x=0.0,
        offset_y=0.0,
        offset_z=0.0,
        notes="calibrated on 2026-01-15",
        offset_db_path=str(db_path),
    )

    assert result["action"] == "created"
    content = db_path.read_text(encoding="utf-8")
    assert "calibrated on 2026-01-15" in content


def test_update_labware_offset_different_slots_are_independent(tmp_path: Path) -> None:
    """Same labware in different slots creates separate entries."""

    db_path = _make_offset_db(tmp_path)

    update_labware_offset(
        labware_id="my_plate",
        position_rack="1",
        offset_x=0.1,
        offset_y=0.0,
        offset_z=0.0,
        offset_db_path=str(db_path),
    )
    update_labware_offset(
        labware_id="my_plate",
        position_rack="2",
        offset_x=0.5,
        offset_y=0.0,
        offset_z=0.0,
        offset_db_path=str(db_path),
    )

    doc = tomlkit.loads(db_path.read_text(encoding="utf-8"))
    offsets = doc.get("offsets", [])
    assert len(offsets) == 2
