"""Tests for project management tools."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

import pytest

from ot2_cherrypick_mcp.tools.project_tools import (
    export_project_archive,
    get_active_project_directory,
    initialize_project,
)


def test_initialize_project_requires_env_var() -> None:
    """initialize_project raises ValueError if OT2_PROJECT_DIR is not set."""
    # Ensure env var is not set
    original = os.environ.pop("OT2_PROJECT_DIR", None)
    try:
        with pytest.raises(ValueError, match="OT2_PROJECT_DIR.*required"):
            initialize_project()
    finally:
        if original:
            os.environ["OT2_PROJECT_DIR"] = original


def test_initialize_project_creates_structure(tmp_path: Path, monkeypatch) -> None:
    """initialize_project creates project directory structure."""
    project_dir = tmp_path / "test_project"
    monkeypatch.setenv("OT2_PROJECT_DIR", str(project_dir))

    result = initialize_project()

    assert result["status"] == "success"
    assert result["project_directory"] == str(project_dir)
    assert project_dir.exists()

    # Check directories created
    assert (project_dir / "CSVs").exists()
    assert (project_dir / "logs").exists()


def test_initialize_project_copies_templates(tmp_path: Path, monkeypatch) -> None:
    """initialize_project copies template files from repo root."""
    project_dir = tmp_path / "test_project"
    monkeypatch.setenv("OT2_PROJECT_DIR", str(project_dir))

    result = initialize_project()

    # Check template files copied
    assert (project_dir / "settings.toml").exists()
    assert (project_dir / "labware_dict.toml").exists()
    assert (project_dir / "CherryPick_OT2.py").exists()

    # Verify files have content
    settings_content = (project_dir / "settings.toml").read_text()
    assert "settings.general" in settings_content

    labware_content = (project_dir / "labware_dict.toml").read_text()
    assert "pipettes" in labware_content

    protocol_content = (project_dir / "CherryPick_OT2.py").read_text()
    assert "def get_values" in protocol_content


def test_initialize_project_copies_csvs(tmp_path: Path, monkeypatch) -> None:
    """initialize_project copies CSV directory with example files."""
    project_dir = tmp_path / "test_project"
    monkeypatch.setenv("OT2_PROJECT_DIR", str(project_dir))

    result = initialize_project()

    csvs_dir = project_dir / "CSVs"
    assert csvs_dir.exists()
    assert csvs_dir.is_dir()

    # Should have at least some CSV files
    csv_files = list(csvs_dir.glob("*.csv"))
    assert len(csv_files) > 0


def test_initialize_project_creates_logs_directory(tmp_path: Path, monkeypatch) -> None:
    """initialize_project creates empty logs directory."""
    project_dir = tmp_path / "test_project"
    monkeypatch.setenv("OT2_PROJECT_DIR", str(project_dir))

    result = initialize_project()

    logs_dir = project_dir / "logs"
    assert logs_dir.exists()
    assert logs_dir.is_dir()


def test_initialize_project_overwrites_existing_files(tmp_path: Path, monkeypatch) -> None:
    """initialize_project overwrites existing files without backups."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    monkeypatch.setenv("OT2_PROJECT_DIR", str(project_dir))

    # Create existing settings file with recognizable content
    existing_settings = project_dir / "settings.toml"
    existing_settings.write_text("# Old settings\n", encoding="utf-8")

    initialize_project()

    # Original file should be replaced with template content
    new_content = existing_settings.read_text(encoding="utf-8")
    assert "# Old settings" not in new_content

    # No backup file should be created
    backup = project_dir / "settings.toml.backup"
    assert not backup.exists()


def test_initialize_project_returns_detailed_result(tmp_path: Path, monkeypatch) -> None:
    """initialize_project returns detailed information about created resources."""
    project_dir = tmp_path / "test_project"
    monkeypatch.setenv("OT2_PROJECT_DIR", str(project_dir))

    result = initialize_project()

    assert "project_directory" in result
    assert "created_files" in result
    assert "created_directories" in result
    assert "status" in result
    assert "message" in result

    # Should list created files
    assert "settings.toml" in result["created_files"]
    assert "labware_dict.toml" in result["created_files"]
    assert "CherryPick_OT2.py" in result["created_files"]

    # Should list created directories
    created_dirs_str = " ".join(result["created_directories"])
    assert "CSVs" in created_dirs_str
    assert "logs" in created_dirs_str


def test_get_active_project_directory_auto_created(monkeypatch) -> None:
    """get_active_project_directory falls back to a temp directory when env missing."""
    monkeypatch.delenv("OT2_PROJECT_DIR", raising=False)
    details = get_active_project_directory()
    path = Path(details["project_directory"])
    try:
        assert path.exists()
        assert details["auto_created"] is True
        assert os.environ.get("OT2_PROJECT_DIR") == str(path)
    finally:
        shutil.rmtree(path, ignore_errors=True)


def test_export_project_archive(tmp_path: Path, monkeypatch) -> None:
    """export_project_archive creates a zip file in the archives directory."""
    project_dir = tmp_path / "project"
    monkeypatch.setenv("OT2_PROJECT_DIR", str(project_dir))
    initialize_project()

    info = export_project_archive()
    archive = Path(info["archive_path"])
    assert archive.exists()
    assert archive.parent == project_dir / "archives"
    assert info["auto_created_workspace"] is False

    inline = export_project_archive(as_base64=True)
    assert "archive_base64" in inline
    assert isinstance(inline["archive_base64"], str)
