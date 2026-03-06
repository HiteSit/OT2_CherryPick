def test_generate_protocol_with_example_csv(client):
    response = client.post("/workflow/generate", json={"csv": "example_basic.csv", "run_simulation": False})
    assert response.status_code == 200
    data = response.json()

    generated = data["generated"]
    assert generated["message"] == "Protocol generated successfully"
    assert generated["protocol_file"].endswith("CherryPick_OT2.py")
    assert data["simulation"] is None
    assert data["logs"]
    assert any("Step 1" in line for line in data["logs"])


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
    assert response.json()["logs"]


def test_send_to_opentrons_without_target_path_uses_shell_settings(client):
    # target_path is now optional - falls back to shell_settings.opentrons_dir_win
    # The request should succeed (validation no longer requires target_path)
    response = client.post("/workflow/generate", json={"csv": "example_basic.csv", "send_to_opentrons": True})
    # Request is accepted (200), but deployment may fail if shell_settings path is invalid
    # The key point is that we no longer get a 422 validation error
    assert response.status_code == 200


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
    assert any("Deployment" in line for line in data["logs"])


def test_simulation_failure_returns_output(client, monkeypatch):
    from gui.backend import state as backend_state
    from ot2_cherrypick_mcp.utils.errors import SimulationError

    def fake_simulate(_protocol_path: str, **_: object):
        raise SimulationError("sim failure")

    monkeypatch.setattr(backend_state, "simulate_protocol", fake_simulate)
    monkeypatch.setattr(
        backend_state.FileStateStore,
        "_read_simulation_log",
        lambda self: {"stdout": "stdout log", "stderr": "stderr log", "returncode": 99},
    )

    response = client.post(
        "/workflow/generate",
        json={"csv": "example_basic.csv", "run_simulation": True, "use_shell_runner": False},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["simulation"]["success"] is False
    assert data["simulation"]["error"]
    assert "Simulation failed" in "\n".join(data["logs"])


def test_shell_runner_path(client, monkeypatch):
    from gui.backend.state import FileStateStore

    def fake_shell(self, csv_path, send_flag):  # noqa: ANN001
        assert str(csv_path).endswith("example_basic.csv")
        return (
            {"success": True, "stdout": "shell ok", "stderr": "", "returncode": 0},
            ["shell log"],
        )

    monkeypatch.setattr(FileStateStore, "run_shell_script", fake_shell)

    response = client.post(
        "/workflow/generate",
        json={"csv": "example_basic.csv", "use_shell_runner": True, "run_simulation": True},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["simulation"]["success"] is True
    assert any("shell log" in line for line in data["logs"])
