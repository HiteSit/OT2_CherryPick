from __future__ import annotations

from pathlib import Path

import pytest

from tests.fixtures.simulation import load_manifest
from tests.simulation_logs.expectations import build_expected_transfers
from tests.simulation_logs.normalize import load_settings


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
    ("fixture_id", "expected_volumes"),
    [
        ("basic-single_x1", [100.0, 50.0, 75.0, 25.0]),
        ("basic-multi_x1", [100.0, 50.0, 75.0, 25.0]),
    ],
)
def test_basic_modes_expected_volumes(
    fixture_id: str,
    expected_volumes: list[float],
    manifest_entries: dict[str, object],
) -> None:
    expectations = _build_for_fixture(fixture_id, manifest_entries)

    assert len(expectations) == 4
    assert [exp.aspirate_volume_ul for exp in expectations] == expected_volumes
    assert [exp.dispense_volume_ul for exp in expectations] == expected_volumes


def test_multi_mode_air_gap(manifest_entries: dict[str, object]) -> None:
    expectations = _build_for_fixture("multi-multi", manifest_entries)

    assert len(expectations) == 2
    assert [exp.dest_well for exp in expectations] == ["A1", "B1"]
    assert all(exp.aspirate_volume_ul == 30.0 for exp in expectations)
    assert all(exp.dispense_volume_ul == 60.0 for exp in expectations)


def test_distribution_multi_expansion(manifest_entries: dict[str, object]) -> None:
    expectations = _build_for_fixture("distribution-multi", manifest_entries)

    assert len(expectations) == 17
    dispense_volumes = [exp.dispense_volume_ul for exp in expectations]
    assert 50.0 in dispense_volumes
    assert 100.0 in dispense_volumes
    assert 12.5 in dispense_volumes
    assert 160.0 in dispense_volumes

    grouped_totals: dict[str, set[float]] = {}
    for exp in expectations:
        assert exp.group_id is not None
        assert exp.group_total_volume_ul is not None
        grouped_totals.setdefault(exp.group_id, set()).add(exp.group_total_volume_ul)

    assert len(grouped_totals) == 4
    assert all(len(totals) == 1 for totals in grouped_totals.values())


def test_home_control_rows_skipped(manifest_entries: dict[str, object]) -> None:
    expectations = _build_for_fixture("home-control-single_x1", manifest_entries)

    assert len(expectations) == 6
    assert all(exp.source_labware_id != "HOME" for exp in expectations)
