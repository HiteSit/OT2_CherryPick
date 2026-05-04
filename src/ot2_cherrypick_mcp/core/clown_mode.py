"""Deterministic CSV transform for the license-controlled clown mode."""

from __future__ import annotations

import csv
import random
from collections import defaultdict
from io import StringIO
from typing import Any


CLOWN_SHUFFLE_SEED = 20260502


class ClownModeError(ValueError):
    """Raised when clown mode cannot safely transform a protocol shape."""


def apply_clown_mode_csv_transform(csv_text: str, settings: dict[str, Any]) -> str:
    """Return a deterministic demo-shuffled CSV string.

    The transform only changes transfer row order, Source Well within the same
    Source Labware, and Dest Well within the same Dest Labware.
    """

    reader = csv.DictReader(StringIO(csv_text.strip()))
    fieldnames = list(reader.fieldnames or [])
    if not fieldnames:
        raise ClownModeError("CSV is empty.")

    if _is_dual_mode(settings, fieldnames):
        raise ClownModeError("clown-mode is not supported for dual-pipette mode.")

    rows: list[dict[str, str]] = []
    for row in reader:
        if _is_home_control_row(row):
            continue
        if _is_distribution_row(row):
            raise ClownModeError("clown-mode is not supported for distribution rows.")
        rows.append({key: row.get(key, "") for key in fieldnames})

    rng = random.Random(CLOWN_SHUFFLE_SEED)
    rng.shuffle(rows)
    _shuffle_column_within_group(rows, group_column="Source Labware", value_column="Source Well", rng=rng)
    _shuffle_column_within_group(rows, group_column="Dest Labware", value_column="Dest Well", rng=rng)

    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().strip()


def _shuffle_column_within_group(
    rows: list[dict[str, str]],
    *,
    group_column: str,
    value_column: str,
    rng: random.Random,
) -> None:
    grouped_indices: dict[str, list[int]] = defaultdict(list)
    for index, row in enumerate(rows):
        grouped_indices[row.get(group_column, "")].append(index)

    for indices in grouped_indices.values():
        values = [rows[index].get(value_column, "") for index in indices]
        rng.shuffle(values)
        for index, value in zip(indices, values):
            rows[index][value_column] = value


def _is_dual_mode(settings: dict[str, Any], fieldnames: list[str]) -> bool:
    mode = (
        settings.get("settings", {})
        .get("general", {})
        .get("mode", "")
    )
    return mode == "dual" or "Mode" in fieldnames


def _is_distribution_row(row: dict[str, str]) -> bool:
    dest_well = (row.get("Dest Well") or "").strip()
    distribution_volume = (row.get("Distribution Volume (ul)") or "").strip()
    return "|" in dest_well or bool(distribution_volume)


def _is_home_control_row(row: dict[str, str]) -> bool:
    values = [str(value).strip().upper() for value in row.values() if str(value or "").strip()]
    return bool(values) and all(value == "HOME" for value in values)


__all__ = ["CLOWN_SHUFFLE_SEED", "ClownModeError", "apply_clown_mode_csv_transform"]
