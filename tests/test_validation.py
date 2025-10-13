"""Tests for configuration validation helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from ot2_cherrypick_mcp.core.validation import validate_configuration
from ot2_cherrypick_mcp.tools.validation_tools import run_validation


def _copy_file(src: Path, dest: Path) -> Path:
    dest.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    return dest


def _setup_inputs(tmp_path: Path):
    repo_root = Path(__file__).resolve().parents[1]
    settings_copy = _copy_file(repo_root / "settings.toml", tmp_path / "settings.toml")
    labware_copy = _copy_file(repo_root / "labware_dict.toml", tmp_path / "labware_dict.toml")
    csv_copy = _copy_file(repo_root / "CSVs" / "example_basic.csv", tmp_path / "example_basic.csv")
    return settings_copy, labware_copy, csv_copy


def test_validate_configuration_returns_ok(tmp_path: Path) -> None:
    settings_copy, labware_copy, csv_copy = _setup_inputs(tmp_path)

    result = validate_configuration(
        settings_path=settings_copy,
        labware_path=labware_copy,
        csv_path=csv_copy,
    )

    assert result["status"] == "ok"
    assert not result["errors"]


def test_validate_configuration_detects_missing_labware(tmp_path: Path) -> None:
    settings_copy, labware_copy, csv_copy = _setup_inputs(tmp_path)

    text = settings_copy.read_text(encoding="utf-8").replace("tube_rack_96_1500ul", "unknown_labware")
    settings_copy.write_text(text, encoding="utf-8")

    result = validate_configuration(
        settings_path=settings_copy,
        labware_path=labware_copy,
        csv_path=csv_copy,
    )

    assert result["status"] == "error"
    assert any("unknown_labware" in err for err in result["errors"])


def test_validate_configuration_reports_csv_column_issue(tmp_path: Path) -> None:
    settings_copy, labware_copy, csv_copy = _setup_inputs(tmp_path)

    csv_copy.write_text("Source Labware,Dest Labware\nfoo,bar\n", encoding="utf-8")

    result = validate_configuration(
        settings_path=settings_copy,
        labware_path=labware_copy,
        csv_path=csv_copy,
    )

    assert result["status"] == "error"
    assert any("missing required columns" in err for err in result["errors"])


def test_run_validation_wrapper(tmp_path: Path) -> None:
    settings_copy, labware_copy, csv_copy = _setup_inputs(tmp_path)

    result = run_validation(
        settings_path=str(settings_copy),
        labware_path=str(labware_copy),
        csv_path=str(csv_copy),
    )

    assert result["status"] == "ok"
