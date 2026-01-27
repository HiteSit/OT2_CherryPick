from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional


_LABWARE_SLOT_PATTERN = re.compile(r"^(?P<labware_id>.+)_(?P<slot>\d+)$")


@dataclass(frozen=True)
class ExpectedTransfer:
    sequence_index: int
    source_labware_id: str
    source_slot: str
    source_well: str
    dest_labware_id: str
    dest_slot: str
    dest_well: str
    aspirate_volume_ul: float
    dispense_volume_ul: float
    group_id: Optional[str] = None
    group_total_volume_ul: Optional[float] = None


def parse_csv_rows(csv_path: Path) -> list[dict[str, str]]:
    with csv_path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return [row for row in reader]


def detect_home_row(row: dict[str, str]) -> bool:
    values: list[str] = []
    for value in row.values():
        if value is None:
            continue
        value_str = str(value).strip()
        if value_str:
            values.append(value_str.upper())
    if not values:
        return False
    return all(value == "HOME" for value in values)


def parse_labware_field(value: str) -> tuple[str, str]:
    value = value.strip()
    match = _LABWARE_SLOT_PATTERN.match(value)
    if match:
        return match.group("labware_id"), match.group("slot")
    return value, ""


def derive_mode(settings: dict) -> str:
    return str(settings.get("settings", {}).get("general", {}).get("mode", "single_X1"))


def _parse_float(value: str | None) -> Optional[float]:
    if value is None:
        return None
    value_str = str(value).strip()
    if not value_str:
        return None
    return float(value_str)


def _parse_distribution_pattern(pattern: str | None) -> tuple[str, Optional[float], Optional[str]]:
    if not pattern:
        return "equal", None, None
    parts = [part.strip().lower() for part in pattern.split(":") if part.strip()]
    if not parts:
        return "equal", None, None
    if parts[0] == "equal":
        return "equal", None, None
    if parts[0] == "geometric":
        factor = float(parts[1]) if len(parts) > 1 else 1.0
        order = parts[2] if len(parts) > 2 else None
        return "geometric", factor, order
    return "equal", None, None


def _expand_distribution(
    *,
    dest_wells: list[str],
    base_volume: float,
    pattern: str | None,
    air_gap_ul: float,
) -> list[tuple[str, float]]:
    mode, factor, order = _parse_distribution_pattern(pattern)
    if mode == "equal":
        volumes = [base_volume for _ in dest_wells]
    else:
        if factor is None:
            factor = 1.0
        volumes = [base_volume * (factor ** index) for index in range(len(dest_wells))]

    pairs = list(zip(dest_wells, volumes, strict=True))
    if order == "asc":
        pairs = sorted(pairs, key=lambda item: item[1])
    elif order == "desc":
        pairs = sorted(pairs, key=lambda item: item[1], reverse=True)

    return [(well, volume + air_gap_ul) for well, volume in pairs]


def _iter_dest_wells(value: str) -> Iterable[str]:
    for item in value.split("|"):
        well = item.strip()
        if well:
            yield well


def build_expected_transfers(csv_path: Path, settings: dict) -> list[ExpectedTransfer]:
    mode = derive_mode(settings)
    if mode not in {"single_X1", "multi_X1", "multi"}:
        mode = "single_X1"

    expectations: list[ExpectedTransfer] = []
    sequence_index = 1
    rows = parse_csv_rows(csv_path)

    for row_index, row in enumerate(rows, start=1):
        if detect_home_row(row):
            continue

        dest_well_raw = (row.get("Dest Well") or "").strip()
        has_pipe = "|" in dest_well_raw
        has_distribution_volume = bool((row.get("Distribution Volume (ul)") or "").strip())
        is_distribution = has_pipe or has_distribution_volume

        source_labware, source_slot = parse_labware_field(row.get("Source Labware", ""))
        dest_labware, dest_slot = parse_labware_field(row.get("Dest Labware", ""))
        source_well = (row.get("Source Well") or "").strip()
        air_gap_ul = _parse_float(row.get("Air Gap")) or 0.0

        if is_distribution:
            dest_wells = list(_iter_dest_wells(dest_well_raw))
            base_volume = _parse_float(row.get("Distribution Volume (ul)"))
            if base_volume is None:
                raise ValueError("Distribution row missing Distribution Volume (ul)")

            pattern = (row.get("Distribution") or "").strip()
            per_dest = _expand_distribution(
                dest_wells=dest_wells,
                base_volume=base_volume,
                pattern=pattern,
                air_gap_ul=air_gap_ul,
            )
            group_total = sum(volume - air_gap_ul for _, volume in per_dest)
            group_id = f"distribution-{row_index}"

            for dest_well, dispense_volume in per_dest:
                expectations.append(
                    ExpectedTransfer(
                        sequence_index=sequence_index,
                        source_labware_id=source_labware,
                        source_slot=source_slot,
                        source_well=source_well,
                        dest_labware_id=dest_labware,
                        dest_slot=dest_slot,
                        dest_well=dest_well,
                        aspirate_volume_ul=group_total,
                        dispense_volume_ul=dispense_volume,
                        group_id=group_id,
                        group_total_volume_ul=group_total,
                    )
                )
                sequence_index += 1
            continue

        volume = _parse_float(row.get("Volume (ul)"))
        if volume is None:
            raise ValueError("Non-distribution row missing Volume (ul)")
        dispense_volume = volume + air_gap_ul

        expectations.append(
            ExpectedTransfer(
                sequence_index=sequence_index,
                source_labware_id=source_labware,
                source_slot=source_slot,
                source_well=source_well,
                dest_labware_id=dest_labware,
                dest_slot=dest_slot,
                dest_well=dest_well_raw,
                aspirate_volume_ul=volume,
                dispense_volume_ul=dispense_volume,
            )
        )
        sequence_index += 1

    return expectations


__all__ = [
    "ExpectedTransfer",
    "parse_csv_rows",
    "detect_home_row",
    "parse_labware_field",
    "derive_mode",
    "build_expected_transfers",
]
