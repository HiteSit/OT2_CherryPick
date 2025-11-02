"""Prompts module - intentionally minimal.

All workflow guidance has been moved to:
- Server APP_INSTRUCTIONS (see server.py)
- Enhanced tool descriptions with inline examples
- Resource descriptions
"""

from __future__ import annotations

from fastmcp import FastMCP

__all__ = ["register_prompts"]


def register_prompts(mcp: FastMCP) -> None:
    """No-op: prompts removed in favor of enhanced tool descriptions."""
    pass
