def test_generate_protocol_with_example_csv(client):
    response = client.post("/workflow/generate", json={"csv": "example_basic.csv", "run_simulation": False})
    assert response.status_code == 200
    data = response.json()

    generated = data["generated"]
    assert generated["message"] == "Protocol generated successfully"
    assert generated["protocol_file"].endswith("CherryPick_OT2.py")
    assert data["simulation"] is None


def test_generate_protocol_after_settings_patch(client):
    patch_payload = {
        "path": "settings.liquid_handling.pre_aspirate_contact.enabled",
        "value": True,
    }
    response = client.patch("/settings", json=patch_payload)
    assert response.status_code == 200
    patched = response.json()
    block = patched["settings"]["liquid_handling"]["pre_aspirate_contact"]
    assert block["enabled"] is True

    response = client.patch(
        "/settings",
        json={
            "path": "settings.liquid_handling.pre_aspirate_contact.aspirate_volume",
            "value": 30,
        },
    )
    assert response.status_code == 200
    block = response.json()["settings"]["liquid_handling"]["pre_aspirate_contact"]
    assert block["aspirate_volume"] == 30

    response = client.post("/workflow/generate", json={"csv": "example_basic.csv"})
    assert response.status_code == 200
    assert response.json()["generated"]["message"] == "Protocol generated successfully"


def test_send_to_opentrons_requires_target_path(client):
    response = client.post("/workflow/generate", json={"csv": "example_basic.csv", "send_to_opentrons": True})
    assert response.status_code == 422


def test_generate_and_deploy_protocol(client, tmp_path):
    target_dir = tmp_path / "opentrons"
    target_dir.mkdir()

    response = client.post(
        "/workflow/generate",
        json={
            "csv": "example_basic.csv",
            "send_to_opentrons": True,
            "target_path": str(target_dir),
            "copy_to_clipboard": False,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["deployment"] is not None
    assert data["deployment"]["copies"]
