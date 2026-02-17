"""Tests for CSV tools with distribution CSV support.

Tests that distribution CSV format is properly validated and persisted
when using the csv_tools functions.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ot2_cherrypick_mcp.tools.csv_tools import save_csv_content
from ot2_cherrypick_mcp.utils.errors import ConfigurationError
from tests.test_data import (
    CSV_DISTRIBUTION_VALID,
    CSV_DISTRIBUTION_GEOMETRIC,
    CSV_MIXED_MODE,
    CSV_DISTRIBUTION_MISSING_VOLUME,
)


class TestDistributionCSVSave:
    """Test saving distribution CSVs using csv_tools."""

    def test_save_distribution_csv_succeeds(self, tmp_path: Path) -> None:
        """Distribution CSV with proper columns should save."""
        result = save_csv_content(
            csv_content=CSV_DISTRIBUTION_VALID,
            filename="dist.csv",
            output_dir=tmp_path,
        )
        assert Path(result["csv_file"]).exists()

        # Verify content was saved correctly
        saved = Path(result["csv_file"]).read_text(encoding="utf-8")
        assert "Distribution Volume (ul)" in saved
        assert "A1|B1|A2|B2" in saved

    def test_save_geometric_distribution_succeeds(self, tmp_path: Path) -> None:
        """Geometric distribution CSV should save successfully."""
        result = save_csv_content(
            csv_content=CSV_DISTRIBUTION_GEOMETRIC,
            filename="geometric.csv",
            output_dir=tmp_path,
        )
        assert Path(result["csv_file"]).exists()

        saved = Path(result["csv_file"]).read_text(encoding="utf-8")
        assert "geometric:0.5" in saved
        assert "geometric:2" in saved

    def test_save_mixed_mode_csv_succeeds(self, tmp_path: Path) -> None:
        """Mixed cherry-pick + distribution CSV should save."""
        result = save_csv_content(
            csv_content=CSV_MIXED_MODE,
            filename="mixed.csv",
            output_dir=tmp_path,
        )
        assert Path(result["csv_file"]).exists()

        saved = Path(result["csv_file"]).read_text(encoding="utf-8")
        assert "Volume (ul)" in saved
        assert "Distribution Volume (ul)" in saved

    def test_save_distribution_with_air_gaps(self, tmp_path: Path) -> None:
        """Distribution CSV with air gap parameters should save."""
        csv_content = """\
Source Labware,Source Well,Dest Labware,Dest Well,Distribution Volume (ul),Distribution,Air Gap,Source Height,Dest Top,Tip Action
tube_rack_96_1500ul_4,A1,384_ppv_55ul_2,A1|B1|C1|D1,15,equal,20,2,-5,keep
""".strip()

        result = save_csv_content(
            csv_content=csv_content,
            filename="air_gap.csv",
            output_dir=tmp_path,
        )
        assert Path(result["csv_file"]).exists()

        saved = Path(result["csv_file"]).read_text(encoding="utf-8")
        assert "Air Gap" in saved
        assert "20" in saved

    def test_save_distribution_with_tip_actions(self, tmp_path: Path) -> None:
        """Distribution CSV with tip action column should save."""
        csv_content = """\
Source Labware,Source Well,Dest Labware,Dest Well,Distribution Volume (ul),Distribution,Tip Action,Source Height,Dest Top
tube_rack_96_1500ul_4,A1,384_ppv_55ul_2,A1|B1|C1,25,equal,keep,2,-5
tube_rack_96_1500ul_4,A2,384_ppv_55ul_2,D1|D2|D3,25,equal,drop,2,-5
""".strip()

        result = save_csv_content(
            csv_content=csv_content,
            filename="tip_actions.csv",
            output_dir=tmp_path,
        )
        assert Path(result["csv_file"]).exists()

        saved = Path(result["csv_file"]).read_text(encoding="utf-8")
        assert "Tip Action" in saved
        assert "keep" in saved
        assert "drop" in saved

    def test_save_distribution_with_mixing(self, tmp_path: Path) -> None:
        """Distribution CSV with mixing parameters should save."""
        csv_content = """\
Source Labware,Source Well,Dest Labware,Dest Well,Distribution Volume (ul),Distribution,Mix Volume,Mix Height,Source Height,Dest Top,Tip Action
tube_rack_96_1500ul_4,A1,384_ppv_55ul_2,A1|B1|C1|D1,30,equal,15,1.5,2,-5,keep
""".strip()

        result = save_csv_content(
            csv_content=csv_content,
            filename="mixing.csv",
            output_dir=tmp_path,
        )
        assert Path(result["csv_file"]).exists()

        saved = Path(result["csv_file"]).read_text(encoding="utf-8")
        assert "Mix Volume" in saved
        assert "Mix Height" in saved

    def test_distribution_csv_missing_all_volumes_fails(self, tmp_path: Path) -> None:
        """Distribution CSV without any volume column should fail."""
        bad_csv = """\
Source Labware,Source Well,Dest Labware,Dest Well,Distribution,Tip Action
tube_rack_96_1500ul_4,A1,384_ppv_55ul_2,A1|B1|C1,equal,keep
""".strip()

        with pytest.raises(ConfigurationError, match="volume column"):
            save_csv_content(
                csv_content=bad_csv,
                filename="bad.csv",
                output_dir=tmp_path,
            )

    def test_distribution_csv_missing_dest_well_fails(self, tmp_path: Path) -> None:
        """Distribution CSV missing Dest Well column should fail."""
        bad_csv = """\
Source Labware,Source Well,Dest Labware,Distribution Volume (ul),Distribution,Source Height,Dest Top,Tip Action
tube_rack_96_1500ul_4,A1,384_ppv_55ul_2,25,equal,2,-5,keep
""".strip()

        with pytest.raises(ConfigurationError, match="Dest Well"):
            save_csv_content(
                csv_content=bad_csv,
                filename="bad.csv",
                output_dir=tmp_path,
            )

    def test_distribution_csv_missing_source_labware_fails(self, tmp_path: Path) -> None:
        """Distribution CSV missing Source Labware column should fail."""
        bad_csv = """\
Source Well,Dest Labware,Dest Well,Distribution Volume (ul),Distribution,Source Height,Dest Top,Tip Action
A1,384_ppv_55ul_2,A1|B1|C1,25,equal,2,-5,keep
""".strip()

        with pytest.raises(ConfigurationError, match="Source Labware"):
            save_csv_content(
                csv_content=bad_csv,
                filename="bad.csv",
                output_dir=tmp_path,
            )

    def test_distribution_csv_preserves_formatting(self, tmp_path: Path) -> None:
        """Distribution CSV formatting should be preserved when saved."""
        csv_content = """\
Source Labware,Source Well,Dest Labware,Dest Well,Distribution Volume (ul),Distribution,Source Height,Dest Top,Tip Action
tube_rack_96_1500ul_4,A1,384_ppv_55ul_2,A1|B1|C1|D1,50.5,equal,2.0,-5.0,keep
tube_rack_96_1500ul_4,A2,384_ppv_55ul_2,E1|F1|G1|H1,100,geometric:0.5,2.0,-5.0,keep
""".strip()

        result = save_csv_content(
            csv_content=csv_content,
            filename="formatted.csv",
            output_dir=tmp_path,
        )

        saved = Path(result["csv_file"]).read_text(encoding="utf-8")
        # Check that numerical precision is preserved
        assert "50.5" in saved
        assert "2.0" in saved
        assert "-5.0" in saved

    def test_distribution_csv_handles_empty_optional_columns(
        self, tmp_path: Path
    ) -> None:
        """Distribution CSV with empty optional columns should save."""
        csv_content = """\
Source Labware,Source Well,Dest Labware,Dest Well,Distribution Volume (ul),Distribution,Air Gap,Tip Action,Source Height,Dest Top
tube_rack_96_1500ul_4,A1,384_ppv_55ul_2,A1|B1|C1,25,equal,,keep,2,-5
tube_rack_96_1500ul_4,A2,384_ppv_55ul_2,D1|D2|D3,25,equal,15,,2,-5
""".strip()

        result = save_csv_content(
            csv_content=csv_content,
            filename="empty_cols.csv",
            output_dir=tmp_path,
        )
        assert Path(result["csv_file"]).exists()

    def test_distribution_csv_multiple_saves(self, tmp_path: Path) -> None:
        """Multiple distribution CSVs can be saved to same directory."""
        result1 = save_csv_content(
            csv_content=CSV_DISTRIBUTION_VALID,
            filename="dist1.csv",
            output_dir=tmp_path,
        )

        result2 = save_csv_content(
            csv_content=CSV_DISTRIBUTION_GEOMETRIC,
            filename="dist2.csv",
            output_dir=tmp_path,
        )

        assert Path(result1["csv_file"]).exists()
        assert Path(result2["csv_file"]).exists()
        assert result1["csv_file"] != result2["csv_file"]

    def test_distribution_csv_returns_correct_path(self, tmp_path: Path) -> None:
        """save_csv_content should return the correct file path."""
        result = save_csv_content(
            csv_content=CSV_DISTRIBUTION_VALID,
            filename="test_dist.csv",
            output_dir=tmp_path,
        )

        expected_path = tmp_path / "test_dist.csv"
        assert result["csv_file"] == str(expected_path)
        assert Path(result["csv_file"]).exists()
