"""
Resource providers exposed by the MCP server.
"""

from .config_resources import register_config_resources
from .file_resources import register_file_resources
from .log_resources import register_log_resources

__all__ = [
    "register_config_resources",
    "register_file_resources",
    "register_log_resources",
]
