"""
Custom exception types for the MCP server.
"""

from __future__ import annotations


class MCPServerError(Exception):
    """Base error for MCP server issues."""


class ConfigurationError(MCPServerError):
    """Raised when configuration files are invalid or missing."""


class ProtocolGenerationError(MCPServerError):
    """Raised when protocol compilation fails."""


class SimulationError(MCPServerError):
    """Raised when OT-2 protocol simulation fails."""


class DeploymentError(MCPServerError):
    """Raised when protocol deployment fails."""
