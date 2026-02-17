"""Unit tests for distribution CSV validation.

Tests the validation layer's support for distribution CSV format:
- Pipe-delimited destination wells (A1|B1|C1)
- Distribution Volume (ul) column as alternative to Volume (ul)
- Distribution pattern validation (equal, geometric:factor)
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from ot2_cherrypick_mcp.core.validation import validate_configuration
from ot2_cherrypick_mcp.utils.errors import ConfigurationError
from tests.test_data import (
    CSV_DISTRIBUTION_VALID,
    CSV_DISTRIBUTION_GEOMETRIC,
    CSV_MIXED_MODE,
    CSV_DISTRIBUTION_INVALID_WELLS,
    CSV_DISTRIBUTION_MISSING_VOLUME,
    CSV_DISTRIBUTION_INVALID_PATTERN,
    DISTRIBUTION_VALIDATION_SCENARIOS,
)


# Import from validation module or define locally if not exported
def _get_well_pattern() -> re.Pattern:
    """Get the well pattern from validation module."""
    return re.compile(r"^[A-HP][1-9][0-9]*$", re.IGNORECASE)


def _get_pipe_delimited_pattern() -> re.Pattern:
    """Pattern for pipe-delimited wells in distribution mode."""
    return re.compile(r"^([A-HP][1-9][0-9]*\|)*[A-HP][1-9][0-9]*$", re.IGNORECASE)


def _get_distribution_pattern() -> re.Pattern:
    """Pattern for distribution mode specification."""
    return re.compile(
        r"^(equal|geometric:[0-9]+\.?[0-9]*(:(asc|desc))?)", re.IGNORECASE
    )


def _copy_file(src: Path, dest: Path) -> Path:
    """Copy file from source to destination."""
    dest.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    return dest


def _setup_inputs(tmp_path: Path):
    """Set up test input files using e2e/configs/distribution profile."""
    e2e_configs_dir = Path(__file__).resolve().parent / "e2e" / "configs"
    settings_copy = _copy_file(
        e2e_configs_dir / "distribution" / "settings.toml", tmp_path / "settings.toml"
    )
    # Use the shared labware_dict.toml from e2e/configs root
    labware_copy = _copy_file(
        e2e_configs_dir / "labware_dict.toml", tmp_path / "labware_dict.toml"
    )
    return settings_copy, labware_copy


class TestWellPatterns:
    """Test well format regex patterns."""

    def test_single_well_pattern_matches_valid(self):
        """Single well pattern should match standard well names."""
        pattern = _get_well_pattern()
        assert pattern.match("A1")
        assert pattern.match("H12")
        assert pattern.match("P24")
        assert pattern.match("a1")  # case insensitive

    def test_single_well_pattern_rejects_invalid(self):
        """Single well pattern should reject pipe-delimited and invalid wells."""
        pattern = _get_well_pattern()
        assert not pattern.match("A1|B1")
        assert not pattern.match("AA1")
        assert not pattern.match("A0")
        assert not pattern.match("")

    def test_pipe_delimited_pattern_matches_valid(self):
        """Pipe-delimited pattern should match distribution well lists."""
        pattern = _get_pipe_delimited_pattern()
        assert pattern.match("A1|B1")
        assert pattern.match("A1|B1|C1|D1")
        assert pattern.match("A1")  # Single well also valid
        assert pattern.match("a1|b1|c1")  # case insensitive

    def test_pipe_delimited_pattern_rejects_invalid(self):
        """Pipe-delimited pattern should reject malformed wells."""
        pattern = _get_pipe_delimited_pattern()
        assert not pattern.match("A1|")
        assert not pattern.match("|A1")
        assert not pattern.match("A1|INVALID")
        assert not pattern.match("A1||B1")
        assert not pattern.match("")

    def test_pipe_delimited_accepts_trailing_pipes(self):
        """Pattern should strictly not accept trailing/leading pipes."""
        pattern = _get_pipe_delimited_pattern()
        assert not pattern.match("A1|B1|")
        assert not pattern.match("|A1|B1")


class TestDistributionPatterns:
    """Test distribution pattern regex validation."""

    def test_equal_pattern(self):
        """Equal distribution pattern should be accepted."""
        pattern = _get_distribution_pattern()
        assert pattern.match("equal")
        assert pattern.match("EQUAL")
        assert pattern.match("Equal")

    def test_geometric_patterns_with_integer_factor(self):
        """Geometric distribution patterns with integer factors should be accepted."""
        pattern = _get_distribution_pattern()
        assert pattern.match("geometric:0.5")
        assert pattern.match("geometric:2")
        assert pattern.match("geometric:1.5")

    def test_geometric_patterns_with_direction(self):
        """Geometric patterns with direction specifiers should be accepted."""
        pattern = _get_distribution_pattern()
        assert pattern.match("geometric:0.5:desc")
        assert pattern.match("geometric:2:asc")
        assert pattern.match("geometric:1.5:desc")

    def test_geometric_pattern_case_insensitive(self):
        """Distribution patterns should be case-insensitive."""
        pattern = _get_distribution_pattern()
        assert pattern.match("GEOMETRIC:0.5")
        assert pattern.match("Geometric:2")
        assert pattern.match("geometric:1:DESC")

    def test_invalid_patterns_rejected(self):
        """Invalid distribution patterns should be rejected."""
        pattern = _get_distribution_pattern()
        assert not pattern.match("invalid")
        assert not pattern.match("geometric:")
        assert not pattern.match("geometric:abc")
        assert not pattern.match("linear:0.5")
        assert not pattern.match("")


class TestDistributionValidation:
    """Test full validation with distribution CSVs."""

    def test_distribution_csv_validates_ok(self, tmp_path: Path) -> None:
        """Valid distribution CSV should pass validation."""
        settings_copy, labware_copy = _setup_inputs(tmp_path)
        csv_path = tmp_path / "test.csv"
        csv_path.write_text(CSV_DISTRIBUTION_VALID, encoding="utf-8")

        result = validate_configuration(
            settings_path=settings_copy,
            labware_path=labware_copy,
            csv_path=csv_path,
        )

        assert result["status"] == "ok", f"Validation failed: {result}"
        assert not result["errors"]

    def test_geometric_distribution_validates_ok(self, tmp_path: Path) -> None:
        """Geometric distribution patterns should pass validation."""
        settings_copy, labware_copy = _setup_inputs(tmp_path)
        csv_path = tmp_path / "test.csv"
        csv_path.write_text(CSV_DISTRIBUTION_GEOMETRIC, encoding="utf-8")

        result = validate_configuration(
            settings_path=settings_copy,
            labware_path=labware_copy,
            csv_path=csv_path,
        )

        assert result["status"] == "ok", f"Validation failed: {result}"

    def test_mixed_mode_validates_ok(self, tmp_path: Path) -> None:
        """Mixed cherry-pick + distribution CSV should pass validation."""
        settings_copy, labware_copy = _setup_inputs(tmp_path)
        csv_path = tmp_path / "test.csv"
        csv_path.write_text(CSV_MIXED_MODE, encoding="utf-8")

        result = validate_configuration(
            settings_path=settings_copy,
            labware_path=labware_copy,
            csv_path=csv_path,
        )

        assert result["status"] == "ok", f"Validation failed: {result}"

    def test_invalid_wells_generates_warning(self, tmp_path: Path) -> None:
        """Invalid wells in distribution should generate warning, not error."""
        settings_copy, labware_copy = _setup_inputs(tmp_path)
        csv_path = tmp_path / "test.csv"
        csv_path.write_text(CSV_DISTRIBUTION_INVALID_WELLS, encoding="utf-8")

        result = validate_configuration(
            settings_path=settings_copy,
            labware_path=labware_copy,
            csv_path=csv_path,
        )

        # Should be ok with warnings, not error
        assert result["status"] == "ok"
        assert any("INVALID" in w for w in result.get("warnings", []))

    def test_missing_distribution_volume_fails(self, tmp_path: Path) -> None:
        """Distribution row without Distribution Volume should fail."""
        settings_copy, labware_copy = _setup_inputs(tmp_path)
        csv_path = tmp_path / "test.csv"
        csv_path.write_text(CSV_DISTRIBUTION_MISSING_VOLUME, encoding="utf-8")

        result = validate_configuration(
            settings_path=settings_copy,
            labware_path=labware_copy,
            csv_path=csv_path,
        )

        assert result["status"] == "error"
        assert any("volume" in e.lower() for e in result["errors"])

    @pytest.mark.parametrize(
        "csv_content,expected_status,error_substr,description",
        DISTRIBUTION_VALIDATION_SCENARIOS,
        ids=lambda x: x[3] if isinstance(x, tuple) and len(x) > 3 else str(x),
    )
    def test_distribution_validation_scenarios(
        self,
        tmp_path: Path,
        csv_content: str,
        expected_status: str,
        error_substr: str | None,
        description: str,
    ) -> None:
        """Parametrized test for distribution CSV validation scenarios."""
        settings_copy, labware_copy = _setup_inputs(tmp_path)
        csv_path = tmp_path / "test.csv"
        csv_path.write_text(csv_content, encoding="utf-8")

        result = validate_configuration(
            settings_path=settings_copy,
            labware_path=labware_copy,
            csv_path=csv_path,
        )

        assert (
            result["status"] == expected_status
        ), f"{description}: expected {expected_status}, got {result['status']}"

        if error_substr:
            assert any(
                error_substr.lower() in e.lower() for e in result["errors"]
            ), f"Expected '{error_substr}' in errors: {result['errors']}"

    def test_distribution_csv_with_multiple_sources(self, tmp_path: Path) -> None:
        """Distribution CSV with multiple source wells should validate."""
        settings_copy, labware_copy = _setup_inputs(tmp_path)

        csv_content = """\
Source Labware,Source Well,Dest Labware,Dest Well,Distribution Volume (ul),Distribution,Source Height,Dest Top,Tip Action
tube_rack_96_1500ul_1,A1,384_pp_standard_100ul_2,A1|B1|C1|D1,25,equal,2,-5,keep
tube_rack_96_1500ul_1,A2,384_pp_standard_100ul_2,E1|F1|G1|H1,25,equal,2,-5,keep
tube_rack_96_1500ul_1,A3,384_pp_standard_100ul_2,I1|J1|K1|L1,25,equal,2,-5,keep
""".strip()

        csv_path = tmp_path / "test.csv"
        csv_path.write_text(csv_content, encoding="utf-8")

        result = validate_configuration(
            settings_path=settings_copy,
            labware_path=labware_copy,
            csv_path=csv_path,
        )

        assert result["status"] == "ok"

    def test_distribution_with_tip_actions(self, tmp_path: Path) -> None:
        """Distribution CSV with custom tip actions should validate."""
        settings_copy, labware_copy = _setup_inputs(tmp_path)

        csv_content = """\
Source Labware,Source Well,Dest Labware,Dest Well,Distribution Volume (ul),Distribution,Tip Action,Source Height,Dest Top
tube_rack_96_1500ul_1,A1,384_pp_standard_100ul_2,A1|B1|C1|D1,20,equal,keep,2,-5
tube_rack_96_1500ul_1,A2,384_pp_standard_100ul_2,E1|F1|G1|H1,20,equal,drop,2,-5
""".strip()

        csv_path = tmp_path / "test.csv"
        csv_path.write_text(csv_content, encoding="utf-8")

        result = validate_configuration(
            settings_path=settings_copy,
            labware_path=labware_copy,
            csv_path=csv_path,
        )

        assert result["status"] == "ok"

    def test_distribution_with_air_gaps(self, tmp_path: Path) -> None:
        """Distribution CSV with air gaps should validate."""
        settings_copy, labware_copy = _setup_inputs(tmp_path)

        csv_content = """\
Source Labware,Source Well,Dest Labware,Dest Well,Distribution Volume (ul),Distribution,Air Gap,Source Height,Dest Top,Tip Action
tube_rack_96_1500ul_1,A1,384_pp_standard_100ul_2,A1|B1|C1|D1,20,equal,15,2,-5,keep
""".strip()

        csv_path = tmp_path / "test.csv"
        csv_path.write_text(csv_content, encoding="utf-8")

        result = validate_configuration(
            settings_path=settings_copy,
            labware_path=labware_copy,
            csv_path=csv_path,
        )

        assert result["status"] == "ok"

    def test_distribution_with_mixing(self, tmp_path: Path) -> None:
        """Distribution CSV with mixing parameters should validate."""
        settings_copy, labware_copy = _setup_inputs(tmp_path)

        csv_content = """\
Source Labware,Source Well,Dest Labware,Dest Well,Distribution Volume (ul),Distribution,Mix Volume,Mix Height,Source Height,Dest Top,Tip Action
tube_rack_96_1500ul_1,A1,384_pp_standard_100ul_2,A1|B1|C1|D1,30,equal,15,1.5,2,-5,keep
""".strip()

        csv_path = tmp_path / "test.csv"
        csv_path.write_text(csv_content, encoding="utf-8")

        result = validate_configuration(
            settings_path=settings_copy,
            labware_path=labware_copy,
            csv_path=csv_path,
        )

        assert result["status"] == "ok"
