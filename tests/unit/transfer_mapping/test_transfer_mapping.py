from __future__ import annotations

from dataclasses import replace
import pytest

from tests.support.fixtures import FixtureEntry, load_fixtures_with_baselines, load_manifest
from tests.support.simulation import (
    build_expected_transfers_for_entry,
    parse_fixture_entry,
)
from tests.unit.simulation_logs.diagnostics import (
    compute_row_coverage,
    format_row_coverage,
    format_transfer_report,
)
from tests.unit.simulation_logs.matching import match_transfers


from tests.unit.simulation_logs.normalize import NormalizedDispenseEvent

@pytest.fixture(scope="module")
def manifest_entries() -> dict[str, FixtureEntry]:
    """Load all fixtures with baselines for tests that need parsed fixture data."""
    entries = load_fixtures_with_baselines()
    return {entry.fixture_id: entry for entry in entries}


def _build_for_fixture(fixture_id: str, manifest_entries: dict[str, FixtureEntry]):
    entry = manifest_entries[fixture_id]
    return build_expected_transfers_for_entry(entry)


@pytest.mark.parametrize(
    "fixture_id",
    [
        "basic-single_x1",
        "basic-multi_x1",
        "multi-multi",
        "distribution-multi",
        "home-control-single_x1",
    ],
)
def test_expected_transfers_match_fixture(
    fixture_id: str, manifest_entries: dict[str, FixtureEntry]
) -> None:
    entry = manifest_entries[fixture_id]
    expectations = build_expected_transfers_for_entry(entry)
    result = parse_fixture_entry(entry)

    match = match_transfers(expectations, result.events)
    coverage = compute_row_coverage(expectations, match)

    assert match.success, format_transfer_report(match, expectations)
    assert coverage.covered_rows == coverage.total_rows, format_row_coverage(coverage)


@pytest.mark.parametrize(
    "entry",
    load_fixtures_with_baselines(),
    ids=lambda entry: entry.fixture_id,
)
def test_manifest_fixture_match_and_coverage(entry: FixtureEntry) -> None:
    expectations = build_expected_transfers_for_entry(entry)
    result = parse_fixture_entry(entry)

    match = match_transfers(expectations, result.events)
    coverage = compute_row_coverage(expectations, match)
    transfer_report = format_transfer_report(match, expectations)
    coverage_report = format_row_coverage(coverage)

    if entry.expect_failure:
        assert not match.success, transfer_report
        assert coverage.covered_rows < coverage.total_rows, (
            f"{transfer_report}\n{coverage_report}"
        )
    else:
        assert match.success, transfer_report
        assert coverage.covered_rows == coverage.total_rows, (
            f"{transfer_report}\n{coverage_report}"
        )


def test_transfer_matching_reports_volume_mismatch(
    manifest_entries: dict[str, FixtureEntry]
) -> None:
    entry = manifest_entries["basic-single_x1"]
    expectations = build_expected_transfers_for_entry(entry)
    result = parse_fixture_entry(entry)

    mutated = [
        replace(
            expectations[0],
            dispense_volume_ul=expectations[0].dispense_volume_ul + 1.0,
        ),
        *expectations[1:],
    ]
    match = match_transfers(mutated, result.events)
    coverage = compute_row_coverage(mutated, match)

    assert not match.success
    assert match.mismatched or match.missing
    assert "dispense" in " ".join(match.mismatched + match.missing).lower()
    assert "coverage" in format_row_coverage(coverage).lower()


def test_transfer_matching_reports_semantic_sections(
    manifest_entries: dict[str, FixtureEntry]
) -> None:
    entry = manifest_entries["basic-single_x1"]
    expectations = build_expected_transfers_for_entry(entry)
    result = parse_fixture_entry(entry)

    assert len(expectations) > 1

    mismatched_index = 0
    missing_expected = expectations[-1]
    mutated = [
        replace(
            expected,
            dispense_volume_ul=expected.dispense_volume_ul + 1.0,
        )
        if index == mismatched_index
        else expected
        for index, expected in enumerate(expectations)
    ]

    filtered_events = [
        event
        for event in result.events
        if not (
            isinstance(event, NormalizedDispenseEvent)
            and event.labware_id == missing_expected.dest_labware_id
            and event.labware_slot == missing_expected.dest_slot
            and event.well == missing_expected.dest_well
        )
    ]

    last_index = max(event.sequence_index for event in filtered_events)
    extra_event = NormalizedDispenseEvent(
        sequence_index=last_index + 1,
        source="stdout",
        labware_display=missing_expected.dest_labware_id,
        labware_id=missing_expected.dest_labware_id,
        labware_slot=missing_expected.dest_slot,
        well="Z99",
        volume_ul=missing_expected.dispense_volume_ul,
        rate_ul_s=1.0,
        pipette_id=None,
    )
    events = [*filtered_events, extra_event]

    match = match_transfers(mutated, events)
    report = format_transfer_report(match, mutated)

    assert not match.success
    assert "Missing:" in report
    assert "Mismatched:" in report
    assert "Extra:" in report
    assert "Coverage:" in report
