"""Project management tools for MCP."""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Dict

from fastmcp import FastMCP

from ..utils.paths import get_repo_root

__all__ = ["register_project_tools", "initialize_project"]


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


def register_project_tools(mcp: FastMCP) -> None:
    """Register project management tools with the MCP server."""

    @mcp.tool()
    def initialize_project_tool() -> str:
        """
        Initialize a new OT2 project directory with template configuration files.

        Reads the project path from the OT2_PROJECT_DIR environment variable
        (configured in your MCP client settings) and creates:
        - settings.toml - Protocol execution parameters
        - labware_dict.toml - Hardware definitions
        - CherryPick_OT2.py - Protocol template for downstream generation
        - CSVs/ - Directory with example transfer CSV files
        - logs/ - Directory for simulation logs

        This tool must be called before using any other OT2 cherry-pick tools
        if the project directory doesn't exist yet.

        Returns:
            Success message with details of created files and directories.

        Raises:
            ValueError: If OT2_PROJECT_DIR environment variable is not set.
        """
        result = initialize_project()
        return result["message"]
