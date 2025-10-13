"""Tool definitions exposed via the MCP server."""

from fastmcp import FastMCP

from .config_tools import register_config_tools
from .labware_tools import register_labware_tools
from .protocol_tools import register_protocol_tools
from .simulation_tools import register_simulation_tools

__all__ = [
    "register_tools",
    "register_protocol_tools",
    "register_config_tools",
    "register_labware_tools",
    "register_simulation_tools",
]


def register_tools(mcp: FastMCP) -> None:
    """Register all MCP tools with the provided FastMCP instance."""

    register_protocol_tools(mcp)
    register_config_tools(mcp)
    register_labware_tools(mcp)
    register_simulation_tools(mcp)
