"""Protocol validation helpers."""

from __future__ import annotations

import csv
import re
import tomllib
from pathlib import Path
from typing import Dict, List

from ..utils.errors import ConfigurationError
from ..utils.paths import resolve_repo_path

CSV_REQUIRED_COLUMNS = {
    "Source Labware",
    "Source Well",
    "Volume (ul)",
    "Dest Labware",
    "Dest Well",
}

WELL_PATTERN = re.compile(r"^[A-HP][1-9][0-9]*$", re.IGNORECASE)


def _load_toml(path: str | Path) -> Dict[str, object]:
    handler_path = resolve_repo_path(path)
    if not handler_path.exists():
        raise ConfigurationError(f"Configuration file not found at {handler_path}")
    return tomllib.loads(handler_path.read_text(encoding="utf-8"))


def _base_labware_id(labware_entry: str) -> str:
    if "_" in labware_entry and labware_entry.split("_")[-1].isdigit():
        return "_".join(labware_entry.split("_")[:-1])
    return labware_entry


def validate_configuration(
    *,
    settings_path: str | Path,
    labware_path: str | Path,
    csv_path: str | Path,
) -> Dict[str, object]:
    """Validate configuration files before protocol generation."""

    errors: List[str] = []
    warnings: List[str] = []

    try:
        settings_data = _load_toml(settings_path)
    except ConfigurationError as exc:
        errors.append(str(exc))
        settings_data = {}

    try:
        labware_data = _load_toml(labware_path)
    except ConfigurationError as exc:
        errors.append(str(exc))
        labware_data = {}

    labware_entries = labware_data.get("labware", []) if isinstance(labware_data, dict) else []
    labware_ids = {entry.get("labware_id") for entry in labware_entries if isinstance(entry, dict)}

    if settings_data:
        working_plate = settings_data.get("settings", {}).get("working_plate", [])  # type: ignore[index]
        if isinstance(working_plate, list):
            for entry in working_plate:
                if not isinstance(entry, dict):
                    continue
                labware_id = entry.get("labware_id")
                if labware_id not in labware_ids:
                    errors.append(
                        f"Labware '{labware_id}' referenced in settings.working_plate is not defined in labware_dict.toml"
                    )

    csv_file = resolve_repo_path(csv_path)
    if not csv_file.exists():
        errors.append(f"CSV transfer map not found at {csv_file}")
        return _result(errors, warnings)

    with csv_file.open("r", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        missing_columns = CSV_REQUIRED_COLUMNS - set(reader.fieldnames or [])
        if missing_columns:
            errors.append(f"CSV file missing required columns: {sorted(missing_columns)}")
        else:
            for row_number, row in enumerate(reader, start=2):
                try:
                    volume = float(row["Volume (ul)"] or 0)
                    if volume <= 0:
                        errors.append(f"Row {row_number}: volume must be positive")
                except ValueError:
                    errors.append(f"Row {row_number}: volume is not a number")

                for key in ("Source Well", "Dest Well"):
                    well = (row.get(key) or "").strip()
                    if well and not WELL_PATTERN.match(well):
                        warnings.append(f"Row {row_number}: well '{well}' has unexpected format for column '{key}'")

                for key in ("Source Labware", "Dest Labware"):
                    labware_value = (row.get(key) or "").strip()
                    base_id = _base_labware_id(labware_value)
                    if base_id and base_id not in labware_ids:
                        errors.append(
                            f"Row {row_number}: labware '{labware_value}' (base '{base_id}') not defined in labware_dict.toml"
                        )

    return _result(errors, warnings)


def _result(errors: List[str], warnings: List[str]) -> Dict[str, object]:
    status = "error" if errors else "ok"
    return {
        "status": status,
        "errors": errors,
        "warnings": warnings,
    }


__all__ = ["validate_configuration"]
