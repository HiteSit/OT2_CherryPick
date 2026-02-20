"""Tests for labware MCP tools."""

from __future__ import annotations

import json
from pathlib import Path
from datetime import date

import pytest
import tomlkit

from ot2_cherrypick_mcp.tools.labware_tools import run_scan_available_labware, update_labware_offset

# Optional imports — new CRUD functions added by the labware refactor.
# Tests that depend on these are skipped if the symbols are not yet present.
try:
    from ot2_cherrypick_mcp.tools.labware_tools import (
        get_labware_offset,
        list_labware_offsets,
        delete_labware_offset,
        manage_official_labware,
    )
    _CRUD_AVAILABLE = True
except ImportError:
    _CRUD_AVAILABLE = False

_requires_crud = pytest.mark.skipif(
    not _CRUD_AVAILABLE,
    reason="Offset CRUD functions not yet implemented",
)


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


# ---------------------------------------------------------------------------
# run_scan_available_labware tests
# ---------------------------------------------------------------------------


def _make_labware_json(load_name: str) -> str:
    """Build minimal Opentrons labware JSON for testing."""
    data = {
        "parameters": {"loadName": load_name},
        "metadata": {
            "displayName": f"{load_name} display",
            "displayCategory": "wellPlate",
        },
        "wells": {f"A{i}": {} for i in range(1, 97)},
    }
    return json.dumps(data)


def test_run_scan_available_labware_with_custom_path(tmp_path: Path, monkeypatch) -> None:
    """run_scan_available_labware returns custom labware from a directory."""
    custom_dir = tmp_path / "custom_labware"
    custom_dir.mkdir()
    (custom_dir / "my_custom_plate.json").write_text(
        _make_labware_json("my_custom_plate"), encoding="utf-8"
    )

    # Point project dir to tmp so official list won't resolve from repo
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    monkeypatch.setenv("OT2_PROJECT_DIR", str(project_dir))

    result = run_scan_available_labware(
        custom_labware_path=str(custom_dir),
        official_list_path=str(tmp_path / "nonexistent.txt"),
    )

    assert isinstance(result["labware"], list)
    assert result["count"] >= 1
    custom_items = [item for item in result["labware"] if item["source"] == "custom"]
    assert len(custom_items) >= 1
    assert any(item["labware_id"] == "my_custom_plate" for item in custom_items)


def test_run_scan_available_labware_with_official_list(tmp_path: Path, monkeypatch) -> None:
    """run_scan_available_labware returns official labware from list file."""
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    official_list = project_dir / "opentrons_labware_official.txt"
    official_list.write_text("nest_96_wellplate_200ul_flat\nbiorad_384_wellplate_50ul\n", encoding="utf-8")
    monkeypatch.setenv("OT2_PROJECT_DIR", str(project_dir))
    # Ensure LABWARE_PATH is absent so no custom directory is injected via env var.
    monkeypatch.delenv("LABWARE_PATH", raising=False)

    result = run_scan_available_labware(
        official_list_path=str(official_list),
    )

    assert result["count"] == 2
    assert result["official_list_exists"] is True
    assert all(item["source"] == "official" for item in result["labware"])


def test_run_scan_available_labware_no_paths_returns_empty(tmp_path: Path, monkeypatch) -> None:
    """run_scan_available_labware returns empty list when no paths resolve.

    LABWARE_PATH must be absent; otherwise the env-var fallback would supply a
    custom directory and the empty-list assertion would break.
    """
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    monkeypatch.setenv("OT2_PROJECT_DIR", str(project_dir))
    monkeypatch.delenv("LABWARE_PATH", raising=False)

    result = run_scan_available_labware(
        custom_labware_path=None,
        official_list_path=str(tmp_path / "nonexistent.txt"),
    )

    assert result["labware"] == []
    assert result["count"] == 0
    assert result["custom_path"] is None
    assert result["official_list_exists"] is False


def test_run_scan_available_labware_deduplicates_custom_over_official(tmp_path: Path, monkeypatch) -> None:
    """Custom labware takes priority; duplicates are deduplicated."""
    project_dir = tmp_path / "proj"
    project_dir.mkdir()

    custom_dir = tmp_path / "custom"
    custom_dir.mkdir()
    (custom_dir / "shared_plate.json").write_text(
        _make_labware_json("shared_plate"), encoding="utf-8"
    )

    official_list = project_dir / "opentrons_labware_official.txt"
    official_list.write_text("shared_plate\nother_plate\n", encoding="utf-8")
    monkeypatch.setenv("OT2_PROJECT_DIR", str(project_dir))

    result = run_scan_available_labware(
        custom_labware_path=str(custom_dir),
        official_list_path=str(official_list),
    )

    ids = [item["labware_id"] for item in result["labware"]]
    # shared_plate appears only once
    assert ids.count("shared_plate") == 1
    # The custom version wins
    shared = next(item for item in result["labware"] if item["labware_id"] == "shared_plate")
    assert shared["source"] == "custom"


def test_run_scan_available_labware_result_structure(tmp_path: Path, monkeypatch) -> None:
    """run_scan_available_labware result has all required keys.

    When LABWARE_PATH is absent and custom_labware_path=None, custom_path in
    the result must be None (not a stale env-var value from the test runner).
    """
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    monkeypatch.setenv("OT2_PROJECT_DIR", str(project_dir))
    monkeypatch.delenv("LABWARE_PATH", raising=False)

    result = run_scan_available_labware(
        custom_labware_path=None,
        official_list_path=str(tmp_path / "nonexistent.txt"),
    )

    assert "labware" in result
    assert "count" in result
    assert "custom_path" in result
    assert result["custom_path"] is None
    assert "official_list_path" in result
    assert "official_list_exists" in result


def test_run_scan_available_labware_env_var_fallback(tmp_path: Path, monkeypatch) -> None:
    """LABWARE_PATH env var is used as custom_labware_path when no explicit path is given.

    This covers the new behaviour introduced in run_scan_available_labware:
        effective_custom_path = custom_labware_path or os.getenv("LABWARE_PATH")

    The result's ``custom_path`` must equal the env-var value, and labware
    found in that directory must appear in the returned list.
    """
    # Build a temporary custom labware directory with one valid JSON file.
    custom_dir = tmp_path / "labware_env"
    custom_dir.mkdir()
    (custom_dir / "env_plate.json").write_text(
        _make_labware_json("env_plate"), encoding="utf-8"
    )

    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    monkeypatch.setenv("OT2_PROJECT_DIR", str(project_dir))
    # Set LABWARE_PATH to the custom directory — this is the env-var fallback.
    monkeypatch.setenv("LABWARE_PATH", str(custom_dir))

    result = run_scan_available_labware(
        # Deliberately omit custom_labware_path so the env var must supply it.
        official_list_path=str(tmp_path / "nonexistent.txt"),
    )

    # The returned custom_path must reflect the env-var value, not None.
    assert result["custom_path"] == str(custom_dir)
    # At least the plate we created must appear as custom labware.
    custom_items = [item for item in result["labware"] if item["source"] == "custom"]
    assert len(custom_items) >= 1
    assert any(item["labware_id"] == "env_plate" for item in custom_items)


# ---------------------------------------------------------------------------
# get_labware_offset tests
# ---------------------------------------------------------------------------


@_requires_crud
def test_get_labware_offset_returns_entry_when_exists(tmp_path: Path) -> None:
    """get_labware_offset returns offset values when entry exists."""
    db_path = tmp_path / "offset_database.toml"
    update_labware_offset(
        labware_id="nest_96_wellplate_200ul_flat",
        position_rack="4",
        offset_x=-0.5,
        offset_y=0.8,
        offset_z=-0.3,
        offset_db_path=str(db_path),
    )

    result = get_labware_offset(
        labware_id="nest_96_wellplate_200ul_flat",
        position_rack="4",
        offset_db_path=str(db_path),
    )

    assert result["found"] is True
    assert result["offset_x"] == -0.5
    assert result["offset_y"] == 0.8
    assert result["offset_z"] == -0.3


@_requires_crud
def test_get_labware_offset_returns_not_found_for_missing_entry(tmp_path: Path) -> None:
    """get_labware_offset returns found=False when no matching entry exists."""
    db_path = tmp_path / "offset_database.toml"
    update_labware_offset(
        labware_id="other_plate",
        position_rack="1",
        offset_x=0.0,
        offset_y=0.0,
        offset_z=0.0,
        offset_db_path=str(db_path),
    )

    result = get_labware_offset(
        labware_id="nest_96_wellplate_200ul_flat",
        position_rack="4",
        offset_db_path=str(db_path),
    )

    assert result["found"] is False


@_requires_crud
def test_get_labware_offset_no_crash_when_db_missing(tmp_path: Path) -> None:
    """get_labware_offset returns found=False gracefully when db file absent."""
    db_path = tmp_path / "nonexistent_offset_db.toml"
    assert not db_path.exists()

    result = get_labware_offset(
        labware_id="any_plate",
        position_rack="1",
        offset_db_path=str(db_path),
    )

    assert result["found"] is False


# ---------------------------------------------------------------------------
# list_labware_offsets tests
# ---------------------------------------------------------------------------


@_requires_crud
def test_list_labware_offsets_returns_all_entries(tmp_path: Path) -> None:
    """list_labware_offsets returns all stored entries."""
    db_path = tmp_path / "offset_database.toml"
    for i, rack in enumerate(["1", "2", "3"]):
        update_labware_offset(
            labware_id=f"plate_{i}",
            position_rack=rack,
            offset_x=float(i) * 0.1,
            offset_y=0.0,
            offset_z=0.0,
            offset_db_path=str(db_path),
        )

    result = list_labware_offsets(offset_db_path=str(db_path))

    assert result["exists"] is True
    assert result["count"] == 3
    assert len(result["offsets"]) == 3


@_requires_crud
def test_list_labware_offsets_empty_when_db_missing(tmp_path: Path) -> None:
    """list_labware_offsets returns empty result when db file absent."""
    db_path = tmp_path / "nonexistent.toml"

    result = list_labware_offsets(offset_db_path=str(db_path))

    assert result["exists"] is False
    assert result["count"] == 0
    assert result["offsets"] == []


# ---------------------------------------------------------------------------
# delete_labware_offset tests
# ---------------------------------------------------------------------------


@_requires_crud
def test_delete_labware_offset_removes_entry(tmp_path: Path) -> None:
    """delete_labware_offset removes the matching entry and returns deleted=True."""
    db_path = tmp_path / "offset_database.toml"
    update_labware_offset(
        labware_id="my_plate",
        position_rack="2",
        offset_x=0.1,
        offset_y=0.2,
        offset_z=0.3,
        offset_db_path=str(db_path),
    )

    result = delete_labware_offset(
        labware_id="my_plate",
        position_rack="2",
        offset_db_path=str(db_path),
    )

    assert result["deleted"] is True

    # Verify file no longer contains the entry
    doc = tomlkit.loads(db_path.read_text(encoding="utf-8"))
    remaining = [e for e in doc.get("offsets", []) if e.get("labware_id") == "my_plate"]
    assert remaining == []


@_requires_crud
def test_delete_labware_offset_returns_not_found(tmp_path: Path) -> None:
    """delete_labware_offset returns deleted=False when entry doesn't exist."""
    db_path = tmp_path / "offset_database.toml"
    db_path.write_text("", encoding="utf-8")

    result = delete_labware_offset(
        labware_id="nonexistent_plate",
        position_rack="5",
        offset_db_path=str(db_path),
    )

    assert result["deleted"] is False
    assert "reason" in result


@_requires_crud
def test_delete_labware_offset_file_not_found(tmp_path: Path) -> None:
    """delete_labware_offset returns deleted=False when db file is absent."""
    db_path = tmp_path / "missing.toml"

    result = delete_labware_offset(
        labware_id="any_plate",
        position_rack="1",
        offset_db_path=str(db_path),
    )

    assert result["deleted"] is False
    assert "reason" in result


@_requires_crud
def test_delete_labware_offset_leaves_other_entries_intact(tmp_path: Path) -> None:
    """Deleting one entry does not affect other entries in the db."""
    db_path = tmp_path / "offset_database.toml"
    for rack in ["1", "2", "3"]:
        update_labware_offset(
            labware_id="plate_x",
            position_rack=rack,
            offset_x=0.1,
            offset_y=0.0,
            offset_z=0.0,
            offset_db_path=str(db_path),
        )

    delete_labware_offset(
        labware_id="plate_x",
        position_rack="2",
        offset_db_path=str(db_path),
    )

    doc = tomlkit.loads(db_path.read_text(encoding="utf-8"))
    remaining = doc.get("offsets", [])
    assert len(remaining) == 2
    racks_left = {str(e["position_rack"]) for e in remaining}
    assert racks_left == {"1", "3"}


# ---------------------------------------------------------------------------
# manage_official_labware tests
# ---------------------------------------------------------------------------


@_requires_crud
def test_manage_official_labware_list_empty_when_file_missing(tmp_path: Path, monkeypatch) -> None:
    """action='list' returns empty result when official list file is absent."""
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    monkeypatch.setenv("OT2_PROJECT_DIR", str(project_dir))

    result = manage_official_labware(
        action="list",
        official_list_path=str(project_dir / "opentrons_labware_official.txt"),
    )

    assert result["exists"] is False
    assert result["count"] == 0
    assert result["entries"] == []


@_requires_crud
def test_manage_official_labware_add_new_entry(tmp_path: Path, monkeypatch) -> None:
    """action='add' inserts a new labware_id and returns status='added'."""
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    monkeypatch.setenv("OT2_PROJECT_DIR", str(project_dir))
    list_path = str(project_dir / "opentrons_labware_official.txt")

    result = manage_official_labware(
        action="add",
        labware_id="nest_96_wellplate_200ul_flat",
        official_list_path=list_path,
    )

    assert result["status"] == "added"

    # Entry must be readable back via list
    listed = manage_official_labware(action="list", official_list_path=list_path)
    assert any(e == "nest_96_wellplate_200ul_flat" for e in listed["entries"])


@_requires_crud
def test_manage_official_labware_add_idempotent(tmp_path: Path, monkeypatch) -> None:
    """action='add' returns already_exists when entry is already present."""
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    monkeypatch.setenv("OT2_PROJECT_DIR", str(project_dir))
    list_path = str(project_dir / "opentrons_labware_official.txt")

    manage_official_labware(
        action="add",
        labware_id="nest_96_wellplate_200ul_flat",
        official_list_path=list_path,
    )
    result = manage_official_labware(
        action="add",
        labware_id="nest_96_wellplate_200ul_flat",
        official_list_path=list_path,
    )

    assert result["status"] == "already_exists"

    # Only one copy in the file
    listed = manage_official_labware(action="list", official_list_path=list_path)
    assert listed["entries"].count("nest_96_wellplate_200ul_flat") == 1


@_requires_crud
def test_manage_official_labware_remove_existing_entry(tmp_path: Path, monkeypatch) -> None:
    """action='remove' deletes an existing entry and returns status='removed'."""
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    monkeypatch.setenv("OT2_PROJECT_DIR", str(project_dir))
    list_path = str(project_dir / "opentrons_labware_official.txt")

    manage_official_labware(
        action="add",
        labware_id="nest_96_wellplate_200ul_flat",
        official_list_path=list_path,
    )
    result = manage_official_labware(
        action="remove",
        labware_id="nest_96_wellplate_200ul_flat",
        official_list_path=list_path,
    )

    assert result["status"] == "removed"

    listed = manage_official_labware(action="list", official_list_path=list_path)
    assert "nest_96_wellplate_200ul_flat" not in listed["entries"]


@_requires_crud
def test_manage_official_labware_remove_not_found(tmp_path: Path, monkeypatch) -> None:
    """action='remove' returns not_found when entry is absent (no error)."""
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    monkeypatch.setenv("OT2_PROJECT_DIR", str(project_dir))
    list_path = str(project_dir / "opentrons_labware_official.txt")

    result = manage_official_labware(
        action="remove",
        labware_id="nonexistent_labware",
        official_list_path=list_path,
    )

    assert result["status"] == "not_found"


@_requires_crud
def test_manage_official_labware_preserves_comments(tmp_path: Path, monkeypatch) -> None:
    """action='add' preserves existing comment lines at the top of the file."""
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    monkeypatch.setenv("OT2_PROJECT_DIR", str(project_dir))
    list_path = project_dir / "opentrons_labware_official.txt"
    list_path.write_text("# Official Opentrons labware\n# Auto-generated\n", encoding="utf-8")

    manage_official_labware(
        action="add",
        labware_id="nest_96_wellplate_200ul_flat",
        official_list_path=str(list_path),
    )

    content = list_path.read_text(encoding="utf-8")
    assert "# Official Opentrons labware" in content
    assert "# Auto-generated" in content
    assert "nest_96_wellplate_200ul_flat" in content


@_requires_crud
def test_manage_official_labware_entries_sorted(tmp_path: Path, monkeypatch) -> None:
    """Entries are written in alphabetical order after add."""
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    monkeypatch.setenv("OT2_PROJECT_DIR", str(project_dir))
    list_path = str(project_dir / "opentrons_labware_official.txt")

    for name in ["zebra_plate", "apple_plate", "mango_plate"]:
        manage_official_labware(action="add", labware_id=name, official_list_path=list_path)

    listed = manage_official_labware(action="list", official_list_path=list_path)
    entries = listed["entries"]
    assert entries == sorted(entries)


@_requires_crud
def test_manage_official_labware_invalid_action_pure_function_raises(tmp_path: Path, monkeypatch) -> None:
    """Passing an invalid action to the pure function raises ValueError."""
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    monkeypatch.setenv("OT2_PROJECT_DIR", str(project_dir))

    with pytest.raises(ValueError, match="Invalid action"):
        manage_official_labware(
            action="frobnicate",
            official_list_path=str(project_dir / "opentrons_labware_official.txt"),
        )


@_requires_crud
def test_manage_official_labware_e2e_lifecycle(tmp_path: Path, monkeypatch) -> None:
    """End-to-end: list → add → list → add-again → remove → list."""
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    monkeypatch.setenv("OT2_PROJECT_DIR", str(project_dir))
    list_path = str(project_dir / "opentrons_labware_official.txt")

    # 1. list — empty
    r1 = manage_official_labware(action="list", official_list_path=list_path)
    assert r1["count"] == 0

    # 2. add
    r2 = manage_official_labware(
        action="add",
        labware_id="nest_96_wellplate_200ul_flat",
        official_list_path=list_path,
    )
    assert r2["status"] == "added"

    # 3. list — entry present
    r3 = manage_official_labware(action="list", official_list_path=list_path)
    assert "nest_96_wellplate_200ul_flat" in r3["entries"]

    # 4. add again — idempotent
    r4 = manage_official_labware(
        action="add",
        labware_id="nest_96_wellplate_200ul_flat",
        official_list_path=list_path,
    )
    assert r4["status"] == "already_exists"

    # 5. remove
    r5 = manage_official_labware(
        action="remove",
        labware_id="nest_96_wellplate_200ul_flat",
        official_list_path=list_path,
    )
    assert r5["status"] == "removed"

    # 6. list — entry gone
    r6 = manage_official_labware(action="list", official_list_path=list_path)
    assert "nest_96_wellplate_200ul_flat" not in r6["entries"]
