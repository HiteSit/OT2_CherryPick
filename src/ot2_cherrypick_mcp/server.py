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

STANDARD WORKFLOW:
1. Configure settings: update_settings(path="...", value="...")
2. Create/upload CSV: generate_csv_template() or upload_csv_content()
3. Generate protocol: generate_protocol(csv_path="CSVs/file.csv")
4. Simulate: simulate_protocol() - check logs://last-simulation
5. Deploy: deploy_to_opentrons(copy_to_clipboard=True)

WORKSPACE MODES:
- With OT2_PROJECT_DIR set: Persistent workspace (files survive restarts)
- Without OT2_PROJECT_DIR: Temporary workspace (auto-created, use export_project_archive() before session ends)
- Templates auto-copy on first access: settings.toml, labware_dict.toml, CherryPick_OT2.py

KEY RESOURCES:
- config://settings - Current TOML configuration
- config://labware - Labware catalog
- status://deck-layout - Visual deck setup
- status://liquid-handling-config - Active liquid params
- logs://last-simulation - Simulation output
- files://csvs - Available CSV files

COMMON SETTINGS PATHS:
- settings.general.tip_reuse: "never" | "per_source" | "always"
- settings.general.mode: "single_X1" | "multi" | "multi_X1"
- settings.general.head_speed.speed: 100-600 (mm/min)
- settings.liquid_handling.delays.post_aspirate: 0-5 (seconds)
- settings.liquid_handling.post_aspirate_wick.enabled: true | false
- settings.working_plate: Array of deck labware

Use list_settings() to explore full configuration structure.

LIQUID PRESETS:
- apply_liquid_preset(preset_name="standard") - Aqueous buffers
- apply_liquid_preset(preset_name="viscous") - DMSO, glycerol
- apply_liquid_preset(preset_name="slippery") - Volatile solvents

TROUBLESHOOTING:
- "Labware not found": Check labware_id in labware_dict.toml matches Opentrons library
- "Slot conflict": Ensure unique position_rack values in working_plate array
- "No tips": Add tip racks to deck or change tip_reuse strategy
- "Multi mode incompatible": Only works with 96/384-well plates

initialize_project() is OPTIONAL (templates auto-copy on access).
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
