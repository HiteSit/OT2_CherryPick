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
from ..utils.paths import get_repo_root, resolve_project_path
from ..utils.toml import TomlHandler

DEFAULT_SETTINGS_PATH = Path("settings.toml")

# ---------------------------------------------------------------------------
# Shorthand aliases: map common short names to full dotted TOML paths.
# Resolved silently so LLM agents don't need to know the full path.
# ---------------------------------------------------------------------------
PATH_ALIASES: Dict[str, str] = {
    # General settings
    "mode": "settings.general.mode",
    "pipette_mode": "settings.general.mode",
    "speed": "settings.general.head_speed.speed",
    "head_speed": "settings.general.head_speed.speed",
    "starting_tip": "settings.general.starting_tip_well",
    "starting_tip_well": "settings.general.starting_tip_well",
    "protocol_name": "settings.general.protocol_name",
    # Liquid handling - pre-aspirate
    "pre_aspirate": "settings.liquid_handling.pre_aspirate_contact.enabled",
    "pre_aspirate_contact": "settings.liquid_handling.pre_aspirate_contact.enabled",
    "pre_aspirate_volume": "settings.liquid_handling.pre_aspirate_contact.aspirate_volume",
    "pre_wet_volume": "settings.liquid_handling.pre_aspirate_contact.aspirate_volume",
    # Liquid handling - wicking
    "wick": "settings.liquid_handling.post_aspirate_wick.enabled",
    "wicking": "settings.liquid_handling.post_aspirate_wick.enabled",
    "tip_wicking": "settings.liquid_handling.post_aspirate_wick.enabled",
    # Liquid handling - delays
    "post_aspirate_delay": "settings.liquid_handling.delays.post_aspirate",
    "delay": "settings.liquid_handling.delays.post_aspirate",
    "aspirate_delay": "settings.liquid_handling.delays.post_aspirate",
    # Liquid handling - push-out
    "push_out": "settings.liquid_handling.push_out.enabled",
    "pushout": "settings.liquid_handling.push_out.enabled",
    "push_out_volume": "settings.liquid_handling.push_out.volume_ul",
    "pushout_volume": "settings.liquid_handling.push_out.volume_ul",
    # Liquid handling - mixing
    "mixing": "settings.liquid_handling.mixing.enabled",
    "mixing_enabled": "settings.liquid_handling.mixing.enabled",
    "mixing_location": "settings.liquid_handling.mixing.location",
    "mixing_reps": "settings.liquid_handling.mixing.repetitions",
    "mixing_repetitions": "settings.liquid_handling.mixing.repetitions",
    "source_remixing": "settings.liquid_handling.mixing.source_remixing",
    # Liquid handling - active preset
    "active_preset": "settings.liquid_handling.active_preset",
}

# Valid values for common settings (used in error messages)
VALID_VALUES: Dict[str, List[str]] = {
    "settings.general.mode": ["single_X1", "multi_X1", "multi", "dual"],
    "settings.liquid_handling.mixing.location": ["destination", "source", "none"],
    "settings.liquid_handling.mixing.source_remixing": ["once", "always"],
}

__all__ = [
    "register_config_tools",
    "update_settings_value",
    "apply_liquid_preset",
    "list_settings_values",
    "add_deck_entry",
    "remove_deck_entry",
    "clear_deck",
    "PATH_ALIASES",
    "VALID_VALUES",
]


# Pre-compute the set of known full paths for auto-create eligibility
_KNOWN_FULL_PATHS: set[str] = set(PATH_ALIASES.values())


def _resolve_path_alias(path: str) -> str:
    """Resolve a shorthand alias to its full dotted path, or return as-is."""
    return PATH_ALIASES.get(path, path)


def _is_known_path(path: str) -> bool:
    """Return True if the path is an alias key or a known alias target."""
    return path in PATH_ALIASES or path in _KNOWN_FULL_PATHS


def _suggest_similar_paths(
    failed_path: str,
    settings_path: str | Path = DEFAULT_SETTINGS_PATH,
) -> List[str]:
    """Return alias names and TOML leaf paths similar to *failed_path*."""

    candidates: List[str] = list(PATH_ALIASES.keys())

    # Also gather actual leaf key names from the TOML
    try:
        result = list_settings_values(settings_path=settings_path)
        for entry in result.get("entries", []):
            full = entry["path"]
            leaf = full.rsplit(".", 1)[-1] if "." in full else full
            # strip array index notation
            if "[" in leaf:
                leaf = leaf.split("[")[0]
            if leaf and leaf not in candidates:
                candidates.append(leaf)
    except ConfigurationError:
        pass

    # Simple prefix / substring matching
    failed_lower = failed_path.lower()
    # Extract the leaf segment for matching
    failed_leaf = failed_lower.rsplit(".", 1)[-1] if "." in failed_lower else failed_lower

    scored: List[tuple[int, str]] = []
    for candidate in candidates:
        c_lower = candidate.lower()
        # Exact prefix match
        if c_lower.startswith(failed_leaf[:3]) and len(failed_leaf) >= 3:
            scored.append((2, candidate))
        # Substring match
        elif failed_leaf in c_lower or c_lower in failed_leaf:
            scored.append((1, candidate))

    # De-duplicate and sort by score descending
    seen: set[str] = set()
    suggestions: List[str] = []
    for _score, name in sorted(scored, key=lambda t: -t[0]):
        display = f"{name} ({PATH_ALIASES[name]})" if name in PATH_ALIASES else name
        if display not in seen:
            seen.add(display)
            suggestions.append(display)
        if len(suggestions) >= 5:
            break

    return suggestions


def _build_settings_error(
    original_error: str,
    path: str,
    settings_path: str | Path = DEFAULT_SETTINGS_PATH,
) -> str:
    """Build an enriched error message with suggestions for recovery."""

    parts = [original_error]

    # Check for valid value hints
    resolved = _resolve_path_alias(path)
    if resolved in VALID_VALUES:
        parts.append(f"Valid values for '{resolved}': {', '.join(VALID_VALUES[resolved])}")

    # Suggest similar paths
    suggestions = _suggest_similar_paths(path, settings_path)
    if suggestions:
        parts.append("Similar settings: " + "; ".join(suggestions))

    parts.append("Use ot2_list_settings() to see all valid paths and current values.")
    return "\n".join(parts)


def _auto_create_value(
    handler: TomlHandler,
    path: str,
    parsed_value: object,
) -> tuple[object, object]:
    """Try to create a missing leaf key if the parent path exists.

    Only used for paths that resolved from a known alias, so we know the
    key *should* exist in the TOML structure.
    """

    tokens = handler._parse_path(path)
    if len(tokens) < 2:
        raise ConfigurationError(f"Cannot auto-create root-level key '{path}'")

    parent_tokens = tokens[:-1]
    leaf_token = tokens[-1]

    # Resolve parent - this will raise if parent doesn't exist
    doc = handler.read_document()
    parent = handler._resolve_tokens(doc, parent_tokens)

    # Create the key in the parent
    new_item = parsed_value if isinstance(parsed_value, tomlkit.items.Item) else tomlkit.item(parsed_value)
    try:
        parent[leaf_token] = new_item  # type: ignore[index]
    except (TypeError, AttributeError) as exc:
        raise ConfigurationError(
            f"Cannot create key '{leaf_token}' in parent (not a table/dict)"
        ) from exc

    handler.write_document(doc)
    return None, parsed_value if not hasattr(parsed_value, "unwrap") else parsed_value.unwrap()


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
    """Update a value within settings.toml using dotted-path access.

    Supports shorthand aliases (e.g. ``"mode"`` resolves to
    ``"settings.general.mode"``).  When an aliased path's leaf key is
    missing from the TOML file the key is auto-created.
    """

    original_path = path
    is_known = _is_known_path(path)
    path = _resolve_path_alias(path)

    handler = TomlHandler(settings_path)
    if _is_working_plate_position(path):
        sanitized = value.strip()
        if len(sanitized) >= 2 and sanitized[0] == sanitized[-1] and sanitized[0] in {'"', "'"}:
            sanitized = sanitized[1:-1]
        parsed_value: object = tomlkit.string(sanitized)
    else:
        parsed_value = _parse_value(value)

    try:
        old_value, new_value = handler.set_value(path, parsed_value)
    except ConfigurationError:
        # If the path is a known alias or alias target, try to auto-create the key
        if is_known:
            old_value, new_value = _auto_create_value(handler, path, parsed_value)
        else:
            raise ConfigurationError(
                _build_settings_error(
                    f"Path '{original_path}' not found in settings.",
                    original_path,
                    settings_path,
                )
            )

    return {
        "settings_file": str(handler.path),
        "path": path,
        "old_value": old_value,
        "new_value": new_value,
        "backup_file": str(handler.path.with_suffix(handler.path.suffix + ".backup")),
    }


def batch_update_settings(
    *,
    updates: Sequence[Dict[str, str]],
    settings_path: str | Path = DEFAULT_SETTINGS_PATH,
) -> Dict[str, object]:
    """Apply multiple setting changes in a single atomic write.

    Each entry in *updates* must have ``"path"`` and ``"value"`` keys.
    Shorthand aliases are resolved the same way as :func:`update_settings_value`.
    """

    handler = TomlHandler(settings_path)
    document = handler.read_document()
    results: List[Dict[str, object]] = []

    for entry in updates:
        raw_path = entry["path"]
        raw_value = entry["value"]

        original_path = raw_path
        is_known = _is_known_path(raw_path)
        resolved = _resolve_path_alias(raw_path)

        if _is_working_plate_position(resolved):
            sanitized = raw_value.strip()
            if len(sanitized) >= 2 and sanitized[0] == sanitized[-1] and sanitized[0] in {'"', "'"}:
                sanitized = sanitized[1:-1]
            parsed_value: object = tomlkit.string(sanitized)
        else:
            parsed_value = _parse_value(raw_value)

        tokens = handler._parse_path(resolved)
        try:
            old_item, new_item = handler._set_value(document, tokens, parsed_value)
            old_value = old_item.unwrap() if hasattr(old_item, "unwrap") else old_item
            new_value = new_item.unwrap() if hasattr(new_item, "unwrap") else new_item
        except ConfigurationError:
            if is_known:
                # Auto-create missing leaf key (same logic as single update)
                if len(tokens) < 2:
                    raise ConfigurationError(f"Cannot auto-create root-level key '{resolved}'")
                parent = handler._resolve_tokens(document, tokens[:-1])
                leaf = tokens[-1]
                new_item = parsed_value if isinstance(parsed_value, tomlkit.items.Item) else tomlkit.item(parsed_value)
                try:
                    parent[leaf] = new_item  # type: ignore[index]
                except (TypeError, AttributeError) as exc:
                    raise ConfigurationError(
                        f"Cannot create key '{leaf}' in parent (not a table/dict)"
                    ) from exc
                old_value = None
                new_value = parsed_value if not hasattr(parsed_value, "unwrap") else parsed_value.unwrap()
            else:
                raise ConfigurationError(
                    _build_settings_error(
                        f"Path '{original_path}' not found in settings.",
                        original_path,
                        settings_path,
                    )
                )

        results.append({
            "path": resolved,
            "old_value": old_value,
            "new_value": new_value,
        })

    handler.write_document(document)

    return {
        "settings_file": str(handler.path),
        "updates": results,
        "count": len(results),
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
        raise ConfigurationError(
            f"Preset '{preset_name}' not found.\n"
            f"Available presets in settings.toml: standard, viscous "
            f"(check [settings.liquid_handling.presets] section for the full list).\n"
            f"Use ot2_list_settings() to see all presets defined in your file."
        ) from exc

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


# ---------------------------------------------------------------------------
# Default deck detection
# ---------------------------------------------------------------------------


def _is_default_deck(settings_path: Path) -> bool:
    """Return True if the current deck layout matches the repo-root template."""
    repo_root_settings = get_repo_root() / "settings.toml"

    if settings_path.resolve() == repo_root_settings.resolve():
        return True

    try:
        with open(repo_root_settings, "rb") as f:
            template_doc = tomllib.load(f)
        with open(settings_path, "rb") as f:
            current_doc = tomllib.load(f)
    except (FileNotFoundError, tomllib.TOMLDecodeError):
        return False

    template_plates = template_doc.get("settings", {}).get("working_plate", [])
    current_plates = current_doc.get("settings", {}).get("working_plate", [])

    def _fingerprint(plates: list[dict[str, Any]]) -> frozenset[tuple[str, str, str]]:
        return frozenset(
            (p.get("type", ""), p.get("labware_id", ""), p.get("position_rack", ""))
            for p in plates
        )

    return _fingerprint(current_plates) == _fingerprint(template_plates)


# ---------------------------------------------------------------------------
# Deck manipulation functions
# ---------------------------------------------------------------------------


def add_deck_entry(
    *,
    entry_type: str,
    labware_id: str,
    position_rack: str,
    connection: str = "",
    mode: str = "",
    module_type: str = "",
    adapter_id: str = "",
    target_temperature: int = 0,
    target_shake_speed: int = 0,
    persist_after_protocol: bool = True,
    offset_x: float | None = None,
    offset_y: float | None = None,
    offset_z: float | None = None,
    settings_path: str | Path = DEFAULT_SETTINGS_PATH,
) -> dict[str, object]:
    """Add a working_plate entry to settings.toml.

    If the current deck matches the repo-root template default,
    ALL existing entries are cleared first (auto-clear on first edit).
    """
    resolved = resolve_project_path(settings_path)
    handler = TomlHandler(resolved)

    auto_cleared = False
    if _is_default_deck(resolved):
        handler.clear_array("settings.working_plate")
        auto_cleared = True

    doc = handler.read_document()
    plates = doc.get("settings", {}).get("working_plate", [])
    for existing in plates:
        if str(existing.get("position_rack", "")) == str(position_rack):
            raise ConfigurationError(
                f"Slot {position_rack} is already occupied by "
                f"'{existing.get('labware_id', '')}'. "
                f"Remove it first with ot2_remove_deck_entry."
            )

    entry: dict[str, object] = {
        "type": entry_type,
        "labware_id": labware_id,
        "position_rack": position_rack,
    }

    if entry_type == "tip":
        if connection:
            entry["connection"] = connection
        if mode:
            entry["mode"] = mode
    elif entry_type == "module":
        if module_type:
            entry["module_type"] = module_type
        if adapter_id:
            entry["adapter_id"] = adapter_id
        entry["target_temperature"] = target_temperature
        entry["target_shake_speed"] = target_shake_speed
        entry["persist_after_protocol"] = persist_after_protocol

    if offset_x is not None:
        entry["offset_x"] = offset_x
    if offset_y is not None:
        entry["offset_y"] = offset_y
    if offset_z is not None:
        entry["offset_z"] = offset_z

    handler.append_array_item("settings.working_plate", entry)

    result: dict[str, object] = {
        "status": "success",
        "added": entry,
        "auto_cleared_default": auto_cleared,
    }
    if auto_cleared:
        result["note"] = (
            "Default template deck was automatically cleared before adding. "
            "This happens once on the first deck edit for a new project."
        )
    return result


def remove_deck_entry(
    *,
    position_rack: str,
    settings_path: str | Path = DEFAULT_SETTINGS_PATH,
) -> dict[str, object]:
    """Remove a working_plate entry by its deck slot number."""
    resolved = resolve_project_path(settings_path)
    handler = TomlHandler(resolved)
    doc = handler.read_document()
    plates = doc.get("settings", {}).get("working_plate", [])

    for idx, entry in enumerate(plates):
        if str(entry.get("position_rack", "")) == str(position_rack):
            removed = handler.remove_array_item("settings.working_plate", idx)
            return {
                "status": "success",
                "removed": removed,
                "slot": position_rack,
            }

    raise ConfigurationError(
        f"No working_plate entry found in slot {position_rack}. "
        f"Use ot2_list_settings to see current deck layout."
    )


def clear_deck(
    *,
    settings_path: str | Path = DEFAULT_SETTINGS_PATH,
) -> dict[str, object]:
    """Remove ALL working_plate entries from settings.toml."""
    resolved = resolve_project_path(settings_path)
    handler = TomlHandler(resolved)
    count = handler.clear_array("settings.working_plate")
    return {
        "status": "success",
        "entries_removed": count,
    }


def register_config_tools(mcp: FastMCP) -> None:
    """Register configuration-oriented MCP tools."""

    @mcp.tool(
        name="ot2_update_settings",
        description="""Update a single setting in settings.toml.

WHEN TO USE: For a SINGLE parameter change (mode, speed, delay, etc.).
For MULTIPLE parameter changes in one request, use ot2_batch_update_settings instead.
For bulk liquid-handling changes, prefer ot2_apply_liquid_preset instead.

SHORTHAND ALIASES (use these instead of full dotted paths):
- "mode" → settings.general.mode  (values: "single_X1", "multi_X1", "multi", "dual")
  "single_X1" = single-channel pipette
  "multi_X1" = 8-channel pipette picking up only ONE tip (single-tip precision)
  "multi" = 8-channel pipette using all 8 tips (full column transfers)
    CSV wells: 96-well → A-row only (A1=col1). 384-well → A-row (odd rows) or B-row (even rows).
  "dual" = multi-pipette mode (requires Mode column in CSV)
- "speed" or "head_speed" → settings.general.head_speed.speed  (100-600 mm/min)
- "starting_tip" → settings.general.starting_tip_well  (e.g. "H1")
- "protocol_name" → settings.general.protocol_name  (display name on OT-2)
- "pre_aspirate" → settings.liquid_handling.pre_aspirate_contact.enabled
- "pre_aspirate_volume" → settings.liquid_handling.pre_aspirate_contact.aspirate_volume
- "wick" or "wicking" → settings.liquid_handling.post_aspirate_wick.enabled
- "delay" or "post_aspirate_delay" → settings.liquid_handling.delays.post_aspirate  (seconds)
- "push_out" → settings.liquid_handling.push_out.enabled
- "push_out_volume" → settings.liquid_handling.push_out.volume_ul  (uL)
- "mixing" → settings.liquid_handling.mixing.enabled
- "mixing_location" → settings.liquid_handling.mixing.location  ("destination", "source", "none")
- "mixing_reps" → settings.liquid_handling.mixing.repetitions  (number)
- "source_remixing" → settings.liquid_handling.mixing.source_remixing  ("once", "always")

Full dotted paths also accepted (e.g. "settings.general.head_speed.speed").
For deck positions use array notation: "settings.working_plate[0].position_rack".

VALUE FORMAT: Booleans as "true"/"false", numbers as bare digits (400, 2.5), strings as plain text (quotes added automatically).

IF UNSURE about valid paths, call ot2_list_settings first.
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
        return update_settings_value(path=path, value=value, settings_path=settings_path)

    @mcp.tool(
        name="ot2_batch_update_settings",
        description="""Update MULTIPLE settings in settings.toml in a single atomic operation.

WHEN TO USE: When the user asks to change TWO OR MORE settings at once.
For a single setting change, use ot2_update_settings instead.
For liquid-type presets (viscous, slippery, standard), use ot2_apply_liquid_preset instead.

INPUT FORMAT: Pass a JSON array of {"path": "...", "value": "..."} objects.
All shorthand aliases from ot2_update_settings work here too.

SHORTHAND ALIASES (same as ot2_update_settings):
- "mode" → settings.general.mode  ("single_X1", "multi_X1", "multi", "dual")
- "speed" / "head_speed" → settings.general.head_speed.speed  (100-600)
- "starting_tip" → settings.general.starting_tip_well
- "protocol_name" → settings.general.protocol_name
- "pre_aspirate" → settings.liquid_handling.pre_aspirate_contact.enabled
- "pre_aspirate_volume" → settings.liquid_handling.pre_aspirate_contact.aspirate_volume
- "wick" / "wicking" → settings.liquid_handling.post_aspirate_wick.enabled
- "delay" / "post_aspirate_delay" → settings.liquid_handling.delays.post_aspirate
- "push_out" → settings.liquid_handling.push_out.enabled
- "push_out_volume" → settings.liquid_handling.push_out.volume_ul
- "mixing" → settings.liquid_handling.mixing.enabled
- "mixing_location" → settings.liquid_handling.mixing.location
- "mixing_reps" → settings.liquid_handling.mixing.repetitions
- "source_remixing" → settings.liquid_handling.mixing.source_remixing

EXAMPLE:
ot2_batch_update_settings(updates=[
  {"path": "mode", "value": "multi_X1"},
  {"path": "speed", "value": "200"},
  {"path": "push_out", "value": "true"},
  {"path": "push_out_volume", "value": "5"}
])

VALUE FORMAT: Same as ot2_update_settings — booleans as "true"/"false",
numbers as bare digits, strings as plain text.

ATOMICITY: All changes are applied to a single TOML read/write cycle.
If any path fails, no changes are written.
""",
        annotations={
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    def batch_update_settings_tool(
        updates: List[Dict[str, str]],
        settings_path: str = str(DEFAULT_SETTINGS_PATH),
    ) -> Dict[str, object]:
        return batch_update_settings(updates=updates, settings_path=settings_path)

    @mcp.tool(
        name="ot2_apply_liquid_preset",
        description="""Apply a named liquid-handling preset that configures multiple parameters at once.

WHEN TO USE: When the user describes a LIQUID TYPE rather than specific parameters.
Use this instead of multiple ot2_update_settings calls for liquid handling.
For individual parameter tweaks after applying a preset, use ot2_update_settings.

LIQUID TYPE → PRESET MAPPING:
- Water, PBS, buffers, cell media → preset_name="standard"
- DMSO, glycerol, oils, PEG, viscous liquids → preset_name="viscous"
- Chloroform, hexane, acetone, ethanol, volatile/slippery solvents → preset_name="slippery"
- Minimal handling, no extra steps → preset_name="minimal"
- Difficult liquids, maximum precision → preset_name="aggressive"

WHAT PRESETS CONFIGURE (atomically):
- Pre-aspirate contact and pre-wetting behavior
- Post-aspirate tip wicking (removes external droplets)
- Post-aspirate delays (settling time for viscous liquids)
- Push-out volume (expels residual liquid from tip)
- Mixing parameters (repetitions, location)

AFTER APPLYING: Settings are updated immediately. You do NOT need to call
ot2_update_settings for the same parameters unless overriding individual values.
Check status://liquid-handling-config to see the active parameters.

EXAMPLE: ot2_apply_liquid_preset(preset_name="viscous")
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
        description="""List every setting path and current value from settings.toml.

WHEN TO USE:
- To discover valid configuration paths for ot2_update_settings
- To inspect current values before or after changes
- To debug "path not found" errors from ot2_update_settings
- To see the full TOML structure including deck layout and presets

Returns dotted-path notation (e.g. "settings.general.mode") with current values.
These paths can be passed directly to ot2_update_settings(path=...).
""",
        annotations={
            "readOnlyHint": True,
            "openWorldHint": False
        }
    )
    def list_settings_tool(
        settings_path: str = str(DEFAULT_SETTINGS_PATH),
    ) -> Dict[str, object]:
        return list_settings_values(settings_path=settings_path)

    # -- Deck manipulation tools ------------------------------------------

    @mcp.tool(
        name="ot2_add_deck_entry",
        description=(
            "Add a labware or module to the OT-2 deck layout in settings.toml.\n\n"
            "WHEN TO USE: When setting up the deck for a new experiment. Call once per labware item.\n"
            "Always include tip rack(s) matching the selected mode.\n\n"
            "AUTO-CLEAR BEHAVIOR: If the current deck is still the project template default\n"
            "(heaterShaker + reservoirs + tip racks), ALL entries are cleared automatically\n"
            "before the first add. This happens once — subsequent adds just append.\n\n"
            "PARAMETERS:\n"
            '- entry_type: "reservoir" (source/dest plates/racks), "tip" (tip racks), "module" (heaterShaker)\n'
            "- labware_id: Must match a labware_id from ot2_scan_available_labware\n"
            '- position_rack: Deck slot number as string ("1"-"11")\n'
            '- connection: (tip racks only) "Pipette_8" or "Pipette_1"\n'
            '- mode: (tip racks only) "multi", "multi_X1", or "single_X1"\n'
            '- module_type: (modules only) "heaterShaker"\n'
            "- adapter_id: (modules only) adapter labware id\n"
            "- offset_x/y/z: Optional per-slot calibration offsets in mm\n\n"
            "EXAMPLE:\n"
            '  ot2_add_deck_entry(entry_type="reservoir", labware_id="tube_rack_96_1500ul", position_rack="4")\n'
            '  ot2_add_deck_entry(entry_type="tip", labware_id="opentrons_96_tiprack_300ul",\n'
            '    position_rack="1", connection="Pipette_8", mode="multi_X1")'
        ),
        annotations={
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": False,
        },
    )
    def add_deck_entry_tool(
        entry_type: str,
        labware_id: str,
        position_rack: str,
        connection: str = "",
        mode: str = "",
        module_type: str = "",
        adapter_id: str = "",
        target_temperature: int = 0,
        target_shake_speed: int = 0,
        persist_after_protocol: bool = True,
        offset_x: float | None = None,
        offset_y: float | None = None,
        offset_z: float | None = None,
        settings_path: str = str(DEFAULT_SETTINGS_PATH),
    ) -> dict[str, object]:
        """Add a labware or module to the deck layout."""
        return add_deck_entry(
            entry_type=entry_type,
            labware_id=labware_id,
            position_rack=position_rack,
            connection=connection,
            mode=mode,
            module_type=module_type,
            adapter_id=adapter_id,
            target_temperature=target_temperature,
            target_shake_speed=target_shake_speed,
            persist_after_protocol=persist_after_protocol,
            offset_x=offset_x,
            offset_y=offset_y,
            offset_z=offset_z,
            settings_path=settings_path,
        )

    @mcp.tool(
        name="ot2_remove_deck_entry",
        description=(
            "Remove a labware or module from the OT-2 deck by slot number.\n\n"
            "WHEN TO USE: To remove a specific item from the deck layout.\n"
            "Identifies the entry by its position_rack (slot number).\n\n"
            "PARAMETERS:\n"
            '- position_rack: Deck slot number as string (e.g. "4", "10")\n\n'
            "RETURNS: The removed entry details. Raises error if slot is empty."
        ),
        annotations={
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": False,
            "openWorldHint": False,
        },
    )
    def remove_deck_entry_tool(
        position_rack: str,
        settings_path: str = str(DEFAULT_SETTINGS_PATH),
    ) -> dict[str, object]:
        """Remove a deck entry by slot number."""
        return remove_deck_entry(
            position_rack=position_rack,
            settings_path=settings_path,
        )

    @mcp.tool(
        name="ot2_clear_deck",
        description=(
            "Remove ALL labware and modules from the OT-2 deck layout.\n\n"
            "WHEN TO USE: To start with a completely empty deck.\n"
            "This is the explicit version of the auto-clear in ot2_add_deck_entry.\n\n"
            "NOTE: After clearing, add at least one labware and one tip rack\n"
            "before running a workflow, otherwise validation will fail."
        ),
        annotations={
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    def clear_deck_tool(
        settings_path: str = str(DEFAULT_SETTINGS_PATH),
    ) -> dict[str, object]:
        """Remove all deck entries."""
        return clear_deck(settings_path=settings_path)
