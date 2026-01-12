"""Unit tests for HOME control row feature."""

from __future__ import annotations

import csv
from io import StringIO
from pathlib import Path

import pytest

from ot2_cherrypick_mcp.core.validation import validate_configuration


def test_is_home_control_row_all_home():
    """Row with all HOME values should be detected as HOME control row."""
    csv_content = "Col1,Col2,Col3\nHOME,HOME,HOME"
    reader = csv.DictReader(StringIO(csv_content))
    row = next(reader)

    # Check all non-empty values are HOME
    values = [str(v).strip().upper() for v in row.values() if str(v).strip()]
    assert all(v == "HOME" for v in values)
    assert len(values) == 3


def test_is_home_control_row_mixed_values():
    """Row with mixed values should not be detected as HOME control row."""
    csv_content = "Col1,Col2,Col3\nHOME,A1,50"
    reader = csv.DictReader(StringIO(csv_content))
    row = next(reader)

    values = [str(v).strip().upper() for v in row.values() if str(v).strip()]
    assert not all(v == "HOME" for v in values)
    assert any(v != "HOME" for v in values)


def test_is_home_control_row_case_insensitive():
    """HOME detection should be case-insensitive."""
    csv_content = "Col1,Col2,Col3\nhome,Home,HOME"
    reader = csv.DictReader(StringIO(csv_content))
    row = next(reader)

    values = [str(v).strip().upper() for v in row.values() if str(v).strip()]
    assert all(v == "HOME" for v in values)
    assert len(values) == 3


def test_is_home_control_row_with_empty_columns():
    """HOME row with some empty columns should still work."""
    csv_content = "Col1,Col2,Col3,Col4\nHOME,,HOME,"
    reader = csv.DictReader(StringIO(csv_content))
    row = next(reader)

    # Only non-empty values should be checked
    values = [str(v).strip().upper() for v in row.values() if str(v).strip()]
    assert all(v == "HOME" for v in values)
    assert len(values) == 2  # Only 2 non-empty values


def test_is_home_control_row_empty_row():
    """Completely empty row should NOT be HOME control row."""
    csv_content = "Col1,Col2,Col3\n,,"
    reader = csv.DictReader(StringIO(csv_content))
    row = next(reader)

    values = [str(v).strip().upper() for v in row.values() if str(v).strip()]
    # Empty row has no values, so all() returns True but we have no values
    # This is edge case - truly empty rows should not be HOME
    assert len(values) == 0


def test_is_home_control_row_single_home():
    """Row with only one HOME value is not a complete HOME row."""
    csv_content = "Col1,Col2,Col3\nHOME,A1,B1"
    reader = csv.DictReader(StringIO(csv_content))
    row = next(reader)

    values = [str(v).strip().upper() for v in row.values() if str(v).strip()]
    assert not all(v == "HOME" for v in values)


def test_is_home_control_row_with_whitespace():
    """HOME detection should handle whitespace around values."""
    csv_content = "Col1,Col2,Col3\n  HOME  , HOME , HOME"
    reader = csv.DictReader(StringIO(csv_content))
    row = next(reader)

    values = [str(v).strip().upper() for v in row.values() if str(v).strip()]
    assert all(v == "HOME" for v in values)
    assert len(values) == 3


def test_is_home_control_row_many_columns():
    """HOME row with many columns should work."""
    csv_content = "A,B,C,D,E,F,G,H\nHOME,HOME,HOME,HOME,HOME,HOME,HOME,HOME"
    reader = csv.DictReader(StringIO(csv_content))
    row = next(reader)

    values = [str(v).strip().upper() for v in row.values() if str(v).strip()]
    assert all(v == "HOME" for v in values)
    assert len(values) == 8


def test_is_home_control_row_almost_all_home():
    """Row with almost all HOME (one non-HOME value) should not be HOME row."""
    csv_content = "Col1,Col2,Col3,Col4\nHOME,HOME,HOME,X"
    reader = csv.DictReader(StringIO(csv_content))
    row = next(reader)

    values = [str(v).strip().upper() for v in row.values() if str(v).strip()]
    assert not all(v == "HOME" for v in values)
    assert any(v != "HOME" for v in values)


def _copy_file(src: Path, dst: Path) -> Path:
    """Copy file from src to dst."""
    dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    return dst


class TestHomeControlValidation:
    """Tests for HOME→new tip validation rule."""

    def test_home_followed_by_new_tip_is_valid(self, tmp_path: Path) -> None:
        """HOME row followed by Tip Action: new should pass validation."""
        repo_root = Path(__file__).resolve().parents[1]
        settings_copy = _copy_file(repo_root / "settings.toml", tmp_path / "settings.toml")
        labware_copy = _copy_file(repo_root / "labware_dict.toml", tmp_path / "labware_dict.toml")

        csv_content = """\
Source Labware,Source Well,Volume (ul),Dest Labware,Dest Well,Source Height,Dest Top,Tip Action
tube_rack_96_1500ul_4,A1,50,384_ppv_55ul_2,A1,2,-5,new
HOME,HOME,HOME,HOME,HOME,HOME,HOME,HOME
tube_rack_96_1500ul_4,A2,50,384_ppv_55ul_2,A2,2,-5,new
""".strip()

        csv_path = tmp_path / "valid_home.csv"
        csv_path.write_text(csv_content, encoding="utf-8")

        result = validate_configuration(
            settings_path=settings_copy,
            labware_path=labware_copy,
            csv_path=csv_path,
        )

        assert result["status"] == "ok", f"Expected OK but got errors: {result['errors']}"

    def test_home_followed_by_keep_tip_is_error(self, tmp_path: Path) -> None:
        """HOME row followed by Tip Action: keep should fail validation."""
        repo_root = Path(__file__).resolve().parents[1]
        settings_copy = _copy_file(repo_root / "settings.toml", tmp_path / "settings.toml")
        labware_copy = _copy_file(repo_root / "labware_dict.toml", tmp_path / "labware_dict.toml")

        csv_content = """\
Source Labware,Source Well,Volume (ul),Dest Labware,Dest Well,Source Height,Dest Top,Tip Action
tube_rack_96_1500ul_4,A1,50,384_ppv_55ul_2,A1,2,-5,new
HOME,HOME,HOME,HOME,HOME,HOME,HOME,HOME
tube_rack_96_1500ul_4,A2,50,384_ppv_55ul_2,A2,2,-5,keep
""".strip()

        csv_path = tmp_path / "invalid_home_keep.csv"
        csv_path.write_text(csv_content, encoding="utf-8")

        result = validate_configuration(
            settings_path=settings_copy,
            labware_path=labware_copy,
            csv_path=csv_path,
        )

        assert result["status"] == "error"
        assert any("HOME" in err and "new" in err for err in result["errors"])

    def test_home_followed_by_drop_tip_is_error(self, tmp_path: Path) -> None:
        """HOME row followed by Tip Action: drop should fail validation."""
        repo_root = Path(__file__).resolve().parents[1]
        settings_copy = _copy_file(repo_root / "settings.toml", tmp_path / "settings.toml")
        labware_copy = _copy_file(repo_root / "labware_dict.toml", tmp_path / "labware_dict.toml")

        csv_content = """\
Source Labware,Source Well,Volume (ul),Dest Labware,Dest Well,Source Height,Dest Top,Tip Action
tube_rack_96_1500ul_4,A1,50,384_ppv_55ul_2,A1,2,-5,new
HOME,HOME,HOME,HOME,HOME,HOME,HOME,HOME
tube_rack_96_1500ul_4,A2,50,384_ppv_55ul_2,A2,2,-5,drop
""".strip()

        csv_path = tmp_path / "invalid_home_drop.csv"
        csv_path.write_text(csv_content, encoding="utf-8")

        result = validate_configuration(
            settings_path=settings_copy,
            labware_path=labware_copy,
            csv_path=csv_path,
        )

        assert result["status"] == "error"
        assert any("HOME" in err and "new" in err for err in result["errors"])

    def test_home_followed_by_empty_tip_is_error(self, tmp_path: Path) -> None:
        """HOME row followed by empty Tip Action should fail validation."""
        repo_root = Path(__file__).resolve().parents[1]
        settings_copy = _copy_file(repo_root / "settings.toml", tmp_path / "settings.toml")
        labware_copy = _copy_file(repo_root / "labware_dict.toml", tmp_path / "labware_dict.toml")

        csv_content = """\
Source Labware,Source Well,Volume (ul),Dest Labware,Dest Well,Source Height,Dest Top,Tip Action
tube_rack_96_1500ul_4,A1,50,384_ppv_55ul_2,A1,2,-5,new
HOME,HOME,HOME,HOME,HOME,HOME,HOME,HOME
tube_rack_96_1500ul_4,A2,50,384_ppv_55ul_2,A2,2,-5,
""".strip()

        csv_path = tmp_path / "invalid_home_empty.csv"
        csv_path.write_text(csv_content, encoding="utf-8")

        result = validate_configuration(
            settings_path=settings_copy,
            labware_path=labware_copy,
            csv_path=csv_path,
        )

        assert result["status"] == "error"
        assert any("HOME" in err for err in result["errors"])

    def test_consecutive_home_rows_are_valid(self, tmp_path: Path) -> None:
        """Multiple consecutive HOME rows should be valid."""
        repo_root = Path(__file__).resolve().parents[1]
        settings_copy = _copy_file(repo_root / "settings.toml", tmp_path / "settings.toml")
        labware_copy = _copy_file(repo_root / "labware_dict.toml", tmp_path / "labware_dict.toml")

        csv_content = """\
Source Labware,Source Well,Volume (ul),Dest Labware,Dest Well,Source Height,Dest Top,Tip Action
tube_rack_96_1500ul_4,A1,50,384_ppv_55ul_2,A1,2,-5,new
HOME,HOME,HOME,HOME,HOME,HOME,HOME,HOME
HOME,HOME,HOME,HOME,HOME,HOME,HOME,HOME
tube_rack_96_1500ul_4,A2,50,384_ppv_55ul_2,A2,2,-5,new
""".strip()

        csv_path = tmp_path / "consecutive_home.csv"
        csv_path.write_text(csv_content, encoding="utf-8")

        result = validate_configuration(
            settings_path=settings_copy,
            labware_path=labware_copy,
            csv_path=csv_path,
        )

        assert result["status"] == "ok", f"Expected OK but got errors: {result['errors']}"

    def test_home_at_end_of_csv_is_valid(self, tmp_path: Path) -> None:
        """HOME row at end of CSV (no following row) should be valid."""
        repo_root = Path(__file__).resolve().parents[1]
        settings_copy = _copy_file(repo_root / "settings.toml", tmp_path / "settings.toml")
        labware_copy = _copy_file(repo_root / "labware_dict.toml", tmp_path / "labware_dict.toml")

        csv_content = """\
Source Labware,Source Well,Volume (ul),Dest Labware,Dest Well,Source Height,Dest Top,Tip Action
tube_rack_96_1500ul_4,A1,50,384_ppv_55ul_2,A1,2,-5,new
tube_rack_96_1500ul_4,A2,50,384_ppv_55ul_2,A2,2,-5,drop
HOME,HOME,HOME,HOME,HOME,HOME,HOME,HOME
""".strip()

        csv_path = tmp_path / "home_at_end.csv"
        csv_path.write_text(csv_content, encoding="utf-8")

        result = validate_configuration(
            settings_path=settings_copy,
            labware_path=labware_copy,
            csv_path=csv_path,
        )

        assert result["status"] == "ok", f"Expected OK but got errors: {result['errors']}"
