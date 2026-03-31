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
- "Change mode AND speed AND delay" → ot2_batch_update_settings(updates=[...])
- "Run everything / generate and simulate" → ot2_full_workflow(csv_path="CSVs/file.csv")
- "Just validate my config" → ot2_validate_configuration(csv_path="CSVs/file.csv")
- "What settings exist?" → ot2_list_settings()
- "What CSVs are available?" → ot2_list_csv_files()
- "Create a CSV template" → ot2_generate_csv_template(...)
- "I have CSV data as text" → ot2_upload_csv_content(csv_content="...", filename="...")
- "Home every N transfers" → ot2_insert_home_rows(csv_path="CSVs/file.csv", every_n_transfers=20)
- "What labware is available?" → ot2_scan_available_labware() (show custom labware as table)
- "Add labware to deck" → ot2_add_deck_entry(entry_type="reservoir", labware_id="...", position_rack="...")
- "Remove slot from deck" → ot2_remove_deck_entry(position_rack="4")
- "Clear the whole deck" → ot2_clear_deck()
- "What offsets are set?" → ot2_list_labware_offsets()
- "Set Opentrons App path" → ot2_create_shell_settings(opentrons_dir_win="C:\\Users\\...\\Opentrons")
- "Push config to GUI / sync to GUI" → ot2_sync_to_gui()
- "Switch to a different project" → ot2_set_project_directory(path="/abs/path")
- "What projects have I used?" → ot2_list_projects()

SHORTHAND ALIASES for ot2_update_settings (use instead of full dotted paths):
mode, speed, head_speed, starting_tip, protocol_name,
pre_aspirate, pre_aspirate_volume, wick, wicking, delay, post_aspirate_delay,
push_out, push_out_volume, mixing, mixing_location, mixing_reps, source_remixing

NEW EXPERIMENT SETUP (follow this order):
1. Set project directory (ot2_set_project_directory or use default)
2. Show available custom labware as a table:
   Call ot2_scan_available_labware → present ONLY custom-source entries to user.
   Do NOT show the full official Opentrons list (too large). Mention it exists if asked.
3. User picks labware → call ot2_add_deck_entry for each item:
   - First add auto-clears the template default deck. This is automatic.
   - Always include a tip rack matching the selected mode (connection + mode fields).
   - Validate: at least one source/destination + one tip rack before proceeding.
4. Configure settings: mode, liquid handling preset, speed, etc.
   (ot2_update_settings / ot2_batch_update_settings / ot2_apply_liquid_preset)
5. Create CSV referencing deck labware:
   (ot2_upload_csv_content or ot2_generate_csv_template)
   CSV labware names = labware_id + "_" + position_rack (e.g. "tube_rack_96_1500ul_4")
6. User chooses what to do next — NEVER auto-chain, always wait for explicit request:
   a. "Deploy to Opentrons" → ot2_full_workflow(csv_path="CSVs/file.csv", deploy=True)
   b. "Send to GUI" → ot2_sync_to_gui
      (If shell_settings.json is missing, ask user for Opentrons path first
       via ot2_create_shell_settings, then retry sync)
   c. Both → only if user explicitly says so

WORKSPACE: Templates auto-copy on first access. initialize_project() is OPTIONAL.
With OT2_PROJECT_DIR: persistent. Without: temporary (use export_project_archive before session ends).
Use ot2_set_project_directory to switch between projects at runtime.

GUI BRIDGE (Docker) — only when user explicitly requests:
- ot2_create_shell_settings: Save Opentrons App Windows path to shell_settings.json
- ot2_sync_to_gui: Push project files into the running Docker GUI container
- These are independent actions. Do NOT chain them automatically with other tools.
- Requires ot2-cherrypick-backend container running. Will NOT auto-start Docker.

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

MULTI MODE CSV WELL RULES (critical for correct CSV generation):
- Each CSV row = 8 simultaneous transfers (entire column). Only 96/384-well plates allowed.
- 96-well plates: Use A-row wells only (A1, A2, A3...). A1 = full column 1 (A1-H1).
- 384-well plates: Use A-row OR B-row wells only.
  A1 = odd rows of column 1 (A1,C1,E1,G1,I1,K1,M1,O1)
  B1 = even rows of column 1 (B1,D1,F1,H1,J1,L1,N1,P1)
- Reservoirs (1/2/8/12 wells): Use A-row wells (A1, A2...).
- NEVER use other row letters (C1, D1, etc.) in multi mode CSVs.

TROUBLESHOOTING:
- "Labware not found" → labware_id in labware_dict.toml must match Opentrons library
- "Slot conflict" → unique position_rack values in working_plate array
- "No tips" → add tip racks to the deck layout via ot2_add_deck_entry
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
