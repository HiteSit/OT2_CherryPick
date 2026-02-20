"""Tests for configuration resources."""

from __future__ import annotations

import asyncio
import shutil
from pathlib import Path

from ot2_cherrypick_mcp.server import create_mcp_app
from ot2_cherrypick_mcp.core.simulation import DEFAULT_LOG_FILE
from ot2_cherrypick_mcp.utils.toml import TomlHandler as RealTomlHandler


def _setup_project_dir(tmp_path: Path) -> Path:
    """Set up a temporary project directory with required files."""
    repo_root = Path(__file__).resolve().parents[1]
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()

    # Copy template files
    shutil.copy2(repo_root / "settings.toml", project_dir / "settings.toml")
    shutil.copy2(repo_root / "labware_dict.toml", project_dir / "labware_dict.toml")

    # Create directories
    (project_dir / "CSVs").mkdir()
    (project_dir / "logs").mkdir()

    return project_dir


def test_settings_resource_registered_and_readable(tmp_path: Path, monkeypatch) -> None:
    """Settings resource should be available and return TOML text."""
    project_dir = _setup_project_dir(tmp_path)
    monkeypatch.setenv("OT2_PROJECT_DIR", str(project_dir))

    app = create_mcp_app()
    resources = asyncio.run(app.get_resources())
    assert "config://settings" in resources
    content = resources["config://settings"].fn()
    assert "settings.general" in content


def test_labware_resource_registered_and_readable(tmp_path: Path, monkeypatch) -> None:
    """Labware resource should be available and return TOML text."""
    project_dir = _setup_project_dir(tmp_path)
    monkeypatch.setenv("OT2_PROJECT_DIR", str(project_dir))

    app = create_mcp_app()
    resources = asyncio.run(app.get_resources())
    assert "config://labware" in resources
    content = resources["config://labware"].fn()
    # After refactor, labware_dict.toml only contains [[pipettes]] (no [[labware]])
    assert "[[pipettes]]" in content


def test_csv_file_resource_lists_files(tmp_path: Path, monkeypatch) -> None:
    """CSV resource should list available files."""
    project_dir = _setup_project_dir(tmp_path)
    monkeypatch.setenv("OT2_PROJECT_DIR", str(project_dir))

    csv_dir = project_dir / "CSVs"
    (csv_dir / "b.csv").write_text("", encoding="utf-8")
    (csv_dir / "a.csv").write_text("", encoding="utf-8")

    app = create_mcp_app()
    resources = asyncio.run(app.get_resources())
    content = resources["files://csvs"].fn()
    assert "a.csv" in content.splitlines()[0]


def test_archive_file_resource_lists_archives(tmp_path: Path, monkeypatch) -> None:
    """Archive resource should list archive files if present."""
    project_dir = _setup_project_dir(tmp_path)
    monkeypatch.setenv("OT2_PROJECT_DIR", str(project_dir))

    archive_dir = project_dir / "archives"
    archive_dir.mkdir()
    (archive_dir / "snapshot.zip").write_text("", encoding="utf-8")

    app = create_mcp_app()
    resources = asyncio.run(app.get_resources())
    content = resources["files://archives"].fn()
    assert "snapshot.zip" in content.splitlines()[0]
def test_last_simulation_resource(tmp_path: Path, monkeypatch) -> None:
    """Log resource should serve latest simulation entry."""
    project_dir = _setup_project_dir(tmp_path)
    monkeypatch.setenv("OT2_PROJECT_DIR", str(project_dir))

    log_path = project_dir / "logs" / "last_simulation.json"
    log_path.write_text("{\"status\": \"ok\"}", encoding="utf-8")

    app = create_mcp_app()
    resources = asyncio.run(app.get_resources())
    content = resources["logs://last-simulation"].fn()
    assert "\"status\"" in content


def test_status_resources(tmp_path: Path, monkeypatch) -> None:
    """Status resources should provide deck and liquid handling summaries."""
    project_dir = _setup_project_dir(tmp_path)
    monkeypatch.setenv("OT2_PROJECT_DIR", str(project_dir))

    # Update the settings file in the project directory
    settings_copy = project_dir / "settings.toml"
    settings_copy.write_text(
        """
[settings]
  [[settings.working_plate]]
  type = "source"
  labware_id = "plate_a"
  position_rack = "1"

  [settings.liquid_handling]
  mode = "test"
""",
        encoding="utf-8",
    )

    app = create_mcp_app()
    resources = asyncio.run(app.get_resources())
    deck = resources["status://deck-layout"].fn()
    liquid = resources["status://liquid-handling-config"].fn()

    assert "plate_a" in deck
    assert "Liquid Handling Configuration" in liquid


def test_offsets_resource_returns_content_when_file_exists(tmp_path: Path, monkeypatch) -> None:
    """config://offsets returns TOML text when offset_database.toml exists."""
    project_dir = _setup_project_dir(tmp_path)
    monkeypatch.setenv("OT2_PROJECT_DIR", str(project_dir))

    offset_db = project_dir / "offset_database.toml"
    offset_db.write_text(
        '[[offsets]]\nlabware_id = "nest_96"\nposition_rack = "4"\n',
        encoding="utf-8",
    )

    app = create_mcp_app()
    resources = asyncio.run(app.get_resources())
    assert "config://offsets" in resources
    content = resources["config://offsets"].fn()
    assert "nest_96" in content


def test_offsets_resource_returns_fallback_when_file_missing(tmp_path: Path, monkeypatch) -> None:
    """config://offsets returns a fallback comment when offset_database.toml is absent."""
    project_dir = _setup_project_dir(tmp_path)
    monkeypatch.setenv("OT2_PROJECT_DIR", str(project_dir))

    # Ensure offset_database.toml does NOT exist
    offset_db = project_dir / "offset_database.toml"
    offset_db.unlink(missing_ok=True)

    app = create_mcp_app()
    resources = asyncio.run(app.get_resources())
    content = resources["config://offsets"].fn()
    # Should return the fallback string without raising an exception
    assert "offset_database.toml" in content or "#" in content


def test_project_directory_status(tmp_path: Path, monkeypatch) -> None:
    """Project directory status resource reports path and auto flag."""
    project_dir = _setup_project_dir(tmp_path)
    monkeypatch.setenv("OT2_PROJECT_DIR", str(project_dir))

    app = create_mcp_app()
    resources = asyncio.run(app.get_resources())
    status = resources["status://project-directory"].fn()

    assert "path" in status
    assert "auto_created" in status
