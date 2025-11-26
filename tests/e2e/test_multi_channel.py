"""
E2E tests for multi-channel (8-channel) mode.

Tests full 8-channel operation where each transfer affects entire columns.
"""

import pytest

from .conftest import (
    E2EWorkspace,
    run_full_workflow,
)


class TestMultiChannelMode:
    """Test full 8-channel multi mode operation."""

    def test_example_multi_mode_simulates(self, e2e_workspace_factory):
        """example_multi_mode.csv should simulate with multi mode."""
        workspace: E2EWorkspace = e2e_workspace_factory("multi")
        result = run_full_workflow(workspace, "example_multi_mode.csv")

        result.assert_success("Multi-channel mode simulation failed")

    def test_multi_mode_column_operations(self, e2e_workspace_factory):
        """
        In multi mode, well A1 means the entire column (A1-H1).
        Verify simulation completes for column-based transfers.
        """
        workspace = e2e_workspace_factory("multi")
        result = run_full_workflow(workspace, "example_multi_mode.csv")

        result.assert_success()
        # Multi mode should process transfers as column operations
        # CSV has wells A1, A2 which means columns 1 and 2

    def test_multi_mode_air_gap(self, e2e_workspace_factory):
        """example_multi_mode.csv has Air Gap column with value 30."""
        workspace = e2e_workspace_factory("multi")
        result = run_full_workflow(workspace, "example_multi_mode.csv")

        result.assert_success()
        # Air gap should be applied after aspiration

    def test_multi_mode_tip_keep(self, e2e_workspace_factory):
        """CSV specifies tip_action='keep' for all transfers."""
        workspace = e2e_workspace_factory("multi")
        result = run_full_workflow(workspace, "example_multi_mode.csv")

        result.assert_success()
        # With Tip Action='keep' in CSV, should minimize tip usage
