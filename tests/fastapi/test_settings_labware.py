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
