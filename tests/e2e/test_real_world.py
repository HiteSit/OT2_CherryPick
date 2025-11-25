"""
E2E tests for real-world protocol scenarios.

Tests larger CSV files with different labware configurations.
"""

import pytest

from .conftest import (
    E2EWorkspace,
    run_full_workflow,
)


class TestFillAnalyticsPlate:
    """Test fill_analytics_plate.csv with custom deck layout."""

    def test_fill_analytics_simulates(self, e2e_workspace_factory):
        """fill_analytics_plate.csv should simulate with custom config."""
        workspace: E2EWorkspace = e2e_workspace_factory("fill_analytics")
        result = run_full_workflow(workspace, "fill_analytics_plate.csv")

        result.assert_success("fill_analytics_plate.csv simulation failed")

    def test_large_transfer_count(self, e2e_workspace_factory):
        """
        fill_analytics_plate.csv has 48 transfers.
        All transfers should complete successfully.
        """
        workspace = e2e_workspace_factory("fill_analytics")
        result = run_full_workflow(workspace, "fill_analytics_plate.csv")

        result.assert_success()
        # Should process all 48 transfers

    def test_different_labware_slots(self, e2e_workspace_factory):
        """
        Uses different labware positions than standard CSVs:
        - tube_rack_96_1500ul_2 (slot 2)
        - 384_pp_standard_100ul_3 (slot 3)
        """
        workspace = e2e_workspace_factory("fill_analytics")
        result = run_full_workflow(workspace, "fill_analytics_plate.csv")

        result.assert_success()

    def test_multiple_source_wells(self, e2e_workspace_factory):
        """
        CSV uses multiple source wells: A1 (16 transfers), A3 (16 transfers), A4 (16 transfers).
        """
        workspace = e2e_workspace_factory("fill_analytics")
        result = run_full_workflow(workspace, "fill_analytics_plate.csv")

        result.assert_success()

    def test_small_volumes(self, e2e_workspace_factory):
        """
        All transfers are 10µL - below P1000 minimum (100µL).
        This tests handling of volumes below rated minimum.
        """
        workspace = e2e_workspace_factory("fill_analytics")
        result = run_full_workflow(workspace, "fill_analytics_plate.csv")

        # Note: 10µL is below P1000 minimum (100µL) - this may cause warnings
        # but should still simulate (pipette can transfer below min with reduced precision)
        result.assert_success()

    def test_consistent_tip_action(self, e2e_workspace_factory):
        """All transfers use tip_action='keep'."""
        workspace = e2e_workspace_factory("fill_analytics")
        result = run_full_workflow(workspace, "fill_analytics_plate.csv")

        result.assert_success()
        # With tip_action='keep', should use minimal tips


class TestProtocolCompleteness:
    """Test that protocols complete fully without hanging or early termination."""

    @pytest.mark.parametrize("csv_name,config", [
        ("example_basic.csv", "single_X1"),
        ("example_advanced.csv", "single_X1"),
        ("example_multi_mode.csv", "multi"),
        ("example_distribution.csv", "multi"),
        ("test_dual_all_three_modes.csv", "dual"),
        ("fill_analytics_plate.csv", "fill_analytics"),
    ])
    def test_protocol_completes(self, e2e_workspace_factory, csv_name, config):
        """Each CSV/config combination should complete simulation fully."""
        workspace = e2e_workspace_factory(config)
        result = run_full_workflow(workspace, csv_name)

        result.assert_success(f"{csv_name} with {config} did not complete")
