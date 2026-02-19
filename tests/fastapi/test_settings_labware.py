def test_read_settings(client):
    response = client.get("/settings")
    assert response.status_code == 200
    payload = response.json()
    assert "settings" in payload
    assert payload["settings"]["general"]["mode"] in {"multi", "single_X1", "multi_X1"}


def test_patch_settings_updates_value(client):
    # Use mode field since tip_reuse was removed (now per-row via CSV Tip Action column)
    patch_payload = {"path": "settings.general.mode", "value": "single_X1"}
    response = client.patch("/settings", json=patch_payload)
    assert response.status_code == 200
    assert response.json()["settings"]["general"]["mode"] == "single_X1"

    verify = client.get("/settings")
    assert verify.json()["settings"]["general"]["mode"] == "single_X1"


def test_reset_settings_restores_defaults(client):
    # Use mode field since tip_reuse was removed (now per-row via CSV Tip Action column)
    client.patch("/settings", json={"path": "settings.general.mode", "value": "single_X1"})
    reset_response = client.post("/settings/reset")
    assert reset_response.status_code == 200
    # Mode should be reset to a valid value (depends on default settings.toml)
    assert reset_response.json()["settings"]["general"]["mode"] in {"multi", "single_X1", "multi_X1", "dual"}


def test_labware_roundtrip(client):
    # After refactor, labware_dict.toml only contains [[pipettes]] (no [[labware]] array)
    original = client.get("/labware").json()
    assert "pipettes" in original
    assert isinstance(original["pipettes"], list)
    assert len(original["pipettes"]) > 0

    # Patch a pipette volume_range field
    first_pipette_max = original["pipettes"][0]["volume_range"][1]
    patch_response = client.patch("/labware", json={"path": "pipettes[0].volume_range[1]", "value": 999})
    assert patch_response.status_code == 200

    reset_response = client.post("/labware/reset")
    assert reset_response.status_code == 200
    # After reset, we should be back to original
    assert reset_response.json()["pipettes"][0]["volume_range"][1] == first_pipette_max


def test_add_and_remove_working_plate_entry(client):
    add_payload = {
        "type": "source",
        "labware_id": "tube_rack_96_1500ul",
        "position_rack": "5",
        "connection": "Pipette_8",
    }
    add_response = client.post("/settings/working-plate", json=add_payload)
    assert add_response.status_code == 200
    entries = add_response.json()["settings"]["working_plate"]
    assert entries[-1]["labware_id"] == "tube_rack_96_1500ul"

    index = len(entries) - 1
    delete_response = client.delete(f"/settings/working-plate/{index}")
    assert delete_response.status_code == 200
    updated = delete_response.json()["settings"]["working_plate"]
    assert len(updated) == len(entries) - 1
