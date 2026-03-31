"""GUI sync tools for bridging MCP project directory with Docker GUI workspace."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Sequence

from fastmcp import FastMCP

from ..utils.errors import ConfigurationError, SyncError
from ..utils.paths import get_project_root

__all__ = [
    "register_gui_sync_tools",
    "create_shell_settings",
    "sync_to_gui",
]

CONTAINER_NAME = "ot2-cherrypick-backend"
CONTAINER_TARGET_DIR = "/app/gui_state"

SYNCABLE_FILES: tuple[str, ...] = (
    "settings.toml",
    "labware_dict.toml",
    "CherryPick_OT2.py",
    "shell_settings.json",
    "opentrons_labware_official.txt",
    "CSVs",
)
# NOTE: offset_database.toml is intentionally EXCLUDED from sync.
# It contains per-slot calibration offsets that may differ between
# MCP workspace and GUI, and should never be overwritten.

_WINDOWS_ABS_PATH = re.compile(r"^[A-Za-z]:\\")


def create_shell_settings(
    *,
    opentrons_dir_win: str,
) -> dict[str, object]:
    """Create shell_settings.json in the MCP project directory.

    Args:
        opentrons_dir_win: Windows absolute path to Opentrons App data dir
            (e.g., ``"C:\\Users\\ricca\\AppData\\Roaming\\Opentrons"``).

    Returns:
        Dict with status, path written, and the cleaned value.

    Raises:
        ConfigurationError: If path format is invalid.
    """
    cleaned = opentrons_dir_win.strip().rstrip("\\")

    if not cleaned:
        raise ConfigurationError(
            "opentrons_dir_win must not be empty. "
            "Provide a Windows absolute path, e.g. "
            '"C:\\Users\\you\\AppData\\Roaming\\Opentrons".'
        )

    if "/" in cleaned:
        raise ConfigurationError(
            f"opentrons_dir_win must be a Windows path with backslashes, "
            f"not forward slashes: {cleaned!r}"
        )

    if not _WINDOWS_ABS_PATH.match(cleaned):
        raise ConfigurationError(
            f"opentrons_dir_win must be a Windows absolute path "
            f"(e.g. C:\\Users\\...): {cleaned!r}"
        )

    project_dir = get_project_root()
    dest = project_dir / "shell_settings.json"
    data = {"opentrons_dir_win": cleaned}
    dest.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    return {
        "status": "success",
        "path": str(dest),
        "opentrons_dir_win": cleaned,
    }


# ---------------------------------------------------------------------------
# Docker helpers
# ---------------------------------------------------------------------------

def _run_docker(
    args: Sequence[str],
    *,
    timeout: int = 10,
) -> subprocess.CompletedProcess[str]:
    """Run a Docker CLI command, translating errors to SyncError."""
    try:
        return subprocess.run(
            ["docker", *args],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError as exc:
        raise SyncError(
            "Docker CLI not found. Install Docker to use GUI sync."
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise SyncError(
            f"Docker command timed out after {timeout}s: docker {' '.join(args)}"
        ) from exc


def _ensure_container_running() -> None:
    """Assert the backend container is running."""
    result = _run_docker(
        ["inspect", "--format", "{{.State.Running}}", CONTAINER_NAME],
    )
    if result.returncode != 0:
        raise SyncError(
            f"Container '{CONTAINER_NAME}' not found. "
            "Start the GUI with 'docker compose up -d' from the docker/ directory."
        )
    if result.stdout.strip().lower() != "true":
        raise SyncError(
            f"Container '{CONTAINER_NAME}' exists but is not running. "
            "Start it with 'docker compose up -d' from the docker/ directory."
        )


# ---------------------------------------------------------------------------
# Sync logic
# ---------------------------------------------------------------------------

def sync_to_gui(
    *,
    files: list[str] | None = None,
) -> dict[str, object]:
    """Sync MCP project directory content to the Docker GUI volume.

    Args:
        files: Optional list of specific files/dirs to sync.
            Defaults to all :data:`SYNCABLE_FILES` that exist in the project dir.

    Returns:
        Dict with synced/skipped lists and container info.

    Raises:
        SyncError: If Docker is unavailable or the container is not running.
        ConfigurationError: If invalid file names are requested.
    """
    # Validate requested files
    to_sync: list[str]
    if files is not None:
        invalid = [f for f in files if f not in SYNCABLE_FILES]
        if invalid:
            raise ConfigurationError(
                f"Unknown file(s): {invalid}. "
                f"Valid options: {list(SYNCABLE_FILES)}"
            )
        to_sync = list(files)
    else:
        to_sync = list(SYNCABLE_FILES)

    # Verify Docker is installed (fast smoke check)
    _run_docker(["version", "--format", "{{.Client.Version}}"])

    # Verify container is running
    _ensure_container_running()

    project_dir = get_project_root()
    synced: list[str] = []
    skipped: list[str] = []
    failed: list[dict[str, str]] = []

    for name in to_sync:
        src = project_dir / name
        if not src.exists():
            skipped.append(name)
            continue

        dest = f"{CONTAINER_NAME}:{CONTAINER_TARGET_DIR}/{name}"

        if src.is_dir():
            # Ensure target directory exists, then copy contents (not the dir itself)
            _run_docker(
                ["exec", CONTAINER_NAME, "mkdir", "-p", f"{CONTAINER_TARGET_DIR}/{name}"],
            )
            result = _run_docker(
                ["cp", f"{src}/.", dest],
                timeout=30,
            )
        else:
            result = _run_docker(["cp", str(src), dest], timeout=30)

        if result.returncode != 0:
            failed.append({"name": name, "error": result.stderr.strip()})
        else:
            synced.append(name)

    if failed:
        details = "; ".join(f"{f['name']}: {f['error']}" for f in failed)
        raise SyncError(f"docker cp failed for: {details}")

    warnings: list[str] = []
    if "shell_settings.json" in skipped:
        warnings.append(
            "shell_settings.json not found in project directory — "
            "the GUI needs this file for simulation and deployment paths. "
            "Use ot2_create_shell_settings to set it up."
        )

    result: dict[str, object] = {
        "status": "success",
        "synced": synced,
        "skipped": skipped,
        "container": CONTAINER_NAME,
    }
    if warnings:
        result["warnings"] = warnings
    return result


# ---------------------------------------------------------------------------
# MCP registration
# ---------------------------------------------------------------------------

def register_gui_sync_tools(mcp: FastMCP) -> None:
    """Register GUI sync tools with FastMCP."""

    @mcp.tool(
        name="ot2_create_shell_settings",
        description=(
            "Create shell_settings.json in the MCP project directory.\n\n"
            "WHEN TO USE:\n"
            "- User mentions Opentrons App path, labware folder, or protocol folder\n"
            "- User says 'set up paths', 'configure Opentrons location', 'where is Opentrons'\n\n"
            "PARAMETER: opentrons_dir_win — Windows absolute path (backslashes required).\n"
            'Typical: "C:\\Users\\<name>\\AppData\\Roaming\\Opentrons"\n'
            "The GUI derives labware/ and protocols/ subdirectories from this root."
        ),
        annotations={
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    def create_shell_settings_tool(
        opentrons_dir_win: str,
    ) -> dict[str, object]:
        """Create shell_settings.json with the Opentrons App data directory path."""
        return create_shell_settings(opentrons_dir_win=opentrons_dir_win)

    @mcp.tool(
        name="ot2_sync_to_gui",
        description=(
            "Sync MCP project directory content to the Docker GUI volume.\n\n"
            "WHEN TO USE: Only when the user explicitly asks to sync/push to the GUI.\n"
            "Do NOT call automatically after other tools — this is a separate, user-initiated action.\n\n"
            "PREREQUISITES:\n"
            "- Docker container 'ot2-cherrypick-backend' must be running.\n"
            "- shell_settings.json should exist in the project directory.\n"
            "  If missing, sync still completes but the GUI won't be able to simulate or deploy.\n"
            "  In that case, ask the user for their Opentrons App path and call\n"
            "  ot2_create_shell_settings first, then retry sync.\n\n"
            "BEHAVIOR: One-way push (MCP → GUI). GUI-only files are preserved.\n"
            "FILES SYNCED (by default all that exist):\n"
            "- settings.toml, labware_dict.toml, CherryPick_OT2.py\n"
            "- shell_settings.json, opentrons_labware_official.txt\n"
            "- CSVs/ directory (additive — GUI-only CSVs are preserved)\n"
            "NOT SYNCED: offset_database.toml (calibration data — never overwritten).\n\n"
            'OPTIONAL: Pass files=["settings.toml", "CSVs"] to sync only specific items.'
        ),
        annotations={
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    def sync_to_gui_tool(
        files: list[str] | None = None,
    ) -> dict[str, object]:
        """Sync project files to the Docker GUI workspace."""
        return sync_to_gui(files=files)
