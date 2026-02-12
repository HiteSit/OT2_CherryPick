"""Configuration management tools exposed via MCP."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date, datetime, time
from pathlib import Path
from typing import Any, Dict, List

import tomlkit
from fastmcp import FastMCP

try:  # Python 3.11+
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python <3.11 fallback
    import tomli as tomllib  # type: ignore[no-redef]

from ..utils.errors import ConfigurationError
from ..utils.paths import resolve_project_path
from ..utils.toml import TomlHandler

DEFAULT_SETTINGS_PATH = Path("settings.toml")

__all__ = [
    "register_config_tools",
    "update_settings_value",
    "apply_liquid_preset",
    "list_settings_values",
]


def _parse_value(raw_value: str) -> tomlkit.items.Item:
    """Parse a TOML literal into a tomlkit item."""

    snippet = f"value = {raw_value}\n"
    try:
        document = tomlkit.parse(snippet)
    except tomlkit.exceptions.TOMLKitError:
        document = tomlkit.parse(f'value = "{raw_value}"\n')
    return document["value"]


def _is_working_plate_position(path: str) -> bool:
    """Return True if the dotted path targets a working_plate position slot."""

    return path.startswith("settings.working_plate[") and path.endswith(".position_rack")


def _normalize_for_output(value: object) -> object:
    """Convert TOML values to JSON-serializable representations."""

    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, Mapping):
        return {key: _normalize_for_output(val) for key, val in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [_normalize_for_output(item) for item in value]
    return str(value)


def list_settings_values(
    *,
    settings_path: str | Path = DEFAULT_SETTINGS_PATH,
) -> Dict[str, object]:
    """Return the complete settings structure with flattened entries."""

    resolved_path = resolve_project_path(settings_path)
    if not resolved_path.exists():
        raise ConfigurationError(f"Settings file not found at {resolved_path}")

    with resolved_path.open("rb") as handle:
        data: Dict[str, Any] = tomllib.load(handle)

    normalized = _normalize_for_output(data)

    entries: List[Dict[str, object]] = []

    def _walk(value: object, path: str) -> None:
        if isinstance(value, Mapping):
            for key, child in value.items():
                child_path = f"{path}.{key}" if path else key
                _walk(child, child_path)
            return

        if isinstance(value, Sequence) and not isinstance(
            value, (str, bytes, bytearray)
        ):
            for index, child in enumerate(value):
                child_path = f"{path}[{index}]" if path else f"[{index}]"
                _walk(child, child_path)
            return

        entries.append({"path": path, "value": _normalize_for_output(value)})

    _walk(normalized, "")

    return {
        "settings_file": str(resolved_path),
        "entries": entries,
        "data": normalized,
        "total_entries": len(entries),
        "message": f"Found {len(entries)} settings entries in {resolved_path.name}.",
    }


def update_settings_value(
    *,
    path: str,
    value: str,
    settings_path: str | Path = DEFAULT_SETTINGS_PATH,
) -> Dict[str, object]:
    """Update a value within settings.toml using dotted-path access."""

    handler = TomlHandler(settings_path)
    if _is_working_plate_position(path):
        sanitized = value.strip()
        if len(sanitized) >= 2 and sanitized[0] == sanitized[-1] and sanitized[0] in {'"', "'"}:
            sanitized = sanitized[1:-1]
        parsed_value = tomlkit.string(sanitized)
    else:
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

    # Also set the active_preset key so the protocol runtime applies this preset
    old_active, new_active = handler.set_value("settings.liquid_handling.active_preset", preset_name)

    return {
        "settings_file": str(handler.path),
        "preset": preset_name,
        "active_preset": preset_name,
        "changes": [
            {"path": path, "old_value": old, "new_value": new}
            for path, old, new in change_results
        ] + [{"path": "settings.liquid_handling.active_preset", "old_value": old_active, "new_value": new_active}],
        "backup_file": str(handler.path.with_suffix(handler.path.suffix + ".backup")),
    }


def register_config_tools(mcp: FastMCP) -> None:
    """Register configuration-oriented MCP tools."""

    @mcp.tool(
        name="ot2_update_settings",
        description="""Update settings.toml values from natural language or exact dotted paths.

**WORKFLOW - When user gives natural language request:**
1. Consult the common mappings below OR read config://settings resource
2. Identify the exact dotted path and TOML-formatted value
3. Call this tool with precise path and value

**COMMON NATURAL LANGUAGE MAPPINGS:**

LIQUID HANDLING:
- "enable/disable pre-aspirate contact" → path: "settings.liquid_handling.pre_aspirate_contact.enabled", value: "true"/"false"
- "set pre-aspirate volume to X" → path: "settings.liquid_handling.pre_aspirate_contact.aspirate_volume", value: X (number)
- "enable/disable tip wick[ing]" → path: "settings.liquid_handling.post_aspirate_wick.enabled", value: "true"/"false"
- "set post-aspirate delay to X" → path: "settings.liquid_handling.delays.post_aspirate", value: X (number)
- "enable/disable push[-]out" → path: "settings.liquid_handling.push_out.enabled", value: "true"/"false"
- "set push[-]out volume to X" → path: "settings.liquid_handling.push_out.volume_ul", value: X (number)

GENERAL SETTINGS:
- "set tip reuse to always/never/per_source" → path: "settings.general.tip_reuse", value: "always"/"never"/"per_source"
- "set mode to single_X1/multi_X1/multi" → path: "settings.general.mode", value: "single_X1"/"multi_X1"/"multi"
- "set [head] speed to X" → path: "settings.general.head_speed.speed", value: X (number, mm/min)
- "set starting tip [well] to X" → path: "settings.general.starting_tip_well", value: "H1" (well name)

DECK POSITIONS (working_plate array items use [index] notation):
- "set source labware position to X" → path: "settings.working_plate[0].position_rack", value: "X" (slot number as string)
- "set destination position to X" → path: "settings.working_plate[1].position_rack", value: "X"
- (Check list_settings tool output to see exact indices)

**IF UNSURE:** Use list_settings tool to see all available paths with current values, then match user intent.

**Value formatting rules:**
- Booleans: "true" or "false" (lowercase, no quotes in value string)
- Strings: just the value (quotes added automatically)
- Numbers: bare number like 400 or 2.0
- For position_rack: always use quoted string like "4" or "5"

**IMPORTANT:** If user request doesn't match common mappings:
1. Read config://settings resource to see full structure
2. Use list_settings tool to get all dotted paths
3. Match user's intent to visible structure
4. Then call update_settings with exact path
""",
        annotations={
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
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
        name="ot2_apply_liquid_preset",
        description="""Apply liquid handling preset configuration for different liquid types.

AVAILABLE PRESETS:
- "standard": Default for aqueous buffers (water, PBS, media)
- "viscous": DMSO, glycerol, oils (slower speeds, longer delays)
- "slippery": Volatile solvents (reduced speed to prevent dripping)
- "minimal": Bare minimum handling (no contact, no wicking)
- "aggressive": Maximum mixing and contact (for difficult liquids)

EXAMPLE:
apply_liquid_preset(preset_name="viscous")

Presets update multiple parameters atomically:
- Flow rates (aspirate/dispense speeds)
- Delays (post-aspirate wait times)
- Contact/wicking behavior
- Push-out volumes

Check status://liquid-handling-config after applying to see active parameters.
""",
        annotations={
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    def apply_liquid_preset_tool(  # pragma: no cover - exercised via apply_liquid_preset tests
        preset_name: str,
        settings_path: str = str(DEFAULT_SETTINGS_PATH),
    ) -> Dict[str, object]:
        return apply_liquid_preset(preset_name=preset_name, settings_path=settings_path)

    @mcp.tool(
        name="ot2_list_settings",
        description="List every setting and value from settings.toml using dotted paths.",
        annotations={
            "readOnlyHint": True,
            "openWorldHint": False
        }
    )
    def list_settings_tool(
        settings_path: str = str(DEFAULT_SETTINGS_PATH),
    ) -> Dict[str, object]:
        return list_settings_values(settings_path=settings_path)
