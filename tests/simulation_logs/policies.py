from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional, Sequence

from tests.simulation_logs.expectations import (
    ExpectedTransfer,
    detect_home_row,
    parse_csv_rows,
    parse_labware_field,
)
from tests.simulation_logs.matching import MatchResult
from tests.simulation_logs.normalize import (
    NormalizedEvent,
    NormalizedMixEvent,
    NormalizedTipDropEvent,
    NormalizedTipPickupEvent,
)


@dataclass(frozen=True)
class PolicyIssue:
    policy: str
    message: str
    row_index: Optional[int] = None

    def format(self) -> str:
        if self.row_index is None:
            return f"[{self.policy}] {self.message}"
        return f"[{self.policy}] row {self.row_index}: {self.message}"


@dataclass
class PolicyResult:
    errors: list[PolicyIssue]
    warnings: list[PolicyIssue]

    def summary(self) -> str:
        if not self.errors and not self.warnings:
            return "Policy checks: no issues."
        lines = [
            f"Policy checks: {len(self.errors)} error(s), {len(self.warnings)} warning(s)."
        ]
        if self.errors:
            lines.append("Errors:")
            lines.extend(issue.format() for issue in self.errors)
        if self.warnings:
            lines.append("Warnings:")
            lines.extend(issue.format() for issue in self.warnings)
        return "\n".join(lines)


@dataclass(frozen=True)
class _RowIntent:
    row_index: int
    dest_labware_id: str
    dest_slot: str
    dest_wells: list[str]
    tip_action: Optional[str]
    mix_volume: Optional[float]
    air_gap: Optional[float]


def evaluate_policies(
    expected_transfers: Sequence[ExpectedTransfer],
    match_result: MatchResult,
    events: Sequence[NormalizedEvent],
    csv_path: Path,
    settings: dict,
) -> PolicyResult:
    intents = _load_row_intents(csv_path)
    errors: list[PolicyIssue] = []
    warnings: list[PolicyIssue] = []

    _evaluate_tip_reuse(intents, events, errors, warnings)
    _evaluate_mix(intents, events, errors, warnings)
    _evaluate_air_gap(intents, match_result, expected_transfers, errors, warnings)

    return PolicyResult(errors=errors, warnings=warnings)


def _load_row_intents(csv_path: Path) -> list[_RowIntent]:
    rows = parse_csv_rows(csv_path)
    intents: list[_RowIntent] = []
    csv_row_index = 0
    for row in rows:
        if detect_home_row(row):
            continue
        csv_row_index += 1

        tip_action = _normalize_action(row.get("Tip Action"))
        mix_volume = _parse_float(row.get("Mix Volume"))
        air_gap = _parse_float(row.get("Air Gap"))

        dest_labware, dest_slot = parse_labware_field(row.get("Dest Labware", ""))
        dest_wells = _parse_dest_wells(row.get("Dest Well"))

        intents.append(
            _RowIntent(
                row_index=csv_row_index,
                dest_labware_id=dest_labware,
                dest_slot=dest_slot,
                dest_wells=dest_wells,
                tip_action=tip_action,
                mix_volume=mix_volume,
                air_gap=air_gap,
            )
        )
    return intents


def _normalize_action(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    normalized = str(value).strip().lower()
    return normalized or None


def _parse_float(value: Optional[str]) -> Optional[float]:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return float(text)


def _parse_dest_wells(value: Optional[str]) -> list[str]:
    if value is None:
        return []
    text = str(value).strip()
    if not text:
        return []
    return [part.strip() for part in text.split("|") if part.strip()]


def _evaluate_tip_reuse(
    intents: Sequence[_RowIntent],
    events: Sequence[NormalizedEvent],
    errors: list[PolicyIssue],
    warnings: list[PolicyIssue],
) -> None:
    action_rows = [intent for intent in intents if intent.tip_action]
    if not action_rows:
        warnings.append(
            PolicyIssue(
                policy="tip_reuse",
                message="Tip Action intent not found; skipping tip reuse policy.",
            )
        )
        return

    expected_pickups, expected_drops, row_indices = _simulate_tip_actions(action_rows)
    observed_pickups = sum(
        isinstance(event, NormalizedTipPickupEvent) for event in events
    )
    observed_drops = sum(isinstance(event, NormalizedTipDropEvent) for event in events)
    row_label = ", ".join(str(row) for row in row_indices)

    if expected_pickups != observed_pickups:
        errors.append(
            PolicyIssue(
                policy="tip_reuse",
                message=(
                    "Tip pickup count mismatch for rows "
                    f"{row_label}: expected {expected_pickups}, observed {observed_pickups}."
                ),
            )
        )
    if expected_drops != observed_drops:
        errors.append(
            PolicyIssue(
                policy="tip_reuse",
                message=(
                    "Tip drop count mismatch for rows "
                    f"{row_label}: expected {expected_drops}, observed {observed_drops}."
                ),
            )
        )


def _simulate_tip_actions(
    intents: Sequence[_RowIntent],
) -> tuple[int, int, list[int]]:
    tip_present = False
    expected_pickups = 0
    expected_drops = 0
    row_indices: list[int] = []

    for intent in intents:
        action = intent.tip_action
        if action is None:
            continue
        row_indices.append(intent.row_index)

        had_tip = tip_present
        if not tip_present:
            expected_pickups += 1
            tip_present = True

        if action == "new" and had_tip:
            expected_drops += 1
            expected_pickups += 1

        if action == "drop":
            expected_drops += 1
            tip_present = False

    if tip_present:
        expected_drops += 1

    return expected_pickups, expected_drops, row_indices


def _evaluate_mix(
    intents: Sequence[_RowIntent],
    events: Sequence[NormalizedEvent],
    errors: list[PolicyIssue],
    warnings: list[PolicyIssue],
) -> None:
    mix_intents = [intent for intent in intents if (intent.mix_volume or 0) > 0]
    if not mix_intents:
        warnings.append(
            PolicyIssue(
                policy="mix",
                message="Mix intent not found; skipping mix policy.",
            )
        )
        return

    mix_events = [event for event in events if isinstance(event, NormalizedMixEvent)]
    if not mix_events:
        warnings.append(
            PolicyIssue(
                policy="mix",
                message="Mix intent present but no mix events found; skipping mix policy.",
            )
        )
        return

    observed = {
        (event.labware_id, event.labware_slot, event.well)
        for event in mix_events
        if event.well is not None
    }
    missing_by_row: dict[int, list[str]] = {}

    for intent in mix_intents:
        for well in intent.dest_wells:
            key = (intent.dest_labware_id, intent.dest_slot, well)
            if key in observed:
                continue
            missing_by_row.setdefault(intent.row_index, []).append(well)

    for row_index, wells in sorted(missing_by_row.items()):
        joined = ", ".join(wells)
        errors.append(
            PolicyIssue(
                policy="mix",
                row_index=row_index,
                message=(
                    "Missing mix evidence for destination wells: "
                    f"{joined}."
                ),
            )
        )


def _evaluate_air_gap(
    intents: Sequence[_RowIntent],
    match_result: MatchResult,
    expected_transfers: Sequence[ExpectedTransfer],
    errors: list[PolicyIssue],
    warnings: list[PolicyIssue],
) -> None:
    air_gap_rows = {intent.row_index for intent in intents if (intent.air_gap or 0) > 0}
    if not air_gap_rows:
        warnings.append(
            PolicyIssue(
                policy="air_gap",
                message="Air gap intent not found; skipping air gap policy.",
            )
        )
        return

    failed_rows: dict[int, list[str]] = {}
    for expected in _iter_air_gap_failures(match_result, air_gap_rows):
        if expected.row_index is None:
            continue
        failed_rows.setdefault(expected.row_index, []).append(_format_expected(expected))

    for row_index, entries in sorted(failed_rows.items()):
        errors.append(
            PolicyIssue(
                policy="air_gap",
                row_index=row_index,
                message="Air gap row missing/mismatched transfers: "
                + "; ".join(entries),
            )
        )


def _iter_air_gap_failures(
    match_result: MatchResult, air_gap_rows: set[int]
) -> Iterable[ExpectedTransfer]:
    for expected in match_result.missing_expected:
        if expected.row_index in air_gap_rows:
            yield expected
    for expected in match_result.mismatched_expected:
        if expected.row_index in air_gap_rows:
            yield expected


def _format_expected(expected: ExpectedTransfer) -> str:
    row_label = None
    if expected.row_index is not None:
        row_label = f"row {expected.row_index}"
    label = (
        f"{expected.source_labware_id}/{expected.source_slot}/{expected.source_well} "
        f"-> {expected.dest_labware_id}/{expected.dest_slot}/{expected.dest_well}"
    )
    if expected.group_id:
        label = f"[{expected.group_id}] {label}"
    if row_label:
        label = f"{row_label} {label}"
    return (
        f"{label} (aspirate {expected.aspirate_volume_ul} uL, "
        f"dispense {expected.dispense_volume_ul} uL)"
    )


__all__ = ["PolicyIssue", "PolicyResult", "evaluate_policies"]
