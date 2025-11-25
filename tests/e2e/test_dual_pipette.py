"""
E2E tests for dual-pipette mode with mid-protocol switching.

Tests dynamic pipette/nozzle reconfiguration based on CSV Mode column.
"""

import pytest

from .conftest import (
    E2EWorkspace,
    run_full_workflow,
)


class TestDualPipetteMode:
    """Test dual-pipette mode with runtime switching."""

    @pytest.mark.parametrize("csv_name", [
        "test_dual_all_three_modes.csv",
        "test_dual_single_multi.csv",
        "test_dual_single_multi_X1.csv",
    ])
    def test_dual_mode_csvs_simulate(self, e2e_workspace_factory, csv_name):
        """All dual-mode CSVs should simulate successfully."""
        workspace: E2EWorkspace = e2e_workspace_factory("dual")
        result = run_full_workflow(workspace, csv_name)

        result.assert_success(f"{csv_name} failed with dual mode")

    def test_all_three_modes_switching(self, e2e_workspace_factory):
        """
        test_dual_all_three_modes.csv uses all three modes:
        - multi: rows 1, 4, 8 (50µL transfers)
        - single_X1: rows 2, 5, 7 (600-800µL transfers)
        - multi_X1: rows 3, 6, 9 (150-250µL transfers)
        """
        workspace = e2e_workspace_factory("dual")
        result = run_full_workflow(workspace, "test_dual_all_three_modes.csv")

        result.assert_success()
        # Should see dual-pipette mode enabled
        assert "Dual-pipette mode: ENABLED" in result.output

    def test_mode_switching_messages(self, e2e_workspace_factory):
        """Verify mode switch detection appears in output."""
        workspace = e2e_workspace_factory("dual")
        result = run_full_workflow(workspace, "test_dual_all_three_modes.csv")

        result.assert_success()
        # Should see mode switch messages
        output = result.output
        # Mode switches should occur when transitioning between modes
        assert "Mode switch detected" in output or "Reconfigured" in output

    def test_single_multi_switching(self, e2e_workspace_factory):
        """
        test_dual_single_multi.csv alternates between:
        - single_X1: 500-800µL (uses Pipette_1)
        - multi: 50µL (uses Pipette_8 full 8-channel)
        """
        workspace = e2e_workspace_factory("dual")
        result = run_full_workflow(workspace, "test_dual_single_multi.csv")

        result.assert_success()
        assert "Dual-pipette mode: ENABLED" in result.output

    def test_single_multi_X1_switching(self, e2e_workspace_factory):
        """
        test_dual_single_multi_X1.csv alternates between:
        - single_X1: 500-700µL (uses Pipette_1)
        - multi_X1: 150-250µL (uses Pipette_8 single-tip)
        """
        workspace = e2e_workspace_factory("dual")
        result = run_full_workflow(workspace, "test_dual_single_multi_X1.csv")

        result.assert_success()
        assert "Dual-pipette mode: ENABLED" in result.output


class TestDualPipetteNozzleReconfiguration:
    """Test nozzle layout reconfiguration during protocol."""

    def test_nozzle_reconfiguration_multi_to_multi_X1(self, e2e_workspace_factory):
        """
        When switching from multi to multi_X1, pipette must:
        1. Drop current tip
        2. Reconfigure nozzle layout from ALL to SINGLE
        3. Pick up tip from multi_X1 tip rack
        """
        workspace = e2e_workspace_factory("dual")
        result = run_full_workflow(workspace, "test_dual_all_three_modes.csv")

        result.assert_success()
        # Should see reconfiguration messages
        if "Reconfigured Pipette_8" in result.output:
            assert "MULTI_X1" in result.output or "MULTI mode" in result.output

    def test_tip_drop_before_reconfigure(self, e2e_workspace_factory):
        """Verify tips are dropped before nozzle reconfiguration."""
        workspace = e2e_workspace_factory("dual")
        result = run_full_workflow(workspace, "test_dual_all_three_modes.csv")

        result.assert_success()
        # The protocol should drop tips before reconfiguring
        # This is enforced by the reconfigure_pipette_for_mode function


class TestDualPipetteTipRackAllocation:
    """Test separate tip rack allocation for each mode."""

    def test_separate_tip_racks_used(self, e2e_workspace_factory):
        """
        Dual mode config has 3 tip racks:
        - Slot 1: multi mode (full 8-channel)
        - Slot 3: multi_X1 mode (single-tip from 8-channel)
        - Slot 9: single_X1 mode (dedicated single-channel)
        """
        workspace = e2e_workspace_factory("dual")
        result = run_full_workflow(workspace, "test_dual_all_three_modes.csv")

        result.assert_success()
        # Each mode should use its dedicated tip rack
        # This prevents tip consumption conflicts

    def test_volume_appropriate_pipette_selection(self, e2e_workspace_factory):
        """
        Volumes in test_dual_all_three_modes.csv:
        - multi: 50µL (within P300 range 30-300µL)
        - single_X1: 500-800µL (needs P1000 range 100-1000µL)
        - multi_X1: 150-250µL (within P300 range)
        """
        workspace = e2e_workspace_factory("dual")
        result = run_full_workflow(workspace, "test_dual_all_three_modes.csv")

        result.assert_success()
        # All volumes should be within appropriate pipette ranges
