"""
OpenTron cherry-pick MCP server package.

This module exposes the public package interface. Concrete implementations
arrive as Phase 1 progresses.
"""

from importlib.metadata import version

__all__ = ["__version__"]

__version__ = version("OT2_CherryPick")
