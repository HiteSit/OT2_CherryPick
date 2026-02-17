"""Validation-related MCP tools."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Literal

from fastmcp import FastMCP

from ..core.validation import validate_configuration
from ..utils.errors import ConfigurationError
from ..utils.formatters import ResponseFormat, ResponseFormatter

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
        name="ot2_validate_configuration",
        description="""Pre-flight validation of settings, labware, and CSV before protocol generation.

WHEN TO USE: Before ot2_generate_protocol to catch configuration errors early.
NOT needed if using ot2_full_workflow (it validates automatically as step 1).

CHECKS PERFORMED:
- TOML syntax and structure (settings.toml, labware_dict.toml)
- Labware references exist in catalog
- Deck slot conflicts (no duplicate position_rack values)
- CSV column structure (required columns present)
- Volume ranges within pipette capacity
- Multi-channel mode compatibility (multi mode requires 96/384-well plates)
- Height specification consistency (cannot use both Height AND Top for same position)

Returns structured errors (must fix) and warnings (should review).
Response Format: json (default), markdown (formatted report), concise (pass/fail).

EXAMPLE: ot2_validate_configuration(csv_path="CSVs/experiment.csv")
""",
        annotations={
            "readOnlyHint": True,
            "openWorldHint": False
        }
    )
    def validate_configuration_tool(  # pragma: no cover - executed via run_validation tests
        csv_path: str,
        settings_path: str = str(DEFAULT_SETTINGS_PATH),
        labware_path: str = str(DEFAULT_LABWARE_PATH),
        response_format: Literal["json", "markdown", "concise"] = "json",
    ) -> str | Dict[str, Any]:
        if not csv_path:
            raise ConfigurationError("csv_path parameter is required")

        result = run_validation(
            settings_path=settings_path,
            labware_path=labware_path,
            csv_path=csv_path,
        )

        if response_format == "json":
            return result

        return ResponseFormatter.format(
            result,
            tool_type="validation",
            format_type=ResponseFormat(response_format),
        )
