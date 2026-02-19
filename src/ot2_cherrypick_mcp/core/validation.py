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

    # ── Build pipette lookup: name -> {volume_range, channels} ──
    pipette_entries = labware_data.get("pipettes", []) if isinstance(labware_data, dict) else []
    pipettes_by_name: Dict[str, Dict[str, object]] = {}
    for pentry in pipette_entries:
        if isinstance(pentry, dict) and pentry.get("name"):
            pipettes_by_name[pentry["name"]] = pentry

    # Build working_plate labware_id set for CSV reference validation
    working_plate_ids: set = set()
    if settings_data:
        working_plate = settings_data.get("settings", {}).get("working_plate", [])  # type: ignore[index]
        if isinstance(working_plate, list):
            for entry in working_plate:
                if not isinstance(entry, dict):
                    continue
                entry_type = entry.get("type", "").lower()
                if entry_type == "module":
                    continue
                labware_id = entry.get("labware_id", "").strip()
                if labware_id:
                    working_plate_ids.add(labware_id)

    # ── Determine mode and active pipette(s) ──
    mode = ""
    if settings_data:
        mode = (
            settings_data.get("settings", {})  # type: ignore[union-attr]
            .get("general", {})
            .get("mode", "")
        )

    # Map mode -> pipette name (matches CherryPick_OT2.py logic)
    # single_X1 -> Pipette_1, multi / multi_X1 -> Pipette_8, dual -> both
    active_pipette_configs: List[Dict[str, object]] = []
    if mode == "single_X1":
        if "Pipette_1" in pipettes_by_name:
            active_pipette_configs.append(pipettes_by_name["Pipette_1"])
    elif mode in ("multi", "multi_X1"):
        if "Pipette_8" in pipettes_by_name:
            active_pipette_configs.append(pipettes_by_name["Pipette_8"])
    elif mode == "dual":
        # Dual mode uses both pipettes; volume checks use per-row Mode column
        for pname in ("Pipette_1", "Pipette_8"):
            if pname in pipettes_by_name:
                active_pipette_configs.append(pipettes_by_name[pname])

    # Note: multi-mode well_count compatibility is now validated at runtime
    # in CherryPick_OT2.py after labware loading (uses len(loaded.wells())).

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

        # Determine whether air-gap and per-row mode columns are present
        has_air_gap_column = "Air Gap" in fieldnames
        has_csv_mode_column = "Mode" in fieldnames

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

                    # ── Parse volume for this row ──
                    row_volume: float | None = None

                    # Validate appropriate volume column
                    if is_distribution:
                        # Distribution row - check Distribution Volume (ul)
                        if "Distribution Volume (ul)" in fieldnames:
                            try:
                                volume = float(row.get("Distribution Volume (ul)") or 0)
                                if volume <= 0:
                                    errors.append(f"Row {row_number}: distribution volume must be positive")
                                else:
                                    row_volume = volume
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
                                else:
                                    row_volume = volume
                            except ValueError:
                                errors.append(f"Row {row_number}: volume is not a number")
                        else:
                            errors.append(f"Row {row_number}: cherry-pick row requires 'Volume (ul)' column")

                    # ── Resolve per-row pipette configs ──
                    # In dual mode with a Mode column, pick the right pipette
                    row_pipette_configs = active_pipette_configs
                    if mode == "dual" and has_csv_mode_column:
                        csv_row_mode = (row.get("Mode") or "").strip().lower()
                        if csv_row_mode == "single_x1" and "Pipette_1" in pipettes_by_name:
                            row_pipette_configs = [pipettes_by_name["Pipette_1"]]
                        elif csv_row_mode in ("multi", "multi_x1") and "Pipette_8" in pipettes_by_name:
                            row_pipette_configs = [pipettes_by_name["Pipette_8"]]

                    # ── Volume vs pipette range checks ──
                    # Skip for distribution rows: the per-well distribution volume can be
                    # below pipette minimum because the runtime aspirates the TOTAL volume
                    # (sum of all per-well volumes), not individual per-well amounts.
                    if row_volume is not None and row_pipette_configs and not is_distribution:
                        for pip_cfg in row_pipette_configs:
                            vol_range = pip_cfg.get("volume_range")
                            if not isinstance(vol_range, (list, tuple)) or len(vol_range) < 2:
                                continue
                            pip_min = float(vol_range[0])
                            pip_max = float(vol_range[1])
                            pip_name = pip_cfg.get("name", "unknown")

                            # Volume below pipette minimum: warning because the
                            # pipette can physically aspirate but with reduced accuracy
                            if row_volume < pip_min:
                                warnings.append(
                                    f"Row {row_number}: volume {row_volume} \u00b5L is below "
                                    f"{pip_name} rated minimum ({pip_min} \u00b5L) "
                                    f"\u2014 accuracy may be reduced"
                                )

                            # Volume above max is handled by split_volume_into_chunks
                            # at runtime, but warn if it will require splitting
                            if row_volume > pip_max:
                                warnings.append(
                                    f"Row {row_number}: volume {row_volume} \u00b5L exceeds "
                                    f"{pip_name} max ({pip_max} \u00b5L) \u2014 will be split "
                                    f"into multiple transfers at runtime"
                                )

                    # ── Air Gap + Volume vs pipette capacity ──
                    # Also skip for distribution rows (runtime handles total volume splitting)
                    if row_volume is not None and has_air_gap_column and row_pipette_configs and not is_distribution:
                        air_gap_str = (row.get("Air Gap") or "").strip()
                        if air_gap_str:
                            try:
                                air_gap_vol = float(air_gap_str)
                                if air_gap_vol > 0:
                                    for pip_cfg in row_pipette_configs:
                                        vol_range = pip_cfg.get("volume_range")
                                        if not isinstance(vol_range, (list, tuple)) or len(vol_range) < 2:
                                            continue
                                        pip_min = float(vol_range[0])
                                        pip_max = float(vol_range[1])
                                        pip_name = pip_cfg.get("name", "unknown")

                                        effective_max = pip_max - air_gap_vol
                                        if effective_max < pip_min:
                                            errors.append(
                                                f"Row {row_number}: air gap ({air_gap_vol} \u00b5L) "
                                                f"leaves insufficient capacity for {pip_name}. "
                                                f"Effective max ({effective_max} \u00b5L) < minimum "
                                                f"({pip_min} \u00b5L)"
                                            )
                                        elif row_volume > effective_max:
                                            # Will require extra splits; warn
                                            warnings.append(
                                                f"Row {row_number}: volume {row_volume} \u00b5L + "
                                                f"air gap {air_gap_vol} \u00b5L exceeds {pip_name} "
                                                f"capacity ({pip_max} \u00b5L) \u2014 additional transfer "
                                                f"splits will occur"
                                            )
                            except ValueError:
                                pass  # Non-numeric air gap is not this check's concern

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
                        if base_id and base_id not in working_plate_ids:
                            errors.append(
                                f"Row {row_number}: labware '{labware_value}' (base '{base_id}') not found in settings.toml working_plate"
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
