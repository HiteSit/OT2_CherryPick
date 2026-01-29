from __future__ import annotations

from tests.unit.simulation_logs import AspirateEvent, DispenseEvent, TipDropEvent, TipPickupEvent
from tests.unit.simulation_logs.adapters import v8_7_0
from tests.support import paths as support_paths

FIXTURE_ROOT = support_paths.simulation_fixtures_root()


def load_stdout(fixture_name: str) -> str:
    return (FIXTURE_ROOT / fixture_name / "stdout.txt").read_text(encoding="utf-8")


def events_of_type(events, event_type):
    return [event for event in events if isinstance(event, event_type)]


def test_v8_7_0_parses_basic_single_x1_actions() -> None:
    result = v8_7_0.parse_text(load_stdout("basic-single_x1"))

    pickups = events_of_type(result.events, TipPickupEvent)
    aspirates = events_of_type(result.events, AspirateEvent)
    dispenses = events_of_type(result.events, DispenseEvent)
    drops = events_of_type(result.events, TipDropEvent)

    assert pickups
    assert aspirates
    assert dispenses
    assert drops

    assert any(
        pickup.labware_slot == "5" and pickup.well == "A1" for pickup in pickups
    )
    assert any(
        aspirate.labware_slot == "4"
        and aspirate.well == "A1"
        and aspirate.volume_ul == 100.0
        for aspirate in aspirates
    )
    assert any(
        dispense.labware_slot == "2"
        and dispense.well == "B1"
        and dispense.volume_ul == 100.0
        for dispense in dispenses
    )
    assert any(drop.labware_slot == "12" for drop in drops)
    assert result.warnings


def test_v8_7_0_parses_distribution_multi_indented_steps() -> None:
    result = v8_7_0.parse_text(load_stdout("distribution-multi"))

    pickups = events_of_type(result.events, TipPickupEvent)
    aspirates = events_of_type(result.events, AspirateEvent)
    dispenses = events_of_type(result.events, DispenseEvent)
    drops = events_of_type(result.events, TipDropEvent)

    assert pickups
    assert aspirates
    assert dispenses
    assert drops

    assert any(pickup.labware_slot == "1" and pickup.well == "A1" for pickup in pickups)
    assert any(
        aspirate.labware_slot == "4"
        and aspirate.well == "A1"
        and aspirate.volume_ul == 200.0
        for aspirate in aspirates
    )
    assert any(
        dispense.labware_slot == "2"
        and dispense.well == "A2"
        and dispense.volume_ul == 50.0
        for dispense in dispenses
    )
    assert any(drop.labware_slot == "12" for drop in drops)
    assert result.warnings
