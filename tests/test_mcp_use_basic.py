"""Basic integration tests for the MCP server skeleton."""

from __future__ import annotations

import asyncio

from ot2_cherrypick_mcp.server import create_mcp_app


def test_generate_protocol_tool_is_registered() -> None:
    """Verify that the FastMCP application exposes OT-2 tools with ot2_ prefix."""
    app = create_mcp_app()
    tools = asyncio.run(app.get_tools())
    assert "ot2_generate_protocol" in tools
    assert "ot2_update_settings" in tools
    assert "ot2_apply_liquid_preset" in tools
    assert "ot2_add_labware_definition" in tools
    assert "ot2_simulate_protocol" in tools
    assert "ot2_generate_csv_template" in tools
    assert "ot2_deploy_to_opentrons" in tools
    assert "ot2_upload_csv_content" in tools
    assert "ot2_validate_configuration" in tools
    assert "ot2_full_workflow" in tools
