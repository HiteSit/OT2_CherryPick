"""Protocol validation helpers."""

from __future__ import annotations

import csv
import re
import tomllib
from pathlib import Path
from typing import Dict, List

from ..utils.errors import ConfigurationError
from ..utils.paths import resolve_project_path

CSV_BASE_REQUIRED = {
    "Source Labware",
    "Source Well",
    "Dest Labware",
    "Dest Well",
}

CSV_VOLUME_COLUMNS = {
    "Volume (ul)",
    "Distribution Volume (ul)",
}

WELL_PATTERN = re.compile(r"^[A-HP][1-9][0-9]*$", re.IGNORECASE)
PIPE_DELIMITED_WELL_PATTERN = re.compile(r"^[A-HP][1-9][0-9]*(\|[A-HP][1-9][0-9]*)*$", re.IGNORECASE)
DISTRIBUTION_PATTERN = re.compile(r"^(equal|geometric:\d+(\.\d+)?(:(asc|desc))?)$", re.IGNORECASE)


def _is_home_control_row(row: Dict[str, str]) -> bool:
    """Check if a CSV row is a HOME control row.

    A HOME row has "HOME" (case-insensitive) in ALL non-empty columns.
    """
    values: List[str] = []
    for value in row.values():
        if value is None:
            continue
        if isinstance(value, list):
            for item in value:
                item_str = str(item).strip()
                if item_str:
                    values.append(item_str.upper())
            continue
        value_str = str(value).strip()
        if value_str:
            values.append(value_str.upper())
    if not values:
        return False
    return all(v == "HOME" for v in values)


def _load_toml(path: str | Path) -> Dict[str, object]:
    handler_path = resolve_project_path(path)
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
                # Skip validation for module entries (modules don't require labware validation)
                entry_type = entry.get("type", "").lower()
                if entry_type == "module":
                    continue
                labware_id = entry.get("labware_id", "").strip()
                # Skip empty labware_id (some configurations may not require it)
                if not labware_id:
                    continue
                if labware_id not in labware_ids:
                    errors.append(
                        f"Labware '{labware_id}' referenced in settings.working_plate is not defined in labware_dict.toml"
                    )

    csv_file = resolve_project_path(csv_path)
    if not csv_file.exists():
        errors.append(f"CSV transfer map not found at {csv_file}")
        return _result(errors, warnings)

    with csv_file.open("r", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        fieldnames = set(reader.fieldnames or [])

        # Check base required columns
        missing_base = CSV_BASE_REQUIRED - fieldnames
        if missing_base:
            errors.append(f"CSV file missing required columns: {sorted(missing_base)}")

        # Check that at least one volume column exists
        has_volume_column = bool(CSV_VOLUME_COLUMNS & fieldnames)
        if not has_volume_column:
            errors.append(f"CSV file must have at least one volume column: {sorted(CSV_VOLUME_COLUMNS)}")

        if not missing_base and has_volume_column:
            prev_row: Dict[str, str] | None = None
            for row_number, row in enumerate(reader, start=2):
                is_home_row = _is_home_control_row(row)

                # Skip column validation for HOME control rows
                if not is_home_row:
                    # Detect if this is a distribution row
                    dest_well = (row.get("Dest Well") or "").strip()
                    has_pipe = "|" in dest_well
                    has_dist_volume = bool(row.get("Distribution Volume (ul)", "").strip())
                    is_distribution = has_pipe or has_dist_volume

                    # Validate appropriate volume column
                    if is_distribution:
                        # Distribution row - check Distribution Volume (ul)
                        if "Distribution Volume (ul)" in fieldnames:
                            try:
                                volume = float(row.get("Distribution Volume (ul)") or 0)
                                if volume <= 0:
                                    errors.append(f"Row {row_number}: distribution volume must be positive")
                            except ValueError:
                                errors.append(f"Row {row_number}: distribution volume is not a number")
                        else:
                            errors.append(f"Row {row_number}: distribution row requires 'Distribution Volume (ul)' column")

                        # Validate Distribution pattern if present
                        dist_pattern = (row.get("Distribution") or "").strip()
                        if dist_pattern and not DISTRIBUTION_PATTERN.match(dist_pattern):
                            warnings.append(f"Row {row_number}: distribution pattern '{dist_pattern}' has unexpected format")
                    else:
                        # Regular cherry-pick row - check Volume (ul)
                        if "Volume (ul)" in fieldnames:
                            try:
                                volume = float(row.get("Volume (ul)") or 0)
                                if volume <= 0:
                                    errors.append(f"Row {row_number}: volume must be positive")
                            except ValueError:
                                errors.append(f"Row {row_number}: volume is not a number")
                        else:
                            errors.append(f"Row {row_number}: cherry-pick row requires 'Volume (ul)' column")

                    # Validate well formats
                    source_well = (row.get("Source Well") or "").strip()
                    if source_well and not WELL_PATTERN.match(source_well):
                        warnings.append(f"Row {row_number}: source well '{source_well}' has unexpected format")

                    # Dest Well can be either single well or pipe-delimited
                    if dest_well:
                        if not (WELL_PATTERN.match(dest_well) or PIPE_DELIMITED_WELL_PATTERN.match(dest_well)):
                            warnings.append(f"Row {row_number}: dest well '{dest_well}' has unexpected format")

                    for key in ("Source Labware", "Dest Labware"):
                        labware_value = (row.get(key) or "").strip()
                        base_id = _base_labware_id(labware_value)
                        if base_id and base_id not in labware_ids:
                            errors.append(
                                f"Row {row_number}: labware '{labware_value}' (base '{base_id}') not defined in labware_dict.toml"
                            )

                # HOME control row validation:
                # If previous row was HOME, current row MUST have Tip Action: new (firmware requirement)
                if prev_row is not None and _is_home_control_row(prev_row):
                    # Current row follows a HOME row - must have Tip Action: new
                    if not is_home_row:  # Skip if current row is also HOME
                        tip_action = (row.get("Tip Action") or "").strip().lower()
                        if tip_action != "new":
                            errors.append(
                                f"Row {row_number}: row after HOME control MUST have Tip Action: new (got '{tip_action or 'empty'}'). "
                                f"This is a firmware requirement - the robot drops tips when homing."
                            )

                prev_row = row

    return _result(errors, warnings)


def _result(errors: List[str], warnings: List[str]) -> Dict[str, object]:
    status = "error" if errors else "ok"
    return {
        "status": status,
        "errors": errors,
        "warnings": warnings,
    }


__all__ = [
    "validate_configuration",
    "CSV_BASE_REQUIRED",
    "CSV_VOLUME_COLUMNS",
    "WELL_PATTERN",
    "PIPE_DELIMITED_WELL_PATTERN",
    "DISTRIBUTION_PATTERN",
]
