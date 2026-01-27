from __future__ import annotations

import re
from typing import Iterable, List

from tests.simulation_logs.models import (
    AspirateEvent,
    DispenseEvent,
    MixEvent,
    ParseResult,
    ParseWarning,
    TipDropEvent,
    TipPickupEvent,
)

PICK_UP_RE = re.compile(
    r"^Picking up tip from (?P<well>[A-H][0-9]+) of (?P<labware>.+) on slot (?P<slot>[0-9]+)$"
)
DROP_TRASH_RE = re.compile(r"^Dropping tip into Trash Bin on slot (?P<slot>[0-9]+)$")
DROP_RACK_RE = re.compile(
    r"^Dropping tip into (?P<well>[A-H][0-9]+) of (?P<labware>.+) on slot (?P<slot>[0-9]+)$"
)
ASPIRATE_RE = re.compile(
    r"^Aspirating (?P<volume>[0-9.]+) uL from (?P<well>[A-H][0-9]+) of (?P<labware>.+) on slot (?P<slot>[0-9]+) at (?P<rate>[0-9.]+) uL/sec$"
)
DISPENSE_RE = re.compile(
    r"^Dispensing (?P<volume>[0-9.]+) uL into (?P<well>[A-H][0-9]+) of (?P<labware>.+) on slot (?P<slot>[0-9]+) at (?P<rate>[0-9.]+) uL/sec$"
)
MIX_RE = re.compile(
    r"^Mixing (?P<volume>[0-9.]+) uL in (?P<well>[A-H][0-9]+) of (?P<labware>.+) on slot (?P<slot>[0-9]+)(?: at (?P<rate>[0-9.]+) uL/sec)?$"
)


def parse_text(text: str, source: str = "stdout") -> ParseResult:
    events: List[object] = []
    warnings: List[ParseWarning] = []

    for index, line in enumerate(text.splitlines(), start=1):
        stripped = line.lstrip()
        if not stripped:
            continue

        match = PICK_UP_RE.match(stripped)
        if match:
            events.append(
                TipPickupEvent(
                    sequence_index=len(events) + 1,
                    source=source,
                    labware_display=match.group("labware"),
                    labware_slot=match.group("slot"),
                    well=match.group("well"),
                )
            )
            continue

        match = DROP_TRASH_RE.match(stripped)
        if match:
            events.append(
                TipDropEvent(
                    sequence_index=len(events) + 1,
                    source=source,
                    labware_display="Trash Bin",
                    labware_slot=match.group("slot"),
                    well=None,
                )
            )
            continue

        match = DROP_RACK_RE.match(stripped)
        if match:
            events.append(
                TipDropEvent(
                    sequence_index=len(events) + 1,
                    source=source,
                    labware_display=match.group("labware"),
                    labware_slot=match.group("slot"),
                    well=match.group("well"),
                )
            )
            continue

        match = ASPIRATE_RE.match(stripped)
        if match:
            events.append(
                AspirateEvent(
                    sequence_index=len(events) + 1,
                    source=source,
                    labware_display=match.group("labware"),
                    labware_slot=match.group("slot"),
                    well=match.group("well"),
                    volume_ul=float(match.group("volume")),
                    rate_ul_s=float(match.group("rate")),
                )
            )
            continue

        match = DISPENSE_RE.match(stripped)
        if match:
            events.append(
                DispenseEvent(
                    sequence_index=len(events) + 1,
                    source=source,
                    labware_display=match.group("labware"),
                    labware_slot=match.group("slot"),
                    well=match.group("well"),
                    volume_ul=float(match.group("volume")),
                    rate_ul_s=float(match.group("rate")),
                )
            )
            continue

        match = MIX_RE.match(stripped)
        if match:
            rate = match.group("rate")
            events.append(
                MixEvent(
                    sequence_index=len(events) + 1,
                    source=source,
                    labware_display=match.group("labware"),
                    labware_slot=match.group("slot"),
                    well=match.group("well"),
                    volume_ul=float(match.group("volume")),
                    rate_ul_s=float(rate) if rate is not None else None,
                )
            )
            continue

        warnings.append(ParseWarning(line=index, reason=f"Unmatched line: {stripped}"))

    return ParseResult(events=events, warnings=warnings)


def parse_lines(lines: Iterable[str], source: str = "stdout") -> ParseResult:
    return parse_text("\n".join(lines), source=source)
