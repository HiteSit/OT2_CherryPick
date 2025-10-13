"""Basic integration tests for the MCP server skeleton."""

from __future__ import annotations

import asyncio

from ot2_cherrypick_mcp.server import create_mcp_app


def test_generate_protocol_tool_is_registered() -> None:
    """Verify that the FastMCP application exposes the generate_protocol tool."""
    app = create_mcp_app()
    tools = asyncio.run(app.get_tools())
    assert "generate_protocol" in tools
    assert "update_settings" in tools
    assert "apply_liquid_preset" in tools
    assert "add_labware_definition" in tools
    assert "simulate_protocol" in tools
    assert "generate_csv_template" in tools
    assert "deploy_to_opentrons" in tools
    assert "validate_configuration" in tools
    assert "full_workflow" in tools
