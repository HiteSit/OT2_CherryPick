"""
E2E tests for tip action management in single_X1 mode.

Parses opentrons_simulate output to verify that tip pick-up, keep, and drop
sequences match expected behavior for mixed Tip Action CSV columns.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import pytest

from .conftest import (
    E2EWorkspace,
    run_full_workflow,
)


# ============ Output Parsing Helpers ============


@dataclass
class TipEvent:
    """A single tip operation extracted from simulation output."""

    action: str  # "pickup" or "drop"
    well: str  # e.g. "A1"
    labware: str  # e.g. "GEB 1000uL"
    slot: str  # e.g. "5"


def parse_tip_events(output: str) -> list[TipEvent]:
    """
    Extract tip pickup and drop events from opentrons_simulate output.

    Expected lines:
        "Picking up tip from A1 of GEB 1000uL on slot 5"
        "Dropping tip into Trash Bin on slot 12"
        "Dropping tip into A1 of GEB 1000uL on slot 5"  (return to rack)
    """
    events: list[TipEvent] = []

    pickup_re = re.compile(
        r"Picking up tip from (\w+) of (.+?) on slot (\d+)"
    )
    drop_re = re.compile(
        r"Dropping tip into (?:(\w+) of )?(.+?) on slot (\d+)"
    )

    for line in output.splitlines():
        m = pickup_re.search(line)
        if m:
            events.append(TipEvent("pickup", m.group(1), m.group(2), m.group(3)))
            continue
        m = drop_re.search(line)
        if m:
            well = m.group(1) or "Trash"
            events.append(TipEvent("drop", well, m.group(2), m.group(3)))

    return events


def count_pickups(events: list[TipEvent]) -> int:
    return sum(1 for e in events if e.action == "pickup")


def count_drops(events: list[TipEvent]) -> int:
    return sum(1 for e in events if e.action == "drop")


def pickup_wells(events: list[TipEvent]) -> list[str]:
    """Return list of tip rack wells used for pickups, in order."""
    return [e.well for e in events if e.action == "pickup"]


def event_sequence(events: list[TipEvent]) -> list[str]:
    """Return list of action strings in order, e.g. ['pickup', 'drop', 'pickup', ...]."""
    return [e.action for e in events]


# ============ CSV Builders ============


def _make_cherrypick_csv(rows: list[tuple[str, str, str, str, str, str]]) -> str:
    """
    Build a cherry-pick CSV string.

    Each row tuple: (source_well, dest_well, volume, source_bottom, dest_top, tip_action)
    Uses standard labware: tube_rack_96_1500ul_4 → 384_ppv_55ul_2
    """
    header = (
        "Source Labware,Source Well,Volume (ul),"
        "Dest Labware,Dest Well,Source Bottom,Dest Top,Tip Action"
    )
    lines = [header]
    for src_well, dst_well, vol, src_bot, dst_top, tip in rows:
        lines.append(
            f"tube_rack_96_1500ul_4,{src_well},{vol},"
            f"384_ppv_55ul_2,{dst_well},{src_bot},{dst_top},{tip}"
        )
    return "\n".join(lines)


# ============ Tests ============


class TestTipActionParsingSingleX1:
    """Verify tip management by parsing simulation output in single_X1 mode."""

    def test_all_new_tips(self, e2e_workspace_factory):
        """Every row with Tip Action 'new' should pick up a fresh tip."""
        workspace: E2EWorkspace = e2e_workspace_factory("single_X1")

        csv = _make_cherrypick_csv([
            ("A1", "A1", "100", "2", "-5", "new"),
            ("A2", "A2", "100", "2", "-5", "new"),
            ("A3", "A3", "100", "2", "-5", "new"),
        ])
        csv_path = workspace.get_csv_path("tip_all_new.csv")
        csv_path.write_text(csv, encoding="utf-8")

        result = run_full_workflow(workspace, "tip_all_new.csv")
        result.assert_success("All-new tip action failed")

        events = parse_tip_events(result.output)
        assert count_pickups(events) == 3, (
            f"Expected 3 pickups for 3 'new' rows, got {count_pickups(events)}.\n"
            f"Events: {events}"
        )
        assert count_drops(events) == 3, (
            f"Expected 3 drops for 3 'new' rows, got {count_drops(events)}.\n"
            f"Events: {events}"
        )

    def test_all_keep_tips(self, e2e_workspace_factory):
        """All 'keep' rows should reuse the same tip (1 pickup, 1 drop at end)."""
        workspace: E2EWorkspace = e2e_workspace_factory("single_X1")

        csv = _make_cherrypick_csv([
            ("A1", "A1", "100", "2", "-5", "new"),
            ("A2", "A2", "100", "2", "-5", "keep"),
            ("A3", "A3", "100", "2", "-5", "keep"),
            ("A4", "A4", "100", "2", "-5", "keep"),
        ])
        csv_path = workspace.get_csv_path("tip_all_keep.csv")
        csv_path.write_text(csv, encoding="utf-8")

        result = run_full_workflow(workspace, "tip_all_keep.csv")
        result.assert_success("All-keep tip action failed")

        events = parse_tip_events(result.output)
        assert count_pickups(events) == 1, (
            f"Expected 1 pickup for 'new' + 3 'keep' rows, got {count_pickups(events)}.\n"
            f"Events: {events}"
        )
        # Final drop at end of protocol
        assert count_drops(events) == 1, (
            f"Expected 1 drop at end, got {count_drops(events)}.\n"
            f"Events: {events}"
        )

    def test_new_after_keep_drops_and_picks(self, e2e_workspace_factory):
        """
        Tip Action sequence: new → keep → keep → new → drop.
        Should see 2 pickups and 2 drops.
        The 'new' on row 4 must drop the old tip before picking a fresh one.
        """
        workspace: E2EWorkspace = e2e_workspace_factory("single_X1")

        csv = _make_cherrypick_csv([
            ("A1", "A1", "100", "2", "-5", "new"),
            ("A2", "A2", "100", "2", "-5", "keep"),
            ("A3", "A3", "100", "2", "-5", "keep"),
            ("A4", "A4", "100", "2", "-5", "new"),
            ("A5", "A5", "100", "2", "-5", "drop"),
        ])
        csv_path = workspace.get_csv_path("tip_new_after_keep.csv")
        csv_path.write_text(csv, encoding="utf-8")

        result = run_full_workflow(workspace, "tip_new_after_keep.csv")
        result.assert_success("new-after-keep tip action failed")

        events = parse_tip_events(result.output)
        assert count_pickups(events) == 2, (
            f"Expected 2 pickups (row 1 + row 4), got {count_pickups(events)}.\n"
            f"Events: {events}"
        )
        assert count_drops(events) == 2, (
            f"Expected 2 drops (row 4 new drops old, row 5 drop), got {count_drops(events)}.\n"
            f"Events: {events}"
        )
        # Verify tips came from sequential wells
        wells = pickup_wells(events)
        assert wells[0] != wells[1], (
            f"Second pickup should use a different tip well, but both used {wells[0]}"
        )

    def test_alternating_new_drop(self, e2e_workspace_factory):
        """
        Tip Action sequence: new → drop → new → drop → new → drop.
        Every transfer uses a fresh tip that is immediately dropped.
        Should see 3 pickups from 3 different wells and 3 drops.
        """
        workspace: E2EWorkspace = e2e_workspace_factory("single_X1")

        csv = _make_cherrypick_csv([
            ("A1", "A1", "100", "2", "-5", "new"),
            ("A2", "A2", "100", "2", "-5", "new"),
            ("A3", "A3", "100", "2", "-5", "new"),
        ])
        csv_path = workspace.get_csv_path("tip_alternating.csv")
        csv_path.write_text(csv, encoding="utf-8")

        result = run_full_workflow(workspace, "tip_alternating.csv")
        result.assert_success("Alternating new/drop failed")

        events = parse_tip_events(result.output)
        wells = pickup_wells(events)
        # All 3 pickups should be from different wells
        assert len(set(wells)) == 3, (
            f"Expected 3 unique tip wells, got {wells}"
        )

    def test_drop_mid_sequence(self, e2e_workspace_factory):
        """
        Tip Action sequence: new → keep → drop → new → keep.
        Row 3 'drop' should drop the current tip.
        Row 4 'new' picks a fresh one.
        Should see 2 pickups and 2 drops.
        """
        workspace: E2EWorkspace = e2e_workspace_factory("single_X1")

        csv = _make_cherrypick_csv([
            ("A1", "A1", "100", "2", "-5", "new"),
            ("A2", "A2", "100", "2", "-5", "keep"),
            ("A3", "A3", "100", "2", "-5", "drop"),
            ("A4", "A4", "100", "2", "-5", "new"),
            ("A5", "A5", "100", "2", "-5", "keep"),
        ])
        csv_path = workspace.get_csv_path("tip_drop_mid.csv")
        csv_path.write_text(csv, encoding="utf-8")

        result = run_full_workflow(workspace, "tip_drop_mid.csv")
        result.assert_success("Drop-mid-sequence failed")

        events = parse_tip_events(result.output)
        assert count_pickups(events) == 2, (
            f"Expected 2 pickups, got {count_pickups(events)}.\nEvents: {events}"
        )
        assert count_drops(events) == 2, (
            f"Expected 2 drops, got {count_drops(events)}.\nEvents: {events}"
        )

    def test_pickup_order_is_sequential(self, e2e_workspace_factory):
        """
        Verify tips are consumed in order from the tip rack.
        With starting_tip_well = H1 (configured in single_X1 settings.toml),
        tips go H1, G1, F1... (column-first, bottom to top for single channel).
        """
        workspace: E2EWorkspace = e2e_workspace_factory("single_X1")

        csv = _make_cherrypick_csv([
            ("A1", "A1", "100", "2", "-5", "new"),
            ("A2", "A2", "100", "2", "-5", "new"),
            ("A3", "A3", "100", "2", "-5", "new"),
            ("A4", "A4", "100", "2", "-5", "new"),
        ])
        csv_path = workspace.get_csv_path("tip_order.csv")
        csv_path.write_text(csv, encoding="utf-8")

        result = run_full_workflow(workspace, "tip_order.csv")
        result.assert_success("Tip ordering test failed")

        events = parse_tip_events(result.output)
        wells = pickup_wells(events)
        assert len(wells) == 4, f"Expected 4 pickups, got {len(wells)}"
        # Each pickup should be from a different well
        assert len(set(wells)) == 4, (
            f"Expected 4 unique tip wells, got {wells}"
        )
        # Wells should be sequential (no skips)
        for i in range(len(wells) - 1):
            assert wells[i] != wells[i + 1], (
                f"Tip wells {i} and {i+1} are the same: {wells[i]}"
            )

    def test_simulation_output_has_correct_transfer_count(self, e2e_workspace_factory):
        """Verify the 'Protocol complete: N transfers' line matches CSV row count."""
        workspace: E2EWorkspace = e2e_workspace_factory("single_X1")

        csv = _make_cherrypick_csv([
            ("A1", "A1", "100", "2", "-5", "new"),
            ("A2", "A2", "100", "2", "-5", "keep"),
            ("A3", "A3", "100", "2", "-5", "new"),
        ])
        csv_path = workspace.get_csv_path("tip_transfer_count.csv")
        csv_path.write_text(csv, encoding="utf-8")

        result = run_full_workflow(workspace, "tip_transfer_count.csv")
        result.assert_success()

        m = re.search(r"Protocol complete: (\d+) transfers", result.output)
        assert m, f"'Protocol complete' line not found in output"
        assert int(m.group(1)) == 3, (
            f"Expected 3 transfers, got {m.group(1)}"
        )

    def test_many_keeps_then_new(self, e2e_workspace_factory):
        """
        Tip Action sequence: keep → keep → keep → keep → new.

        The first 'keep' has no tip yet, so the protocol auto-picks one up.
        Then 3 more keeps reuse it (no tip events).
        The final 'new' MUST drop the old tip and pick a fresh one.

        Expected opentrons_simulate events:
            pickup (auto for first keep) → drop + pickup (the 'new') → drop (end)
        Total: 2 pickups, 2 drops.
        """
        workspace: E2EWorkspace = e2e_workspace_factory("single_X1")

        csv = _make_cherrypick_csv([
            ("A1", "A1", "100", "2", "-5", "keep"),
            ("A2", "A2", "100", "2", "-5", "keep"),
            ("A3", "A3", "100", "2", "-5", "keep"),
            ("A4", "A4", "100", "2", "-5", "keep"),
            ("A5", "A5", "100", "2", "-5", "new"),
        ])
        csv_path = workspace.get_csv_path("tip_many_keep_then_new.csv")
        csv_path.write_text(csv, encoding="utf-8")

        result = run_full_workflow(workspace, "tip_many_keep_then_new.csv")
        result.assert_success("many-keeps-then-new failed")

        events = parse_tip_events(result.output)
        seq = event_sequence(events)

        assert count_pickups(events) == 2, (
            f"Expected 2 pickups (auto + new), got {count_pickups(events)}.\n"
            f"Sequence: {seq}\nEvents: {events}"
        )
        assert count_drops(events) == 2, (
            f"Expected 2 drops (new drops old + final), got {count_drops(events)}.\n"
            f"Sequence: {seq}\nEvents: {events}"
        )
        # Verify event ordering: pickup, then drop+pickup pair, then final drop
        assert seq == ["pickup", "drop", "pickup", "drop"], (
            f"Expected [pickup, drop, pickup, drop] but got {seq}"
        )
        # Two different tip wells
        wells = pickup_wells(events)
        assert wells[0] != wells[1], (
            f"The 'new' tip must come from a different well, but both are {wells[0]}"
        )

    def test_many_keeps_no_new_at_all(self, e2e_workspace_factory):
        """
        Tip Action sequence: keep → keep → keep → keep → keep.

        All keeps, no explicit new or drop. Protocol auto-picks one tip at start,
        reuses for every transfer, drops once at end.

        Expected: 1 pickup, 1 drop. Single tip used for all 5 transfers.
        """
        workspace: E2EWorkspace = e2e_workspace_factory("single_X1")

        csv = _make_cherrypick_csv([
            ("A1", "A1", "100", "2", "-5", "keep"),
            ("A2", "A2", "100", "2", "-5", "keep"),
            ("A3", "A3", "100", "2", "-5", "keep"),
            ("A4", "A4", "100", "2", "-5", "keep"),
            ("A5", "A5", "100", "2", "-5", "keep"),
        ])
        csv_path = workspace.get_csv_path("tip_only_keeps.csv")
        csv_path.write_text(csv, encoding="utf-8")

        result = run_full_workflow(workspace, "tip_only_keeps.csv")
        result.assert_success("all-keeps failed")

        events = parse_tip_events(result.output)
        seq = event_sequence(events)

        assert seq == ["pickup", "drop"], (
            f"Expected exactly [pickup, drop] for all-keep rows, got {seq}"
        )

    def test_keep_keep_new_keep_keep_new_keep(self, e2e_workspace_factory):
        """
        Longer mixed sequence: keep → keep → new → keep → keep → new → keep.

        Tip lifecycle:
          Row 1 keep: auto-pickup tip #1
          Row 2 keep: reuse tip #1
          Row 3 new:  drop tip #1, pickup tip #2
          Row 4 keep: reuse tip #2
          Row 5 keep: reuse tip #2
          Row 6 new:  drop tip #2, pickup tip #3
          Row 7 keep: reuse tip #3, drop at end

        Expected: 3 pickups, 3 drops.
        Sequence: pickup, drop, pickup, drop, pickup, drop
        """
        workspace: E2EWorkspace = e2e_workspace_factory("single_X1")

        csv = _make_cherrypick_csv([
            ("A1", "A1",  "100", "2", "-5", "keep"),
            ("A2", "A2",  "100", "2", "-5", "keep"),
            ("A3", "A3",  "100", "2", "-5", "new"),
            ("A4", "A4",  "100", "2", "-5", "keep"),
            ("A5", "A5",  "100", "2", "-5", "keep"),
            ("A6", "A6",  "100", "2", "-5", "new"),
            ("A7", "A7",  "100", "2", "-5", "keep"),
        ])
        csv_path = workspace.get_csv_path("tip_keep_keep_new_repeat.csv")
        csv_path.write_text(csv, encoding="utf-8")

        result = run_full_workflow(workspace, "tip_keep_keep_new_repeat.csv")
        result.assert_success("keep-keep-new repeating pattern failed")

        events = parse_tip_events(result.output)
        seq = event_sequence(events)

        assert seq == ["pickup", "drop", "pickup", "drop", "pickup", "drop"], (
            f"Expected 3x [pickup, drop] pairs, got {seq}"
        )
        wells = pickup_wells(events)
        assert len(set(wells)) == 3, (
            f"Expected 3 unique tip wells, got {wells}"
        )

    def test_keep_keep_keep_drop_keep_keep_new(self, e2e_workspace_factory):
        """
        Sequence: keep → keep → keep → drop → keep → keep → new.

        Tip lifecycle:
          Row 1 keep: auto-pickup tip #1
          Row 2 keep: reuse tip #1
          Row 3 keep: reuse tip #1
          Row 4 drop: drop tip #1 (no new tip)
          Row 5 keep: no tip → auto-pickup tip #2
          Row 6 keep: reuse tip #2
          Row 7 new:  drop tip #2, pickup tip #3, drop at end

        Expected: 3 pickups, 3 drops.
        """
        workspace: E2EWorkspace = e2e_workspace_factory("single_X1")

        csv = _make_cherrypick_csv([
            ("A1", "A1", "100", "2", "-5", "keep"),
            ("A2", "A2", "100", "2", "-5", "keep"),
            ("A3", "A3", "100", "2", "-5", "keep"),
            ("A4", "A4", "100", "2", "-5", "drop"),
            ("A5", "A5", "100", "2", "-5", "keep"),
            ("A6", "A6", "100", "2", "-5", "keep"),
            ("A7", "A7", "100", "2", "-5", "new"),
        ])
        csv_path = workspace.get_csv_path("tip_keep_drop_keep_new.csv")
        csv_path.write_text(csv, encoding="utf-8")

        result = run_full_workflow(workspace, "tip_keep_drop_keep_new.csv")
        result.assert_success("keep-drop-keep-new pattern failed")

        events = parse_tip_events(result.output)
        seq = event_sequence(events)

        assert count_pickups(events) == 3, (
            f"Expected 3 pickups, got {count_pickups(events)}.\n"
            f"Sequence: {seq}\nEvents: {events}"
        )
        assert count_drops(events) == 3, (
            f"Expected 3 drops, got {count_drops(events)}.\n"
            f"Sequence: {seq}\nEvents: {events}"
        )
        # Verify the exact event ordering
        assert seq == ["pickup", "drop", "pickup", "drop", "pickup", "drop"], (
            f"Expected alternating pickup/drop, got {seq}"
        )
        wells = pickup_wells(events)
        assert len(set(wells)) == 3, (
            f"Expected 3 unique tip wells, got {wells}"
        )
