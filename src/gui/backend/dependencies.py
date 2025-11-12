"""
Global dependency factories for the GUI backend.
"""

from __future__ import annotations

from functools import lru_cache

from .state import FileStateStore


@lru_cache(maxsize=1)
def get_state_store() -> FileStateStore:
    """Return the singleton file-backed state store."""

    return FileStateStore()


__all__ = ["get_state_store"]
