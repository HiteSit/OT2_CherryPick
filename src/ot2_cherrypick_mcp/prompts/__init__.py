"""Prompt registration for FastMCP."""

from __future__ import annotations

from fastmcp import FastMCP

from .workflow_prompts import register_workflow_prompts

__all__ = ["register_prompts", "register_workflow_prompts"]


def register_prompts(mcp: FastMCP) -> None:
    """Register all prompts with the provided FastMCP instance."""

    register_workflow_prompts(mcp)
