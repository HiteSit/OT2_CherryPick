from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Sequence, cast

from tests.simulation_logs.expectations import ExpectedTransfer
from tests.simulation_logs.normalize import (
    NormalizedAspirateEvent,
    NormalizedDispenseEvent,
    NormalizedEvent,
)


@dataclass(frozen=True)
class MatchResult:
    success: bool
    missing: list[str]
    extra: list[str]
    mismatched: list[str]
    missing_expected: list[ExpectedTransfer]
    mismatched_expected: list[ExpectedTransfer]
    matched_count: int

    def summary(self) -> str:
        if self.success:
            return f"Matched {self.matched_count} transfers."
        return (
            "Matched "
            f"{self.matched_count} transfers. Missing: {len(self.missing)}. "
            f"Extra: {len(self.extra)}. Mismatched: {len(self.mismatched)}."
        )

    def report(self) -> str:
        lines = [self.summary()]
        if self.missing:
            lines.append("Missing:")
            lines.extend(self.missing)
        if self.mismatched:
            lines.append("Mismatched:")
            lines.extend(self.mismatched)
        if self.extra:
            lines.append("Extra:")
            lines.extend(self.extra)
        return "\n".join(lines)


def match_transfers(
    expected_transfers: Sequence[ExpectedTransfer],
    events: Sequence[NormalizedEvent],
    *,
    allow_extra_events: bool = False,
) -> MatchResult:
    ordered_expected = sorted(expected_transfers, key=lambda exp: exp.sequence_index)
    filtered_events = _filter_transfer_events(events)

    missing: list[str] = []
    extra: list[str] = []
    mismatched: list[str] = []
    missing_expected: list[ExpectedTransfer] = []
    mismatched_expected: list[ExpectedTransfer] = []
    matched_count = 0
    event_index = 0
    expected_index = 0

    while expected_index < len(ordered_expected):
        if event_index >= len(filtered_events):
            missing.extend(
                _describe_missing(expected)
                for expected in ordered_expected[expected_index:]
            )
            break

        expected = ordered_expected[expected_index]
        if expected.group_id:
            group_id = expected.group_id
            group_entries: list[ExpectedTransfer] = []
            while (
                expected_index < len(ordered_expected)
                and ordered_expected[expected_index].group_id == group_id
            ):
                group_entries.append(ordered_expected[expected_index])
                expected_index += 1
            event_index, group_matched = _match_distribution_group(
                group_entries,
                filtered_events,
                event_index,
                missing=missing,
                missing_expected=missing_expected,
                extra=extra,
                mismatched=mismatched,
                mismatched_expected=mismatched_expected,
            )
            matched_count += group_matched
            continue

        event_index, matched = _match_single_transfer(
            expected,
            filtered_events,
            event_index,
            missing=missing,
            missing_expected=missing_expected,
            extra=extra,
            mismatched=mismatched,
            mismatched_expected=mismatched_expected,
        )
        if matched:
            matched_count += 1
        expected_index += 1

    if event_index < len(filtered_events):
        extra.extend(_format_event(event) for event in filtered_events[event_index:])

    success = not missing and not mismatched and (allow_extra_events or not extra)
    return MatchResult(
        success=success,
        missing=missing,
        extra=extra,
        mismatched=mismatched,
        missing_expected=missing_expected,
        mismatched_expected=mismatched_expected,
        matched_count=matched_count,
    )


def _filter_transfer_events(
    events: Sequence[NormalizedEvent],
) -> list[NormalizedAspirateEvent | NormalizedDispenseEvent]:
    transfer_events = [
        event
        for event in events
        if isinstance(event, (NormalizedAspirateEvent, NormalizedDispenseEvent))
    ]
    return sorted(transfer_events, key=lambda event: event.sequence_index)


def _match_distribution_group(
    group_entries: Sequence[ExpectedTransfer],
    events: Sequence[NormalizedAspirateEvent | NormalizedDispenseEvent],
    event_index: int,
    *,
    missing: list[str],
    missing_expected: list[ExpectedTransfer],
    extra: list[str],
    mismatched: list[str],
    mismatched_expected: list[ExpectedTransfer],
) -> tuple[int, int]:
    if not group_entries:
        return event_index, 0
    leader = group_entries[0]
    group_total = leader.group_total_volume_ul
    if group_total is None:
        mismatched.append(f"Missing group_total_volume_ul for {leader.group_id}")
        mismatched_expected.append(leader)
        return event_index, 0

    aspirate, event_index = _advance_to_match_aspirate(
        events,
        event_index,
        lambda event: _matches_aspirate_identifiers(event, leader),
        extra,
    )
    if aspirate is None:
        for entry in group_entries:
            missing.append(_describe_missing(entry))
            missing_expected.append(entry)
        return event_index, 0

    if aspirate.volume_ul != group_total:
        mismatched.append(
            _describe_volume_mismatch(
                "aspirate",
                expected_volume=group_total,
                event=aspirate,
                expected=leader,
            )
        )
        mismatched_expected.append(leader)

    group_matched = 0
    for entry in group_entries:
        dispense, event_index = _advance_to_match_dispense(
            events,
            event_index,
            lambda event: _matches_dispense_identifiers(event, entry),
            extra,
        )
        if dispense is None:
            missing.append(_describe_missing(entry))
            missing_expected.append(entry)
            continue
        if dispense.volume_ul != entry.dispense_volume_ul:
            mismatched.append(
                _describe_volume_mismatch(
                    "dispense",
                    expected_volume=entry.dispense_volume_ul,
                    event=dispense,
                    expected=entry,
                )
            )
            mismatched_expected.append(entry)
            continue
        group_matched += 1

    return event_index, group_matched


def _match_single_transfer(
    expected: ExpectedTransfer,
    events: Sequence[NormalizedAspirateEvent | NormalizedDispenseEvent],
    event_index: int,
    *,
    missing: list[str],
    missing_expected: list[ExpectedTransfer],
    extra: list[str],
    mismatched: list[str],
    mismatched_expected: list[ExpectedTransfer],
) -> tuple[int, bool]:
    aspirate, event_index = _advance_to_match_aspirate(
        events,
        event_index,
        lambda event: _matches_aspirate_identifiers(event, expected),
        extra,
    )
    if aspirate is None:
        missing.append(_describe_missing(expected))
        missing_expected.append(expected)
        return event_index, False

    if aspirate.volume_ul < expected.aspirate_volume_ul:
        return _match_split_transfer(
            expected,
            cast(NormalizedAspirateEvent, aspirate),
            events,
            event_index,
            missing=missing,
            missing_expected=missing_expected,
            extra=extra,
            mismatched=mismatched,
            mismatched_expected=mismatched_expected,
        )

    if aspirate.volume_ul != expected.aspirate_volume_ul:
        mismatched.append(
            _describe_volume_mismatch(
                "aspirate",
                expected_volume=expected.aspirate_volume_ul,
                event=aspirate,
                expected=expected,
            )
        )
        mismatched_expected.append(expected)

    dispense, event_index = _advance_to_match_dispense(
        events,
        event_index,
        lambda event: _matches_dispense_identifiers(event, expected),
        extra,
    )
    if dispense is None:
        missing.append(_describe_missing(expected))
        missing_expected.append(expected)
        return event_index, False

    if dispense.volume_ul != expected.dispense_volume_ul:
        mismatched.append(
            _describe_volume_mismatch(
                "dispense",
                expected_volume=expected.dispense_volume_ul,
                event=dispense,
                expected=expected,
            )
        )
        mismatched_expected.append(expected)
        return event_index, False

    return event_index, aspirate.volume_ul == expected.aspirate_volume_ul


def _match_split_transfer(
    expected: ExpectedTransfer,
    first_aspirate: NormalizedAspirateEvent,
    events: Sequence[NormalizedAspirateEvent | NormalizedDispenseEvent],
    event_index: int,
    *,
    missing: list[str],
    missing_expected: list[ExpectedTransfer],
    extra: list[str],
    mismatched: list[str],
    mismatched_expected: list[ExpectedTransfer],
) -> tuple[int, bool]:
    remaining_aspirate = expected.aspirate_volume_ul
    remaining_dispense = expected.dispense_volume_ul
    running_aspirate = 0.0
    running_dispense = 0.0

    current_aspirate: NormalizedAspirateEvent | None = first_aspirate

    while running_aspirate < expected.aspirate_volume_ul or running_dispense < expected.dispense_volume_ul:
        if current_aspirate is None:
            current_aspirate, event_index = _advance_to_match_aspirate(
                events,
                event_index,
                lambda event: _matches_aspirate_identifiers(event, expected),
                extra,
            )
            if current_aspirate is None:
                missing.append(_describe_missing(expected))
                missing_expected.append(expected)
                return event_index, False

        if current_aspirate.volume_ul > remaining_aspirate:
            mismatched.append(
                _describe_split_mismatch(
                    "aspirate",
                    expected=expected,
                    event=current_aspirate,
                    remaining_volume=remaining_aspirate,
                )
            )
            mismatched_expected.append(expected)
            return event_index, False

        running_aspirate += current_aspirate.volume_ul
        remaining_aspirate = expected.aspirate_volume_ul - running_aspirate

        dispense, event_index = _advance_to_match_dispense(
            events,
            event_index,
            lambda event: _matches_dispense_identifiers(event, expected),
            extra,
        )
        if dispense is None:
            missing.append(_describe_missing(expected))
            missing_expected.append(expected)
            return event_index, False

        if dispense.volume_ul > remaining_dispense:
            mismatched.append(
                _describe_split_mismatch(
                    "dispense",
                    expected=expected,
                    event=dispense,
                    remaining_volume=remaining_dispense,
                )
            )
            mismatched_expected.append(expected)
            return event_index, False

        running_dispense += dispense.volume_ul
        remaining_dispense = expected.dispense_volume_ul - running_dispense

        if (
            running_aspirate == expected.aspirate_volume_ul
            and running_dispense == expected.dispense_volume_ul
        ):
            return event_index, True

        current_aspirate = None

    mismatched.append(
        _describe_split_totals(expected, running_aspirate, running_dispense)
    )
    mismatched_expected.append(expected)
    return event_index, False


def _advance_to_match_aspirate(
    events: Sequence[NormalizedAspirateEvent | NormalizedDispenseEvent],
    event_index: int,
    predicate: Callable[[NormalizedAspirateEvent], bool],
    extra: list[str],
) -> tuple[NormalizedAspirateEvent | None, int]:
    while event_index < len(events):
        event = events[event_index]
        if isinstance(event, NormalizedAspirateEvent) and predicate(event):
            return event, event_index + 1
        extra.append(_format_event(event))
        event_index += 1
    return None, event_index


def _advance_to_match_dispense(
    events: Sequence[NormalizedAspirateEvent | NormalizedDispenseEvent],
    event_index: int,
    predicate: Callable[[NormalizedDispenseEvent], bool],
    extra: list[str],
) -> tuple[NormalizedDispenseEvent | None, int]:
    while event_index < len(events):
        event = events[event_index]
        if isinstance(event, NormalizedDispenseEvent) and predicate(event):
            return event, event_index + 1
        extra.append(_format_event(event))
        event_index += 1
    return None, event_index


def _matches_aspirate_identifiers(
    event: NormalizedAspirateEvent, expected: ExpectedTransfer
) -> bool:
    return (
        event.labware_id == expected.source_labware_id
        and event.labware_slot == expected.source_slot
        and event.well == expected.source_well
    )


def _matches_dispense_identifiers(
    event: NormalizedDispenseEvent, expected: ExpectedTransfer
) -> bool:
    return (
        event.labware_id == expected.dest_labware_id
        and event.labware_slot == expected.dest_slot
        and event.well == expected.dest_well
    )


def _describe_missing(expected: ExpectedTransfer) -> str:
    return f"Missing transfer: {_format_expected(expected)}"


def _describe_volume_mismatch(
    action: str,
    *,
    expected_volume: float,
    event: NormalizedAspirateEvent | NormalizedDispenseEvent,
    expected: ExpectedTransfer,
) -> str:
    return (
        f"Expected {action} {expected_volume} uL for {_format_expected(expected)}, "
        f"got {event.volume_ul} uL"
    )


def _describe_split_mismatch(
    action: str,
    *,
    expected: ExpectedTransfer,
    event: NormalizedAspirateEvent | NormalizedDispenseEvent,
    remaining_volume: float,
) -> str:
    return (
        f"Split {action} exceeds remaining volume for {_format_expected(expected)} "
        f"(remaining {remaining_volume} uL, got {event.volume_ul} uL)"
    )


def _describe_split_totals(
    expected: ExpectedTransfer,
    aspirate_total: float,
    dispense_total: float,
) -> str:
    return (
        "Split transfer totals did not match for "
        f"{_format_expected(expected)} (aspirate {aspirate_total} uL, "
        f"dispense {dispense_total} uL)"
    )


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


def _format_event(event: NormalizedAspirateEvent | NormalizedDispenseEvent) -> str:
    if isinstance(event, NormalizedAspirateEvent):
        action = "aspirate"
        target = "from"
    else:
        action = "dispense"
        target = "into"
    return (
        f"{event.sequence_index}: {action} {event.volume_ul} uL {target} "
        f"{event.labware_id}/{event.labware_slot}/{event.well}"
    )


__all__ = ["MatchResult", "match_transfers"]
