"""Validation-related MCP tools."""

from __future__ import annotations

from pathlib import Path
from typing import Dict

from fastmcp import FastMCP

from ..core.validation import validate_configuration
from ..utils.errors import ConfigurationError

DEFAULT_SETTINGS_PATH = Path("settings.toml")
DEFAULT_LABWARE_PATH = Path("labware_dict.toml")

__all__ = ["register_validation_tools", "run_validation"]


def run_validation(
    *,
    settings_path: str | Path = DEFAULT_SETTINGS_PATH,
    labware_path: str | Path = DEFAULT_LABWARE_PATH,
    csv_path: str,
) -> Dict[str, object]:
    """Run configuration validation and return structured results."""

    return validate_configuration(
        settings_path=settings_path,
        labware_path=labware_path,
        csv_path=csv_path,
    )


def register_validation_tools(mcp: FastMCP) -> None:
    """Register validation tools with the FastMCP application."""

    @mcp.tool(
        name="validate_configuration",
        description="Validate TOML and CSV inputs before generating protocols.",
    )
    def validate_configuration_tool(  # pragma: no cover - executed via run_validation tests
        csv_path: str,
        settings_path: str = str(DEFAULT_SETTINGS_PATH),
        labware_path: str = str(DEFAULT_LABWARE_PATH),
    ) -> Dict[str, object]:
        if not csv_path:
            raise ConfigurationError("csv_path parameter is required")
        return run_validation(
            settings_path=settings_path,
            labware_path=labware_path,
            csv_path=csv_path,
        )
