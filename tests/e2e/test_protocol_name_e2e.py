"""E2E tests for customizable protocol name feature.

Verifies that:
- Protocols with custom protocol_name generate and simulate successfully
- The embedded JSON contains the custom name in general settings
- The metadata protocolName is updated in the generated protocol
- Simulation output contains the protocol name comment
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
        reason="Custom labware path not found. Set OPENTRONS_DIR environment variable.",
    ),
]


def _extract_embedded_json(protocol_path) -> dict:
    """Extract the embedded JSON from a generated protocol file."""
    text = protocol_path.read_text(encoding="utf-8")
    match = re.search(r'json\.loads\("""(.+?)"""\)', text, re.DOTALL)
    assert match, "Could not find embedded JSON in protocol file"
    return json.loads(match.group(1))


def _extract_protocol_name_from_metadata(protocol_path) -> str:
    """Extract protocolName from the metadata dict in a protocol file."""
    text = protocol_path.read_text(encoding="utf-8")
    match = re.search(r"'protocolName'\s*:\s*'([^']*)'", text)
    assert match, "Could not find protocolName in metadata"
    return match.group(1)


class TestProtocolNameGeneration:
    """E2E tests for protocol generation with custom protocol_name."""

    def test_generate_protocol_with_custom_name(self, e2e_workspace_factory):
        """Protocol generation succeeds with custom protocol_name."""
        workspace: E2EWorkspace = e2e_workspace_factory("protocol_name")
        csv_path = workspace.get_csv_path("example_basic.csv")

        success, output = generate_protocol(workspace, csv_path)
        assert success, f"Protocol generation failed:\n{output}"

    def test_custom_name_in_embedded_json(self, e2e_workspace_factory):
        """Embedded JSON contains the custom protocol_name in general settings."""
        workspace: E2EWorkspace = e2e_workspace_factory("protocol_name")
        csv_path = workspace.get_csv_path("example_basic.csv")

        success, _ = generate_protocol(workspace, csv_path)
        assert success

        data = _extract_embedded_json(workspace.protocol_path)
        general = data["settings"]["settings"]["general"]
        assert general["protocol_name"] == "My Custom Protocol"

    def test_custom_name_in_metadata(self, e2e_workspace_factory):
        """Metadata protocolName is updated to the custom name."""
        workspace: E2EWorkspace = e2e_workspace_factory("protocol_name")
        csv_path = workspace.get_csv_path("example_basic.csv")

        success, _ = generate_protocol(workspace, csv_path)
        assert success

        name = _extract_protocol_name_from_metadata(workspace.protocol_path)
        assert name == "My Custom Protocol"


class TestProtocolNameSimulation:
    """E2E tests for simulation with custom protocol_name."""

    def test_simulate_with_custom_name(self, e2e_workspace_factory):
        """Full workflow (generate + simulate) succeeds with custom protocol_name."""
        workspace: E2EWorkspace = e2e_workspace_factory("protocol_name")
        result = run_full_workflow(workspace, "example_basic.csv")

        result.assert_success("Simulation failed with custom protocol name")

    def test_protocol_name_comment_in_simulation(self, e2e_workspace_factory):
        """Simulation output contains the protocol name comment."""
        workspace: E2EWorkspace = e2e_workspace_factory("protocol_name")
        result = run_full_workflow(workspace, "example_basic.csv")

        result.assert_success("Simulation failed with custom protocol name")
        assert "Protocol: My Custom Protocol" in result.output


class TestDefaultNamePreserved:
    """E2E tests verifying backward compatibility with no custom name."""

    def test_generate_protocol_with_default_name(self, e2e_workspace_factory):
        """Single_X1 profile (no protocol_name) generates successfully."""
        workspace: E2EWorkspace = e2e_workspace_factory("single_X1")
        csv_path = workspace.get_csv_path("example_basic.csv")

        success, output = generate_protocol(workspace, csv_path)
        assert success, f"Protocol generation failed:\n{output}"

    def test_default_name_metadata_unchanged(self, e2e_workspace_factory):
        """Without protocol_name, metadata retains the default name."""
        workspace: E2EWorkspace = e2e_workspace_factory("single_X1")
        csv_path = workspace.get_csv_path("example_basic.csv")

        success, _ = generate_protocol(workspace, csv_path)
        assert success

        name = _extract_protocol_name_from_metadata(workspace.protocol_path)
        assert name == "Unified Cherry-Pick & Distribution Protocol (CherryPick_OT2)"

    def test_no_protocol_name_comment_without_setting(self, e2e_workspace_factory):
        """Without protocol_name, no 'Protocol:' comment appears in simulation."""
        workspace: E2EWorkspace = e2e_workspace_factory("single_X1")
        result = run_full_workflow(workspace, "example_basic.csv")

        result.assert_success("Simulation failed without protocol name")
        assert "Protocol: " not in result.output
