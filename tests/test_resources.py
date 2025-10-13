"""Tests for configuration resources."""

from __future__ import annotations

import asyncio

from ot2_cherrypick_mcp.server import create_mcp_app


def test_settings_resource_registered_and_readable() -> None:
    """Settings resource should be available and return TOML text."""
    app = create_mcp_app()
    resources = asyncio.run(app.get_resources())
    assert "config://settings" in resources
    content = resources["config://settings"].fn()
    assert "settings.general" in content


def test_labware_resource_registered_and_readable() -> None:
    """Labware resource should be available and return TOML text."""
    app = create_mcp_app()
    resources = asyncio.run(app.get_resources())
    assert "config://labware" in resources
    content = resources["config://labware"].fn()
    assert "[[labware]]" in content
