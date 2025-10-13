"""Workflow orchestration tools for the MCP server."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

from fastmcp import FastMCP

from .protocol_tools import run_generate_protocol
from .simulation_tools import run_simulation
from .validation_tools import run_validation
from ..utils.errors import (
    ConfigurationError,
    ProtocolGenerationError,
    SimulationError,
)

DEFAULT_SETTINGS_PATH = Path("settings.toml")
DEFAULT_LABWARE_PATH = Path("labware_dict.toml")
DEFAULT_PROTOCOL_PATH = Path("CherryPick_OT2.py")

__all__ = ["register_workflow_tools", "run_full_workflow"]


def run_full_workflow(
    *,
    csv_path: str,
    settings_path: str | Path = DEFAULT_SETTINGS_PATH,
    labware_path: str | Path = DEFAULT_LABWARE_PATH,
    protocol_path: str | Path = DEFAULT_PROTOCOL_PATH,
    simulate: bool = True,
    labware_env_path: Optional[str | Path] = None,
) -> Dict[str, object]:
    """Execute validation, generation, and optional simulation in sequence."""

    validation = run_validation(
        csv_path=csv_path,
        settings_path=settings_path,
        labware_path=labware_path,
    )

    response: Dict[str, object] = {"validation": validation}

    if validation.get("status") == "error":
        response.update({
            "status": "error",
            "generation": None,
            "simulation": None,
        })
        return response

    try:
        generation = run_generate_protocol(
            csv_path=csv_path,
            settings_path=settings_path,
            labware_path=labware_path,
            protocol_path=protocol_path,
        )
    except (ConfigurationError, ProtocolGenerationError) as exc:
        response.update({
            "status": "error",
            "generation": {"error": str(exc)},
            "simulation": None,
        })
        return response

    response["generation"] = generation

    if not simulate:
        response.update({"status": "ok", "simulation": None})
        return response

    try:
        simulation = run_simulation(
            protocol_path=protocol_path,
            labware_path=labware_env_path,
        )
    except SimulationError as exc:
        response.update({
            "status": "error",
            "simulation": {"error": str(exc)},
        })
        return response

    response["simulation"] = simulation
    response["status"] = "ok"
    return response


def register_workflow_tools(mcp: FastMCP) -> None:
    """Register workflow orchestration tools."""

    @mcp.tool(
        name="full_workflow",
        description="Validate configuration, generate protocol, and optionally simulate.",
    )
    def full_workflow_tool(  # pragma: no cover - executed via run_full_workflow tests
        csv_path: str,
        settings_path: str = str(DEFAULT_SETTINGS_PATH),
        labware_path: str = str(DEFAULT_LABWARE_PATH),
        protocol_path: str = str(DEFAULT_PROTOCOL_PATH),
        simulate: bool = True,
        labware_env_path: Optional[str] = None,
    ) -> Dict[str, object]:
        return run_full_workflow(
            csv_path=csv_path,
            settings_path=settings_path,
            labware_path=labware_path,
            protocol_path=protocol_path,
            simulate=simulate,
            labware_env_path=labware_env_path,
        )
