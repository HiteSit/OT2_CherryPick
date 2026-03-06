"""Deployment tools exposed via MCP."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Optional, Sequence

from fastmcp import FastMCP

from ..core.deployment import DEFAULT_CLIP_COMMAND, deploy_protocol, deploy_to_opentrons_dir
from ..utils.errors import ConfigurationError, DeploymentError

DEFAULT_PROTOCOL_PATH = Path("CherryPick_OT2.py")

__all__ = ["register_deployment_tools", "run_deployment"]


def run_deployment(
    *,
    protocol_path: str | Path = DEFAULT_PROTOCOL_PATH,
    target_path: Optional[str | Path] = None,
    opentrons_dir: Optional[str | Path] = None,
    copy_to_clipboard: bool = False,
    clipboard_command: Sequence[str] | None = DEFAULT_CLIP_COMMAND,
) -> Dict[str, object]:
    """Deploy the generated protocol via filesystem/clipboard.

    Priority: explicit target_path > opentrons_dir param > OPENTRONS_DIR env var.
    When opentrons_dir is resolved, uses auto-UUID deployment.
    """

    # Priority: explicit target_path > opentrons_dir param > OPENTRONS_DIR env var
    if target_path is not None:
        return deploy_protocol(
            protocol_path=protocol_path,
            target_path=target_path,
            copy_to_clipboard=copy_to_clipboard,
            clipboard_command=clipboard_command,
        )

    effective_opentrons_dir = opentrons_dir or os.getenv("OPENTRONS_DIR")
    if effective_opentrons_dir is not None:
        return deploy_to_opentrons_dir(
            protocol_path=protocol_path,
            opentrons_dir=effective_opentrons_dir,
            copy_to_clipboard=copy_to_clipboard,
            clipboard_command=clipboard_command,
        )

    return deploy_protocol(
        protocol_path=protocol_path,
        copy_to_clipboard=copy_to_clipboard,
        clipboard_command=clipboard_command,
    )


def register_deployment_tools(mcp: FastMCP) -> None:
    """Register deployment-related tools with FastMCP."""

    @mcp.tool(
        name="ot2_deploy_to_opentrons",
        description="""Deploy the compiled protocol to Opentrons App or clipboard.

WHEN TO USE: After successful simulation. NOT needed if using ot2_full_workflow
with deploy=True (it deploys automatically).

DEPLOYMENT MODES (in priority order):
1. Explicit target_path: deploy_to_opentrons(target_path="/path/to/dir/") — manual override
2. opentrons_dir: deploy_to_opentrons(opentrons_dir="/path/to/Opentrons") — auto-creates UUID protocol dir
3. OPENTRONS_DIR env var: auto-detected, same auto-UUID behavior as #2
4. Clipboard only: deploy_to_opentrons(copy_to_clipboard=True)

AUTO-UUID DEPLOYMENT (opentrons_dir):
When opentrons_dir is set (or read from OPENTRONS_DIR env var), the protocol is deployed to:
  {opentrons_dir}/protocols/{new-uuid}/src/{protocol_file}
This creates a fresh protocol entry in the Opentrons App automatically.

CLIPBOARD COMMANDS by platform:
- Windows/WSL: "clip.exe" (default)
- macOS: "pbcopy"
- Linux (X11): "xclip -selection clipboard"

After deployment the protocol is ready to import into Opentrons App,
run Labware Position Check for calibration, and execute on the OT-2 robot.
""",
        annotations={
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    def deploy_tool(  # pragma: no cover - executed via run_deployment tests
        protocol_path: str = str(DEFAULT_PROTOCOL_PATH),
        target_path: Optional[str] = None,
        opentrons_dir: Optional[str] = None,
        copy_to_clipboard: bool = False,
        clipboard_command: Optional[str] = None,
    ) -> Dict[str, object]:
        command_seq: Sequence[str] | None = None
        if clipboard_command is not None:
            command_seq = [clipboard_command]
        try:
            return run_deployment(
                protocol_path=protocol_path,
                target_path=target_path,
                opentrons_dir=opentrons_dir,
                copy_to_clipboard=copy_to_clipboard,
                clipboard_command=command_seq,
            )
        except (ConfigurationError, DeploymentError) as exc:
            raise DeploymentError(f"Deployment failed: {exc}") from exc
