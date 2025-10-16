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
APP_INSTRUCTIONS = (
    "Generate and manage OT-2 cherry-pick protocols using repository-stored "
    "configuration files."
)

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

    # Validate project directory is configured and exists
    project_dir_env = os.getenv("OT2_PROJECT_DIR")
    if not project_dir_env:
        raise ValueError(
            "OT2_PROJECT_DIR environment variable is required.\n"
            "Add it to your MCP configuration's env section pointing to your project directory.\n"
            "Example: \"OT2_PROJECT_DIR\": \"/path/to/my/project\""
        )

    from pathlib import Path

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
