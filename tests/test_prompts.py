"""Tests for registered prompt templates."""

from __future__ import annotations

import asyncio

from ot2_cherrypick_mcp.server import create_mcp_app


def test_prompts_registered() -> None:
    app = create_mcp_app()
    prompts = asyncio.run(app.get_prompts())
    if isinstance(prompts, dict):
        prompt_names = set(prompts.keys())
    else:
        prompt_names = {prompt.name for prompt in prompts}
    assert "setup_new_experiment" in prompt_names
    assert "troubleshoot_simulation_error" in prompt_names
