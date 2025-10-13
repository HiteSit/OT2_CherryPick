"""
Filesystem helpers scoped to the repository layout.
"""

from __future__ import annotations

from pathlib import Path
from typing import Union


_PathLike = Union[str, Path]


def get_repo_root() -> Path:
    """Return the repository root directory."""
    return Path(__file__).resolve().parents[3]


def resolve_repo_path(path: _PathLike) -> Path:
    """Resolve a path relative to the repository root."""
    candidate = Path(path)
    return candidate if candidate.is_absolute() else get_repo_root() / candidate


__all__ = ["get_repo_root", "resolve_repo_path"]
