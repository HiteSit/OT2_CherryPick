"""Labware management tools for the MCP server."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

import tomlkit
from fastmcp import FastMCP

from ..utils.errors import ConfigurationError
from ..utils.toml import TomlHandler

DEFAULT_LABWARE_PATH = Path("labware_dict.toml")

__all__ = ["register_labware_tools", "add_labware_definition"]


@dataclass
class LabwareSpecification:
    labware_id: str
    category: str
    well_count: int
    well_volume: int
    offset_x: Optional[float] = None
    offset_y: Optional[float] = None
    offset_z: Optional[float] = None

    def to_toml_table(self) -> tomlkit.items.Table:
        table = tomlkit.table()
        table.add("category", tomlkit.item(self.category))
        table.add("labware_id", tomlkit.item(self.labware_id))
        table.add("well_count", tomlkit.item(self.well_count))
        table.add("well_volume", tomlkit.item(self.well_volume))

        if self.offset_x is not None:
            table.add("offset_x", tomlkit.item(self.offset_x))
        if self.offset_y is not None:
            table.add("offset_y", tomlkit.item(self.offset_y))
        if self.offset_z is not None:
            table.add("offset_z", tomlkit.item(self.offset_z))

        return table


def add_labware_definition(
    *,
    labware_id: str,
    category: str,
    well_count: int,
    well_volume: int,
    offset_x: Optional[float] = None,
    offset_y: Optional[float] = None,
    offset_z: Optional[float] = None,
    labware_path: str | Path = DEFAULT_LABWARE_PATH,
) -> Dict[str, object]:
    """Append a new labware entry to labware_dict.toml."""

    handler = TomlHandler(labware_path)

    existing = handler.get_value("labware")
    if any(entry.get("labware_id") == labware_id for entry in existing):
        raise ConfigurationError(f"Labware with id '{labware_id}' already exists")

    spec = LabwareSpecification(
        labware_id=labware_id,
        category=category,
        well_count=well_count,
        well_volume=well_volume,
        offset_x=offset_x,
        offset_y=offset_y,
        offset_z=offset_z,
    )

    handler.append_array_item("labware", spec.to_toml_table())

    return {
        "labware_file": str(handler.path),
        "labware_id": labware_id,
        "category": category,
        "backup_file": str(handler.path.with_suffix(handler.path.suffix + ".backup")),
    }


def register_labware_tools(mcp: FastMCP) -> None:
    """Register labware manipulation tools."""

    @mcp.tool(
        name="ot2_add_labware_definition",
        description="""Add labware to catalog with calibration offsets.

EXAMPLE:
add_labware_definition(
    labware_id="custom_96_plate",
    category="plate",
    well_count=96,
    well_volume=200,
    offset_x=-0.5,
    offset_y=0.8,
    offset_z=-0.3
)

CALIBRATION OFFSETS:
- offset_x: Negative = left, Positive = right (mm)
- offset_y: Negative = front, Positive = back (mm)
- offset_z: Negative = down, Positive = up (mm)

Offsets compensate for:
- Manufacturing tolerances (±0.1-0.5mm typical)
- Deck positioning variations
- Thermal expansion
- Wear and tear

Without offsets, tips may crash into edges or miss wells entirely.
Determine offsets via "Labware Position Check" in Opentrons App.
""",
        annotations={
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    )
    def add_labware_definition_tool(  # pragma: no cover - exercised via tests
        labware_id: str,
        category: str,
        well_count: int,
        well_volume: int,
        offset_x: Optional[float] = None,
        offset_y: Optional[float] = None,
        offset_z: Optional[float] = None,
        labware_path: str = str(DEFAULT_LABWARE_PATH),
    ) -> Dict[str, object]:
        return add_labware_definition(
            labware_id=labware_id,
            category=category,
            well_count=well_count,
            well_volume=well_volume,
            offset_x=offset_x,
            offset_y=offset_y,
            offset_z=offset_z,
            labware_path=labware_path,
        )
