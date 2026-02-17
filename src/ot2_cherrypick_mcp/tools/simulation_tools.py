"""Simulation related MCP tools."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Literal, Optional

from fastmcp import FastMCP

from ..core.simulation import DEFAULT_LOG_FILE, simulate_protocol
from ..utils.errors import ConfigurationError, SimulationError
from ..utils.formatters import ResponseFormat, ResponseFormatter

DEFAULT_PROTOCOL_PATH = Path("CherryPick_OT2.py")

__all__ = ["register_simulation_tools", "run_simulation"]


def run_simulation(
    *,
    protocol_path: str | Path = DEFAULT_PROTOCOL_PATH,
    labware_path: Optional[str | Path] = None,
    timeout: int = 180,
    log_file: str | Path | None = DEFAULT_LOG_FILE,
) -> Dict[str, object]:
    """Execute an OT-2 simulation and return captured output."""

    result = simulate_protocol(
        protocol_path=protocol_path,
        labware_path=labware_path,
        timeout=timeout,
        log_file=log_file,
    )

    return {
        "command": result["command"],
        "stdout": result["stdout"],
        "stderr": result["stderr"],
        "returncode": result["returncode"],
        "log_file": str(log_file) if log_file is not None else None,
    }


def register_simulation_tools(mcp: FastMCP) -> None:
    """Register simulation tools with the FastMCP app."""

    @mcp.tool(
        name="ot2_simulate_protocol",
        description="""Run opentrons_simulate to validate a compiled protocol without real hardware.

WHEN TO USE: After ot2_generate_protocol to verify the protocol is valid.
NOT needed if using ot2_full_workflow (it simulates automatically).

LABWARE PATH: Defaults to LABWARE_PATH env variable (directory with custom JSON labware files).
Only override if you have .json labware files in a non-standard location.
This is NOT labware_dict.toml - it's the Opentrons custom labware directory.

COMMON ERRORS AND FIXES:
- "Labware not found" → Check labware_id in labware_dict.toml matches Opentrons library names
- "Slot conflict" → Ensure unique position_rack values in settings.toml working_plate array
- "No tips available" → Add tip racks to deck or change tip_reuse to "always"
- "Invalid well" → CSV references a well that doesn't exist on that labware type

Check logs://last-simulation for detailed output after running.
Response Format: json (default), markdown (formatted summary), concise (pass/fail).
""",
        annotations={
            "readOnlyHint": True,
            "openWorldHint": True
        }
    )
    def simulate_protocol_tool(  # pragma: no cover - executed via run_simulation tests
        protocol_path: str = str(DEFAULT_PROTOCOL_PATH),
        labware_path: Optional[str] = None,
        timeout: int = 180,
        log_file: Optional[str] = str(DEFAULT_LOG_FILE),
        response_format: Literal["json", "markdown", "concise"] = "json",
    ) -> str | Dict[str, Any]:
        try:
            result = run_simulation(
                protocol_path=protocol_path,
                labware_path=labware_path,
                timeout=timeout,
                log_file=log_file,
            )

            if response_format == "json":
                return result

            return ResponseFormatter.format(
                result,
                tool_type="simulation",
                format_type=ResponseFormat(response_format),
            )
        except (ConfigurationError, SimulationError) as exc:
            raise SimulationError(f"Simulation failed: {exc}") from exc
