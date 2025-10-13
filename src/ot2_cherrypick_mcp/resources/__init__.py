"""
Resource providers exposed by the MCP server.
"""

from .config_resources import register_config_resources

__all__ = ["register_config_resources"]
