"""
Style-preserving TOML utilities.

Phase 1 only establishes the module skeleton; concrete functionality will follow
once the MCP tools require it.
"""

from __future__ import annotations

from typing import Any


class TomlHandler:
    """Placeholder interface for the TOML handler."""

    def __init__(self, path: str) -> None:
        self.path = path

    def read(self) -> Any:  # pragma: no cover - stub
        """Read the TOML document from disk."""
        raise NotImplementedError

    def write(self, document: Any) -> None:  # pragma: no cover - stub
        """Persist the TOML document to disk."""
        raise NotImplementedError

    def get_value(self, dotted_path: str) -> Any:  # pragma: no cover - stub
        """Retrieve a value using dotted path access."""
        raise NotImplementedError

    def set_value(self, dotted_path: str, value: Any) -> None:  # pragma: no cover - stub
        """Set a value using dotted path access."""
        raise NotImplementedError
