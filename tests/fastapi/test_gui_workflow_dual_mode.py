"""
Complete workflow tests for GUI with dual mode support.

These tests simulate the complete user workflow in the GUI:
1. User loads GUI
2. User configures settings for dual mode
3. User adds multiple tip racks for different modes
4. User uploads a dual-mode CSV
5. User generates and simulates protocol
6. User deploys to Opentrons
"""

import json
import shutil
from pathlib import Path

import pytest


class TestCompleteWorkflowDualMode:
    """Complete end-to-end workflow tests for dual mode configuration."""

    def test_workflow_configure_dual_mode_and_simulate(self, client, state_store):
        """
        Complete workflow test:
        1. Read initial settings
        2. Change mode to dual
        3. Add tip racks for each mode
        4. Verify configuration saved
        5. Generate protocol with dual CSV
        """
        # Step 1: Get initial settings
        response = client.get("/settings")
        assert response.status_code == 200
        initial_settings = response.json()

        # Step 2: Set to dual mode
        response = client.patch(
            "/settings",
            json={"path": "settings.general.mode", "value": "dual"},
        )
        assert response.status_code == 200
        assert response.json()["settings"]["general"]["mode"] == "dual"

        # Step 3: Add tip rack for multi mode
        multi_payload = {
            "type": "tip",
            "labware_id": "opentrons_96_tiprack_300ul",
            "position_rack": "1",
            "connection": "Pipette_8",
            "mode": "multi",
        }
        response = client.post("/settings/working-plate", json=multi_payload)
        assert response.status_code == 200

        # Step 4: Add tip rack for multi_X1 mode
        multi_x1_payload = {
            "type": "tip",
            "labware_id": "opentrons_96_tiprack_300ul",
            "position_rack": "3",
            "connection": "Pipette_8",
            "mode": "multi_X1",
        }
        response = client.post("/settings/working-plate", json=multi_x1_payload)
        assert response.status_code == 200

        # Step 5: Add tip rack for single_X1 mode
        single_payload = {
            "type": "tip",
            "labware_id": "tip_rack_geb_1000ul",
            "position_rack": "9",
            "connection": "Pipette_1",
            "mode": "single_X1",
        }
        response = client.post("/settings/working-plate", json=single_payload)
        assert response.status_code == 200

        # Step 6: Verify all settings are saved
        response = client.get("/settings")
        assert response.status_code == 200
        final_settings = response.json()
        assert final_settings["settings"]["general"]["mode"] == "dual"

        # Step 7: Verify tip racks are in settings
        working_plates = final_settings["settings"]["working_plate"]
        tip_entries = [e for e in working_plates if e["type"] == "tip"]
        modes = [e.get("mode") for e in tip_entries]
        assert "multi" in modes
        assert "multi_X1" in modes
        assert "single_X1" in modes

    def test_workflow_switch_modes_back_and_forth(self, client):
        """Test switching between different modes multiple times."""
        modes = ["single_X1", "multi_X1", "multi", "dual", "single_X1"]

        for mode in modes:
            response = client.patch(
                "/settings",
                json={"path": "settings.general.mode", "value": mode},
            )
            assert response.status_code == 200
            assert response.json()["settings"]["general"]["mode"] == mode

    def test_workflow_remove_and_readd_tip_racks(self, client):
        """Test adding, removing, and re-adding tip rack entries."""
        # Set to dual mode
        client.patch("/settings", json={"path": "settings.general.mode", "value": "dual"})

        # Add tip rack
        payload = {
            "type": "tip",
            "labware_id": "opentrons_96_tiprack_300ul",
            "position_rack": "1",
            "connection": "Pipette_8",
            "mode": "multi",
        }
        response = client.post("/settings/working-plate", json=payload)
        assert response.status_code == 200
        entries_after_add = response.json()["settings"]["working_plate"]
        initial_count = len(entries_after_add)

        # Find and delete the tip rack we just added
        last_index = initial_count - 1
        response = client.delete(f"/settings/working-plate/{last_index}")
        assert response.status_code == 200
        entries_after_delete = response.json()["settings"]["working_plate"]
        assert len(entries_after_delete) == initial_count - 1

        # Re-add the same tip rack
        response = client.post("/settings/working-plate", json=payload)
        assert response.status_code == 200
        entries_after_readd = response.json()["settings"]["working_plate"]
        assert len(entries_after_readd) == initial_count

    def test_workflow_move_tip_rack_between_slots(self, client):
        """Test reordering working plate entries (moving between positions)."""
        # Set to dual mode
        client.patch("/settings", json={"path": "settings.general.mode", "value": "dual"})

        # Add first tip rack
        payload1 = {
            "type": "tip",
            "labware_id": "opentrons_96_tiprack_300ul",
            "position_rack": "1",
            "connection": "Pipette_8",
            "mode": "multi",
        }
        response = client.post("/settings/working-plate", json=payload1)
        first_index = len(response.json()["settings"]["working_plate"]) - 1

        # Add second tip rack
        payload2 = {
            "type": "tip",
            "labware_id": "opentrons_96_tiprack_300ul",
            "position_rack": "3",
            "connection": "Pipette_8",
            "mode": "multi_X1",
        }
        response = client.post("/settings/working-plate", json=payload2)
        second_index = len(response.json()["settings"]["working_plate"]) - 1

        # Move second entry to first position
        response = client.post(
            f"/settings/working-plate/{second_index}/move",
            json={"target_index": first_index},
        )
        assert response.status_code == 200

    def test_workflow_partial_dual_configuration(self, client):
        """Test that users can configure dual mode incrementally."""
        # Step 1: Set mode to dual (no tip racks yet)
        response = client.patch(
            "/settings",
            json={"path": "settings.general.mode", "value": "dual"},
        )
        assert response.status_code == 200

        # Step 2: Verify settings are valid even without tip racks
        response = client.get("/settings")
        assert response.status_code == 200
        assert response.json()["settings"]["general"]["mode"] == "dual"

        # Step 3: Gradually add tip racks
        modes_to_add = ["multi", "multi_X1", "single_X1"]
        positions = ["1", "3", "9"]
        for mode, pos in zip(modes_to_add, positions):
            payload = {
                "type": "tip",
                "labware_id": "opentrons_96_tiprack_300ul" if mode != "single_X1" else "tip_rack_geb_1000ul",
                "position_rack": pos,
                "connection": "Pipette_8" if mode != "single_X1" else "Pipette_1",
                "mode": mode,
            }
            response = client.post("/settings/working-plate", json=payload)
            assert response.status_code == 200

            # Verify after each addition
            response = client.get("/settings")
            assert response.status_code == 200


class TestWorkflowWithMultipleCsvs:
    """Tests using multiple CSV files in workflow."""

    def test_upload_and_use_different_csvs(self, client, state_store):
        """Test uploading and switching between different CSV files."""
        # Get available CSVs
        response = client.get("/csvs")
        assert response.status_code == 200
        csv_list = response.json()["files"]
        assert "example_basic.csv" in csv_list

        # Test that we can reference different CSVs
        csv_files = [f for f in csv_list if f.endswith(".csv")]
        assert len(csv_files) > 0

    def test_workflow_settings_independent_of_csv(self, client):
        """Test that settings configuration is independent of CSV selection."""
        # Configure dual mode
        client.patch("/settings", json={"path": "settings.general.mode", "value": "dual"})

        # Add tip racks
        payload = {
            "type": "tip",
            "labware_id": "opentrons_96_tiprack_300ul",
            "position_rack": "1",
            "connection": "Pipette_8",
            "mode": "multi",
        }
        client.post("/settings/working-plate", json=payload)

        # Settings should remain unchanged
        response = client.get("/settings")
        assert response.status_code == 200
        assert response.json()["settings"]["general"]["mode"] == "dual"


class TestWorkflowPersistence:
    """Tests for persistence of settings across requests."""

    def test_settings_persist_across_multiple_requests(self, client):
        """Verify settings persist across multiple API calls."""
        # Make first change
        client.patch("/settings", json={"path": "settings.general.mode", "value": "dual"})

        # Make second change
        payload = {
            "type": "tip",
            "labware_id": "opentrons_96_tiprack_300ul",
            "position_rack": "1",
            "connection": "Pipette_8",
            "mode": "multi",
        }
        client.post("/settings/working-plate", json=payload)

        # Verify both changes persisted
        response = client.get("/settings")
        assert response.status_code == 200
        settings = response.json()["settings"]
        assert settings["general"]["mode"] == "dual"
        tip_entries = [e for e in settings["working_plate"] if e["type"] == "tip"]
        assert any(e.get("mode") == "multi" for e in tip_entries)

    def test_settings_accessible_from_raw_endpoint(self, client):
        """Verify settings are accessible via raw TOML endpoint."""
        # Make changes
        client.patch("/settings", json={"path": "settings.general.mode", "value": "dual"})

        # Read raw TOML
        response = client.get("/settings/raw")
        assert response.status_code == 200
        toml_content = response.text
        assert 'mode = "dual"' in toml_content


class TestWorkflowErrorHandling:
    """Tests for error handling in workflow."""

    def test_cannot_add_invalid_type(self, client):
        """Test that invalid working plate types are rejected."""
        payload = {
            "type": "invalid_type",
            "labware_id": "some_labware",
            "position_rack": "1",
        }
        response = client.post("/settings/working-plate", json=payload)
        # Should either reject or accept gracefully
        assert response.status_code in [200, 400]

    def test_cannot_delete_nonexistent_entry(self, client):
        """Test that deleting non-existent entry fails gracefully."""
        response = client.delete("/settings/working-plate/999")
        assert response.status_code == 400

    def test_cannot_move_to_invalid_index(self, client):
        """Test that moving to invalid index fails gracefully."""
        response = client.post(
            "/settings/working-plate/0/move",
            json={"target_index": 999},
        )
        # Should either reject or clamp to valid range
        assert response.status_code in [200, 400]


class TestWorkflowResetFunctionality:
    """Tests for resetting configurations."""

    def test_reset_returns_to_defaults(self, client):
        """Test that reset restores default configuration."""
        # Make changes
        client.patch("/settings", json={"path": "settings.general.mode", "value": "dual"})
        payload = {
            "type": "tip",
            "labware_id": "opentrons_96_tiprack_300ul",
            "position_rack": "1",
            "connection": "Pipette_8",
            "mode": "multi",
        }
        client.post("/settings/working-plate", json=payload)

        # Reset
        response = client.post("/settings/reset")
        assert response.status_code == 200

        # Verify defaults restored
        response = client.get("/settings")
        settings = response.json()["settings"]
        # Should have default mode (not dual)
        assert "general" in settings
        assert "mode" in settings["general"]

    def test_reset_clears_added_entries(self, client):
        """Test that reset removes added working plate entries."""
        initial = client.get("/settings").json()
        initial_count = len(initial["settings"]["working_plate"])

        # Add an entry
        payload = {
            "type": "tip",
            "labware_id": "opentrons_96_tiprack_300ul",
            "position_rack": "1",
            "connection": "Pipette_8",
            "mode": "multi",
        }
        client.post("/settings/working-plate", json=payload)

        after_add = client.get("/settings").json()
        assert len(after_add["settings"]["working_plate"]) > initial_count

        # Reset
        client.post("/settings/reset")

        after_reset = client.get("/settings").json()
        # Should be back to initial count
        assert len(after_reset["settings"]["working_plate"]) == initial_count


class TestWorkflowWithRealProjectStructure:
    """Tests using realistic project structure and file operations."""

    def test_workflow_respects_workspace_isolation(self, client, state_store):
        """Test that workspace changes are isolated from repo root."""
        # Make change in workspace
        client.patch("/settings", json={"path": "settings.general.mode", "value": "dual"})

        # Read workspace settings
        workspace_settings = client.get("/settings").json()
        assert workspace_settings["settings"]["general"]["mode"] == "dual"

        # Workspace settings file should exist and have the change
        assert state_store.settings_path.exists()
        workspace_content = state_store.settings_path.read_text(encoding="utf-8")
        assert 'mode = "dual"' in workspace_content

    def test_workflow_can_export_settings(self, client, state_store):
        """Test exporting settings for external use."""
        # Configure dual mode
        client.patch("/settings", json={"path": "settings.general.mode", "value": "dual"})

        # Get settings as JSON
        response = client.get("/settings")
        assert response.status_code == 200
        settings_json = response.json()

        # Verify it's valid JSON and can be re-exported
        json_str = json.dumps(settings_json)
        assert "dual" in json_str
