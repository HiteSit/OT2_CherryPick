"""Configuration management tools exposed via MCP."""

from __future__ import annotations

from pathlib import Path
from typing import Dict

import tomlkit
from fastmcp import FastMCP

from ..utils.errors import ConfigurationError
from ..utils.toml import TomlHandler

DEFAULT_SETTINGS_PATH = Path("settings.toml")

__all__ = ["register_config_tools", "update_settings_value", "apply_liquid_preset"]


def _parse_value(raw_value: str) -> tomlkit.items.Item:
    """Parse a TOML literal into a tomlkit item."""

    snippet = f"value = {raw_value}\n"
    try:
        document = tomlkit.parse(snippet)
    except tomlkit.exceptions.TOMLKitError:
        document = tomlkit.parse(f'value = "{raw_value}"\n')
    return document["value"]


def update_settings_value(
    *,
    path: str,
    value: str,
    settings_path: str | Path = DEFAULT_SETTINGS_PATH,
) -> Dict[str, object]:
    """Update a value within settings.toml using dotted-path access."""

    handler = TomlHandler(settings_path)
    parsed_value = _parse_value(value)
    old_value, new_value = handler.set_value(path, parsed_value)
    return {
        "settings_file": str(handler.path),
        "path": path,
        "old_value": old_value,
        "new_value": new_value,
        "backup_file": str(handler.path.with_suffix(handler.path.suffix + ".backup")),
    }


def apply_liquid_preset(
    *,
    preset_name: str,
    settings_path: str | Path = DEFAULT_SETTINGS_PATH,
) -> Dict[str, object]:
    """Apply a liquid handling preset by copying preset values into active settings."""

    handler = TomlHandler(settings_path)
    preset_path = f"settings.liquid_handling.presets.{preset_name}"

    try:
        preset_values = handler.get_value(preset_path)
    except ConfigurationError as exc:
        raise ConfigurationError(f"Preset '{preset_name}' not found: {exc}") from exc

    if not isinstance(preset_values, dict):
        raise ConfigurationError(f"Preset '{preset_name}' is not a table of values")

    updates = [
        (f"settings.liquid_handling.{key}", value)
        for key, value in preset_values.items()
    ]

    change_results = handler.set_values(updates)

    return {
        "settings_file": str(handler.path),
        "preset": preset_name,
        "changes": [
            {"path": path, "old_value": old, "new_value": new}
            for path, old, new in change_results
        ],
        "backup_file": str(handler.path.with_suffix(handler.path.suffix + ".backup")),
    }


def register_config_tools(mcp: FastMCP) -> None:
    """Register configuration-oriented MCP tools."""

    @mcp.tool(
        name="update_settings",
        description=(
            "Update a dotted-path value in settings.toml while preserving formatting and backups."
        ),
    )
    def update_settings_tool(  # pragma: no cover - exercised via update_settings_value tests
        path: str,
        value: str,
        settings_path: str = str(DEFAULT_SETTINGS_PATH),
    ) -> Dict[str, object]:
        try:
            return update_settings_value(path=path, value=value, settings_path=settings_path)
        except ConfigurationError as exc:
            raise ConfigurationError(f"Failed to update settings: {exc}") from exc

    @mcp.tool(
        name="apply_liquid_preset",
        description="Apply a liquid handling preset defined under settings.liquid_handling.presets.",
    )
    def apply_liquid_preset_tool(  # pragma: no cover - exercised via apply_liquid_preset tests
        preset_name: str,
        settings_path: str = str(DEFAULT_SETTINGS_PATH),
    ) -> Dict[str, object]:
        return apply_liquid_preset(preset_name=preset_name, settings_path=settings_path)
