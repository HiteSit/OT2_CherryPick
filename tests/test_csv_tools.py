"""Tests for CSV helper tools."""

from __future__ import annotations

from pathlib import Path

import pytest

from ot2_cherrypick_mcp.tools.csv_tools import (
    generate_csv_template,
    insert_home_rows,
    list_csv_files,
    save_csv_content,
)
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
    assert content[0] == "Source Labware,Source Well,Dest Labware,Dest Well,Volume (ul),Source Bottom,Dest Top,Tip Action"
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


def test_save_csv_content_writes_file(tmp_path: Path) -> None:
    content = "Source Labware,Source Well,Volume (ul),Dest Labware,Dest Well,Source Bottom,Dest Top,Tip Action\n"
    result = save_csv_content(
        csv_content=content,
        filename="uploaded.csv",
        output_dir=tmp_path,
    )
    path = Path(result["csv_file"])
    assert path.exists()
    assert path.read_text(encoding="utf-8").startswith("Source Labware")


def test_save_csv_content_missing_columns_raises(tmp_path: Path) -> None:
    with pytest.raises(ConfigurationError):
        save_csv_content(
            csv_content="foo,bar\n1,2",
            filename="bad.csv",
            output_dir=tmp_path,
        )


# --- insert_home_rows tests ---

def _write_csv(tmp_path: Path, filename: str, rows: list[str]) -> Path:
    """Helper: write CSV lines to a file and return the path."""
    path = tmp_path / filename
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return path


_HEADER = "Source Labware,Source Well,Volume (ul),Dest Labware,Dest Well,Tip Action"


def _transfer_row(well: str, tip: str = "keep") -> str:
    return f"rack_4,{well},50,plate_2,{well},{tip}"


def test_insert_home_rows_basic(tmp_path: Path) -> None:
    """HOME rows are inserted every N transfers."""
    csv_path = _write_csv(tmp_path, "basic.csv", [
        _HEADER,
        _transfer_row("A1", "new"),
        _transfer_row("A2"),
        _transfer_row("A3"),
        _transfer_row("A4"),
        _transfer_row("A5"),
        _transfer_row("A6"),
    ])

    result = insert_home_rows(csv_path=str(csv_path), every_n_transfers=3)

    assert result["home_rows_inserted"] == 1
    assert result["original_transfer_rows"] == 6
    assert result["total_rows_now"] == 7  # 6 transfers + 1 HOME

    lines = csv_path.read_text(encoding="utf-8").strip().splitlines()
    # HOME should be after 3rd transfer (line index 4 = row 4 after header)
    assert lines[4] == "HOME,HOME,HOME,HOME,HOME,HOME"
    # Row after HOME must be forced to "new"
    assert lines[5].endswith(",new")


def test_insert_home_rows_forces_tip_action_new(tmp_path: Path) -> None:
    """Rows after inserted HOME rows get Tip Action forced to 'new'."""
    csv_path = _write_csv(tmp_path, "tip.csv", [
        _HEADER,
        _transfer_row("A1", "new"),
        _transfer_row("A2", "keep"),  # will be after HOME, should become "new"
    ])

    result = insert_home_rows(csv_path=str(csv_path), every_n_transfers=1)

    assert result["home_rows_inserted"] == 1
    assert len(result["tip_actions_forced_to_new"]) == 1

    lines = csv_path.read_text(encoding="utf-8").strip().splitlines()
    # Row 1: A1 transfer, Row 2: HOME, Row 3: A2 transfer with tip=new
    assert lines[2] == "HOME,HOME,HOME,HOME,HOME,HOME"
    assert lines[3].endswith(",new")


def test_insert_home_rows_preserves_existing_home(tmp_path: Path) -> None:
    """Existing HOME rows reset the counter but are not duplicated."""
    csv_path = _write_csv(tmp_path, "existing.csv", [
        _HEADER,
        _transfer_row("A1", "new"),
        _transfer_row("A2"),
        "HOME,HOME,HOME,HOME,HOME,HOME",
        _transfer_row("A3", "new"),
        _transfer_row("A4"),
    ])

    result = insert_home_rows(csv_path=str(csv_path), every_n_transfers=3)

    # The existing HOME resets counter; only 2 transfers after it, so no new HOME needed
    assert result["home_rows_inserted"] == 0
    assert result["total_rows_now"] == 5  # unchanged


def test_insert_home_rows_no_home_at_end(tmp_path: Path) -> None:
    """No HOME row is inserted after the last transfer."""
    csv_path = _write_csv(tmp_path, "end.csv", [
        _HEADER,
        _transfer_row("A1", "new"),
        _transfer_row("A2"),
        _transfer_row("A3"),
    ])

    result = insert_home_rows(csv_path=str(csv_path), every_n_transfers=3)

    # Exactly 3 transfers = no HOME needed (would be pointless at the end)
    assert result["home_rows_inserted"] == 0


def test_insert_home_rows_invalid_interval_raises(tmp_path: Path) -> None:
    """Zero or negative interval raises an error."""
    csv_path = _write_csv(tmp_path, "bad.csv", [_HEADER, _transfer_row("A1", "new")])

    with pytest.raises(ConfigurationError):
        insert_home_rows(csv_path=str(csv_path), every_n_transfers=0)


def test_insert_home_rows_already_new_tip_not_forced(tmp_path: Path) -> None:
    """Rows already having Tip Action: new are not listed as forced."""
    csv_path = _write_csv(tmp_path, "already_new.csv", [
        _HEADER,
        _transfer_row("A1", "new"),
        _transfer_row("A2", "new"),  # already "new", follows HOME
    ])

    result = insert_home_rows(csv_path=str(csv_path), every_n_transfers=1)

    assert result["home_rows_inserted"] == 1
    assert result["tip_actions_forced_to_new"] == []  # nothing forced
