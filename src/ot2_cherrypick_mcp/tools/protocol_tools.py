"""
Protocol-related MCP tools.

This module exposes helpers that wrap the legacy `helper_cherry_pick` script so
they can be consumed safely by MCP clients.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from fastmcp import FastMCP

from ..core import protocol_generator
from ..utils.errors import ConfigurationError, ProtocolGenerationError
from ..utils.paths import resolve_project_path

DEFAULT_LABWARE_PATH = Path("labware_dict.toml")
DEFAULT_SETTINGS_PATH = Path("settings.toml")
DEFAULT_PROTOCOL_PATH = Path("CherryPick_OT2.py")

__all__ = ["register_protocol_tools", "run_generate_protocol"]


def run_generate_protocol(
    *,
    csv_path: str,
    settings_path: str | Path = DEFAULT_SETTINGS_PATH,
    labware_path: str | Path = DEFAULT_LABWARE_PATH,
    protocol_path: str | Path = DEFAULT_PROTOCOL_PATH,
    verbose: bool = False,
) -> Dict[str, Any]:
    """
    Generate a protocol by embedding TOML/CSV configuration in the protocol file.

    Args:
        csv_path: Path to the transfer CSV definition.
        settings_path: Path to the settings TOML file.
        labware_path: Path to the labware dictionary TOML file.
        protocol_path: Path to the target OT-2 protocol file.
        verbose: Enable legacy verbose output (defaults to False for MCP use).

    Returns:
        Dict with protocol metadata as produced by `helper_cherry_pick`.

    Raises:
        ConfigurationError: When any of the configuration inputs are missing.
        ProtocolGenerationError: When the helper script fails for another reason.
    """

    csv_file = resolve_project_path(csv_path)
    labware_file = resolve_project_path(labware_path)
    settings_file = resolve_project_path(settings_path)
    protocol_file = resolve_project_path(protocol_path)

    for path, description in (
        (csv_file, "CSV transfer map"),
        (labware_file, "labware TOML"),
        (settings_file, "settings TOML"),
    ):
        if not path.exists():
            raise ConfigurationError(f"{description} not found at {path}")

    if not protocol_file.exists():
        raise ConfigurationError(f"Protocol template not found at {protocol_file}")

    try:
        result = protocol_generator.generate_protocol(
            str(labware_file),
            str(settings_file),
            str(csv_file),
            str(protocol_file),
            verbose=verbose,
        )
    except FileNotFoundError as exc:
        raise ConfigurationError(str(exc)) from exc
    except ValueError as exc:
        raise ProtocolGenerationError(str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive
        raise ProtocolGenerationError(str(exc)) from exc

    return {
        "protocol_file": str(protocol_file),
        "json_size": result.get("json_size"),
        "message": result.get("message"),
    }


def register_protocol_tools(mcp: FastMCP) -> None:
    """Register protocol-related tools with the FastMCP application."""

    @mcp.tool(
        name="ot2_generate_protocol",
        description=(
            "Compile TOML configuration and a transfer CSV into an OT-2 protocol "
            "file with embedded JSON."
        ),
        annotations={
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    def generate_protocol_tool(  # pragma: no cover - exercised via run_generate_protocol tests
        csv_path: str,
        settings_path: str = str(DEFAULT_SETTINGS_PATH),
        labware_path: str = str(DEFAULT_LABWARE_PATH),
        protocol_path: str = str(DEFAULT_PROTOCOL_PATH),
        verbose: bool = False,
    ) -> Dict[str, Any]:
        """
        Generate a cherry-pick protocol.

        Args:
            csv_path: Path to the transfer CSV definition.
            settings_path: Path to the protocol settings TOML file.
            labware_path: Path to the labware dictionary TOML file.
            protocol_path: Path to the protocol file to update.
            verbose: Enable verbose logging from the legacy helper.
        """

        return run_generate_protocol(
            csv_path=csv_path,
            settings_path=settings_path,
            labware_path=labware_path,
            protocol_path=protocol_path,
            verbose=verbose,
        )


