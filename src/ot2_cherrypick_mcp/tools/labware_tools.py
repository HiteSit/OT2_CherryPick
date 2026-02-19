"""Labware offset management tools for the MCP server."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Dict, Optional

import tomlkit
from fastmcp import FastMCP

from ..utils.errors import ConfigurationError
from ..utils.paths import resolve_project_path

DEFAULT_OFFSET_DB_PATH = Path("offset_database.toml")

__all__ = ["register_labware_tools", "update_labware_offset"]


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
