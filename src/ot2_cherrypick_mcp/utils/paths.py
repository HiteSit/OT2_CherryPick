"""
Filesystem helpers scoped to the repository layout.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Union


_PathLike = Union[str, Path]


def get_repo_root() -> Path:
    """Return the repository root directory (where source code is installed)."""
    return Path(__file__).resolve().parents[3]


def get_project_root() -> Path:
    """
    Return the project directory from OT2_PROJECT_DIR environment variable.

    The project directory is where configuration files, CSVs, and generated
    protocols are stored. This is separate from the codebase installation.

    Returns:
        Path to the project directory.

    Raises:
        ValueError: If OT2_PROJECT_DIR is not set or directory doesn't exist.
    """
    project_dir = os.getenv("OT2_PROJECT_DIR")
    if not project_dir:
        raise ValueError(
            "OT2_PROJECT_DIR environment variable is required. "
            "Set it to your project directory path in the MCP configuration."
        )

    path = Path(project_dir)
    if not path.exists():
        raise ValueError(
            f"Project directory does not exist: {path}\n"
            f"Use the 'initialize_project' tool to create the project structure."
        )

    return path


def resolve_repo_path(path: _PathLike) -> Path:
    """Resolve a path relative to the repository root."""
    candidate = Path(path)
    return candidate if candidate.is_absolute() else get_repo_root() / candidate


def resolve_project_path(path: _PathLike) -> Path:
    """Resolve a path relative to the project root."""
    candidate = Path(path)
    return candidate if candidate.is_absolute() else get_project_root() / candidate


__all__ = ["get_repo_root", "get_project_root", "resolve_repo_path", "resolve_project_path"]
