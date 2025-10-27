"""Project management tools for MCP."""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Dict

from fastmcp import FastMCP

from ..core.archive import create_project_archive
from ..utils.paths import get_repo_root, project_directory_info

__all__ = [
    "register_project_tools",
    "initialize_project",
    "get_active_project_directory",
    "export_project_archive",
]


def initialize_project() -> Dict[str, object]:
    """
    Initialize a new OT2 project directory with template files.

    Reads the project directory path from the OT2_PROJECT_DIR environment
    variable and creates the necessary structure with configuration templates.

    Creates:
        - settings.toml (from template)
        - labware_dict.toml (from template)
        - CherryPick_OT2.py (protocol template)
        - CSVs/ directory with example files
        - logs/ directory (empty)

    Returns:
        Dict with project initialization summary.

    Raises:
        ValueError: If OT2_PROJECT_DIR is not set.
        IOError: If template files cannot be copied.
    """
    # Get project directory from environment
    project_dir_str = os.getenv("OT2_PROJECT_DIR")
    if not project_dir_str:
        raise ValueError(
            "OT2_PROJECT_DIR environment variable is required. "
            "Set it in your MCP configuration before calling initialize_project."
        )

    project_dir = Path(project_dir_str)

    # Create project directory if it doesn't exist
    project_dir.mkdir(parents=True, exist_ok=True)

    # Get repo root to find template files
    repo_root = get_repo_root()

    # Track what was created
    created_files = []
    created_dirs = []

    # Copy template files
    templates = [
        ("settings.toml", "settings.toml"),
        ("labware_dict.toml", "labware_dict.toml"),
        ("CherryPick_OT2.py", "CherryPick_OT2.py"),
    ]

    for src_name, dest_name in templates:
        src_path = repo_root / src_name
        dest_path = project_dir / dest_name

        if not src_path.exists():
            raise IOError(f"Template file not found: {src_path}")
        shutil.copy2(src_path, dest_path)
        created_files.append(dest_name)

    # Copy CSVs directory
    src_csvs = repo_root / "CSVs"
    dest_csvs = project_dir / "CSVs"

    if src_csvs.exists() and src_csvs.is_dir():
        if dest_csvs.exists():
            created_dirs.append("CSVs/ (already exists, skipped)")
        else:
            shutil.copytree(src_csvs, dest_csvs)
            csv_files = list(dest_csvs.glob("*.csv"))
            created_dirs.append(f"CSVs/ ({len(csv_files)} files)")
    else:
        # Create empty CSVs directory if template doesn't exist
        dest_csvs.mkdir(exist_ok=True)
        created_dirs.append("CSVs/ (empty)")

    # Create logs directory
    logs_dir = project_dir / "logs"
    logs_dir.mkdir(exist_ok=True)
    if not (logs_dir / ".gitkeep").exists():
        (logs_dir / ".gitkeep").touch()
    created_dirs.append("logs/")

    return {
        "project_directory": str(project_dir),
        "created_files": created_files,
        "created_directories": created_dirs,
        "status": "success",
        "message": (
            f"Project initialized at {project_dir}\n"
            f"Created {len(created_files)} files and {len(created_dirs)} directories.\n"
            f"You can now use other MCP tools to work with this project."
        ),
    }


def get_active_project_directory() -> Dict[str, object]:
    """Return information about the current project directory."""
    info = project_directory_info()
    path = info["path"]
    return {
        "project_directory": str(path),
        "auto_created": bool(info["auto_created"]),
        "message": (
            "Temporary directory created for this session."
            if info["auto_created"]
            else "Using project directory provided by OT2_PROJECT_DIR."
        ),
    }


def export_project_archive(*, as_base64: bool = False) -> Dict[str, object]:
    """Archive the current project workspace."""
    return create_project_archive(as_base64=as_base64)


def register_project_tools(mcp: FastMCP) -> None:
    """Register project management tools with the MCP server."""

    @mcp.tool(
        name="initialize_project",
        description=(
            "Create the OT-2 project structure by copying template TOML files, "
            "the protocol stub, and the CSV/log directories. Reads "
            "OT2_PROJECT_DIR from the environment and should be called before "
            "other tools when the workspace is missing."
        ),
    )
    def initialize_project_tool() -> str:
        """Initialize the OT-2 project directory and return a status message."""
        result = initialize_project()
        return result["message"]

    @mcp.tool(
        name="get_project_directory",
        description=(
            "Return the path of the currently active OT-2 project directory. "
            "If the server auto-created a temporary workspace, auto_created "
            "will be True so you can decide whether to export or initialize it."
        ),
    )
    def get_project_directory_tool() -> Dict[str, object]:
        """Provide project directory details to the caller."""
        return get_active_project_directory()

    @mcp.tool(
        name="export_project_archive",
        description=(
            "Create a zip archive of the current project workspace. Optionally set "
            "as_base64=true to receive the archive contents inline."
        ),
    )
    def export_project_archive_tool(as_base64: bool = False) -> Dict[str, object]:
        """Generate an archive and return its location (and optional payload)."""
        return export_project_archive(as_base64=as_base64)
