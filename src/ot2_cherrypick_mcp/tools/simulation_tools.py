"""Simulation related MCP tools."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

from fastmcp import FastMCP

from ..core.simulation import DEFAULT_LOG_FILE, simulate_protocol
from ..utils.errors import ConfigurationError, SimulationError

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
        name="simulate_protocol",
        description="""Run opentrons_simulate for the generated protocol.

IMPORTANT: The labware_path parameter expects a DIRECTORY containing JSON labware files,
NOT the labware_dict.toml configuration file.

**Default behavior (RECOMMENDED):**
- Omit labware_path parameter entirely (or pass None)
- The simulator will use the LABWARE_PATH environment variable configured in the MCP server
- This points to the Opentrons custom labware directory with JSON definitions

**Only provide labware_path if:**
- You need to override the default labware directory
- You have a specific directory path containing .json labware files

Example: simulate_protocol(protocol_path="CherryPick_OT2.py")  # Uses env LABWARE_PATH
DO NOT: simulate_protocol(protocol_path="CherryPick_OT2.py", labware_path="labware_dict.toml")  # ERROR!
""",
    )
    def simulate_protocol_tool(  # pragma: no cover - executed via run_simulation tests
        protocol_path: str = str(DEFAULT_PROTOCOL_PATH),
        labware_path: Optional[str] = None,
        timeout: int = 180,
        log_file: Optional[str] = str(DEFAULT_LOG_FILE),
    ) -> Dict[str, object]:
        try:
            return run_simulation(
                protocol_path=protocol_path,
                labware_path=labware_path,
                timeout=timeout,
                log_file=log_file,
            )
        except (ConfigurationError, SimulationError) as exc:
            raise SimulationError(f"Simulation failed: {exc}") from exc
