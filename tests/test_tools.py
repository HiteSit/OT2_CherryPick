"""Tests for protocol tools."""

from __future__ import annotations

from pathlib import Path

import helper_cherry_pick
import pytest

from ot2_cherrypick_mcp.tools.protocol_tools import run_generate_protocol
from ot2_cherrypick_mcp.utils.errors import ConfigurationError


def test_run_generate_protocol_updates_protocol_file(tmp_path: Path) -> None:
    """Ensure the helper embeds configuration into the target protocol file."""
    repo_root = Path(__file__).resolve().parents[1]

    protocol_source = repo_root / "CherryPick_OT2.py"
    protocol_copy = tmp_path / "CherryPick_OT2.py"
    protocol_copy.write_text(protocol_source.read_text(encoding="utf-8"), encoding="utf-8")

    result = run_generate_protocol(
        csv_path=str(repo_root / "CSVs" / "example_basic.csv"),
        settings_path=str(repo_root / "settings.toml"),
        labware_path=str(repo_root / "labware_dict.toml"),
        protocol_path=str(protocol_copy),
    )

    assert result["protocol_file"] == str(protocol_copy)
    assert result["json_size"] > 0
    assert "Protocol generated successfully" in result["message"]

    expected_json = helper_cherry_pick.create_json_config(
        str(repo_root / "labware_dict.toml"),
        str(repo_root / "settings.toml"),
        str(repo_root / "CSVs" / "example_basic.csv"),
        verbose=False,
    )
    updated_content = protocol_copy.read_text(encoding="utf-8")
    assert expected_json in updated_content
    assert "_all_values = json.loads" in updated_content


def test_run_generate_protocol_missing_csv_raises(tmp_path: Path) -> None:
    """Missing input files surface as configuration errors."""
    protocol_copy = tmp_path / "CherryPick_OT2.py"
    protocol_copy.write_text("", encoding="utf-8")

    with pytest.raises(ConfigurationError):
        run_generate_protocol(
            csv_path=str(tmp_path / "missing.csv"),
            settings_path=str(tmp_path / "settings.toml"),
            labware_path=str(tmp_path / "labware_dict.toml"),
            protocol_path=str(protocol_copy),
        )


def test_run_generate_protocol_with_offset_db(tmp_path: Path) -> None:
    """When offset_database.toml exists, offset_db_file appears in result."""
    repo_root = Path(__file__).resolve().parents[1]

    protocol_copy = tmp_path / "CherryPick_OT2.py"
    protocol_copy.write_text((repo_root / "CherryPick_OT2.py").read_text(encoding="utf-8"), encoding="utf-8")

    # Create a minimal offset database
    offset_db = tmp_path / "offset_database.toml"
    offset_db.write_text("", encoding="utf-8")

    result = run_generate_protocol(
        csv_path=str(repo_root / "CSVs" / "example_basic.csv"),
        settings_path=str(repo_root / "settings.toml"),
        labware_path=str(repo_root / "labware_dict.toml"),
        protocol_path=str(protocol_copy),
        offset_db_path=str(offset_db),
    )

    assert "offset_db_file" in result
    assert result["offset_db_file"] == str(offset_db)


def test_run_generate_protocol_without_offset_db(tmp_path: Path, monkeypatch) -> None:
    """When offset_database.toml does not exist, offset_db_file is None in result."""
    repo_root = Path(__file__).resolve().parents[1]

    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    monkeypatch.setenv("OT2_PROJECT_DIR", str(project_dir))

    # Ensure offset_database.toml does NOT exist in the project dir
    offset_db = project_dir / "offset_database.toml"
    assert not offset_db.exists()

    protocol_copy = project_dir / "CherryPick_OT2.py"
    protocol_copy.write_text((repo_root / "CherryPick_OT2.py").read_text(encoding="utf-8"), encoding="utf-8")

    result = run_generate_protocol(
        csv_path=str(repo_root / "CSVs" / "example_basic.csv"),
        settings_path=str(repo_root / "settings.toml"),
        labware_path=str(repo_root / "labware_dict.toml"),
        protocol_path=str(protocol_copy),
        offset_db_path=str(offset_db),
    )

    assert "offset_db_file" in result
    assert result["offset_db_file"] is None
