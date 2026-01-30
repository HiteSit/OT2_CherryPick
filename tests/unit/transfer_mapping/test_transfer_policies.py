from __future__ import annotations

from pathlib import Path

import pytest

from tests.support.fixtures import FixtureEntry, load_fixtures_with_baselines, load_manifest
from tests.support.simulation import (
    build_fixture_context,
    load_settings_profile,
)
from tests.unit.simulation_logs.expectations import (
    build_expected_transfers,
    parse_labware_field,
)
from tests.unit.simulation_logs.matching import MatchResult, match_transfers
from tests.unit.simulation_logs.policies import evaluate_policies


from tests.unit.simulation_logs.normalize import (
    NormalizedMixEvent,
    NormalizedTipDropEvent,
    NormalizedTipPickupEvent,
)

@pytest.fixture(scope="module")
def manifest_entries() -> dict[str, FixtureEntry]:
    """Load all fixtures with baselines for tests that need parsed fixture data."""
    entries = load_fixtures_with_baselines()
    return {entry.fixture_id: entry for entry in entries}


@pytest.mark.parametrize(
    "entry",
    load_fixtures_with_baselines(),
    ids=lambda entry: entry.fixture_id,
)
def test_manifest_fixtures_policy_evaluation(entry: FixtureEntry) -> None:
    expected, parsed, csv_path, settings = build_fixture_context(entry)
    match = match_transfers(expected, parsed.events)
    result = evaluate_policies(expected, match, parsed.events, csv_path, settings)
    summary = result.summary()

    if entry.expect_failure:
        assert not match.success, summary
        assert summary is not None, summary
    else:
        assert not result.errors, summary


@pytest.mark.parametrize("fixture_id", ["basic-single_x1", "distribution-multi"])
def test_policy_tip_reuse_from_fixtures(
    fixture_id: str, manifest_entries: dict[str, FixtureEntry]
) -> None:
    entry = manifest_entries[fixture_id]
    expected, parsed, csv_path, settings = build_fixture_context(entry)
    match = match_transfers(expected, parsed.events)
    events = parsed.events
    result = evaluate_policies(expected, match, events, csv_path, settings)
    assert not result.errors, result.summary()


def test_policy_air_gap_fill_analytics(
    manifest_entries: dict[str, FixtureEntry]
) -> None:
    entry = manifest_entries["fill-analytics"]
    expected, parsed, csv_path, settings = build_fixture_context(entry)
    match = match_transfers(expected, parsed.events)
    events = parsed.events
    result = evaluate_policies(expected, match, events, csv_path, settings)
    assert not result.errors, result.summary()


def test_policy_mix_with_evidence(tmp_path: Path) -> None:
    csv_path = tmp_path / "mix.csv"
    csv_path.write_text(
        "Source Labware,Source Well,Volume (ul),Dest Labware,Dest Well,Mix Volume\n"
        "tube_rack_96_1500ul_4,A1,50,384_ppv_55ul_2,B1,20\n",
        encoding="utf-8",
    )

    settings = load_settings_profile("single_X1")
    expected_transfers = build_expected_transfers(csv_path, settings)
    dest_labware, dest_slot = parse_labware_field("384_ppv_55ul_2")
    events = [
        NormalizedMixEvent(
            sequence_index=1,
            source="stdout",
            labware_display=dest_labware,
            labware_id=dest_labware,
            labware_slot=dest_slot,
            well="B1",
            volume_ul=20.0,
            rate_ul_s=None,
            pipette_id=None,
        )
    ]
    match = MatchResult(
        success=True,
        missing=[],
        extra=[],
        mismatched=[],
        missing_expected=[],
        mismatched_expected=[],
        matched_count=len(expected_transfers),
    )
    result = evaluate_policies(expected_transfers, match, events, csv_path, settings)
    assert not result.errors, result.summary()


def test_policy_tip_reuse_reports_missing_pickups(tmp_path: Path) -> None:
    csv_path = tmp_path / "tip_reuse.csv"
    csv_path.write_text(
        "Source Labware,Source Well,Volume (ul),Dest Labware,Dest Well,Tip Action\n"
        "tube_rack_96_1500ul_4,A1,50,384_ppv_55ul_2,B1,new\n",
        encoding="utf-8",
    )

    settings = load_settings_profile("single_X1")
    expected_transfers = build_expected_transfers(csv_path, settings)
    match = match_transfers(expected_transfers, [])

    result = evaluate_policies(expected_transfers, match, [], csv_path, settings)

    assert any(issue.policy == "tip_reuse" for issue in result.errors)
    assert "tip_reuse" in result.summary()


def test_policy_mix_reports_missing_row_index(tmp_path: Path) -> None:
    csv_path = tmp_path / "mix_intent.csv"
    csv_path.write_text(
        "Source Labware,Source Well,Volume (ul),Dest Labware,Dest Well,Mix Volume\n"
        "tube_rack_96_1500ul_4,A1,50,384_ppv_55ul_2,B1,20\n",
        encoding="utf-8",
    )

    settings = load_settings_profile("single_X1")
    expected_transfers = build_expected_transfers(csv_path, settings)
    dest_labware, dest_slot = parse_labware_field("384_ppv_55ul_2")
    events = [
        NormalizedMixEvent(
            sequence_index=1,
            source="stdout",
            labware_display=dest_labware,
            labware_id=dest_labware,
            labware_slot=dest_slot,
            well="C1",
            volume_ul=20.0,
            rate_ul_s=None,
            pipette_id=None,
        )
    ]
    match = match_transfers(expected_transfers, [])

    result = evaluate_policies(expected_transfers, match, events, csv_path, settings)

    assert any(issue.policy == "mix" for issue in result.errors)
    assert "row 1" in result.summary()


def test_policy_air_gap_reports_row_index(tmp_path: Path) -> None:
    csv_path = tmp_path / "air_gap.csv"
    csv_path.write_text(
        "Source Labware,Source Well,Volume (ul),Dest Labware,Dest Well,Air Gap\n"
        "tube_rack_96_1500ul_4,A1,50,384_ppv_55ul_2,B1,10\n",
        encoding="utf-8",
    )

    settings = load_settings_profile("single_X1")
    expected_transfers = build_expected_transfers(csv_path, settings)
    match = MatchResult(
        success=False,
        missing=[],
        extra=[],
        mismatched=[],
        missing_expected=expected_transfers,
        mismatched_expected=[],
        matched_count=0,
    )
    events = [
        NormalizedTipPickupEvent(
            sequence_index=1,
            source="stdout",
            labware_display="opentrons_96_tiprack_300ul",
            labware_id="opentrons_96_tiprack_300ul",
            labware_slot="5",
            well="A1",
            pipette_id=None,
        ),
        NormalizedTipDropEvent(
            sequence_index=2,
            source="stdout",
            labware_display="trash",
            labware_id="trash_bin",
            labware_slot="12",
            well=None,
            pipette_id=None,
        ),
    ]

    result = evaluate_policies(expected_transfers, match, events, csv_path, settings)

    assert any(issue.policy == "air_gap" for issue in result.errors)
    assert "row 1" in result.summary()
