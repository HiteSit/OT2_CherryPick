"""Project management tools for MCP."""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Dict

from fastmcp import FastMCP

from ..core.archive import create_project_archive
from ..utils.paths import get_project_root, get_repo_root, project_directory_info

__all__ = [
    "register_project_tools",
    "initialize_project",
    "get_active_project_directory",
    "export_project_archive",
]


def initialize_project() -> Dict[str, object]:
    """
    Initialize project directory with full workspace structure.

    Note: Template files (settings.toml, labware_dict.toml, CherryPick_OT2.py)
    are auto-copied on first tool access, so this function is OPTIONAL.
    Use it when you want to explicitly set up a complete workspace with
    example CSV files.

    Creates:
        - settings.toml (from template, if not exists)
        - labware_dict.toml (from template, if not exists)
        - CherryPick_OT2.py (protocol template, if not exists)
        - CSVs/ directory with example files
        - logs/ directory (empty)

    Works in both modes:
        - With OT2_PROJECT_DIR set: Initializes persistent workspace
        - Without OT2_PROJECT_DIR: Initializes temporary workspace

    Returns:
        Dict with project initialization summary including workspace mode info.

    Raises:
        IOError: If template files cannot be copied.
    """
    # Use get_project_root which handles both temp and persistent modes
    # and auto-copies basic templates
    project_dir = get_project_root()

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

    # Copy CSVs directory (or files if directory already exists)
    src_csvs = repo_root / "CSVs"
    dest_csvs = project_dir / "CSVs"

    if src_csvs.exists() and src_csvs.is_dir():
        dest_csvs.mkdir(exist_ok=True)  # Ensure directory exists

        # Copy CSV files from source to destination
        csv_count = 0
        for csv_file in src_csvs.glob("*.csv"):
            dest_file = dest_csvs / csv_file.name
            if not dest_file.exists():  # Don't overwrite existing files
                shutil.copy2(csv_file, dest_file)
                csv_count += 1

        created_dirs.append(f"CSVs/ ({csv_count} files copied)")
    else:
        # Create empty CSVs directory if source doesn't exist
        dest_csvs.mkdir(exist_ok=True)
        created_dirs.append("CSVs/ (empty)")

    # Create logs directory
    logs_dir = project_dir / "logs"
    logs_dir.mkdir(exist_ok=True)
    if not (logs_dir / ".gitkeep").exists():
        (logs_dir / ".gitkeep").touch()
    created_dirs.append("logs/")

    # Check if this is temp or persistent workspace
    workspace_info = project_directory_info()
    workspace_mode = "temporary" if workspace_info["auto_created"] else "persistent"

    return {
        "project_directory": str(project_dir),
        "workspace_mode": workspace_mode,
        "created_files": created_files,
        "created_directories": created_dirs,
        "status": "success",
        "message": (
            f"Project initialized at {project_dir} ({workspace_mode} workspace)\n"
            f"Created {len(created_files)} files and {len(created_dirs)} directories.\n"
            f"{'Use export_project_archive() to save before session ends.' if workspace_mode == 'temporary' else 'Files will persist across sessions.'}"
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
        name="ot2_initialize_project",
        description=(
            "OPTIONAL: Explicitly initialize project workspace with example CSVs. "
            "Template files (settings.toml, labware_dict.toml, CherryPick_OT2.py) "
            "auto-copy on first tool access, so initialization is not required. "
            "Works in both temp (no OT2_PROJECT_DIR) and persistent modes. "
            "Use to set up complete workspace with example files."
        ),
        annotations={
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    def initialize_project_tool() -> str:
        """Initialize the OT-2 project directory and return a status message."""
        result = initialize_project()
        return result["message"]

    @mcp.tool(
        name="ot2_get_project_directory",
        description=(
            "Return the path of the currently active OT-2 project directory. "
            "If the server auto-created a temporary workspace, auto_created "
            "will be True so you can decide whether to export or initialize it."
        ),
        annotations={
            "readOnlyHint": True,
            "openWorldHint": False
        }
    )
    def get_project_directory_tool() -> Dict[str, object]:
        """Provide project directory details to the caller."""
        return get_active_project_directory()

    @mcp.tool(
        name="ot2_export_project_archive",
        description=(
            "Create a zip archive of the current project workspace. Optionally set "
            "as_base64=true to receive the archive contents inline."
        ),
        annotations={
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": False
        }
    )
    def export_project_archive_tool(as_base64: bool = False) -> Dict[str, object]:
        """Generate an archive and return its location (and optional payload)."""
        return export_project_archive(as_base64=as_base64)
