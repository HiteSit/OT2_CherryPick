"""Tests for protocol tools."""

from __future__ import annotations

from pathlib import Path

import pytest

from ot2_cherrypick_mcp.tools.protocol_tools import run_generate_protocol
from ot2_cherrypick_mcp.utils.errors import ConfigurationError


def test_run_generate_protocol_updates_protocol_file(tmp_path: Path) -> None:
    """Ensure the helper embeds configuration into the target protocol file."""
    repo_root = Path(__file__).resolve().parents[1]

    protocol_source = repo_root / "CherryPick_OT2.py"
    protocol_copy = tmp_path / "CherryPick_OT2.py"
    protocol_copy.write_text(protocol_source.read_text(encoding="utf-8"), encoding="utf-8")

    result = run_generate_protocol(
        csv_path=str(repo_root / "CSVs" / "example_basic.csv"),
        settings_path=str(repo_root / "settings.toml"),
        labware_path=str(repo_root / "labware_dict.toml"),
        protocol_path=str(protocol_copy),
    )

    assert result["protocol_file"] == str(protocol_copy)
    assert result["json_size"] > 0
    assert "Protocol generated successfully" in result["message"]

    updated_content = protocol_copy.read_text(encoding="utf-8")
    original_content = protocol_source.read_text(encoding="utf-8")
    assert updated_content != original_content
    assert "_all_values = json.loads" in updated_content


def test_run_generate_protocol_missing_csv_raises(tmp_path: Path) -> None:
    """Missing input files surface as configuration errors."""
    protocol_copy = tmp_path / "CherryPick_OT2.py"
    protocol_copy.write_text("", encoding="utf-8")

    with pytest.raises(ConfigurationError):
        run_generate_protocol(
            csv_path=str(tmp_path / "missing.csv"),
            settings_path=str(tmp_path / "settings.toml"),
            labware_path=str(tmp_path / "labware_dict.toml"),
            protocol_path=str(protocol_copy),
        )
