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
    register_file_resources(app)
    register_log_resources(app)
    register_status_resources(app)
    register_prompts(app)
    return app


def main() -> None:
    """Run the MCP server via STDIO transport."""
    configure_logging()
    repo_root = get_repo_root()
    os.chdir(repo_root)

    transport = os.getenv("MCP_TRANSPORT", "http")
    host = os.getenv("MCP_HOST", "127.0.0.2")
    port_str = int(os.getenv("MCP_PORT", "8000"))
    path = os.getenv("MCP_PATH", "/mcp")

    create_mcp_app().run()


if __name__ == "__main__":
    main()
