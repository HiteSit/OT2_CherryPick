"""Tests for simulation helpers and tools."""

from __future__ import annotations

from pathlib import Path
from subprocess import CompletedProcess

import pytest

from ot2_cherrypick_mcp.core.simulation import simulate_protocol
from ot2_cherrypick_mcp.tools.simulation_tools import run_simulation
from ot2_cherrypick_mcp.utils.errors import ConfigurationError, SimulationError


def _copy_protocol(tmp_path: Path) -> Path:
    repo_root = Path(__file__).resolve().parents[1]
    source = repo_root / "CherryPick_OT2.py"
    destination = tmp_path / "CherryPick_OT2.py"
    destination.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    return destination


def test_simulate_protocol_success(tmp_path: Path) -> None:
    """Successful simulations return captured output."""

    protocol_copy = _copy_protocol(tmp_path)

    def runner(command):
        return CompletedProcess(command, 0, stdout="ok", stderr="")

    log_path = tmp_path / "log.json"
    result = simulate_protocol(protocol_copy, runner=runner, log_file=log_path)
    assert result["returncode"] == 0
    assert result["stdout"] == "ok"
    assert log_path.exists()


def test_simulate_protocol_with_labware(tmp_path: Path) -> None:
    """Custom labware paths are appended to the command invocation."""

    protocol_copy = _copy_protocol(tmp_path)
    labware_dir = tmp_path / "labware"
    labware_dir.mkdir()

    recorded = {}

    def runner(command):
        recorded["command"] = command
        return CompletedProcess(command, 0, stdout="", stderr="")

    simulate_protocol(protocol_copy, labware_path=labware_dir, runner=runner, log_file=None)
    assert "--custom-labware" in recorded["command"]
    assert str(labware_dir) in recorded["command"]


def test_simulate_protocol_failure_raises(tmp_path: Path) -> None:
    """Non-zero exit codes raise SimulationError."""

    protocol_copy = _copy_protocol(tmp_path)

    def runner(command):
        return CompletedProcess(command, 1, stdout="", stderr="boom")

    with pytest.raises(SimulationError):
        simulate_protocol(protocol_copy, runner=runner)


def test_simulate_protocol_missing_file_raises() -> None:
    """Missing protocol files raise configuration errors."""

    with pytest.raises(ConfigurationError):
        simulate_protocol("nonexistent.py", runner=lambda cmd: CompletedProcess(cmd, 0, "", ""))


def test_run_simulation_uses_core(monkeypatch, tmp_path: Path) -> None:
    """Tool wrapper returns sanitized dictionary from core helper."""

    protocol_copy = _copy_protocol(tmp_path)

    def fake_simulate(**kwargs):
        assert Path(kwargs["protocol_path"]) == protocol_copy
        assert kwargs["log_file"] == tmp_path / "custom_log.json"
        return {
            "command": ["opentrons_simulate"],
            "stdout": "ok",
            "stderr": "",
            "returncode": 0,
            "protocol_path": str(protocol_copy),
            "labware_path": None,
        }

    monkeypatch.setattr("ot2_cherrypick_mcp.tools.simulation_tools.simulate_protocol", fake_simulate)
    result = run_simulation(protocol_path=str(protocol_copy), log_file=tmp_path / "custom_log.json")
    assert result["returncode"] == 0
    assert result["log_file"].endswith("custom_log.json")
