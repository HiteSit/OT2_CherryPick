"""E2E contract tests for license-gated protocol generation."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.support.license_gate_contract import (
    assert_allowed_clown_mutation,
    embedded_csv_text,
    generate_protocol_in_process,
    maybe_patch_license_client,
    patch_protocol_generation_denial,
    patch_protocol_generation_mode,
    read_input_csv_text,
)
from tests.support.workspace import E2EWorkspace


pytestmark = pytest.mark.e2e


def _workspace(tmp_path: Path, name: str, config_profile: str) -> E2EWorkspace:
    root = tmp_path / name
    root.mkdir()
    return E2EWorkspace.create(root, config_profile)


def test_normal_mode_keeps_embedded_csv_unchanged(
    e2e_workspace_factory,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace: E2EWorkspace = e2e_workspace_factory("single_X1")
    csv_path = workspace.get_csv_path("example_basic.csv")
    original_csv = read_input_csv_text(csv_path)
    maybe_patch_license_client(monkeypatch, allowed=True, mode="normal-mode")

    generate_protocol_in_process(workspace, csv_path)

    assert embedded_csv_text(workspace.protocol_path) == original_csv
    assert read_input_csv_text(csv_path) == original_csv


def test_clown_mode_deterministically_mutates_embedded_csv(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    patch_protocol_generation_mode(monkeypatch, mode="clown-mode")
    first_workspace = _workspace(tmp_path, "first", "single_X1")
    second_workspace = _workspace(tmp_path, "second", "single_X1")
    first_csv_path = first_workspace.get_csv_path("example_basic.csv")
    second_csv_path = second_workspace.get_csv_path("example_basic.csv")
    original_csv = read_input_csv_text(first_csv_path)

    generate_protocol_in_process(first_workspace, first_csv_path)
    generate_protocol_in_process(second_workspace, second_csv_path)

    first_embedded_csv = embedded_csv_text(first_workspace.protocol_path)
    second_embedded_csv = embedded_csv_text(second_workspace.protocol_path)
    assert first_embedded_csv == second_embedded_csv
    assert_allowed_clown_mutation(original_csv, first_embedded_csv)
    assert read_input_csv_text(first_csv_path) == original_csv


def test_license_denial_fails_before_protocol_update(
    e2e_workspace_factory,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    patch_protocol_generation_denial(monkeypatch, reason="unknown_machine")
    workspace: E2EWorkspace = e2e_workspace_factory("single_X1")
    csv_path = workspace.get_csv_path("example_basic.csv")
    original_protocol = workspace.protocol_path.read_text(encoding="utf-8")

    with pytest.raises(Exception):
        generate_protocol_in_process(workspace, csv_path)

    assert workspace.protocol_path.read_text(encoding="utf-8") == original_protocol
