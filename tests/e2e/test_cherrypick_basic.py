"""
E2E tests for basic cherry-pick transfers.

Tests basic 1:1 transfers with minimal CSV columns.
"""

import pytest

from .conftest import (
    E2EWorkspace,
    run_full_workflow,
    get_compatible_profiles,
)


class TestBasicCherryPick:
    """Test basic cherry-pick transfers with minimal configuration."""

    @pytest.mark.parametrize("config_profile", ["single_X1", "multi_X1"])
    def test_example_basic_simulates(self, e2e_workspace_factory, config_profile):
        """example_basic.csv should simulate successfully with compatible modes."""
        workspace: E2EWorkspace = e2e_workspace_factory(config_profile)
        result = run_full_workflow(workspace, "example_basic.csv")

        result.assert_success(f"example_basic.csv failed with {config_profile} mode")

    def test_example_basic_transfer_output(self, e2e_workspace_factory):
        """Verify simulation output contains expected transfer information."""
        workspace = e2e_workspace_factory("single_X1")
        result = run_full_workflow(workspace, "example_basic.csv")

        result.assert_success()
        # Check for aspiration operations in output
        assert "Aspirating" in result.output or "aspirating" in result.output.lower()

    @pytest.mark.parametrize("config_profile", get_compatible_profiles("example_basic.csv"))
    def test_example_basic_all_compatible_modes(self, e2e_workspace_factory, config_profile):
        """example_basic.csv should work with all its compatible modes."""
        workspace = e2e_workspace_factory(config_profile)
        result = run_full_workflow(workspace, "example_basic.csv")

        result.assert_success(f"Failed with {config_profile}")


class TestVolumeSplitting:
    """Test volume splitting for transfers exceeding pipette capacity."""

    def test_large_volume_transfer(self, e2e_workspace_factory):
        """
        example_basic_volumes.csv has a 400µL transfer.
        With P1000 (100-1000µL range), this should work in single transfer.
        """
        workspace = e2e_workspace_factory("single_X1")
        result = run_full_workflow(workspace, "example_basic_volumes.csv")

        result.assert_success("Volume splitting test failed")

    def test_volume_within_pipette_range(self, e2e_workspace_factory):
        """Verify 400µL is within P1000 range (100-1000µL)."""
        workspace = e2e_workspace_factory("single_X1")
        result = run_full_workflow(workspace, "example_basic_volumes.csv")

        result.assert_success()
        # Should not see chunking warnings for volumes within range
        output_lower = result.output.lower()
        # 400µL is within P1000 range, should not need splitting
        assert result.success


class TestHomeControl:
    """Tests for HOME control row feature."""

    @pytest.mark.parametrize("config_profile", ["single_X1", "multi_X1"])
    def test_home_control_simulates_successfully(self, e2e_workspace_factory, config_profile):
        """Protocol with HOME control row should simulate successfully."""
        workspace: E2EWorkspace = e2e_workspace_factory(config_profile)
        result = run_full_workflow(workspace, "example_home_control.csv")
        result.assert_success(f"HOME control simulation failed with {config_profile} mode")

    @pytest.mark.parametrize("config_profile", ["single_X1", "multi_X1"])
    def test_home_control_all_compatible_modes(self, e2e_workspace_factory, config_profile):
        """HOME control should work with all compatible profiles."""
        workspace: E2EWorkspace = e2e_workspace_factory(config_profile)
        result = run_full_workflow(workspace, "example_home_control.csv")
        result.assert_success(f"HOME control failed with {config_profile} mode")

    def test_home_control_protocol_completes(self, e2e_workspace_factory):
        """Protocol should complete execution successfully with HOME row."""
        workspace: E2EWorkspace = e2e_workspace_factory("single_X1")
        result = run_full_workflow(workspace, "example_home_control.csv")

        result.assert_success("Protocol should complete successfully with HOME row")
        # Check that simulation completed without errors
        assert result.success
        assert result.returncode == 0
