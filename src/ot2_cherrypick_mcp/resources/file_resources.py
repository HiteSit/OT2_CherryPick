"""File listing resources exposed via MCP."""

from __future__ import annotations

from pathlib import Path

from fastmcp import FastMCP

from ..utils.paths import resolve_project_path

DEFAULT_CSV_DIR = Path("CSVs")

__all__ = ["register_file_resources"]


def register_file_resources(mcp: FastMCP) -> None:
    """Register file oriented resources with the FastMCP app."""

    @mcp.resource("files://csvs", description="List of available CSV transfer files")
    def list_csvs() -> str:  # pragma: no cover - simple wrapper
        csv_dir = resolve_project_path(DEFAULT_CSV_DIR)
        if not csv_dir.exists():
            return ""
        files = sorted(path.name for path in csv_dir.glob("*.csv"))
        return "\n".join(files)
