from __future__ import annotations

import json
from pathlib import Path

from tests.unit.simulation_logs.normalize import (
    NormalizedAspirateEvent,
    NormalizedDispenseEvent,
    NormalizedLabwareLoadEvent,
    NormalizedTipDropEvent,
    NormalizedTipPickupEvent,
)
from tests.unit.simulation_logs.parse import parse_fixture, select_adapter
from tests.unit.simulation_logs.adapters import v8_7_0
from tests.support import paths as support_paths
from tests.support.simulation import load_settings_profile

FIXTURE_ROOT = support_paths.simulation_fixtures_root()


def events_of_type(events, event_type):
    return [event for event in events if isinstance(event, event_type)]


def assert_identifiers(events) -> None:
    for event in events:
        assert event.labware_id
        assert event.labware_slot
        assert event.pipette_id


def assert_fixture_has_normalized_events(fixture_id: str) -> None:
    result = parse_fixture(fixture_id)
    metadata = json.loads((FIXTURE_ROOT / fixture_id / "metadata.json").read_text("utf-8"))
    settings_profile = metadata["settings_profile"]
    settings = load_settings_profile(settings_profile)
    expected_loads = len(settings["settings"]["working_plate"])

    loads = events_of_type(result.events, NormalizedLabwareLoadEvent)
    pickups = events_of_type(result.events, NormalizedTipPickupEvent)
    aspirates = events_of_type(result.events, NormalizedAspirateEvent)
    dispenses = events_of_type(result.events, NormalizedDispenseEvent)
    drops = events_of_type(result.events, NormalizedTipDropEvent)

    assert len(loads) == expected_loads
    assert pickups
    assert aspirates
    assert dispenses
    assert drops

    assert_identifiers(loads)
    assert_identifiers(pickups)
    assert_identifiers(aspirates)
    assert_identifiers(dispenses)
    assert_identifiers(drops)


def test_parse_fixture_normalizes_basic_single_x1() -> None:
    assert_fixture_has_normalized_events("basic-single_x1")


def test_parse_fixture_normalizes_distribution_multi() -> None:
    assert_fixture_has_normalized_events("distribution-multi")


def test_select_adapter_uses_v8_7_0() -> None:
    adapter = select_adapter({"simulator_version": "opentrons_simulate 8.7.0"})
    assert adapter is v8_7_0.parse_text


def test_unknown_simulator_version_returns_warning(tmp_path: Path) -> None:
    fixture_dir = tmp_path / "unknown-version"
    fixture_dir.mkdir()
    (fixture_dir / "stdout.txt").write_text("", encoding="utf-8")
    (fixture_dir / "stderr.txt").write_text("", encoding="utf-8")
    (fixture_dir / "metadata.json").write_text(
        json.dumps(
            {
                "fixture_id": "unknown-version",
                "settings_profile": "single_X1",
                "simulator_version": "opentrons_simulate 99.0.0",
            }
        ),
        encoding="utf-8",
    )

    from tests.unit.simulation_logs import parse as parse_module

    # Save original value and restore after test
    original_fixture_root = parse_module.FIXTURE_ROOT
    try:
        parse_module.FIXTURE_ROOT = tmp_path
        result = parse_module.parse_fixture("unknown-version")

        assert result.warnings
        assert not result.events
    finally:
        parse_module.FIXTURE_ROOT = original_fixture_root
