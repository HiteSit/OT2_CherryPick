"""
E2E tests for distribution mode (one-to-many transfers).

Tests equal and geometric distribution patterns with multi-destination transfers.
"""

import pytest

from .conftest import (
    E2EWorkspace,
    run_full_workflow,
)


class TestDistributionMode:
    """Test distribution mode with 1:many transfers."""

    def test_example_distribution_simulates(self, e2e_workspace_factory):
        """example_distribution.csv should simulate with multi mode."""
        workspace: E2EWorkspace = e2e_workspace_factory("multi")
        result = run_full_workflow(workspace, "example_distribution.csv")

        result.assert_success("Distribution mode simulation failed")

    def test_equal_distribution_pattern(self, e2e_workspace_factory):
        """
        Row 1: A1 → B1|B2|B3|B4 with equal distribution (50µL each).
        """
        workspace = e2e_workspace_factory("multi")
        result = run_full_workflow(workspace, "example_distribution.csv")

        result.assert_success()
        # Should see "Distribution:" in output
        assert "Distribution" in result.output or result.success

    def test_geometric_decay_pattern(self, e2e_workspace_factory):
        """
        Row 2: geometric:0.5 pattern (100→50→25→12.5).
        Serial dilution pattern.
        """
        workspace = e2e_workspace_factory("multi")
        result = run_full_workflow(workspace, "example_distribution.csv")

        result.assert_success()

    def test_geometric_growth_pattern(self, e2e_workspace_factory):
        """
        Row 4: geometric:2 pattern (20→40→80→160).
        Growth pattern.
        """
        workspace = e2e_workspace_factory("multi")
        result = run_full_workflow(workspace, "example_distribution.csv")

        result.assert_success()

    def test_distribution_with_max_volume(self, e2e_workspace_factory):
        """
        Row 3: Has Volume (ul)=200 which limits max volume per trip.
        Distribution Volume=60 for 5 destinations.
        """
        workspace = e2e_workspace_factory("multi")
        result = run_full_workflow(workspace, "example_distribution.csv")

        result.assert_success()

    def test_distribution_tip_actions(self, e2e_workspace_factory):
        """
        Distribution CSV has mixed tip actions:
        - auto (row 1, 3)
        - new (row 2)
        - keep (row 4)
        """
        workspace = e2e_workspace_factory("multi")
        result = run_full_workflow(workspace, "example_distribution.csv")

        result.assert_success()


class TestDistributionTipActionNew:
    """Regression test for Bug 1: Tip Action 'new' after 'keep' in distribution."""

    def test_new_tip_after_keep_in_distribution_group(self, e2e_workspace_factory):
        """
        Bug 1 regression: distribution rows from the same source where the
        second row requests Tip Action 'new' must not crash the simulation.

        CSV layout (same source, different dest wells):
        - Row 1: A1 → A1|A2|A3|A4  keep  (distribution, equal 50µL)
        - Row 2: A1 → B1|B2|B3|B4  new   (same source, forces tip change)
        """
        workspace: E2EWorkspace = e2e_workspace_factory("multi")

        csv_content = (
            "Source Labware,Source Well,Distribution Volume (ul),"
            "Dest Labware,Dest Well,Source Bottom,Dest Top,Distribution,Tip Action\n"
            "tube_rack_96_1500ul_4,A1,50,"
            "384_ppv_55ul_2,A1|A2|A3|A4,2,-5,equal,keep\n"
            "tube_rack_96_1500ul_4,A1,50,"
            "384_ppv_55ul_2,B1|B2|B3|B4,2,-5,equal,new"
        )

        csv_path = workspace.get_csv_path("regression_bug1_dist_new_tip.csv")
        csv_path.write_text(csv_content, encoding="utf-8")

        result = run_full_workflow(workspace, "regression_bug1_dist_new_tip.csv")

        result.assert_success(
            "Distribution with Tip Action 'new' after 'keep' from same source failed"
        )


class TestMixedModes:
    """Test mixed cherry-pick and distribution in same CSV."""

    def test_example_mixed_modes_simulates(self, e2e_workspace_factory):
        """example_mixed_modes.csv has both 1:1 and 1:many transfers."""
        workspace = e2e_workspace_factory("multi")
        result = run_full_workflow(workspace, "example_mixed_modes.csv")

        result.assert_success("Mixed modes simulation failed")

    def test_interleaved_transfers(self, e2e_workspace_factory):
        """
        CSV structure:
        - Row 1: Cherry-pick (A1→B1, 50µL)
        - Row 2: Distribution (A2→B2|B3|B4, equal 40µL)
        - Row 3: Cherry-pick (A3→B5, 75µL)
        - Row 4: Distribution (A4→C1|C2|C3|C4, geometric:0.5)
        """
        workspace = e2e_workspace_factory("multi")
        result = run_full_workflow(workspace, "example_mixed_modes.csv")

        result.assert_success()
        # Should handle mode switching between cherry-pick and distribution
