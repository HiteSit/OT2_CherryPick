from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence, Union

import tomllib

from tests.simulation_logs.models import (
    AspirateEvent,
    DispenseEvent,
    LabwareLoadEvent,
    MixEvent,
    RawEvent,
    SourceStream,
    TipDropEvent,
    TipPickupEvent,
)

TRASH_SLOT = "12"
TRASH_LABWARE_ID = "trash_bin"


@dataclass(frozen=True)
class NormalizedLabwareLoadEvent:
    sequence_index: int
    source: SourceStream
    labware_display: str
    labware_id: str
    labware_slot: str
    pipette_id: Optional[str]


@dataclass(frozen=True)
class NormalizedTipPickupEvent:
    sequence_index: int
    source: SourceStream
    labware_display: str
    labware_id: str
    labware_slot: str
    well: Optional[str]
    pipette_id: Optional[str]


@dataclass(frozen=True)
class NormalizedTipDropEvent:
    sequence_index: int
    source: SourceStream
    labware_display: Optional[str]
    labware_id: str
    labware_slot: str
    well: Optional[str]
    pipette_id: Optional[str]


@dataclass(frozen=True)
class NormalizedAspirateEvent:
    sequence_index: int
    source: SourceStream
    labware_display: str
    labware_id: str
    labware_slot: str
    well: str
    volume_ul: float
    rate_ul_s: float
    pipette_id: Optional[str]


@dataclass(frozen=True)
class NormalizedDispenseEvent:
    sequence_index: int
    source: SourceStream
    labware_display: str
    labware_id: str
    labware_slot: str
    well: str
    volume_ul: float
    rate_ul_s: float
    pipette_id: Optional[str]


@dataclass(frozen=True)
class NormalizedMixEvent:
    sequence_index: int
    source: SourceStream
    labware_display: str
    labware_id: str
    labware_slot: str
    well: Optional[str]
    volume_ul: Optional[float]
    rate_ul_s: Optional[float]
    pipette_id: Optional[str]


NormalizedEvent = Union[
    NormalizedLabwareLoadEvent,
    NormalizedTipPickupEvent,
    NormalizedTipDropEvent,
    NormalizedAspirateEvent,
    NormalizedDispenseEvent,
    NormalizedMixEvent,
]


def load_settings(settings_path: Path) -> dict:
    return tomllib.loads(settings_path.read_text(encoding="utf-8"))


def map_slot_to_labware(settings: dict) -> dict[str, str]:
    working_plate = settings.get("settings", {}).get("working_plate", [])
    slot_map = {
        str(entry["position_rack"]): str(entry["labware_id"]) for entry in working_plate
    }
    if TRASH_SLOT not in slot_map:
        slot_map[TRASH_SLOT] = TRASH_LABWARE_ID
    return slot_map


def map_tiprack_slot_to_pipette(settings: dict) -> dict[str, str]:
    working_plate = settings.get("settings", {}).get("working_plate", [])
    tip_map: dict[str, str] = {}
    for entry in working_plate:
        connection = entry.get("connection")
        if connection:
            tip_map[str(entry["position_rack"])] = str(connection)
    return tip_map


def synthesize_labware_load_events(settings: dict) -> list[NormalizedLabwareLoadEvent]:
    working_plate = settings.get("settings", {}).get("working_plate", [])
    tip_map = map_tiprack_slot_to_pipette(settings)
    configured_pipettes = sorted(set(tip_map.values()))
    default_pipette = configured_pipettes[0] if len(configured_pipettes) == 1 else None
    events: list[NormalizedLabwareLoadEvent] = []
    for entry in working_plate:
        slot = str(entry["position_rack"])
        labware_id = str(entry["labware_id"])
        pipette_id = tip_map.get(slot, default_pipette)
        events.append(
            NormalizedLabwareLoadEvent(
                sequence_index=0,
                source="stdout",
                labware_display=labware_id,
                labware_id=labware_id,
                labware_slot=slot,
                pipette_id=pipette_id,
            )
        )
    return events


def normalize_events(raw_events: Sequence[RawEvent], settings: dict) -> list[NormalizedEvent]:
    slot_map = map_slot_to_labware(settings)
    tip_map = map_tiprack_slot_to_pipette(settings)
    configured_pipettes = sorted(set(tip_map.values()))
    default_pipette = configured_pipettes[0] if len(configured_pipettes) == 1 else None

    normalized: list[NormalizedEvent] = []
    sequence_index = 1
    for event in synthesize_labware_load_events(settings):
        normalized.append(event.__class__(
            sequence_index=sequence_index,
            source=event.source,
            labware_display=event.labware_display,
            labware_id=event.labware_id,
            labware_slot=event.labware_slot,
            pipette_id=event.pipette_id,
        ))
        sequence_index += 1

    last_tip_pipette: Optional[str] = None

    for event in raw_events:
        slot = str(event.labware_slot)
        if slot not in slot_map:
            raise ValueError(f"Unknown labware slot in event: {slot}")
        labware_id = slot_map[slot]

        if isinstance(event, LabwareLoadEvent):
            pipette_id = default_pipette
            normalized.append(
                NormalizedLabwareLoadEvent(
                    sequence_index=sequence_index,
                    source=event.source,
                    labware_display=event.labware_display,
                    labware_id=labware_id,
                    labware_slot=slot,
                    pipette_id=pipette_id,
                )
            )
        elif isinstance(event, TipPickupEvent):
            pipette_id = tip_map.get(slot, default_pipette)
            if pipette_id is None:
                raise ValueError(f"Unknown pipette mapping for tip rack slot: {slot}")
            last_tip_pipette = pipette_id
            normalized.append(
                NormalizedTipPickupEvent(
                    sequence_index=sequence_index,
                    source=event.source,
                    labware_display=event.labware_display,
                    labware_id=labware_id,
                    labware_slot=slot,
                    well=event.well,
                    pipette_id=pipette_id,
                )
            )
        elif isinstance(event, TipDropEvent):
            pipette_id = last_tip_pipette or default_pipette
            if pipette_id is None:
                raise ValueError("Unable to infer pipette for tip drop event")
            normalized.append(
                NormalizedTipDropEvent(
                    sequence_index=sequence_index,
                    source=event.source,
                    labware_display=event.labware_display,
                    labware_id=labware_id,
                    labware_slot=slot,
                    well=event.well,
                    pipette_id=pipette_id,
                )
            )
            last_tip_pipette = None
        elif isinstance(event, AspirateEvent):
            pipette_id = last_tip_pipette or default_pipette
            if pipette_id is None:
                raise ValueError("Unable to infer pipette for aspirate event")
            normalized.append(
                NormalizedAspirateEvent(
                    sequence_index=sequence_index,
                    source=event.source,
                    labware_display=event.labware_display,
                    labware_id=labware_id,
                    labware_slot=slot,
                    well=event.well,
                    volume_ul=event.volume_ul,
                    rate_ul_s=event.rate_ul_s,
                    pipette_id=pipette_id,
                )
            )
        elif isinstance(event, DispenseEvent):
            pipette_id = last_tip_pipette or default_pipette
            if pipette_id is None:
                raise ValueError("Unable to infer pipette for dispense event")
            normalized.append(
                NormalizedDispenseEvent(
                    sequence_index=sequence_index,
                    source=event.source,
                    labware_display=event.labware_display,
                    labware_id=labware_id,
                    labware_slot=slot,
                    well=event.well,
                    volume_ul=event.volume_ul,
                    rate_ul_s=event.rate_ul_s,
                    pipette_id=pipette_id,
                )
            )
        elif isinstance(event, MixEvent):
            pipette_id = last_tip_pipette or default_pipette
            if pipette_id is None:
                raise ValueError("Unable to infer pipette for mix event")
            normalized.append(
                NormalizedMixEvent(
                    sequence_index=sequence_index,
                    source=event.source,
                    labware_display=event.labware_display,
                    labware_id=labware_id,
                    labware_slot=slot,
                    well=event.well,
                    volume_ul=event.volume_ul,
                    rate_ul_s=event.rate_ul_s,
                    pipette_id=pipette_id,
                )
            )
        else:
            raise ValueError(f"Unsupported event type: {type(event)!r}")

        sequence_index += 1

    return normalized
