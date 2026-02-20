"""Project management tools for MCP."""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Dict, List

from fastmcp import Context, FastMCP

from ..core.archive import create_project_archive
from ..core.project_context import ProjectContext
from ..utils.paths import (
    _ensure_templates_exist,
    get_project_root,
    get_repo_root,
    project_directory_info,
    reset_auto_project_dir,
)

__all__ = [
    "register_project_tools",
    "initialize_project",
    "get_active_project_directory",
    "export_project_archive",
    "set_project_directory",
    "list_projects",
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
        - offset_database.toml (from template, if exists in repo root)
        - opentrons_labware_official.txt (from template, if exists in repo root)
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

    # Copy required template files
    required_templates = [
        ("settings.toml", "settings.toml"),
        ("labware_dict.toml", "labware_dict.toml"),
        ("CherryPick_OT2.py", "CherryPick_OT2.py"),
    ]
    optional_templates = [
        ("offset_database.toml", "offset_database.toml"),
        ("opentrons_labware_official.txt", "opentrons_labware_official.txt"),
    ]

    for src_name, dest_name in required_templates:
        src_path = repo_root / src_name
        dest_path = project_dir / dest_name

        if not src_path.exists():
            raise IOError(f"Template file not found: {src_path}")
        shutil.copy2(src_path, dest_path)
        created_files.append(dest_name)

    for src_name, dest_name in optional_templates:
        src_path = repo_root / src_name
        dest_path = project_dir / dest_name
        if src_path.exists():
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


def set_project_directory(
    *,
    path: str,
    initialize_templates: bool = True,
    project_ctx: ProjectContext | None = None,
) -> str:
    """Switch the active project directory at runtime.

    Args:
        path: Absolute path to the new project directory.
        initialize_templates: Whether to copy template files into the directory.
        project_ctx: The lifespan ProjectContext (passed from the tool wrapper).

    Returns:
        A human-readable summary of the switch.
    """
    if not os.path.isabs(path):
        raise ValueError(f"Path must be absolute, got: {path}")

    new_path = Path(path)
    old_path = get_project_root()

    # Create directory if needed
    new_path.mkdir(parents=True, exist_ok=True)

    # Optionally copy templates
    if initialize_templates:
        _ensure_templates_exist(new_path)

    # Update the environment variable for backward compat
    os.environ["OT2_PROJECT_DIR"] = str(new_path)

    # Reset the cached auto-created dir so get_project_root() re-reads env
    reset_auto_project_dir()

    # Update the lifespan context if available
    if project_ctx is not None:
        project_ctx.switch_to(new_path, auto_created=False)

    # Build summary
    existing_files = [f.name for f in new_path.iterdir() if f.is_file()]
    csv_dir = new_path / "CSVs"
    available_csvs: List[str] = []
    if csv_dir.is_dir():
        available_csvs = [f.name for f in csv_dir.glob("*.csv")]

    lines = [
        f"Switched project directory.",
        f"  Old: {old_path}",
        f"  New: {new_path}",
    ]
    if existing_files:
        lines.append(f"  Existing files: {', '.join(sorted(existing_files))}")
    if available_csvs:
        lines.append(f"  Available CSVs: {', '.join(sorted(available_csvs))}")
    if not existing_files and not available_csvs:
        lines.append("  Directory is empty (templates were copied)." if initialize_templates else "  Directory is empty.")

    return "\n".join(lines)


def list_projects(
    *,
    scan_parent_directory: str = "",
    project_ctx: ProjectContext | None = None,
) -> str:
    """List active, recent, and optionally discovered projects.

    Args:
        scan_parent_directory: If provided, scan this absolute path for
            subdirectories containing a settings.toml file.
        project_ctx: The lifespan ProjectContext (passed from the tool wrapper).

    Returns:
        Formatted text listing projects.
    """
    lines: List[str] = []

    # Current active project
    current = get_project_root()
    info = project_directory_info()
    mode = "temporary" if info["auto_created"] else "persistent"
    lines.append(f"Active project: {current} ({mode})")

    # Recent projects from context
    recent: List[str] = []
    if project_ctx is not None:
        recent = project_ctx.recent_projects

    if recent:
        lines.append("")
        lines.append("Recent projects:")
        for i, rp in enumerate(recent, 1):
            exists = Path(rp).is_dir()
            marker = "" if exists else " [not found]"
            lines.append(f"  {i}. {rp}{marker}")
    else:
        lines.append("")
        lines.append("Recent projects: (none)")

    # Optional scan
    if scan_parent_directory:
        if not os.path.isabs(scan_parent_directory):
            lines.append("")
            lines.append(f"Error: scan_parent_directory must be absolute, got: {scan_parent_directory}")
        else:
            parent = Path(scan_parent_directory)
            if parent.is_dir():
                discovered: List[str] = []
                for child in sorted(parent.iterdir()):
                    if child.is_dir() and (child / "settings.toml").exists():
                        discovered.append(str(child))
                lines.append("")
                if discovered:
                    lines.append(f"Projects found in {parent}:")
                    for dp in discovered:
                        lines.append(f"  - {dp}")
                else:
                    lines.append(f"No projects with settings.toml found in {parent}")
            else:
                lines.append("")
                lines.append(f"Directory not found: {parent}")

    return "\n".join(lines)


def _get_project_ctx(ctx: Context) -> ProjectContext | None:
    """Safely extract the ProjectContext from the FastMCP lifespan context."""
    try:
        lc = ctx.request_context.lifespan_context
        if isinstance(lc, ProjectContext):
            return lc
    except (AttributeError, ValueError):
        pass
    return None


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

    @mcp.tool(
        name="ot2_set_project_directory",
        description=(
            "Switch the active project directory at runtime. "
            "Provide an absolute path. The directory is created if it does not "
            "exist. By default, template files are copied into the new directory. "
            "The previous project is saved to the recent-projects history. "
            "Use ot2_list_projects() to see history and discover projects."
        ),
        annotations={
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True
        }
    )
    def set_project_directory_tool(
        ctx: Context,
        path: str,
        initialize_templates: bool = True,
    ) -> str:
        """Switch the active project directory."""
        project_ctx = _get_project_ctx(ctx)
        return set_project_directory(
            path=path,
            initialize_templates=initialize_templates,
            project_ctx=project_ctx,
        )

    @mcp.tool(
        name="ot2_list_projects",
        description=(
            "List the active project, recent project history, and optionally "
            "scan a parent directory for subdirectories that contain a "
            "settings.toml file (i.e. valid OT-2 project directories)."
        ),
        annotations={
            "readOnlyHint": True,
            "openWorldHint": True
        }
    )
    def list_projects_tool(
        ctx: Context,
        scan_parent_directory: str = "",
    ) -> str:
        """List active and recent projects."""
        project_ctx = _get_project_ctx(ctx)
        return list_projects(
            scan_parent_directory=scan_parent_directory,
            project_ctx=project_ctx,
        )
