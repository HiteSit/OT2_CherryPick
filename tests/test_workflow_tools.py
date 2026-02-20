"""Tests for workflow orchestration tools."""

from __future__ import annotations

from pathlib import Path

import pytest

from ot2_cherrypick_mcp.tools.workflow_tools import run_full_workflow


def _copy_repo_file(source: Path, destination: Path) -> Path:
    destination.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    return destination


def _prepare_inputs(tmp_path: Path):
    repo_root = Path(__file__).resolve().parents[1]
    settings_copy = _copy_repo_file(repo_root / "settings.toml", tmp_path / "settings.toml")
    labware_copy = _copy_repo_file(repo_root / "labware_dict.toml", tmp_path / "labware_dict.toml")
    csv_copy = _copy_repo_file(repo_root / "CSVs" / "example_basic.csv", tmp_path / "example_basic.csv")
    protocol_copy = _copy_repo_file(repo_root / "CherryPick_OT2.py", tmp_path / "CherryPick_OT2.py")
    return settings_copy, labware_copy, csv_copy, protocol_copy


def test_full_workflow_runs_validation_and_generation(monkeypatch, tmp_path: Path) -> None:
    settings_copy, labware_copy, csv_copy, protocol_copy = _prepare_inputs(tmp_path)

    def fake_simulation(**kwargs):
        return {"command": ["opentrons_simulate"], "stdout": "ok", "stderr": "", "returncode": 0}

    monkeypatch.setattr(
        "ot2_cherrypick_mcp.tools.workflow_tools.run_simulation",
        lambda **kwargs: fake_simulation(**kwargs),
    )

    result = run_full_workflow(
        csv_path=str(csv_copy),
        settings_path=str(settings_copy),
        labware_path=str(labware_copy),
        protocol_path=str(protocol_copy),
        labware_env_path=None,
    )

    assert result["status"] == "ok"
    assert result["validation"]["status"] == "ok"
    assert result["generation"]["protocol_file"] == str(protocol_copy)
    assert result["simulation"]["stdout"] == "ok"
    assert result["deployment"] is None


def test_full_workflow_halts_on_validation_error(monkeypatch, tmp_path: Path) -> None:
    settings_copy, labware_copy, csv_copy, protocol_copy = _prepare_inputs(tmp_path)

    csv_copy.write_text("Source Labware,Dest Labware\nfoo,bar\n", encoding="utf-8")

    simulated_called = False

    def fake_simulation(**kwargs):  # pragma: no cover - ensure not called
        nonlocal simulated_called
        simulated_called = True
        return {}

    monkeypatch.setattr(
        "ot2_cherrypick_mcp.tools.workflow_tools.run_simulation",
        lambda **kwargs: fake_simulation(**kwargs),
    )

    result = run_full_workflow(
        csv_path=str(csv_copy),
        settings_path=str(settings_copy),
        labware_path=str(labware_copy),
        protocol_path=str(protocol_copy),
    )

    assert result["status"] == "error"
    assert result["generation"] is None
    assert result["simulation"] is None
    assert result.get("deployment") is None
    assert simulated_called is False


def test_full_workflow_passes_offset_db_path_to_generate(monkeypatch, tmp_path: Path) -> None:
    """run_full_workflow threads offset_db_path through to run_generate_protocol."""
    settings_copy, labware_copy, csv_copy, protocol_copy = _prepare_inputs(tmp_path)

    # Create an offset database file
    offset_db = tmp_path / "offset_database.toml"
    offset_db.write_text("", encoding="utf-8")

    captured = {}

    original_generate = __import__(
        "ot2_cherrypick_mcp.tools.protocol_tools", fromlist=["run_generate_protocol"]
    ).run_generate_protocol

    def capturing_generate(**kwargs):
        captured["offset_db_path"] = kwargs.get("offset_db_path")
        return original_generate(**kwargs)

    monkeypatch.setattr(
        "ot2_cherrypick_mcp.tools.workflow_tools.run_generate_protocol",
        lambda **kwargs: capturing_generate(**kwargs),
    )

    monkeypatch.setattr(
        "ot2_cherrypick_mcp.tools.workflow_tools.run_simulation",
        lambda **kwargs: {"stdout": "ok", "stderr": "", "returncode": 0},
    )

    result = run_full_workflow(
        csv_path=str(csv_copy),
        settings_path=str(settings_copy),
        labware_path=str(labware_copy),
        protocol_path=str(protocol_copy),
        offset_db_path=str(offset_db),
    )

    assert result["status"] == "ok"
    assert captured.get("offset_db_path") == str(offset_db)


def test_full_workflow_backward_compat_no_offset_db(monkeypatch, tmp_path: Path) -> None:
    """run_full_workflow works when offset_db_path is not provided (backward compat)."""
    settings_copy, labware_copy, csv_copy, protocol_copy = _prepare_inputs(tmp_path)

    monkeypatch.setattr(
        "ot2_cherrypick_mcp.tools.workflow_tools.run_simulation",
        lambda **kwargs: {"stdout": "ok", "stderr": "", "returncode": 0},
    )

    # Call without offset_db_path — should not raise
    result = run_full_workflow(
        csv_path=str(csv_copy),
        settings_path=str(settings_copy),
        labware_path=str(labware_copy),
        protocol_path=str(protocol_copy),
    )

    assert result["status"] == "ok"


def test_full_workflow_with_deployment(monkeypatch, tmp_path: Path) -> None:
    settings_copy, labware_copy, csv_copy, protocol_copy = _prepare_inputs(tmp_path)

    def fake_simulation(**kwargs):
        return {"command": ["opentrons_simulate"], "stdout": "ok", "stderr": "", "returncode": 0}

    monkeypatch.setattr(
        "ot2_cherrypick_mcp.tools.workflow_tools.run_simulation",
        lambda **kwargs: fake_simulation(**kwargs),
    )

    def fake_deployment(**kwargs):
        return {"protocol_file": kwargs["protocol_path"], "copies": ["target.py"], "clipboard": None}

    monkeypatch.setattr(
        "ot2_cherrypick_mcp.tools.workflow_tools.run_deployment",
        lambda **kwargs: fake_deployment(**kwargs),
    )

    result = run_full_workflow(
        csv_path=str(csv_copy),
        settings_path=str(settings_copy),
        labware_path=str(labware_copy),
        protocol_path=str(protocol_copy),
        deploy=True,
        deployment_target=str(tmp_path / "out" / "CherryPick_OT2.py"),
    )

    assert result["status"] == "ok"
    assert result["deployment"]["copies"] == ["target.py"]
