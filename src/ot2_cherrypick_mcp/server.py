"""
Server entry point for the OpenTron cherry-pick MCP integration.
"""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastmcp import FastMCP

from .core.project_context import ProjectContext
from .prompts import register_prompts
from .resources import (
    register_config_resources,
    register_file_resources,
    register_log_resources,
    register_status_resources,
)
from .tools import register_tools
from .utils.logging_config import configure_logging

logger = logging.getLogger(__name__)

APP_NAME = "OT-2 Cherry Pick MCP Server"
APP_INSTRUCTIONS = """OT-2 Cherry-Pick Protocol Generator.

TOOL SELECTION GUIDE - match user intent to the right tool:
- "Set up for viscous/DMSO/glycerol" → ot2_apply_liquid_preset(preset_name="viscous")
- "Set up for volatile/chloroform/hexane" → ot2_apply_liquid_preset(preset_name="slippery")
- "Set up for water/PBS/buffers" → ot2_apply_liquid_preset(preset_name="standard")
- "Change mode/speed/delay" → ot2_update_settings(path="mode", value="multi_X1")
- "Change mode AND speed AND delay" → ot2_batch_update_settings(updates=[{"path":"mode","value":"multi_X1"},{"path":"speed","value":"200"}])
- "Run everything / generate and simulate" → ot2_full_workflow(csv_path="CSVs/file.csv")
- "Just validate my config" → ot2_validate_configuration(csv_path="CSVs/file.csv")
- "What settings exist?" → ot2_list_settings()
- "What CSVs are available?" → ot2_list_csv_files()
- "Create a CSV template" → ot2_generate_csv_template(...)
- "I have CSV data as text" → ot2_upload_csv_content(csv_content="...", filename="...")
- "Home every N transfers" → ot2_insert_home_rows(csv_path="CSVs/file.csv", every_n_transfers=20)
- "Use 8-channel with single tip" → ot2_update_settings(path="mode", value="multi_X1")
- "Configure for cell suspensions" → ot2_update_settings(path="mixing_location", value="source")
- "Make robot move slower" → ot2_update_settings(path="speed", value="200")
- "Switch to a different project" → ot2_set_project_directory(path="/abs/path")
- "What projects have I used?" → ot2_list_projects()
- "What offsets are set?" → ot2_list_labware_offsets()
- "Get offset for labware X in slot Y" → ot2_get_labware_offset(labware_id="...", position_rack="...")
- "Delete offset for labware X slot Y" → ot2_delete_labware_offset(labware_id="...", position_rack="...")
- "Add labware to official list" → ot2_manage_official_labware(action="add", labware_id="...")
- "Show official labware list" → ot2_manage_official_labware(action="list")

SHORTHAND ALIASES for ot2_update_settings (use instead of full dotted paths):
mode, speed, head_speed, starting_tip, protocol_name,
pre_aspirate, pre_aspirate_volume, wick, wicking, delay, post_aspirate_delay,
push_out, push_out_volume, mixing, mixing_location, mixing_reps, source_remixing

STANDARD WORKFLOW:
1. Configure: ot2_apply_liquid_preset or ot2_update_settings
2. Create CSV: ot2_generate_csv_template or ot2_upload_csv_content
3. Run pipeline: ot2_full_workflow(csv_path="CSVs/file.csv")

WORKSPACE: Templates auto-copy on first access. initialize_project() is OPTIONAL.
With OT2_PROJECT_DIR: persistent. Without: temporary (use export_project_archive before session ends).
Use ot2_set_project_directory to switch between projects at runtime.

KEY RESOURCES:
- config://settings - TOML configuration
- config://labware - Labware catalog
- config://offsets - Per-slot calibration offsets (offset_database.toml)
- status://deck-layout - Visual deck setup
- status://liquid-handling-config - Active liquid params
- logs://last-simulation - Simulation output

LIQUID PRESETS:
- "standard" → water, PBS, buffers, cell media (contact + wick, no delays)
- "viscous" → DMSO, glycerol, oils, PEG (delays + push-out + wick)
- "slippery" → chloroform, hexane, acetone, ethanol (pre-wet + slow speed)

TROUBLESHOOTING:
- "Labware not found" → labware_id in labware_dict.toml must match Opentrons library
- "Slot conflict" → unique position_rack values in working_plate array
- "No tips" → add tip racks to the deck layout in settings.toml
- "Multi mode incompatible" → multi mode requires 96/384-well plates only
"""

_RECENT_PROJECTS_FILE = Path.home() / ".ot2_cherrypick_recent_projects.json"

__all__ = ["create_mcp_app", "main"]


@asynccontextmanager
async def app_lifespan(app: FastMCP) -> AsyncIterator[ProjectContext]:
    """Create the ProjectContext on startup and persist history on shutdown."""
    from .utils.paths import get_project_root, project_directory_info

    project_dir = get_project_root()
    dir_info = project_directory_info()
    ctx = ProjectContext(
        project_dir=project_dir,
        auto_created=bool(dir_info["auto_created"]),
    )

    # Load recent projects from disk
    if _RECENT_PROJECTS_FILE.exists():
        try:
            data = json.loads(_RECENT_PROJECTS_FILE.read_text())
            if isinstance(data, list):
                ctx.recent_projects = [str(p) for p in data[:10]]
        except (json.JSONDecodeError, OSError):
            logger.debug("Could not load recent projects file, starting fresh")

    try:
        yield ctx
    finally:
        # Persist recent projects on shutdown
        try:
            _RECENT_PROJECTS_FILE.write_text(json.dumps(ctx.recent_projects))
        except OSError:
            logger.debug("Could not persist recent projects file")


def create_mcp_app() -> FastMCP:
    """Instantiate the FastMCP application with registered tools."""
    app = FastMCP(name=APP_NAME, instructions=APP_INSTRUCTIONS, lifespan=app_lifespan)
    register_tools(app)
    register_config_resources(app)
    register_file_resources(app)
    register_log_resources(app)
    register_status_resources(app)
    register_prompts(app)
    return app


def main() -> None:
    """Run the MCP server via STDIO transport."""
    configure_logging()

    # Run the MCP server (project directory is resolved inside the lifespan)
    create_mcp_app().run()


if __name__ == "__main__":
    main()
