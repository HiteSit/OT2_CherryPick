"""E2E tests for liquid handling preset resolution.

Verifies that:
- Protocols with active_preset generate and simulate successfully
- The embedded JSON contains preset definitions and active_preset key
- Simulation output contains the preset application comment
"""

from __future__ import annotations

import json
import re

import pytest

from tests.support.workspace import (
    E2EWorkspace,
    generate_protocol,
    run_full_workflow,
    CUSTOM_LABWARE_PATH,
)

# Skip entire module if custom labware is not available
pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(
        CUSTOM_LABWARE_PATH is None,
        reason="Custom labware path not found. Set LABWARE_PATH environment variable.",
    ),
]


def _extract_embedded_json(protocol_path) -> dict:
    """Extract the embedded JSON from a generated protocol file."""
    text = protocol_path.read_text(encoding="utf-8")
    # The JSON is in: json.loads("""...""")
    match = re.search(r'json\.loads\("""(.+?)"""\)', text, re.DOTALL)
    assert match, "Could not find embedded JSON in protocol file"
    return json.loads(match.group(1))


class TestPresetViscous:
    """E2E tests for viscous preset activation."""

    def test_viscous_preset_generates_successfully(self, e2e_workspace_factory):
        """Protocol generation succeeds with active_preset='viscous'."""
        workspace: E2EWorkspace = e2e_workspace_factory("preset_viscous")
        csv_path = workspace.get_csv_path("example_basic.csv")

        success, output = generate_protocol(workspace, csv_path)
        assert success, f"Protocol generation failed:\n{output}"

    def test_viscous_preset_embedded_json_has_preset_data(self, e2e_workspace_factory):
        """Embedded JSON contains active_preset and preset definitions."""
        workspace: E2EWorkspace = e2e_workspace_factory("preset_viscous")
        csv_path = workspace.get_csv_path("example_basic.csv")

        success, _ = generate_protocol(workspace, csv_path)
        assert success

        data = _extract_embedded_json(workspace.protocol_path)
        lh = data["settings"]["settings"]["liquid_handling"]

        assert lh["active_preset"] == "viscous"
        assert "presets" in lh
        assert "viscous" in lh["presets"]
        assert "standard" in lh["presets"]

        # Verify viscous preset values are embedded correctly
        viscous = lh["presets"]["viscous"]
        assert viscous["delays"]["post_aspirate"] == 2.0
        assert viscous["push_out"]["enabled"] is True
        assert viscous["push_out"]["volume_ul"] == 5

    def test_viscous_preset_simulates_successfully(self, e2e_workspace_factory):
        """Full workflow (generate + simulate) succeeds with viscous preset."""
        workspace: E2EWorkspace = e2e_workspace_factory("preset_viscous")
        result = run_full_workflow(workspace, "example_basic.csv")

        result.assert_success("Simulation failed with viscous preset active")

    def test_viscous_preset_comment_in_simulation(self, e2e_workspace_factory):
        """Simulation output contains the preset application comment."""
        workspace: E2EWorkspace = e2e_workspace_factory("preset_viscous")
        result = run_full_workflow(workspace, "example_basic.csv")

        result.assert_success("Simulation failed with viscous preset")
        assert "Applying liquid handling preset: viscous" in result.output


class TestPresetStandard:
    """E2E tests for standard preset activation."""

    def test_standard_preset_simulates_successfully(self, e2e_workspace_factory):
        """Full workflow succeeds with standard preset."""
        workspace: E2EWorkspace = e2e_workspace_factory("preset_standard")
        result = run_full_workflow(workspace, "example_basic.csv")

        result.assert_success("Simulation failed with standard preset active")

    def test_standard_preset_embedded_json_correct(self, e2e_workspace_factory):
        """Embedded JSON has standard preset values."""
        workspace: E2EWorkspace = e2e_workspace_factory("preset_standard")
        csv_path = workspace.get_csv_path("example_basic.csv")

        success, _ = generate_protocol(workspace, csv_path)
        assert success

        data = _extract_embedded_json(workspace.protocol_path)
        lh = data["settings"]["settings"]["liquid_handling"]

        assert lh["active_preset"] == "standard"

        standard = lh["presets"]["standard"]
        assert standard["push_out"]["enabled"] is False
        assert standard["delays"]["post_aspirate"] == 0
        assert standard["pre_aspirate_contact"]["enabled"] is True

    def test_standard_preset_comment_in_simulation(self, e2e_workspace_factory):
        """Simulation output contains the standard preset comment."""
        workspace: E2EWorkspace = e2e_workspace_factory("preset_standard")
        result = run_full_workflow(workspace, "example_basic.csv")

        result.assert_success("Simulation failed with standard preset")
        assert "Applying liquid handling preset: standard" in result.output


class TestNoPreset:
    """E2E tests verifying backward compatibility with no preset."""

    def test_no_preset_simulates_successfully(self, e2e_workspace_factory):
        """Single_X1 profile (no preset) still works fine."""
        workspace: E2EWorkspace = e2e_workspace_factory("single_X1")
        result = run_full_workflow(workspace, "example_basic.csv")

        result.assert_success("Simulation failed without preset (backward compat)")

    def test_no_preset_no_preset_comment(self, e2e_workspace_factory):
        """Without active_preset, no preset comment appears in simulation."""
        workspace: E2EWorkspace = e2e_workspace_factory("single_X1")
        result = run_full_workflow(workspace, "example_basic.csv")

        result.assert_success("Simulation failed without preset")
        assert "Applying liquid handling preset" not in result.output
