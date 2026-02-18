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
    list_projects,
    set_project_directory,
)
from ot2_cherrypick_mcp.core.project_context import ProjectContext
from ot2_cherrypick_mcp.utils.paths import reset_auto_project_dir


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
    reset_auto_project_dir()
    details = get_active_project_directory()
    path = Path(details["project_directory"])
    try:
        assert path.exists()
        assert details["auto_created"] is True
        assert os.environ.get("OT2_PROJECT_DIR") == str(path)
    finally:
        reset_auto_project_dir()
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


# ---------------------------------------------------------------------------
# ProjectContext unit tests
# ---------------------------------------------------------------------------


class TestProjectContext:
    """Tests for the ProjectContext dataclass."""

    def test_switch_to_saves_history(self, tmp_path: Path) -> None:
        """switch_to saves the current directory to recent_projects."""
        old_dir = tmp_path / "old"
        new_dir = tmp_path / "new"
        old_dir.mkdir()
        new_dir.mkdir()

        ctx = ProjectContext(project_dir=old_dir)
        ctx.switch_to(new_dir)

        assert ctx.project_dir == new_dir
        assert str(old_dir) in ctx.recent_projects

    def test_switch_to_avoids_duplicates(self, tmp_path: Path) -> None:
        """switch_to does not create duplicate entries in history."""
        dir_a = tmp_path / "a"
        dir_b = tmp_path / "b"
        dir_a.mkdir()
        dir_b.mkdir()

        ctx = ProjectContext(project_dir=dir_a)
        ctx.switch_to(dir_b)
        ctx.switch_to(dir_a)

        # dir_a should appear only once (most recent switch put dir_b in history)
        assert ctx.recent_projects.count(str(dir_b)) == 1

    def test_switch_to_trims_history(self, tmp_path: Path) -> None:
        """switch_to trims recent_projects to max 10 entries."""
        dirs = []
        for i in range(12):
            d = tmp_path / f"d{i}"
            d.mkdir()
            dirs.append(d)

        ctx = ProjectContext(project_dir=dirs[0])
        for d in dirs[1:]:
            ctx.switch_to(d)

        assert len(ctx.recent_projects) <= 10

    def test_resolve_path_relative(self, tmp_path: Path) -> None:
        """resolve_path resolves relative paths against project_dir."""
        ctx = ProjectContext(project_dir=tmp_path)
        resolved = ctx.resolve_path("CSVs/test.csv")
        assert resolved == tmp_path / "CSVs" / "test.csv"

    def test_resolve_path_absolute(self, tmp_path: Path) -> None:
        """resolve_path returns absolute paths unchanged."""
        ctx = ProjectContext(project_dir=tmp_path)
        absolute = Path("/some/absolute/path")
        assert ctx.resolve_path(absolute) == absolute

    def test_info_returns_serializable_dict(self, tmp_path: Path) -> None:
        """info() returns a dict with expected keys."""
        ctx = ProjectContext(project_dir=tmp_path, auto_created=True)
        info = ctx.info()
        assert info["project_dir"] == str(tmp_path)
        assert info["auto_created"] is True
        assert isinstance(info["recent_projects"], list)


# ---------------------------------------------------------------------------
# reset_auto_project_dir tests
# ---------------------------------------------------------------------------


def test_reset_auto_project_dir_clears_cache(monkeypatch) -> None:
    """reset_auto_project_dir allows get_project_root to re-read env."""
    from ot2_cherrypick_mcp.utils import paths as paths_mod

    # First call without env var creates auto dir
    monkeypatch.delenv("OT2_PROJECT_DIR", raising=False)
    reset_auto_project_dir()

    from ot2_cherrypick_mcp.utils.paths import get_project_root
    auto_path = get_project_root()
    assert paths_mod._AUTO_PROJECT_DIR is not None

    # Now set an env var and reset
    new_dir = auto_path.parent / "explicit_project"
    new_dir.mkdir(exist_ok=True)
    monkeypatch.setenv("OT2_PROJECT_DIR", str(new_dir))
    reset_auto_project_dir()

    result = get_project_root()
    assert result == new_dir

    # Cleanup
    reset_auto_project_dir()
    shutil.rmtree(auto_path, ignore_errors=True)
    shutil.rmtree(new_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# set_project_directory tests
# ---------------------------------------------------------------------------


def test_set_project_directory_switches(tmp_path: Path, monkeypatch) -> None:
    """set_project_directory updates env var and returns summary."""
    old_dir = tmp_path / "old_project"
    new_dir = tmp_path / "new_project"
    old_dir.mkdir()
    monkeypatch.setenv("OT2_PROJECT_DIR", str(old_dir))
    reset_auto_project_dir()

    result = set_project_directory(path=str(new_dir), initialize_templates=True)

    assert "Switched project directory" in result
    assert str(new_dir) in result
    assert os.environ["OT2_PROJECT_DIR"] == str(new_dir)
    assert new_dir.exists()


def test_set_project_directory_rejects_relative() -> None:
    """set_project_directory raises ValueError for relative paths."""
    with pytest.raises(ValueError, match="absolute"):
        set_project_directory(path="relative/path")


def test_set_project_directory_updates_context(tmp_path: Path, monkeypatch) -> None:
    """set_project_directory calls switch_to on ProjectContext when provided."""
    old_dir = tmp_path / "old"
    new_dir = tmp_path / "new"
    old_dir.mkdir()
    monkeypatch.setenv("OT2_PROJECT_DIR", str(old_dir))
    reset_auto_project_dir()

    ctx = ProjectContext(project_dir=old_dir)
    set_project_directory(
        path=str(new_dir),
        initialize_templates=False,
        project_ctx=ctx,
    )

    assert ctx.project_dir == new_dir
    assert str(old_dir) in ctx.recent_projects


# ---------------------------------------------------------------------------
# list_projects tests
# ---------------------------------------------------------------------------


def test_list_projects_shows_active(tmp_path: Path, monkeypatch) -> None:
    """list_projects reports the active project directory."""
    project_dir = tmp_path / "active"
    project_dir.mkdir()
    monkeypatch.setenv("OT2_PROJECT_DIR", str(project_dir))
    reset_auto_project_dir()

    result = list_projects()
    assert "Active project:" in result
    assert str(project_dir) in result


def test_list_projects_shows_recent(tmp_path: Path, monkeypatch) -> None:
    """list_projects includes recent projects from context."""
    project_dir = tmp_path / "current"
    project_dir.mkdir()
    monkeypatch.setenv("OT2_PROJECT_DIR", str(project_dir))
    reset_auto_project_dir()

    ctx = ProjectContext(
        project_dir=project_dir,
        recent_projects=["/tmp/old_project_1", "/tmp/old_project_2"],
    )
    result = list_projects(project_ctx=ctx)
    assert "/tmp/old_project_1" in result
    assert "/tmp/old_project_2" in result


def test_list_projects_scans_parent(tmp_path: Path, monkeypatch) -> None:
    """list_projects discovers projects in a parent directory."""
    project_dir = tmp_path / "current"
    project_dir.mkdir()
    monkeypatch.setenv("OT2_PROJECT_DIR", str(project_dir))
    reset_auto_project_dir()

    # Create two subdirectories, one with settings.toml
    parent = tmp_path / "experiments"
    parent.mkdir()
    proj_a = parent / "proj_a"
    proj_a.mkdir()
    (proj_a / "settings.toml").write_text("[settings]\n", encoding="utf-8")

    proj_b = parent / "proj_b"
    proj_b.mkdir()
    # proj_b has no settings.toml

    result = list_projects(scan_parent_directory=str(parent))
    assert "proj_a" in result
    assert "proj_b" not in result
