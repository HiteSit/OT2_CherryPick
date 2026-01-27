from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from tests.fixtures.simulation import load_manifest
from tests.simulation_logs.diagnostics import (
    compute_row_coverage,
    format_row_coverage,
    format_transfer_report,
)
from tests.simulation_logs.expectations import build_expected_transfers
from tests.simulation_logs.matching import match_transfers
from tests.simulation_logs.normalize import load_settings
from tests.simulation_logs.parse import parse_fixture


@pytest.fixture(scope="module")
def manifest_entries() -> dict[str, object]:
    entries = load_manifest()
    return {entry.fixture_id: entry for entry in entries}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _load_settings_profile(profile: str) -> dict:
    settings_path = _repo_root() / "tests" / "e2e" / "configs" / profile / "settings.toml"
    return load_settings(settings_path)


def _build_for_fixture(fixture_id: str, manifest_entries: dict[str, object]):
    entry = manifest_entries[fixture_id]
    csv_path = _repo_root() / entry.csv_path
    settings = _load_settings_profile(entry.settings_profile)
    return build_expected_transfers(csv_path, settings)


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
    fixture_id: str, manifest_entries: dict[str, object]
) -> None:
    expectations = _build_for_fixture(fixture_id, manifest_entries)
    result = parse_fixture(fixture_id)

    match = match_transfers(expectations, result.events)
    coverage = compute_row_coverage(expectations, match)

    assert match.success, format_transfer_report(match, expectations)
    assert coverage.covered_rows == coverage.total_rows, format_row_coverage(coverage)


def test_transfer_matching_reports_volume_mismatch(
    manifest_entries: dict[str, object]
) -> None:
    expectations = _build_for_fixture("basic-single_x1", manifest_entries)
    result = parse_fixture("basic-single_x1")

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
