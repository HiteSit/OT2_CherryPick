"""Labware offset management tools for the MCP server."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Dict, Literal, Optional

import tomlkit
from fastmcp import FastMCP

from ..core.labware_scanner import scan_available_labware
from ..utils.errors import ConfigurationError
from ..utils.paths import resolve_project_path

DEFAULT_OFFSET_DB_PATH = Path("offset_database.toml")

__all__ = [
    "register_labware_tools",
    "update_labware_offset",
    "get_labware_offset",
    "list_labware_offsets",
    "delete_labware_offset",
    "run_scan_available_labware",
    "manage_official_labware",
]


def update_labware_offset(
    *,
    labware_id: str,
    position_rack: str,
    offset_x: float,
    offset_y: float,
    offset_z: float,
    notes: str = "",
    offset_db_path: str | Path = DEFAULT_OFFSET_DB_PATH,
) -> Dict[str, object]:
    """Write or update a calibration offset entry in offset_database.toml."""

    resolved = resolve_project_path(offset_db_path)

    if resolved.exists():
        content = resolved.read_text(encoding="utf-8")
        doc = tomlkit.loads(content)
    else:
        doc = tomlkit.document()

    offsets_array = doc.get("offsets")
    if offsets_array is None:
        offsets_array = tomlkit.aot()
        doc.add("offsets", offsets_array)

    # Check for existing entry and update it
    position_rack_str = str(position_rack)
    for entry in offsets_array:
        if entry.get("labware_id") == labware_id and str(entry.get("position_rack", "")) == position_rack_str:
            entry["offset_x"] = offset_x
            entry["offset_y"] = offset_y
            entry["offset_z"] = offset_z
            entry["last_calibrated"] = date.today().isoformat()
            if notes:
                entry["notes"] = notes
            resolved.write_text(tomlkit.dumps(doc), encoding="utf-8")
            return {
                "offset_db_file": str(resolved),
                "labware_id": labware_id,
                "position_rack": position_rack_str,
                "action": "updated",
            }

    # Create new entry
    new_entry = tomlkit.table()
    new_entry.add("labware_id", labware_id)
    new_entry.add("position_rack", position_rack_str)
    new_entry.add("offset_x", offset_x)
    new_entry.add("offset_y", offset_y)
    new_entry.add("offset_z", offset_z)
    new_entry.add("last_calibrated", date.today().isoformat())
    if notes:
        new_entry.add("notes", notes)
    offsets_array.append(new_entry)

    resolved.write_text(tomlkit.dumps(doc), encoding="utf-8")
    return {
        "offset_db_file": str(resolved),
        "labware_id": labware_id,
        "position_rack": position_rack_str,
        "action": "created",
    }


def run_scan_available_labware(
    *,
    custom_labware_path: Optional[str] = None,
    official_list_path: str | Path = "opentrons_labware_official.txt",
) -> Dict[str, object]:
    """Scan custom labware directory and official list, return merged catalog."""
    resolved_official = resolve_project_path(official_list_path)
    results = scan_available_labware(
        custom_labware_path=custom_labware_path,
        official_list_path=str(resolved_official) if resolved_official.exists() else None,
    )
    return {
        "labware": results,
        "count": len(results),
        "custom_path": custom_labware_path,
        "official_list_path": str(resolved_official),
        "official_list_exists": resolved_official.exists(),
    }


def get_labware_offset(
    *,
    labware_id: str,
    position_rack: str,
    offset_db_path: str | Path = DEFAULT_OFFSET_DB_PATH,
) -> Dict[str, object]:
    """Get a single calibration offset entry by labware_id + position_rack."""
    resolved = resolve_project_path(offset_db_path)
    if not resolved.exists():
        return {"found": False, "labware_id": labware_id, "position_rack": position_rack}

    doc = tomlkit.loads(resolved.read_text(encoding="utf-8"))
    offsets_array = doc.get("offsets") or []
    position_rack_str = str(position_rack)
    for entry in offsets_array:
        if entry.get("labware_id") == labware_id and str(entry.get("position_rack", "")) == position_rack_str:
            return {
                "found": True,
                "labware_id": labware_id,
                "position_rack": position_rack_str,
                "offset_x": entry.get("offset_x"),
                "offset_y": entry.get("offset_y"),
                "offset_z": entry.get("offset_z"),
                "last_calibrated": entry.get("last_calibrated"),
                "notes": entry.get("notes", ""),
            }
    return {"found": False, "labware_id": labware_id, "position_rack": position_rack}


def list_labware_offsets(
    *,
    offset_db_path: str | Path = DEFAULT_OFFSET_DB_PATH,
) -> Dict[str, object]:
    """List all calibration offset entries in offset_database.toml."""
    resolved = resolve_project_path(offset_db_path)
    if not resolved.exists():
        return {"offsets": [], "count": 0, "offset_db_file": str(resolved), "exists": False}

    doc = tomlkit.loads(resolved.read_text(encoding="utf-8"))
    offsets_array = doc.get("offsets") or []
    entries = [
        {
            "labware_id": e.get("labware_id"),
            "position_rack": e.get("position_rack"),
            "offset_x": e.get("offset_x"),
            "offset_y": e.get("offset_y"),
            "offset_z": e.get("offset_z"),
            "last_calibrated": e.get("last_calibrated"),
            "notes": e.get("notes", ""),
        }
        for e in offsets_array
    ]
    return {"offsets": entries, "count": len(entries), "offset_db_file": str(resolved), "exists": True}


def delete_labware_offset(
    *,
    labware_id: str,
    position_rack: str,
    offset_db_path: str | Path = DEFAULT_OFFSET_DB_PATH,
) -> Dict[str, object]:
    """Delete a calibration offset entry by labware_id + position_rack."""
    resolved = resolve_project_path(offset_db_path)
    if not resolved.exists():
        return {"deleted": False, "labware_id": labware_id, "position_rack": position_rack, "reason": "file not found"}

    doc = tomlkit.loads(resolved.read_text(encoding="utf-8"))
    offsets_array = doc.get("offsets")
    if not offsets_array:
        return {"deleted": False, "labware_id": labware_id, "position_rack": position_rack, "reason": "no offsets in database"}

    position_rack_str = str(position_rack)
    new_aot = tomlkit.aot()
    deleted = False
    for entry in offsets_array:
        if entry.get("labware_id") == labware_id and str(entry.get("position_rack", "")) == position_rack_str:
            deleted = True
            continue  # skip = delete
        new_aot.append(entry)

    if deleted:
        doc["offsets"] = new_aot
        resolved.write_text(tomlkit.dumps(doc), encoding="utf-8")

    return {
        "deleted": deleted,
        "labware_id": labware_id,
        "position_rack": position_rack_str,
        "reason": "not found" if not deleted else None,
    }


def manage_official_labware(
    *,
    action: Literal["add", "remove", "list"],
    labware_id: Optional[str] = None,
    official_list_path: str | Path = "opentrons_labware_official.txt",
) -> Dict[str, object]:
    """Add, remove, or list entries in opentrons_labware_official.txt."""
    if action not in ("add", "remove", "list"):
        raise ValueError(f"Invalid action '{action}'. Must be 'add', 'remove', or 'list'.")

    resolved = resolve_project_path(official_list_path)

    # Read existing entries (skip blank lines and comments)
    if resolved.exists():
        lines = resolved.read_text(encoding="utf-8").splitlines()
    else:
        lines = []

    entries = [l.strip() for l in lines if l.strip() and not l.strip().startswith("#")]
    comments = [l for l in lines if l.strip().startswith("#")]

    if action == "list":
        return {
            "action": "list",
            "entries": entries,
            "count": len(entries),
            "official_list_path": str(resolved),
            "exists": resolved.exists(),
        }

    if labware_id is None:
        raise ValueError(f"labware_id is required for action '{action}'")

    if action == "add":
        if labware_id in entries:
            return {
                "action": "add",
                "labware_id": labware_id,
                "status": "already_exists",
                "count": len(entries),
            }
        entries.append(labware_id)
        content = "\n".join(comments + sorted(entries)) + "\n"
        resolved.write_text(content, encoding="utf-8")
        return {
            "action": "add",
            "labware_id": labware_id,
            "status": "added",
            "count": len(entries),
        }

    # action == "remove"
    if labware_id not in entries:
        return {
            "action": "remove",
            "labware_id": labware_id,
            "status": "not_found",
            "count": len(entries),
        }
    entries = [e for e in entries if e != labware_id]
    content = "\n".join(comments + sorted(entries)) + "\n"
    resolved.write_text(content, encoding="utf-8")
    return {
        "action": "remove",
        "labware_id": labware_id,
        "status": "removed",
        "count": len(entries),
    }


def register_labware_tools(mcp: FastMCP) -> None:
    """Register labware management tools."""

    @mcp.tool(
        name="ot2_add_labware_definition",
        description="""Save or update a calibration offset for a specific labware in a specific deck slot.

Offsets are stored in offset_database.toml and automatically merged into the protocol
during generation. They are applied per labware_id + slot combination.

EXAMPLE:
update_labware_offset(
    labware_id="nest_96_wellplate_200ul_flat",
    position_rack="4",
    offset_x=-0.5,
    offset_y=0.8,
    offset_z=-0.3
)

CALIBRATION OFFSETS:
- offset_x: Negative = left, Positive = right (mm)
- offset_y: Negative = front, Positive = back (mm)
- offset_z: Negative = down, Positive = up (mm)

Determine offsets via "Labware Position Check" in Opentrons App.
""",
        annotations={
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    def update_labware_offset_tool(  # pragma: no cover - exercised via tests
        labware_id: str,
        position_rack: str,
        offset_x: float,
        offset_y: float,
        offset_z: float,
        notes: str = "",
        offset_db_path: str = str(DEFAULT_OFFSET_DB_PATH),
    ) -> Dict[str, object]:
        return update_labware_offset(
            labware_id=labware_id,
            position_rack=position_rack,
            offset_x=offset_x,
            offset_y=offset_y,
            offset_z=offset_z,
            notes=notes,
            offset_db_path=offset_db_path,
        )

    @mcp.tool(
        name="ot2_scan_available_labware",
        description="""List all labware available for use in settings.toml.

WHEN TO USE: Before configuring deck layout to discover valid labware_id values.
Returns merged list of custom labware (from JSON files) and official Opentrons labware.
Custom labware takes priority over official labware when IDs collide.

PARAMETERS:
- custom_labware_path: Path to directory with custom labware JSON files.
  Typically the Windows path converted to WSL format:
  /mnt/c/Users/you/AppData/Roaming/Opentrons/labware
  If omitted, only the official list is returned.
- official_list_path: Path to opentrons_labware_official.txt (auto-resolved from project dir).

RETURNS: List of labware items with fields:
  - labware_id: Use this value in settings.toml working_plate[].labware_id
  - display_name: Human-readable name
  - display_category: plate, tubeRack, reservoir, etc.
  - well_count: Number of wells (null for official list entries)
  - source: "custom" or "official"
""",
        annotations={
            "readOnlyHint": True,
            "openWorldHint": False,
        }
    )
    def scan_available_labware_tool(
        custom_labware_path: Optional[str] = None,
        official_list_path: str = "opentrons_labware_official.txt",
    ) -> Dict[str, object]:
        return run_scan_available_labware(
            custom_labware_path=custom_labware_path,
            official_list_path=official_list_path,
        )

    @mcp.tool(
        name="ot2_get_labware_offset",
        description="""Get the calibration offset for a specific labware in a specific slot.

Returns the stored x/y/z offsets and calibration date, or found=False if not set.
Use this to check if a labware+slot combination already has calibration data.
""",
        annotations={"readOnlyHint": True, "openWorldHint": False}
    )
    def get_labware_offset_tool(
        labware_id: str,
        position_rack: str,
        offset_db_path: str = str(DEFAULT_OFFSET_DB_PATH),
    ) -> Dict[str, object]:
        return get_labware_offset(
            labware_id=labware_id,
            position_rack=position_rack,
            offset_db_path=offset_db_path,
        )

    @mcp.tool(
        name="ot2_list_labware_offsets",
        description="""List all calibration offsets stored in offset_database.toml.

Returns all labware+slot combinations that have been calibrated.
Use this to audit calibration state before running a protocol.
""",
        annotations={"readOnlyHint": True, "openWorldHint": False}
    )
    def list_labware_offsets_tool(
        offset_db_path: str = str(DEFAULT_OFFSET_DB_PATH),
    ) -> Dict[str, object]:
        return list_labware_offsets(offset_db_path=offset_db_path)

    @mcp.tool(
        name="ot2_delete_labware_offset",
        description="""Delete a calibration offset entry from offset_database.toml.

Removes the offset for a specific labware_id + position_rack combination.
After deletion, the protocol generator will use zero offsets for that labware+slot.
Returns deleted=True on success, deleted=False if entry was not found.
""",
        annotations={
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": False,
            "openWorldHint": False,
        }
    )
    def delete_labware_offset_tool(
        labware_id: str,
        position_rack: str,
        offset_db_path: str = str(DEFAULT_OFFSET_DB_PATH),
    ) -> Dict[str, object]:
        return delete_labware_offset(
            labware_id=labware_id,
            position_rack=position_rack,
            offset_db_path=offset_db_path,
        )

    @mcp.tool(
        name="ot2_manage_official_labware",
        description="""Add, remove, or list entries in opentrons_labware_official.txt.

This file contains the list of official Opentrons labware load names that appear
in the labware picker when configuring deck layout.

ACTIONS:
- "list": Returns all current entries. No labware_id needed.
- "add": Adds a new official labware load name to the list.
- "remove": Removes a labware load name from the list.

WHEN TO USE:
- To see what official labware is recognized: action="list"
- To add a new Opentrons labware that's missing from the list: action="add"
- To clean up entries no longer needed: action="remove"

EXAMPLE load names (from Opentrons API):
  "nest_96_wellplate_200ul_flat"
  "opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap"
  "opentrons_96_tiprack_300ul"

NOTE: This does NOT affect custom labware (JSON files). Use ot2_scan_available_labware
to discover custom labware from the Opentrons App labware directory.
""",
        annotations={
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        }
    )
    def manage_official_labware_tool(
        action: str,  # "add", "remove", or "list"
        labware_id: Optional[str] = None,
        official_list_path: str = "opentrons_labware_official.txt",
    ) -> Dict[str, object]:
        valid_actions = ("add", "remove", "list")
        if action not in valid_actions:
            return {"error": f"Invalid action '{action}'. Must be one of: {valid_actions}"}
        return manage_official_labware(
            action=action,  # type: ignore[arg-type]
            labware_id=labware_id,
            official_list_path=official_list_path,
        )
