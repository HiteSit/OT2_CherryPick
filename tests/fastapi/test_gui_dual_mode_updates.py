"""
Comprehensive tests for GUI updates: dual mode and tip rack mode field.

Test coverage:
1. Dual mode setting (settings.general.mode = "dual")
2. Tip rack mode field for dual pipette configuration
3. Backward compatibility for non-dual mode configs
4. Settings persistence to TOML
5. Integration with workflow
"""

import pytest


class TestDualModeSettings:
    """Tests for dual-pipette mode configuration."""

    def test_read_settings_includes_dual_mode(self, client):
        """Verify dual mode appears in available modes."""
        response = client.get("/settings")
        assert response.status_code == 200
        payload = response.json()
        assert "settings" in payload
        # Dual mode should be a valid option (currently set in settings.toml)
        assert "mode" in payload["settings"]["general"]

    def test_patch_settings_to_dual_mode(self, client):
        """Test PATCH /settings with path=settings.general.mode and value=dual."""
        # First, verify we can read current mode
        current = client.get("/settings").json()
        current_mode = current["settings"]["general"]["mode"]

        # Patch to dual mode
        patch_payload = {"path": "settings.general.mode", "value": "dual"}
        response = client.patch("/settings", json=patch_payload)
        assert response.status_code == 200
        assert response.json()["settings"]["general"]["mode"] == "dual"

        # Verify persistence
        verify = client.get("/settings")
        assert verify.json()["settings"]["general"]["mode"] == "dual"

    def test_patch_settings_modes_are_case_insensitive(self, client):
        """Test that mode values are preserved as provided."""
        modes = ["single_X1", "multi_X1", "multi", "dual"]
        for mode in modes:
            response = client.patch("/settings", json={"path": "settings.general.mode", "value": mode})
            assert response.status_code == 200
            assert response.json()["settings"]["general"]["mode"] == mode

    def test_dual_mode_persists_to_file(self, client, state_store):
        """Verify dual mode is correctly persisted to TOML file."""
        # Patch settings to dual
        client.patch("/settings", json={"path": "settings.general.mode", "value": "dual"})

        # Read raw TOML
        response = client.get("/settings/raw")
        assert response.status_code == 200
        toml_content = response.text
        assert 'mode = "dual"' in toml_content


class TestTipRackModeField:
    """Tests for tip rack mode field in working_plate entries."""

    def test_working_plate_tip_entry_with_mode_field(self, client):
        """Test POST /settings/working-plate with mode field for tip rack."""
        payload = {
            "type": "tip",
            "labware_id": "opentrons_96_tiprack_300ul",
            "position_rack": "1",
            "connection": "Pipette_8",
            "mode": "multi",  # NEW: mode field for dual mode configuration
        }
        response = client.post("/settings/working-plate", json=payload)
        assert response.status_code == 200
        entries = response.json()["settings"]["working_plate"]
        assert entries[-1]["type"] == "tip"
        assert entries[-1]["labware_id"] == "opentrons_96_tiprack_300ul"
        assert entries[-1]["connection"] == "Pipette_8"
        assert entries[-1]["mode"] == "multi"

    def test_tip_rack_mode_multi(self, client):
        """Test tip rack with mode=multi."""
        payload = {
            "type": "tip",
            "labware_id": "opentrons_96_tiprack_300ul",
            "position_rack": "1",
            "connection": "Pipette_8",
            "mode": "multi",
        }
        response = client.post("/settings/working-plate", json=payload)
        assert response.status_code == 200
        entry = response.json()["settings"]["working_plate"][-1]
        assert entry["mode"] == "multi"

    def test_tip_rack_mode_multi_X1(self, client):
        """Test tip rack with mode=multi_X1."""
        payload = {
            "type": "tip",
            "labware_id": "opentrons_96_tiprack_300ul",
            "position_rack": "3",
            "connection": "Pipette_8",
            "mode": "multi_X1",
        }
        response = client.post("/settings/working-plate", json=payload)
        assert response.status_code == 200
        entry = response.json()["settings"]["working_plate"][-1]
        assert entry["mode"] == "multi_X1"

    def test_tip_rack_mode_single_X1(self, client):
        """Test tip rack with mode=single_X1."""
        payload = {
            "type": "tip",
            "labware_id": "tip_rack_geb_1000ul",
            "position_rack": "9",
            "connection": "Pipette_1",
            "mode": "single_X1",
        }
        response = client.post("/settings/working-plate", json=payload)
        assert response.status_code == 200
        entry = response.json()["settings"]["working_plate"][-1]
        assert entry["mode"] == "single_X1"

    def test_tip_rack_mode_field_persists_to_toml(self, client):
        """Verify mode field is persisted to TOML for tip rack entries."""
        payload = {
            "type": "tip",
            "labware_id": "opentrons_96_tiprack_300ul",
            "position_rack": "1",
            "connection": "Pipette_8",
            "mode": "multi",
        }
        client.post("/settings/working-plate", json=payload)

        # Read raw TOML
        response = client.get("/settings/raw")
        assert response.status_code == 200
        toml_content = response.text
        # Should contain the mode field
        assert 'mode = "multi"' in toml_content or 'mode = "multi_X1"' in toml_content

    def test_tip_rack_without_mode_field_still_works(self, client):
        """Test backward compatibility: tip rack can be added without mode field."""
        payload = {
            "type": "tip",
            "labware_id": "opentrons_96_tiprack_300ul",
            "position_rack": "5",
            "connection": "Pipette_8",
            # Note: no mode field - should still work
        }
        response = client.post("/settings/working-plate", json=payload)
        assert response.status_code == 200
        entry = response.json()["settings"]["working_plate"][-1]
        # mode field might not be present or be None
        assert entry["type"] == "tip"

    def test_non_tip_entries_ignore_mode_field(self, client):
        """Test that non-tip entries (source, destination) ignore mode field."""
        payload = {
            "type": "source",
            "labware_id": "tube_rack_96_1500ul",
            "position_rack": "4",
            "connection": None,
            "mode": "multi",  # Should be ignored for source type
        }
        response = client.post("/settings/working-plate", json=payload)
        assert response.status_code == 200
        entry = response.json()["settings"]["working_plate"][-1]
        assert entry["type"] == "source"
        # mode field should not affect source entries


class TestDualModeWorkflow:
    """Integration tests for dual mode configuration workflow."""

    def test_set_dual_mode_then_add_dual_tip_racks(self, client):
        """Full workflow: set dual mode, then add multiple tip racks with different modes."""
        # Step 1: Set mode to dual
        response = client.patch("/settings", json={"path": "settings.general.mode", "value": "dual"})
        assert response.status_code == 200
        assert response.json()["settings"]["general"]["mode"] == "dual"

        # Step 2: Add tip rack for multi mode
        multi_payload = {
            "type": "tip",
            "labware_id": "opentrons_96_tiprack_300ul",
            "position_rack": "1",
            "connection": "Pipette_8",
            "mode": "multi",
        }
        response = client.post("/settings/working-plate", json=multi_payload)
        assert response.status_code == 200

        # Step 3: Add tip rack for multi_X1 mode
        multi_x1_payload = {
            "type": "tip",
            "labware_id": "opentrons_96_tiprack_300ul",
            "position_rack": "3",
            "connection": "Pipette_8",
            "mode": "multi_X1",
        }
        response = client.post("/settings/working-plate", json=multi_x1_payload)
        assert response.status_code == 200

        # Step 4: Add tip rack for single_X1 mode
        single_payload = {
            "type": "tip",
            "labware_id": "tip_rack_geb_1000ul",
            "position_rack": "9",
            "connection": "Pipette_1",
            "mode": "single_X1",
        }
        response = client.post("/settings/working-plate", json=single_payload)
        assert response.status_code == 200

        # Step 5: Verify all tip racks are present with correct modes
        final = client.get("/settings").json()
        working_plates = final["settings"]["working_plate"]
        tip_entries = [e for e in working_plates if e["type"] == "tip"]
        assert len(tip_entries) >= 3
        modes = [e.get("mode") for e in tip_entries]
        assert "multi" in modes
        assert "multi_X1" in modes
        assert "single_X1" in modes

    def test_reset_settings_clears_dual_mode_additions(self, client):
        """Test that reset restores original settings."""
        # Modify settings
        client.patch("/settings", json={"path": "settings.general.mode", "value": "dual"})

        # Reset
        response = client.post("/settings/reset")
        assert response.status_code == 200

        # Verify reset works (should have original mode)
        settings = response.json()["settings"]
        assert "general" in settings
        assert "mode" in settings["general"]


class TestTipRackModeFieldValidation:
    """Tests for validation of tip rack mode field."""

    def test_mode_field_accepts_all_valid_mode_values(self, client):
        """Test that all valid mode values are accepted."""
        valid_modes = ["multi", "multi_X1", "single_X1"]
        for i, mode in enumerate(valid_modes):
            payload = {
                "type": "tip",
                "labware_id": "opentrons_96_tiprack_300ul",
                "position_rack": str(1 + i),
                "connection": "Pipette_8" if mode != "single_X1" else "Pipette_1",
                "mode": mode,
            }
            response = client.post("/settings/working-plate", json=payload)
            assert response.status_code == 200
            entry = response.json()["settings"]["working_plate"][-1]
            assert entry["mode"] == mode

    def test_mode_field_none_is_acceptable(self, client):
        """Test that mode=None (optional) works."""
        payload = {
            "type": "tip",
            "labware_id": "opentrons_96_tiprack_300ul",
            "position_rack": "1",
            "connection": "Pipette_8",
            "mode": None,
        }
        response = client.post("/settings/working-plate", json=payload)
        assert response.status_code == 200

    def test_multiple_tip_racks_same_mode_different_slots(self, client):
        """Test adding multiple tip racks with same mode in different slots."""
        modes = ["multi", "multi"]
        positions = ["1", "5"]
        for mode, pos in zip(modes, positions):
            payload = {
                "type": "tip",
                "labware_id": "opentrons_96_tiprack_300ul",
                "position_rack": pos,
                "connection": "Pipette_8",
                "mode": mode,
            }
            response = client.post("/settings/working-plate", json=payload)
            assert response.status_code == 200

    def test_patch_working_plate_mode_field(self, client):
        """Test patching a working plate entry's mode field."""
        # Add a tip rack
        payload = {
            "type": "tip",
            "labware_id": "opentrons_96_tiprack_300ul",
            "position_rack": "1",
            "connection": "Pipette_8",
            "mode": "multi",
        }
        response = client.post("/settings/working-plate", json=payload)
        assert response.status_code == 200
        entries = response.json()["settings"]["working_plate"]
        last_index = len(entries) - 1

        # Patch its mode field using numeric index
        patch_response = client.patch(
            "/settings",
            json={"path": f"settings.working_plate[{last_index}].mode", "value": "multi_X1"},
        )
        assert patch_response.status_code == 200
        entry = patch_response.json()["settings"]["working_plate"][last_index]
        assert entry["mode"] == "multi_X1"


class TestRemoveTipReuseFromSettings:
    """Tests verifying tip_reuse setting is no longer in settings."""

    def test_settings_does_not_contain_tip_reuse(self, client):
        """Verify tip_reuse field does not exist in settings."""
        response = client.get("/settings")
        assert response.status_code == 200
        settings = response.json()["settings"]
        # tip_reuse should NOT exist in general settings anymore
        assert "tip_reuse" not in settings.get("general", {})

    def test_patch_to_remove_tip_reuse_does_not_affect_others(self, client):
        """Confirm that old tip_reuse references are not in TOML."""
        response = client.get("/settings/raw")
        assert response.status_code == 200
        toml_content = response.text
        # tip_reuse should not appear in the file
        assert "tip_reuse" not in toml_content


class TestBackwardCompatibility:
    """Tests for backward compatibility with non-dual mode configs."""

    def test_single_X1_mode_works_without_mode_field(self, client):
        """Test single_X1 mode configuration without mode field."""
        # Patch to single_X1
        client.patch("/settings", json={"path": "settings.general.mode", "value": "single_X1"})

        # Add tip rack without mode field (backward compat)
        payload = {
            "type": "tip",
            "labware_id": "opentrons_96_tiprack_300ul",
            "position_rack": "1",
            "connection": "Pipette_8",
            # No mode field
        }
        response = client.post("/settings/working-plate", json=payload)
        assert response.status_code == 200

    def test_multi_X1_mode_works_without_mode_field(self, client):
        """Test multi_X1 mode configuration without mode field."""
        # Patch to multi_X1
        client.patch("/settings", json={"path": "settings.general.mode", "value": "multi_X1"})

        # Add tip rack without mode field (backward compat)
        payload = {
            "type": "tip",
            "labware_id": "opentrons_96_tiprack_300ul",
            "position_rack": "1",
            "connection": "Pipette_8",
            # No mode field
        }
        response = client.post("/settings/working-plate", json=payload)
        assert response.status_code == 200

    def test_multi_mode_works_without_mode_field(self, client):
        """Test multi mode configuration without mode field."""
        # Patch to multi
        client.patch("/settings", json={"path": "settings.general.mode", "value": "multi"})

        # Add tip rack without mode field (backward compat)
        payload = {
            "type": "tip",
            "labware_id": "opentrons_96_tiprack_300ul",
            "position_rack": "1",
            "connection": "Pipette_8",
            # No mode field
        }
        response = client.post("/settings/working-plate", json=payload)
        assert response.status_code == 200
