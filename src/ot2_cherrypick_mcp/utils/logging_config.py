"""
Logging configuration helpers.

The server uses stderr-only logging to stay compatible with MCP transports.
"""

from __future__ import annotations

import logging
import sys
from typing import Optional


def configure_logging(level: int = logging.INFO, logger_name: Optional[str] = None) -> None:
    """
    Configure logging for the MCP server.

    Args:
        level: Logging level to apply to the configured logger.
        logger_name: Optional logger name to configure. When omitted the root
            logger is configured.
    """
    target_logger = logging.getLogger(logger_name)
    target_logger.setLevel(level)

    handler = logging.StreamHandler(stream=sys.stderr)
    handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    )

    target_logger.handlers.clear()
    target_logger.addHandler(handler)
