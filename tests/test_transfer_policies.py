from __future__ import annotations

from pathlib import Path

import pytest

from tests.fixtures.simulation import load_manifest
from tests.simulation_logs import (
    MatchResult,
    build_expected_transfers,
    evaluate_policies,
    match_transfers,
    parse_fixture,
)
from tests.simulation_logs.expectations import parse_labware_field
from tests.simulation_logs.normalize import NormalizedMixEvent, load_settings


@pytest.fixture(scope="module")
def manifest_entries() -> dict[str, object]:
    entries = load_manifest()
    return {entry.fixture_id: entry for entry in entries}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _load_settings_profile(profile: str) -> dict:
    settings_path = _repo_root() / "tests" / "e2e" / "configs" / profile / "settings.toml"
    return load_settings(settings_path)


def _build_fixture_context(
    fixture_id: str, manifest_entries: dict[str, object]
):
    entry = manifest_entries[fixture_id]
    csv_path = _repo_root() / entry.csv_path
    settings = _load_settings_profile(entry.settings_profile)
    expected_transfers = build_expected_transfers(csv_path, settings)
    parsed = parse_fixture(fixture_id)
    match = match_transfers(expected_transfers, parsed.events)
    return expected_transfers, match, parsed.events, csv_path, settings


@pytest.mark.parametrize("fixture_id", ["basic-single_x1", "distribution-multi"])
def test_policy_tip_reuse_from_fixtures(
    fixture_id: str, manifest_entries: dict[str, object]
) -> None:
    expected, match, events, csv_path, settings = _build_fixture_context(
        fixture_id, manifest_entries
    )
    result = evaluate_policies(expected, match, events, csv_path, settings)
    assert not result.errors, result.summary()


def test_policy_air_gap_fill_analytics(
    manifest_entries: dict[str, object]
) -> None:
    expected, match, events, csv_path, settings = _build_fixture_context(
        "fill-analytics", manifest_entries
    )
    result = evaluate_policies(expected, match, events, csv_path, settings)
    assert not result.errors, result.summary()


def test_policy_mix_with_evidence(tmp_path: Path) -> None:
    csv_path = tmp_path / "mix.csv"
    csv_path.write_text(
        "Source Labware,Source Well,Volume (ul),Dest Labware,Dest Well,Mix Volume\n"
        "tube_rack_96_1500ul_4,A1,50,384_ppv_55ul_2,B1,20\n",
        encoding="utf-8",
    )

    settings = _load_settings_profile("single_X1")
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
