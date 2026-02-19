"""Tests for the labware scanner and offset database functionality."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import tomlkit

from ot2_cherrypick_mcp.core.labware_scanner import (
    load_official_labware_list,
    scan_available_labware,
    scan_custom_labware,
)
from ot2_cherrypick_mcp.core.protocol_generator import (
    _load_offset_database,
    _merge_offsets_into_settings,
)
from ot2_cherrypick_mcp.tools.labware_tools import update_labware_offset


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_labware_json(load_name: str, well_count: int = 96, category: str = "wellPlate") -> dict:
    """Build a minimal Opentrons labware JSON structure."""
    return {
        "parameters": {"loadName": load_name},
        "metadata": {
            "displayName": f"{load_name} display",
            "displayCategory": category,
        },
        "wells": {f"A{i}": {} for i in range(1, well_count + 1)},
    }


# ---------------------------------------------------------------------------
# scan_custom_labware tests
# ---------------------------------------------------------------------------


class TestScanCustomLabware:
    """Tests for scan_custom_labware()."""

    def test_empty_directory_returns_empty(self, tmp_path: Path) -> None:
        results = scan_custom_labware(str(tmp_path))
        assert results == []

    def test_nonexistent_directory_returns_empty(self, tmp_path: Path) -> None:
        missing = tmp_path / "nonexistent"
        results = scan_custom_labware(str(missing))
        assert results == []

    def test_single_valid_json_file(self, tmp_path: Path) -> None:
        json_path = tmp_path / "my_plate.json"
        json_path.write_text(
            json.dumps(_make_labware_json("my_custom_plate_96", well_count=96)),
            encoding="utf-8",
        )

        results = scan_custom_labware(str(tmp_path))
        assert len(results) == 1
        assert results[0]["labware_id"] == "my_custom_plate_96"
        assert results[0]["well_count"] == 96
        assert results[0]["source"] == "custom"

    def test_multiple_json_files_sorted(self, tmp_path: Path) -> None:
        for name in ["plate_b.json", "plate_a.json", "plate_c.json"]:
            load_name = name.replace(".json", "")
            (tmp_path / name).write_text(
                json.dumps(_make_labware_json(load_name)), encoding="utf-8"
            )

        results = scan_custom_labware(str(tmp_path))
        assert len(results) == 3
        # Results should be sorted by filename
        names = [r["labware_id"] for r in results]
        assert names == sorted(names)

    def test_invalid_json_file_skipped(self, tmp_path: Path) -> None:
        (tmp_path / "bad.json").write_text("not valid json", encoding="utf-8")
        (tmp_path / "good.json").write_text(
            json.dumps(_make_labware_json("good_plate")), encoding="utf-8"
        )

        results = scan_custom_labware(str(tmp_path))
        assert len(results) == 1
        assert results[0]["labware_id"] == "good_plate"

    def test_json_missing_parameters_skipped(self, tmp_path: Path) -> None:
        (tmp_path / "incomplete.json").write_text(
            json.dumps({"metadata": {"displayName": "Missing params"}}),
            encoding="utf-8",
        )

        results = scan_custom_labware(str(tmp_path))
        assert results == []

    def test_display_name_and_category_extracted(self, tmp_path: Path) -> None:
        data = _make_labware_json("nest_plate", category="Reservoir")
        (tmp_path / "nest_plate.json").write_text(json.dumps(data), encoding="utf-8")

        results = scan_custom_labware(str(tmp_path))
        assert results[0]["display_name"] == "nest_plate display"
        assert results[0]["display_category"] == "Reservoir"

    def test_non_json_files_ignored(self, tmp_path: Path) -> None:
        (tmp_path / "readme.txt").write_text("this is a readme", encoding="utf-8")
        (tmp_path / "plate.csv").write_text("a,b,c", encoding="utf-8")

        results = scan_custom_labware(str(tmp_path))
        assert results == []


# ---------------------------------------------------------------------------
# load_official_labware_list tests
# ---------------------------------------------------------------------------


class TestLoadOfficialLabwareList:
    """Tests for load_official_labware_list()."""

    def test_nonexistent_file_returns_empty(self, tmp_path: Path) -> None:
        missing = tmp_path / "missing.txt"
        results = load_official_labware_list(str(missing))
        assert results == []

    def test_valid_list_file(self, tmp_path: Path) -> None:
        list_file = tmp_path / "official.txt"
        list_file.write_text(
            "# Comment line\nnest_96_wellplate_200ul_flat\nbiorad_384_wellplate_50ul\n",
            encoding="utf-8",
        )

        results = load_official_labware_list(str(list_file))
        assert len(results) == 2
        assert results[0]["labware_id"] == "nest_96_wellplate_200ul_flat"
        assert results[1]["labware_id"] == "biorad_384_wellplate_50ul"
        assert all(r["source"] == "official" for r in results)

    def test_empty_lines_skipped(self, tmp_path: Path) -> None:
        list_file = tmp_path / "official.txt"
        list_file.write_text(
            "plate_a\n\n\nplate_b\n",
            encoding="utf-8",
        )

        results = load_official_labware_list(str(list_file))
        assert len(results) == 2

    def test_comment_lines_skipped(self, tmp_path: Path) -> None:
        list_file = tmp_path / "official.txt"
        list_file.write_text(
            "# This is a comment\nplate_a\n# Another comment\nplate_b\n",
            encoding="utf-8",
        )

        results = load_official_labware_list(str(list_file))
        assert len(results) == 2
        assert results[0]["labware_id"] == "plate_a"
        assert results[1]["labware_id"] == "plate_b"

    def test_well_count_is_none(self, tmp_path: Path) -> None:
        """Official list doesn't have well count data."""
        list_file = tmp_path / "official.txt"
        list_file.write_text("nest_96_wellplate_200ul_flat\n", encoding="utf-8")

        results = load_official_labware_list(str(list_file))
        assert results[0]["well_count"] is None

    def test_actual_official_list_file(self) -> None:
        """Test that the actual opentrons_labware_official.txt can be loaded."""
        repo_root = Path(__file__).resolve().parents[1]
        official_path = repo_root / "opentrons_labware_official.txt"
        if not official_path.exists():
            pytest.skip("opentrons_labware_official.txt not found at repo root")

        results = load_official_labware_list(str(official_path))
        assert len(results) > 0
        # All entries should have labware_id
        assert all(r["labware_id"] for r in results)


# ---------------------------------------------------------------------------
# scan_available_labware tests
# ---------------------------------------------------------------------------


class TestScanAvailableLabware:
    """Tests for scan_available_labware()."""

    def test_no_args_returns_empty(self) -> None:
        results = scan_available_labware()
        assert results == []

    def test_custom_only(self, tmp_path: Path) -> None:
        (tmp_path / "plate.json").write_text(
            json.dumps(_make_labware_json("custom_plate")), encoding="utf-8"
        )

        results = scan_available_labware(custom_labware_path=str(tmp_path))
        assert len(results) == 1
        assert results[0]["source"] == "custom"

    def test_official_only(self, tmp_path: Path) -> None:
        list_file = tmp_path / "official.txt"
        list_file.write_text("nest_plate\nbiorad_plate\n", encoding="utf-8")

        results = scan_available_labware(official_list_path=str(list_file))
        assert len(results) == 2
        assert all(r["source"] == "official" for r in results)

    def test_custom_takes_priority_over_official(self, tmp_path: Path) -> None:
        """Custom labware with same ID as official should appear only once (as custom)."""
        custom_dir = tmp_path / "custom"
        custom_dir.mkdir()
        (custom_dir / "shared_name.json").write_text(
            json.dumps(_make_labware_json("shared_name")), encoding="utf-8"
        )

        list_file = tmp_path / "official.txt"
        list_file.write_text("shared_name\nother_plate\n", encoding="utf-8")

        results = scan_available_labware(
            custom_labware_path=str(custom_dir),
            official_list_path=str(list_file),
        )

        # shared_name appears only once as custom
        shared = [r for r in results if r["labware_id"] == "shared_name"]
        assert len(shared) == 1
        assert shared[0]["source"] == "custom"

        # other_plate appears as official
        other = [r for r in results if r["labware_id"] == "other_plate"]
        assert len(other) == 1
        assert other[0]["source"] == "official"

    def test_combined_total(self, tmp_path: Path) -> None:
        custom_dir = tmp_path / "custom"
        custom_dir.mkdir()
        (custom_dir / "custom_plate.json").write_text(
            json.dumps(_make_labware_json("custom_plate")), encoding="utf-8"
        )

        list_file = tmp_path / "official.txt"
        list_file.write_text("plate_a\nplate_b\nplate_c\n", encoding="utf-8")

        results = scan_available_labware(
            custom_labware_path=str(custom_dir),
            official_list_path=str(list_file),
        )
        assert len(results) == 4  # 1 custom + 3 official


# ---------------------------------------------------------------------------
# Offset database load and merge tests
# ---------------------------------------------------------------------------


class TestOffsetDatabase:
    """Tests for _load_offset_database() and _merge_offsets_into_settings()."""

    def _make_offset_db(self, tmp_path: Path, entries: list[dict]) -> Path:
        db_path = tmp_path / "offset_database.toml"
        doc = tomlkit.document()
        array = tomlkit.aot()
        for entry in entries:
            t = tomlkit.table()
            for k, v in entry.items():
                t.add(k, v)
            array.append(t)
        doc.add("offsets", array)
        db_path.write_text(tomlkit.dumps(doc), encoding="utf-8")
        return db_path

    def test_load_nonexistent_file_returns_empty(self, tmp_path: Path) -> None:
        missing = str(tmp_path / "missing.toml")
        result = _load_offset_database(missing)
        assert result == {}

    def test_load_none_returns_empty(self) -> None:
        result = _load_offset_database(None)
        assert result == {}

    def test_load_single_entry(self, tmp_path: Path) -> None:
        db_path = self._make_offset_db(tmp_path, [
            {
                "labware_id": "nest_96_wellplate_200ul_flat",
                "position_rack": "4",
                "offset_x": -0.5,
                "offset_y": 0.8,
                "offset_z": -0.3,
            }
        ])

        result = _load_offset_database(str(db_path))
        key = "nest_96_wellplate_200ul_flat:4"
        assert key in result
        assert result[key]["offset_x"] == -0.5
        assert result[key]["offset_y"] == 0.8
        assert result[key]["offset_z"] == -0.3

    def test_load_multiple_entries(self, tmp_path: Path) -> None:
        db_path = self._make_offset_db(tmp_path, [
            {"labware_id": "plate_a", "position_rack": "1", "offset_x": 0.1, "offset_y": 0.0, "offset_z": 0.0},
            {"labware_id": "plate_b", "position_rack": "2", "offset_x": 0.2, "offset_y": 0.0, "offset_z": 0.0},
        ])

        result = _load_offset_database(str(db_path))
        assert len(result) == 2
        assert "plate_a:1" in result
        assert "plate_b:2" in result

    def test_load_empty_file_returns_empty(self, tmp_path: Path) -> None:
        db_path = tmp_path / "empty.toml"
        db_path.write_text("", encoding="utf-8")
        result = _load_offset_database(str(db_path))
        assert result == {}

    def test_merge_fills_missing_offsets(self, tmp_path: Path) -> None:
        offset_db = {
            "nest_plate:4": {"offset_x": -0.5, "offset_y": 0.8, "offset_z": -0.3}
        }
        sample_settings = {
            "settings": {
                "working_plate": [
                    {"labware_id": "nest_plate", "position_rack": "4", "type": "source"}
                ]
            }
        }

        _merge_offsets_into_settings(sample_settings, offset_db)

        plate = sample_settings["settings"]["working_plate"][0]
        assert plate["offset_x"] == -0.5
        assert plate["offset_y"] == 0.8
        assert plate["offset_z"] == -0.3

    def test_merge_does_not_override_explicit_offsets(self, tmp_path: Path) -> None:
        """Explicit offsets in settings.toml should not be overwritten by offset_db."""
        offset_db = {
            "nest_plate:4": {"offset_x": -0.5, "offset_y": 0.8, "offset_z": -0.3}
        }
        sample_settings = {
            "settings": {
                "working_plate": [
                    {
                        "labware_id": "nest_plate",
                        "position_rack": "4",
                        "type": "source",
                        "offset_x": 1.0,  # Explicit offset
                        "offset_y": 2.0,
                        "offset_z": 3.0,
                    }
                ]
            }
        }

        _merge_offsets_into_settings(sample_settings, offset_db)

        # Explicit offsets should be preserved
        plate = sample_settings["settings"]["working_plate"][0]
        assert plate["offset_x"] == 1.0
        assert plate["offset_y"] == 2.0
        assert plate["offset_z"] == 3.0

    def test_merge_no_match_leaves_plate_unchanged(self) -> None:
        offset_db = {
            "other_plate:5": {"offset_x": -0.5, "offset_y": 0.0, "offset_z": 0.0}
        }
        sample_settings = {
            "settings": {
                "working_plate": [
                    {"labware_id": "my_plate", "position_rack": "4", "type": "source"}
                ]
            }
        }

        _merge_offsets_into_settings(sample_settings, offset_db)

        # Plate should not have offset fields added
        plate = sample_settings["settings"]["working_plate"][0]
        assert "offset_x" not in plate

    def test_merge_empty_offset_db_no_change(self) -> None:
        sample_settings = {
            "settings": {
                "working_plate": [
                    {"labware_id": "my_plate", "position_rack": "4"}
                ]
            }
        }
        original = dict(sample_settings["settings"]["working_plate"][0])

        _merge_offsets_into_settings(sample_settings, {})

        assert sample_settings["settings"]["working_plate"][0] == original


# ---------------------------------------------------------------------------
# offset_database.toml write/read roundtrip via update_labware_offset
# ---------------------------------------------------------------------------


class TestOffsetDatabaseRoundtrip:
    """Integration tests for writing and reading back offset database entries."""

    def test_write_and_reload(self, tmp_path: Path) -> None:
        db_path = tmp_path / "offset_database.toml"

        update_labware_offset(
            labware_id="test_plate",
            position_rack="3",
            offset_x=0.25,
            offset_y=-0.10,
            offset_z=0.05,
            offset_db_path=str(db_path),
        )

        loaded = _load_offset_database(str(db_path))
        key = "test_plate:3"
        assert key in loaded
        assert abs(loaded[key]["offset_x"] - 0.25) < 1e-6
        assert abs(loaded[key]["offset_y"] - (-0.10)) < 1e-6
        assert abs(loaded[key]["offset_z"] - 0.05) < 1e-6

    def test_protocol_generation_with_offsets(self, tmp_path: Path) -> None:
        """End-to-end: offset from DB should appear in protocol after generation."""
        import shutil
        from ot2_cherrypick_mcp.core.protocol_generator import generate_protocol

        repo_root = Path(__file__).resolve().parents[1]

        # Copy required files
        settings = tmp_path / "settings.toml"
        labware = tmp_path / "labware_dict.toml"
        csv = tmp_path / "test.csv"
        protocol = tmp_path / "CherryPick_OT2.py"

        shutil.copy2(repo_root / "settings.toml", settings)
        shutil.copy2(repo_root / "labware_dict.toml", labware)
        shutil.copy2(repo_root / "CSVs" / "example_basic.csv", csv)
        shutil.copy2(repo_root / "CherryPick_OT2.py", protocol)

        # Create offset database
        db_path = tmp_path / "offset_database.toml"
        update_labware_offset(
            labware_id="384_ppv_55ul",
            position_rack="2",
            offset_x=-0.5,
            offset_y=0.8,
            offset_z=-0.3,
            offset_db_path=str(db_path),
        )

        # Generate protocol with offset DB
        result = generate_protocol(
            labware_toml_path=str(labware),
            settings_toml_path=str(settings),
            csv_path=str(csv),
            protocol_path=str(protocol),
            verbose=False,
            offset_db_path=str(db_path),
        )

        assert result["json_size"] > 0
        # Verify the offset values appear in the embedded JSON
        protocol_content = protocol.read_text(encoding="utf-8")
        assert "offset_x" in protocol_content or "-0.5" in protocol_content


# ---------------------------------------------------------------------------
# FastAPI backend endpoint tests for new labware routes
# ---------------------------------------------------------------------------

import shutil as _shutil

from fastapi.testclient import TestClient
from gui.backend.main import create_app
from gui.backend.dependencies import get_state_store
from gui.backend.state import FileStateStore
from ot2_cherrypick_mcp.utils.paths import get_repo_root as _get_repo_root


def _make_client(workspace_name: str, monkeypatch) -> tuple[TestClient, FileStateStore]:
    """Create a FastAPI test client with an isolated workspace."""
    monkeypatch.setenv("OT2_GUI_WORKSPACE", workspace_name)
    get_state_store.cache_clear()
    store = FileStateStore()
    repo_root = _get_repo_root()
    _shutil.copy2(
        repo_root / "CSVs" / "example_basic.csv",
        store.csv_dir / "example_basic.csv",
    )
    app = create_app()
    app.dependency_overrides[get_state_store] = lambda: store
    return TestClient(app), store


class TestLabwareApiEndpoints:
    """Tests for the new /labware/available and /labware/offsets FastAPI endpoints."""

    def test_get_available_labware_returns_list(self, tmp_path, monkeypatch) -> None:
        """GET /labware/available returns a list of labware entries."""
        client, store = _make_client("test_labware_api", monkeypatch)
        try:
            with client:
                response = client.get("/labware/available")
                assert response.status_code == 200
                data = response.json()
                assert isinstance(data, list)
        finally:
            get_state_store.cache_clear()
            if store.workspace_dir.exists():
                _shutil.rmtree(store.workspace_dir, ignore_errors=True)

    def test_get_offsets_empty_db(self, tmp_path, monkeypatch) -> None:
        """GET /labware/offsets returns empty offsets when no offsets stored."""
        client, store = _make_client("test_offsets_api", monkeypatch)
        try:
            with client:
                response = client.get("/labware/offsets")
                assert response.status_code == 200
                data = response.json()
                # When no offsets exist, we get either {"offsets": []} or {}
                # (depends on whether the offset_database.toml has an offsets array or not)
                assert isinstance(data, dict)
                offsets = data.get("offsets", [])
                assert isinstance(offsets, list)
                assert len(offsets) == 0
        finally:
            get_state_store.cache_clear()
            if store.workspace_dir.exists():
                _shutil.rmtree(store.workspace_dir, ignore_errors=True)

    def test_post_offsets_creates_entry(self, tmp_path, monkeypatch) -> None:
        """POST /labware/offsets creates a new offset entry."""
        client, store = _make_client("test_post_offsets", monkeypatch)
        try:
            with client:
                payload = {
                    "labware_id": "nest_96_wellplate_200ul_flat",
                    "position_rack": "4",
                    "offset_x": -0.5,
                    "offset_y": 0.8,
                    "offset_z": -0.3,
                }
                response = client.post("/labware/offsets", json=payload)
                assert response.status_code == 200
                data = response.json()
                assert data["labware_id"] == "nest_96_wellplate_200ul_flat"
                assert data["action"] in ("created", "updated")

                # Verify it's readable back
                get_response = client.get("/labware/offsets")
                assert get_response.status_code == 200
                offsets = get_response.json().get("offsets", [])
                matching = [o for o in offsets if o.get("labware_id") == "nest_96_wellplate_200ul_flat"]
                assert len(matching) == 1
        finally:
            get_state_store.cache_clear()
            if store.workspace_dir.exists():
                _shutil.rmtree(store.workspace_dir, ignore_errors=True)

    def test_post_offsets_missing_fields_returns_error(self, tmp_path, monkeypatch) -> None:
        """POST /labware/offsets with missing required fields returns 400."""
        client, store = _make_client("test_post_bad_offsets", monkeypatch)
        try:
            with client:
                # Missing labware_id
                response = client.post("/labware/offsets", json={"position_rack": "4"})
                assert response.status_code == 400
        finally:
            get_state_store.cache_clear()
            if store.workspace_dir.exists():
                _shutil.rmtree(store.workspace_dir, ignore_errors=True)
