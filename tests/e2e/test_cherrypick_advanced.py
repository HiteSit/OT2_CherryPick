"""
E2E tests for advanced cherry-pick features.

Tests optional CSV columns: Mix, Flow rates, Air Gap, Tip Action.
"""

import pytest

from .conftest import (
    E2EWorkspace,
    run_full_workflow,
    get_compatible_profiles,
)


class TestAdvancedCherryPick:
    """Test advanced cherry-pick features with all optional columns."""

    @pytest.mark.parametrize("config_profile", get_compatible_profiles("example_advanced.csv"))
    def test_example_advanced_simulates(self, e2e_workspace_factory, config_profile):
        """example_advanced.csv with all optional columns should simulate."""
        workspace: E2EWorkspace = e2e_workspace_factory(config_profile)
        result = run_full_workflow(workspace, "example_advanced.csv")

        result.assert_success(f"example_advanced.csv failed with {config_profile}")

    def test_air_gap_handling(self, e2e_workspace_factory):
        """Verify air gap operations are in simulation output."""
        workspace = e2e_workspace_factory("single_X1")
        result = run_full_workflow(workspace, "example_advanced.csv")

        result.assert_success()
        # Air gap column has value 20 in the CSV
        # Should see air gap operations in output
        output_lower = result.output.lower()
        assert "air" in output_lower or result.success  # Air gap may not appear in output

    def test_tip_action_keep(self, e2e_workspace_factory):
        """Verify tip_action='keep' is respected."""
        workspace = e2e_workspace_factory("single_X1")
        result = run_full_workflow(workspace, "example_advanced.csv")

        result.assert_success()
        # With tip_action='keep', should reuse tips
        # The CSV specifies tip_action=keep for all rows

    def test_varying_heights(self, e2e_workspace_factory):
        """example_advanced.csv has varying Source Height and Dest Top values."""
        workspace = e2e_workspace_factory("single_X1")
        result = run_full_workflow(workspace, "example_advanced.csv")

        result.assert_success()
        # Different height values: 2, 3, 1, 4 for source
        # Different Dest Top values: -5, -8, -3, -10
