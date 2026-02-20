"""Workflow orchestration tools for the MCP server."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Literal, Optional

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
from ..utils.formatters import ResponseFormat, ResponseFormatter

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
    offset_db_path: str | Path = "offset_database.toml",
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
            offset_db_path=offset_db_path,
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
        name="ot2_full_workflow",
        description="""Execute the complete protocol pipeline: validate → generate → simulate → deploy.

WHEN TO USE: This is the PREFERRED tool when you want to go from configured settings
to a validated protocol in a single call. Use this instead of calling ot2_validate_configuration,
ot2_generate_protocol, and ot2_simulate_protocol separately.

WHEN NOT TO USE: When you only need one step (just validation, just simulation, etc.)
Use the individual tools instead.

TYPICAL USAGE:
ot2_full_workflow(csv_path="CSVs/experiment.csv")  # validate + generate + simulate
ot2_full_workflow(csv_path="CSVs/experiment.csv", deploy=True, copy_to_clipboard=True)

STEPS (in order):
1. Validate: CSV format, deck layout, labware references
2. Generate: Compile TOML + CSV into CherryPick_OT2.py
3. Simulate: Run opentrons_simulate (skip with simulate=False)
4. Deploy: Copy to target path / clipboard (skip with deploy=False)

Stops on first error and reports which stage failed.
Check logs://last-simulation for simulation details after running.

Response Format: json (default), markdown (pipeline view), concise (one-line status).
""",
        annotations={
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True
        }
    )
    def full_workflow_tool(  # pragma: no cover - executed via run_full_workflow tests
        csv_path: str,
        settings_path: str = str(DEFAULT_SETTINGS_PATH),
        labware_path: str = str(DEFAULT_LABWARE_PATH),
        protocol_path: str = str(DEFAULT_PROTOCOL_PATH),
        offset_db_path: str = "offset_database.toml",
        simulate: bool = True,
        labware_env_path: Optional[str] = None,
        deploy: bool = False,
        deployment_target: Optional[str] = None,
        copy_to_clipboard: bool = False,
        clipboard_command: Optional[str] = None,
        response_format: Literal["json", "markdown", "concise"] = "json",
    ) -> str | Dict[str, Any]:
        result = run_full_workflow(
            csv_path=csv_path,
            settings_path=settings_path,
            labware_path=labware_path,
            protocol_path=protocol_path,
            offset_db_path=offset_db_path,
            simulate=simulate,
            labware_env_path=labware_env_path,
            deploy=deploy,
            deployment_target=deployment_target,
            copy_to_clipboard=copy_to_clipboard,
            clipboard_command=clipboard_command,
        )

        if response_format == "json":
            return result

        return ResponseFormatter.format(
            result,
            tool_type="workflow",
            format_type=ResponseFormat(response_format),
        )
