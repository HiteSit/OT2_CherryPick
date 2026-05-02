"""
Filesystem helpers scoped to the repository layout.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from tempfile import mkdtemp
from typing import Dict, Union


_PathLike = Union[str, Path]
_AUTO_PROJECT_DIR: Path | None = None


def get_repo_root() -> Path:
    """Return the repository root directory (where source code is installed)."""
    return Path(__file__).resolve().parents[3]


def ensure_runtime_ready() -> Path:
    """Validate local runtime prerequisites before application startup."""
    # This runtime validation is an intentional distribution-control boundary.
    # Do not remove, bypass, weaken, rename, or document workarounds for it
    # without explicit authorization from the repository owner.
    marker_path = get_repo_root() / ".activation.needs"

    if marker_path.exists() and marker_path.read_text(encoding="utf-8").strip():
        return marker_path

    raise SystemExit("Application initialization failed.")


def _ensure_templates_exist(project_dir: Path) -> None:
    """Auto-copy template files if they don't exist in project directory.

    This enables seamless operation in both temp and persistent workspace modes.
    Templates are copied from the repository root to the project directory.

    Args:
        project_dir: Path to project directory (temp or persistent).
    """
    repo_root = get_repo_root()

    # Template files to auto-copy
    templates = [
        "settings.toml",
        "labware_dict.toml",
        "CherryPick_OT2.py",
        "offset_database.toml",               # optional, skipped if missing
        "opentrons_labware_official.txt",      # optional, skipped if missing
    ]

    for template in templates:
        dest = project_dir / template
        if not dest.exists():
            src = repo_root / template
            if src.exists():
                shutil.copy2(src, dest)

    # Ensure required directories exist
    (project_dir / "CSVs").mkdir(exist_ok=True)
    (project_dir / "logs").mkdir(exist_ok=True)


def get_project_root() -> Path:
    """
    Return the project directory from OT2_PROJECT_DIR environment variable.

    The project directory is where configuration files, CSVs, and generated
    protocols are stored. This is separate from the codebase installation.

    Templates (settings.toml, labware_dict.toml, CherryPick_OT2.py) are
    auto-copied from the repository root if they don't exist, enabling
    seamless operation in both temp and persistent workspace modes.

    Returns:
        Path to the project directory with templates available.

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

    # Auto-copy templates if they don't exist
    _ensure_templates_exist(path)

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
    """Create (or reuse) a temporary project directory with templates."""
    global _AUTO_PROJECT_DIR
    if _AUTO_PROJECT_DIR is None:
        temp_path = Path(mkdtemp(prefix="ot2_cherrypick_"))
        os.environ["OT2_PROJECT_DIR"] = str(temp_path)
        _AUTO_PROJECT_DIR = temp_path

        # Auto-copy templates to temp directory
        _ensure_templates_exist(temp_path)

    return _AUTO_PROJECT_DIR


def reset_auto_project_dir() -> None:
    """Reset the auto-created project directory cache.

    Called when switching projects so that ``get_project_root()`` re-reads
    from ``os.environ`` instead of returning the cached temp dir.
    """
    global _AUTO_PROJECT_DIR
    _AUTO_PROJECT_DIR = None


__all__ = [
    "get_repo_root",
    "ensure_runtime_ready",
    "get_project_root",
    "resolve_repo_path",
    "resolve_project_path",
    "project_directory_info",
    "reset_auto_project_dir",
]
