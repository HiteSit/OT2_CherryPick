"""Tests for deployment helpers and tools."""

from __future__ import annotations

from pathlib import Path
import subprocess

import pytest

from ot2_cherrypick_mcp.core.deployment import deploy_protocol
from ot2_cherrypick_mcp.tools.deployment_tools import run_deployment
from ot2_cherrypick_mcp.utils.errors import ConfigurationError, DeploymentError


def _copy_protocol(tmp_path: Path) -> Path:
    repo_root = Path(__file__).resolve().parents[1]
    destination = tmp_path / "CherryPick_OT2.py"
    destination.write_text((repo_root / "CherryPick_OT2.py").read_text(encoding="utf-8"), encoding="utf-8")
    return destination


def test_deploy_protocol_copies_file(tmp_path: Path) -> None:
    protocol_copy = _copy_protocol(tmp_path)
    target = tmp_path / "out" / "CherryPick_OT2.py"

    result = deploy_protocol(protocol_copy, target_path=target)

    assert Path(result["copies"][0]).exists()
    assert target.exists()


def test_deploy_protocol_clipboard_runner(tmp_path: Path) -> None:
    protocol_copy = _copy_protocol(tmp_path)

    result = deploy_protocol(
        protocol_copy,
        copy_to_clipboard=True,
        clipboard_command=["/bin/cat"],
        clipboard_runner=lambda command, data: subprocess.CompletedProcess(command, 0, stdout="", stderr=""),
    )

    assert result["clipboard"]["returncode"] == 0


def test_deploy_protocol_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(ConfigurationError):
        deploy_protocol(tmp_path / "missing.py")


def test_run_deployment_uses_default(monkeypatch, tmp_path: Path) -> None:
    protocol_copy = _copy_protocol(tmp_path)

    monkeypatch.setattr(
        "ot2_cherrypick_mcp.core.deployment.deploy_protocol",
        lambda **kwargs: {"protocol_file": kwargs["protocol_path"], "copies": [], "clipboard": None},
    )

    result = run_deployment(protocol_path=str(protocol_copy))
    assert result["protocol_file"] == str(protocol_copy)


def test_deploy_protocol_clipboard_missing_command(tmp_path: Path) -> None:
    protocol_copy = _copy_protocol(tmp_path)

    with pytest.raises(DeploymentError):
        deploy_protocol(protocol_copy, copy_to_clipboard=True, clipboard_command=["/nonexistent/clip.exe"])
