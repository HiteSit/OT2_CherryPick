"""Tests for CSV helper tools."""

from __future__ import annotations

from pathlib import Path

import pytest

from ot2_cherrypick_mcp.tools.csv_tools import generate_csv_template, list_csv_files
from ot2_cherrypick_mcp.utils.errors import ConfigurationError


def test_generate_csv_template_creates_file(tmp_path: Path) -> None:
    result = generate_csv_template(
        filename="template.csv",
        transfers=3,
        source_labware="tube_rack_96_1500ul",
        dest_labware="384_ppv_55ul",
        default_volume=10.0,
        source_height=2.0,
        dest_top=-5.0,
        output_dir=tmp_path,
    )

    output = Path(result["csv_file"])
    assert output.exists()

    content = output.read_text(encoding="utf-8").strip().splitlines()
    assert content[0] == "Source Labware,Source Well,Volume (ul),Dest Labware,Dest Well,Source Height,Dest Top"
    assert len(content) == 1 + 3
    assert "tube_rack_96_1500ul" in content[1]
    assert "384_ppv_55ul" in content[1]


def test_generate_csv_template_duplicate_raises(tmp_path: Path) -> None:
    generate_csv_template(
        filename="template.csv",
        transfers=1,
        source_labware="tube_rack_96_1500ul",
        dest_labware="384_ppv_55ul",
        output_dir=tmp_path,
    )

    with pytest.raises(ConfigurationError):
        generate_csv_template(
            filename="template.csv",
            transfers=1,
            source_labware="tube_rack_96_1500ul",
            dest_labware="384_ppv_55ul",
            output_dir=tmp_path,
        )


def test_list_csv_files_returns_sorted(tmp_path: Path) -> None:
    (tmp_path / "b.csv").write_text("", encoding="utf-8")
    (tmp_path / "a.csv").write_text("", encoding="utf-8")
    files = list_csv_files(tmp_path)
    assert files == [str(tmp_path / "a.csv"), str(tmp_path / "b.csv")]
