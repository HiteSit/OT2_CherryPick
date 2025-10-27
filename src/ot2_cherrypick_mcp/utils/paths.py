"""
Filesystem helpers scoped to the repository layout.
"""

from __future__ import annotations

import os
from pathlib import Path
from tempfile import mkdtemp
from typing import Dict, Union


_PathLike = Union[str, Path]
_AUTO_PROJECT_DIR: Path | None = None


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

    If OT2_PROJECT_DIR is not defined, the server falls back to an auto-created
    temporary directory (and records it so the user can retrieve the path).

    Raises:
        ValueError: If OT2_PROJECT_DIR is set but points to a non-directory path.
    """
    project_dir = os.getenv("OT2_PROJECT_DIR")
    if not project_dir:
        return _ensure_auto_project_dir()

    path = Path(project_dir)
    if path.exists() and not path.is_dir():
        raise ValueError(f"Project directory path is not a directory: {path}")

    path.mkdir(parents=True, exist_ok=True)
    return path


def resolve_repo_path(path: _PathLike) -> Path:
    """Resolve a path relative to the repository root."""
    candidate = Path(path)
    return candidate if candidate.is_absolute() else get_repo_root() / candidate


def resolve_project_path(path: _PathLike) -> Path:
    """Resolve a path relative to the project root."""
    candidate = Path(path)
    return candidate if candidate.is_absolute() else get_project_root() / candidate


def project_directory_info() -> Dict[str, object]:
    """Return the active project directory and metadata."""
    root = get_project_root()
    auto_created = _AUTO_PROJECT_DIR is not None and root == _AUTO_PROJECT_DIR
    return {"path": root, "auto_created": auto_created}


def _ensure_auto_project_dir() -> Path:
    """Create (or reuse) a temporary project directory."""
    global _AUTO_PROJECT_DIR
    if _AUTO_PROJECT_DIR is None:
        temp_path = Path(mkdtemp(prefix="ot2_cherrypick_"))
        os.environ["OT2_PROJECT_DIR"] = str(temp_path)
        _AUTO_PROJECT_DIR = temp_path
    return _AUTO_PROJECT_DIR


__all__ = [
    "get_repo_root",
    "get_project_root",
    "resolve_repo_path",
    "resolve_project_path",
    "project_directory_info",
]
