"""
Server entry point for the OpenTron cherry-pick MCP integration.
"""

from __future__ import annotations

import os

from fastmcp import FastMCP

from .resources import register_config_resources
from .tools import register_tools
from .utils.logging_config import configure_logging
from .utils.paths import get_repo_root

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
    return app


def main() -> None:
    """Run the MCP server via STDIO transport."""
    configure_logging()
    repo_root = get_repo_root()
    os.chdir(repo_root)
    create_mcp_app().run()


if __name__ == "__main__":
    main()
