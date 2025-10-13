"""
Configuration resource definitions for MCP clients.
"""

from __future__ import annotations

from fastmcp import FastMCP

from ..utils.errors import ConfigurationError
from ..utils.toml import TomlHandler

__all__ = ["register_config_resources"]


def _read_toml_text(path: str) -> str:
    handler = TomlHandler(path)
    return handler.read_text()


def register_config_resources(mcp: FastMCP) -> None:
    """Register TOML configuration resources with the FastMCP app."""

    @mcp.resource("config://settings", description="settings.toml configuration file")
    def get_settings() -> str:  # pragma: no cover - simple wrapper
        try:
            return _read_toml_text("settings.toml")
        except ConfigurationError as exc:
            return f"Error reading settings.toml: {exc}"

    @mcp.resource("config://labware", description="labware_dict.toml catalog file")
    def get_labware() -> str:  # pragma: no cover - simple wrapper
        try:
            return _read_toml_text("labware_dict.toml")
        except ConfigurationError as exc:
            return f"Error reading labware_dict.toml: {exc}"
