"""Status resources derived from configuration files."""

from __future__ import annotations

from fastmcp import FastMCP

from ..utils.errors import ConfigurationError
from ..utils.paths import project_directory_info
from ..utils.toml import TomlHandler

__all__ = ["register_status_resources"]


def register_status_resources(mcp: FastMCP) -> None:
    """Register status-oriented resources."""

    @mcp.resource("status://deck-layout", description="Summary of current deck configuration")
    def deck_layout() -> str:  # pragma: no cover - formatting logic tested separately
        try:
            handler = TomlHandler("settings.toml")
            working_plate = handler.get_value("settings.working_plate")
        except ConfigurationError as exc:
            return f"Unable to load deck layout: {exc}"

        if not isinstance(working_plate, list) or not working_plate:
            return "No working_plate entries defined in settings.toml."

        lines = ["Deck Layout:"]
        for entry in working_plate:
            if not isinstance(entry, dict):
                continue
            slot = entry.get("position_rack", "unknown-slot")
            plate_type = entry.get("type", "unknown-type")
            labware_id = entry.get("labware_id", "unknown-labware")
            lines.append(f"- Slot {slot}: {labware_id} [{plate_type}]")

        return "\n".join(lines)

    @mcp.resource(
        "status://liquid-handling-config",
        description="Active liquid handling parameters from settings.toml",
    )
    def liquid_handling() -> str:  # pragma: no cover - formatting logic tested separately
        try:
            handler = TomlHandler("settings.toml")
            config = handler.get_value("settings.liquid_handling")
        except ConfigurationError as exc:
            return f"Unable to load liquid handling configuration: {exc}"

        if not isinstance(config, dict):
            return "settings.liquid_handling is not a table."

        lines = ["Liquid Handling Configuration:"]
        for key, value in config.items():
            if key == "presets":
                continue
            lines.append(f"- {key}: {value}")

        return "\n".join(lines)

    @mcp.resource(
        "status://project-directory",
        description="Active project directory path and whether it was auto-created",
    )
    def project_directory_status() -> str:
        info = project_directory_info()
        root = info["path"]
        auto = "yes" if info["auto_created"] else "no"
        return "Project Directory:\n" f"- path: {root}\n" f"- auto_created: {auto}"
