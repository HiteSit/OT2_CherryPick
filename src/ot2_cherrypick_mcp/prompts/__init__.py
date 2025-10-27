"""Prompt registration for FastMCP."""

from __future__ import annotations

from fastmcp import FastMCP

from .csv_labware_prompts import register_csv_labware_prompts
from .optimization_prompts import register_optimization_prompts
from .pipette_prompts import register_pipette_prompts
from .workflow_prompts import register_workflow_prompts

__all__ = [
    "register_prompts",
    "register_workflow_prompts",
    "register_pipette_prompts",
    "register_csv_labware_prompts",
    "register_optimization_prompts",
]


def register_prompts(mcp: FastMCP) -> None:
    """Register all prompts with the provided FastMCP instance."""

    register_workflow_prompts(mcp)
    register_pipette_prompts(mcp)
    register_csv_labware_prompts(mcp)
    register_optimization_prompts(mcp)
