"""
Server entry point for the OpenTron cherry-pick MCP integration.
"""

from __future__ import annotations

import os

from fastmcp import FastMCP

from .prompts import register_prompts
from .resources import (
    register_config_resources,
    register_file_resources,
    register_log_resources,
    register_status_resources,
)
from .tools import register_tools
from .utils.logging_config import configure_logging

APP_NAME = "OT-2 Cherry Pick MCP Server"
APP_INSTRUCTIONS = """OT-2 Cherry-Pick Protocol Generator.

TOOL SELECTION GUIDE - match user intent to the right tool:
- "Set up for viscous/DMSO/glycerol" → ot2_apply_liquid_preset(preset_name="viscous")
- "Set up for volatile/chloroform/hexane" → ot2_apply_liquid_preset(preset_name="slippery")
- "Set up for water/PBS/buffers" → ot2_apply_liquid_preset(preset_name="standard")
- "Change tip reuse/mode/speed/delay" → ot2_update_settings(path="tip_reuse", value="never")
- "Run everything / generate and simulate" → ot2_full_workflow(csv_path="CSVs/file.csv")
- "Just validate my config" → ot2_validate_configuration(csv_path="CSVs/file.csv")
- "What settings exist?" → ot2_list_settings()
- "What CSVs are available?" → ot2_list_csv_files()
- "Create a CSV template" → ot2_generate_csv_template(...)
- "I have CSV data as text" → ot2_upload_csv_content(csv_content="...", filename="...")
- "Use 8-channel with single tip" → ot2_update_settings(path="mode", value="multi_X1")
- "Configure for cell suspensions" → ot2_update_settings(path="mixing_location", value="source")
- "Make robot move slower" → ot2_update_settings(path="speed", value="200")

SHORTHAND ALIASES for ot2_update_settings (use instead of full dotted paths):
tip_reuse, mode, speed, head_speed, starting_tip, protocol_name,
pre_aspirate, pre_aspirate_volume, wick, wicking, delay, post_aspirate_delay,
push_out, push_out_volume, mixing, mixing_location, mixing_reps, source_remixing

STANDARD WORKFLOW:
1. Configure: ot2_apply_liquid_preset or ot2_update_settings
2. Create CSV: ot2_generate_csv_template or ot2_upload_csv_content
3. Run pipeline: ot2_full_workflow(csv_path="CSVs/file.csv")

WORKSPACE: Templates auto-copy on first access. initialize_project() is OPTIONAL.
With OT2_PROJECT_DIR: persistent. Without: temporary (use export_project_archive before session ends).

KEY RESOURCES:
- config://settings - TOML configuration
- config://labware - Labware catalog
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
- "No tips" → add tip racks or set tip_reuse to "always"
- "Multi mode incompatible" → multi mode requires 96/384-well plates only
"""

__all__ = ["create_mcp_app", "main"]


def create_mcp_app() -> FastMCP:
    """Instantiate the FastMCP application with registered tools."""
    app = FastMCP(name=APP_NAME, instructions=APP_INSTRUCTIONS)
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

    from .utils.paths import get_project_root

    try:
        project_dir = get_project_root()
    except ValueError as e:
        raise ValueError(f"Project directory validation failed: {e}") from e

    # Change to project directory for all operations
    os.chdir(project_dir)

    # Run the MCP server
    create_mcp_app().run()


if __name__ == "__main__":
    main()
