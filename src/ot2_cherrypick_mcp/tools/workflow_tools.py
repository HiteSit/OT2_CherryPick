"""Workflow orchestration tools for the MCP server."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

from fastmcp import FastMCP

from .deployment_tools import run_deployment
from .protocol_tools import run_generate_protocol
from .simulation_tools import run_simulation
from .validation_tools import run_validation
from ..utils.errors import (
    ConfigurationError,
    DeploymentError,
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
    deploy: bool = False,
    deployment_target: Optional[str | Path] = None,
    copy_to_clipboard: bool = False,
    clipboard_command: Optional[str] = None,
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

    if simulate:
        try:
            simulation = run_simulation(
                protocol_path=protocol_path,
                labware_path=labware_env_path,
            )
        except SimulationError as exc:
            response.update({
                "status": "error",
                "simulation": {"error": str(exc)},
                "deployment": None,
            })
            return response

        response["simulation"] = simulation
    else:
        response["simulation"] = None

    if not deploy:
        response["status"] = "ok"
        response["deployment"] = None
        return response

    deployment_kwargs = {
        "protocol_path": protocol_path,
        "target_path": deployment_target,
        "copy_to_clipboard": copy_to_clipboard,
    }
    if clipboard_command is not None:
        deployment_kwargs["clipboard_command"] = [clipboard_command]

    try:
        deployment = run_deployment(**deployment_kwargs)
    except (ConfigurationError, DeploymentError) as exc:
        response.update({
            "status": "error",
            "deployment": {"error": str(exc)},
        })
        return response

    response["deployment"] = deployment
    response["status"] = "ok"
    return response


def register_workflow_tools(mcp: FastMCP) -> None:
    """Register workflow orchestration tools."""

    @mcp.tool(
        name="full_workflow",
        description="""Execute complete protocol workflow: validate → generate → simulate → deploy.

TYPICAL USAGE:
full_workflow(
    csv_path="CSVs/experiment.csv",
    simulate=True,
    deploy=False
)

STEPS PERFORMED:
1. Validate configuration (CSV format, deck layout, labware references)
2. Generate protocol (compile TOML + CSV → CherryPick_OT2.py)
3. Simulate (optional, validates with opentrons_simulate)
4. Deploy (optional, copy to target path or clipboard)

Returns comprehensive results from all stages.
Check logs://last-simulation for simulation details.

PARAMETERS:
- csv_path: Transfer map CSV file
- simulate: Run opentrons_simulate (default: True)
- deploy: Deploy after successful simulation (default: False)
- deployment_target: Path to copy protocol file
- copy_to_clipboard: Also copy to clipboard (default: False)
""",
    )
    def full_workflow_tool(  # pragma: no cover - executed via run_full_workflow tests
        csv_path: str,
        settings_path: str = str(DEFAULT_SETTINGS_PATH),
        labware_path: str = str(DEFAULT_LABWARE_PATH),
        protocol_path: str = str(DEFAULT_PROTOCOL_PATH),
        simulate: bool = True,
        labware_env_path: Optional[str] = None,
        deploy: bool = False,
        deployment_target: Optional[str] = None,
        copy_to_clipboard: bool = False,
        clipboard_command: Optional[str] = None,
    ) -> Dict[str, object]:
        return run_full_workflow(
            csv_path=csv_path,
            settings_path=settings_path,
            labware_path=labware_path,
            protocol_path=protocol_path,
            simulate=simulate,
            labware_env_path=labware_env_path,
            deploy=deploy,
            deployment_target=deployment_target,
            copy_to_clipboard=copy_to_clipboard,
            clipboard_command=clipboard_command,
        )
