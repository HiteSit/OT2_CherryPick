def test_read_settings(client):
    response = client.get("/settings")
    assert response.status_code == 200
    payload = response.json()
    assert "settings" in payload
    assert payload["settings"]["general"]["mode"] in {"multi", "single_X1", "multi_X1"}


def test_patch_settings_updates_value(client):
    patch_payload = {"path": "settings.general.tip_reuse", "value": "never"}
    response = client.patch("/settings", json=patch_payload)
    assert response.status_code == 200
    assert response.json()["settings"]["general"]["tip_reuse"] == "never"

    verify = client.get("/settings")
    assert verify.json()["settings"]["general"]["tip_reuse"] == "never"


def test_reset_settings_restores_defaults(client):
    client.patch("/settings", json={"path": "settings.general.tip_reuse", "value": "never"})
    reset_response = client.post("/settings/reset")
    assert reset_response.status_code == 200
    assert reset_response.json()["settings"]["general"]["tip_reuse"] == "always"


def test_labware_roundtrip(client):
    original = client.get("/labware").json()
    assert "labware" in original
    patch_response = client.patch("/labware", json={"path": "labware[0].well_volume", "value": 200})
    assert patch_response.status_code == 200
    assert patch_response.json()["labware"][0]["well_volume"] == 200

    reset_response = client.post("/labware/reset")
    assert reset_response.status_code == 200
    assert reset_response.json()["labware"][0]["well_volume"] == original["labware"][0]["well_volume"]


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
