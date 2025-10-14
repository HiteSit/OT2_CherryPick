"""Resources exposing simulation logs."""

from __future__ import annotations

from pathlib import Path

from fastmcp import FastMCP

from ..core.simulation import DEFAULT_LOG_FILE
from ..utils.paths import resolve_project_path

__all__ = ["register_log_resources"]


def register_log_resources(mcp: FastMCP) -> None:
    """Register log resources with the FastMCP app."""

    @mcp.resource("logs://last-simulation", description="Most recent simulation log entry")
    def last_simulation() -> str:  # pragma: no cover - simple wrapper
        log_path = resolve_project_path(DEFAULT_LOG_FILE)
        if not log_path.exists():
            return ""
        return log_path.read_text(encoding="utf-8")
