"""Tests for GUI sync tools (create_shell_settings and sync_to_gui)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from ot2_cherrypick_mcp.tools.gui_sync_tools import (
    CONTAINER_NAME,
    CONTAINER_TARGET_DIR,
    SYNCABLE_FILES,
    create_shell_settings,
    sync_to_gui,
)
from ot2_cherrypick_mcp.utils.errors import ConfigurationError, SyncError


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def project_dir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Patch get_project_root to return a temporary directory."""
    monkeypatch.setattr(
        "ot2_cherrypick_mcp.tools.gui_sync_tools.get_project_root",
        lambda: tmp_path,
    )
    return tmp_path


def _populate_project(project_dir: Path) -> None:
    """Create all syncable files in *project_dir* so sync has something to copy."""
    for name in SYNCABLE_FILES:
        p = project_dir / name
        if name == "CSVs":
            p.mkdir(exist_ok=True)
            (p / "example.csv").write_text("a,b\n1,2\n", encoding="utf-8")
        else:
            p.write_text(f"# {name}\n", encoding="utf-8")


def _make_docker_runner(
    *,
    docker_installed: bool = True,
    container_exists: bool = True,
    container_running: bool = True,
    cp_fail_names: frozenset[str] = frozenset(),
) -> ...:
    """Return a fake ``subprocess.run`` that simulates Docker CLI behaviour."""

    def fake_run(cmd, **kwargs):  # noqa: ANN001, ANN003
        if not docker_installed:
            raise FileNotFoundError("docker")

        prog = cmd[:2]

        if prog == ["docker", "version"]:
            return subprocess.CompletedProcess(cmd, 0, stdout="24.0.0\n", stderr="")

        if prog == ["docker", "inspect"]:
            if not container_exists:
                return subprocess.CompletedProcess(
                    cmd, 1, stdout="", stderr="No such object"
                )
            running = "true" if container_running else "false"
            return subprocess.CompletedProcess(cmd, 0, stdout=f"{running}\n", stderr="")

        if prog == ["docker", "exec"]:
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

        if prog == ["docker", "cp"]:
            # cmd looks like ["docker", "cp", "<src>", "<container>:<dest>"]
            src_path = cmd[2]
            src_name = Path(src_path.rstrip("/.")).name
            if src_name in cp_fail_names:
                return subprocess.CompletedProcess(
                    cmd, 1, stdout="", stderr=f"copy failed for {src_name}"
                )
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

        return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="unknown command")

    return fake_run


@pytest.fixture()
def mock_docker_running(monkeypatch: pytest.MonkeyPatch):
    """Patch subprocess.run with a fake that reports Docker running."""
    monkeypatch.setattr(
        "ot2_cherrypick_mcp.tools.gui_sync_tools.subprocess.run",
        _make_docker_runner(),
    )


# ===================================================================
# create_shell_settings tests
# ===================================================================


class TestCreateShellSettings:
    def test_valid_path(self, project_dir: Path) -> None:
        result = create_shell_settings(
            opentrons_dir_win=r"C:\Users\ricca\AppData\Roaming\Opentrons",
        )
        assert result["status"] == "success"
        dest = Path(result["path"])
        data = json.loads(dest.read_text(encoding="utf-8"))
        assert data["opentrons_dir_win"] == r"C:\Users\ricca\AppData\Roaming\Opentrons"

    def test_trailing_backslash_stripped(self, project_dir: Path) -> None:
        result = create_shell_settings(opentrons_dir_win=r"C:\Users\foo\\")
        assert result["opentrons_dir_win"] == r"C:\Users\foo"

    def test_whitespace_stripped(self, project_dir: Path) -> None:
        result = create_shell_settings(opentrons_dir_win=r"  C:\Opentrons  ")
        assert result["opentrons_dir_win"] == r"C:\Opentrons"

    def test_rejects_linux_path(self, project_dir: Path) -> None:
        with pytest.raises(ConfigurationError, match="backslashes"):
            create_shell_settings(opentrons_dir_win="/mnt/c/Users/foo")

    def test_rejects_relative_path(self, project_dir: Path) -> None:
        with pytest.raises(ConfigurationError, match="Windows absolute path"):
            create_shell_settings(opentrons_dir_win=r"Users\foo")

    def test_rejects_forward_slashes(self, project_dir: Path) -> None:
        with pytest.raises(ConfigurationError, match="backslashes"):
            create_shell_settings(opentrons_dir_win="C:/Users/foo")

    def test_rejects_empty_string(self, project_dir: Path) -> None:
        with pytest.raises(ConfigurationError, match="must not be empty"):
            create_shell_settings(opentrons_dir_win="")

    def test_overwrites_existing(self, project_dir: Path) -> None:
        create_shell_settings(opentrons_dir_win=r"C:\Old")
        result = create_shell_settings(opentrons_dir_win=r"C:\New")
        data = json.loads(Path(result["path"]).read_text(encoding="utf-8"))
        assert data["opentrons_dir_win"] == r"C:\New"

    def test_uses_project_dir(self, project_dir: Path) -> None:
        result = create_shell_settings(opentrons_dir_win=r"D:\Opentrons")
        assert Path(result["path"]).parent == project_dir


# ===================================================================
# sync_to_gui tests
# ===================================================================


class TestSyncToGui:
    def test_happy_path(
        self, project_dir: Path, mock_docker_running: None,
    ) -> None:
        _populate_project(project_dir)
        result = sync_to_gui()
        assert result["status"] == "success"
        assert set(result["synced"]) == set(SYNCABLE_FILES)
        assert result["skipped"] == []
        assert result["container"] == CONTAINER_NAME

    def test_partial_files(
        self, project_dir: Path, mock_docker_running: None,
    ) -> None:
        # Only create settings.toml
        (project_dir / "settings.toml").write_text("# settings\n", encoding="utf-8")
        result = sync_to_gui()
        assert "settings.toml" in result["synced"]
        assert len(result["skipped"]) == len(SYNCABLE_FILES) - 1

    def test_selective_sync(
        self, project_dir: Path, mock_docker_running: None,
    ) -> None:
        _populate_project(project_dir)
        result = sync_to_gui(files=["settings.toml"])
        assert result["synced"] == ["settings.toml"]
        # Other files exist but were not requested
        assert result["skipped"] == []

    def test_invalid_file_name(
        self, project_dir: Path, mock_docker_running: None,
    ) -> None:
        with pytest.raises(ConfigurationError, match="Unknown file"):
            sync_to_gui(files=["bogus.txt"])

    def test_docker_not_installed(
        self, project_dir: Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(
            "ot2_cherrypick_mcp.tools.gui_sync_tools.subprocess.run",
            _make_docker_runner(docker_installed=False),
        )
        with pytest.raises(SyncError, match="Docker CLI not found"):
            sync_to_gui()

    def test_container_not_found(
        self, project_dir: Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(
            "ot2_cherrypick_mcp.tools.gui_sync_tools.subprocess.run",
            _make_docker_runner(container_exists=False),
        )
        with pytest.raises(SyncError, match="not found"):
            sync_to_gui()

    def test_container_stopped(
        self, project_dir: Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(
            "ot2_cherrypick_mcp.tools.gui_sync_tools.subprocess.run",
            _make_docker_runner(container_running=False),
        )
        with pytest.raises(SyncError, match="not running"):
            sync_to_gui()

    def test_docker_cp_fails(
        self, project_dir: Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _populate_project(project_dir)
        monkeypatch.setattr(
            "ot2_cherrypick_mcp.tools.gui_sync_tools.subprocess.run",
            _make_docker_runner(cp_fail_names=frozenset({"settings.toml"})),
        )
        with pytest.raises(SyncError, match="docker cp failed"):
            sync_to_gui()

    def test_csvs_directory_handling(
        self, project_dir: Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Verify CSVs dir uses the '/.' copy pattern and mkdir -p."""
        _populate_project(project_dir)
        calls: list[list[str]] = []

        original_runner = _make_docker_runner()

        def tracking_run(cmd, **kwargs):  # noqa: ANN001, ANN003
            calls.append(list(cmd))
            return original_runner(cmd, **kwargs)

        monkeypatch.setattr(
            "ot2_cherrypick_mcp.tools.gui_sync_tools.subprocess.run",
            tracking_run,
        )

        sync_to_gui(files=["CSVs"])

        # Should have: docker version, docker inspect, docker exec mkdir, docker cp
        mkdir_calls = [c for c in calls if c[:2] == ["docker", "exec"] and "mkdir" in c]
        assert len(mkdir_calls) == 1
        assert f"{CONTAINER_TARGET_DIR}/CSVs" in mkdir_calls[0]

        cp_calls = [c for c in calls if c[:2] == ["docker", "cp"]]
        assert len(cp_calls) == 1
        assert cp_calls[0][2].endswith("/.")

    def test_empty_project_dir(
        self, project_dir: Path, mock_docker_running: None,
    ) -> None:
        result = sync_to_gui()
        assert result["status"] == "success"
        assert result["synced"] == []
        assert set(result["skipped"]) == set(SYNCABLE_FILES)

    def test_shell_settings_missing_warns(
        self, project_dir: Path, mock_docker_running: None,
    ) -> None:
        """sync_to_gui includes a warning when shell_settings.json is skipped."""
        _populate_project(project_dir)
        # Remove shell_settings.json so it gets skipped
        shell_settings = project_dir / "shell_settings.json"
        if shell_settings.exists():
            shell_settings.unlink()

        result = sync_to_gui()
        assert result["status"] == "success"
        assert "shell_settings.json" in result["skipped"]
        assert "warnings" in result
        assert any("shell_settings.json" in w for w in result["warnings"])
