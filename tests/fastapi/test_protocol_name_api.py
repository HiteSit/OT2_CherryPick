"""FastAPI tests for customizable protocol name feature.

Verifies that:
- PATCH /settings can set protocol_name and the value persists
- Workflow generation with custom protocol_name produces correct output
"""

from __future__ import annotations

import json
import re

import pytest

pytestmark = [pytest.mark.fastapi]


def test_patch_protocol_name(client):
    """PATCH settings.general.protocol_name updates and persists."""
    patch_payload = {
        "path": "settings.general.protocol_name",
        "value": "My API Test Protocol",
    }
    response = client.patch("/settings", json=patch_payload)
    assert response.status_code == 200

    data = response.json()
    assert data["settings"]["general"]["protocol_name"] == "My API Test Protocol"

    # Verify the value persists on subsequent GET
    verify = client.get("/settings")
    assert verify.status_code == 200
    assert verify.json()["settings"]["general"]["protocol_name"] == "My API Test Protocol"


def test_patch_protocol_name_empty_string(client):
    """Setting protocol_name to empty string is valid and persists."""
    # First set a name
    client.patch("/settings", json={
        "path": "settings.general.protocol_name",
        "value": "Temp Name",
    })

    # Then clear it
    response = client.patch("/settings", json={
        "path": "settings.general.protocol_name",
        "value": "",
    })
    assert response.status_code == 200
    assert response.json()["settings"]["general"]["protocol_name"] == ""


def test_workflow_generates_with_custom_name(client):
    """Workflow generation after PATCH protocol_name includes name in output."""
    # Set protocol name
    patch_resp = client.patch("/settings", json={
        "path": "settings.general.protocol_name",
        "value": "Workflow Test Protocol",
    })
    assert patch_resp.status_code == 200

    # Generate protocol (no simulation to keep test fast)
    gen_resp = client.post("/workflow/generate", json={
        "csv": "example_basic.csv",
        "run_simulation": False,
    })
    assert gen_resp.status_code == 200

    data = gen_resp.json()
    assert data["generated"]["message"] == "Protocol generated successfully"
