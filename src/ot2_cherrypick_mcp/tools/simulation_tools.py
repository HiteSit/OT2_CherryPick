"""Simulation related MCP tools."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

from fastmcp import FastMCP

from ..core.simulation import simulate_protocol
from ..utils.errors import ConfigurationError, SimulationError

DEFAULT_PROTOCOL_PATH = Path("CherryPick_OT2.py")

__all__ = ["register_simulation_tools", "run_simulation"]


def run_simulation(
    *,
    protocol_path: str | Path = DEFAULT_PROTOCOL_PATH,
    labware_path: Optional[str | Path] = None,
    timeout: int = 180,
) -> Dict[str, object]:
    """Execute an OT-2 simulation and return captured output."""

    result = simulate_protocol(
        protocol_path=protocol_path,
        labware_path=labware_path,
        timeout=timeout,
    )

    return {
        "command": result["command"],
        "stdout": result["stdout"],
        "stderr": result["stderr"],
        "returncode": result["returncode"],
    }


def register_simulation_tools(mcp: FastMCP) -> None:
    """Register simulation tools with the FastMCP app."""

    @mcp.tool(
        name="simulate_protocol",
        description="Run opentrons_simulate for the generated protocol.",
    )
    def simulate_protocol_tool(  # pragma: no cover - executed via run_simulation tests
        protocol_path: str = str(DEFAULT_PROTOCOL_PATH),
        labware_path: Optional[str] = None,
        timeout: int = 180,
    ) -> Dict[str, object]:
        try:
            return run_simulation(protocol_path=protocol_path, labware_path=labware_path, timeout=timeout)
        except (ConfigurationError, SimulationError) as exc:
            raise SimulationError(f"Simulation failed: {exc}") from exc
