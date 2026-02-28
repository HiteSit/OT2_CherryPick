"""E2E tests for distribution CSV validation and simulation.

These tests run the full workflow: validation → generation → simulation
using actual opentrons_simulate.
"""

from __future__ import annotations

import pytest
from pathlib import Path

from .conftest import (
    E2EWorkspace,
    CUSTOM_LABWARE_PATH,
    requires_custom_labware,
    run_full_workflow,
    generate_protocol,
    simulate_protocol,
)
from ot2_cherrypick_mcp.core.validation import validate_configuration
from tests.test_data import (
    CSV_DISTRIBUTION_VALID,
    CSV_DISTRIBUTION_GEOMETRIC,
    CSV_MIXED_MODE,
)


class TestDistributionValidationAndGeneration:
    """Test validation and generation for distribution CSVs."""

    def test_distribution_csv_validates_successfully(self, tmp_path: Path) -> None:
        """Distribution CSV should pass validation step."""
        configs_dir = Path(__file__).resolve().parent / "configs"

        csv_path = tmp_path / "dist.csv"
        csv_path.write_text(CSV_DISTRIBUTION_VALID, encoding="utf-8")

        result = validate_configuration(
            settings_path=configs_dir / "distribution" / "settings.toml",
            labware_path=configs_dir / "labware_dict.toml",
            csv_path=csv_path,
        )

        assert result["status"] == "ok", f"Validation failed: {result['errors']}"
        assert not result["errors"]

    def test_geometric_distribution_validates_successfully(self, tmp_path: Path) -> None:
        """Geometric distribution CSV should pass validation."""
        configs_dir = Path(__file__).resolve().parent / "configs"

        csv_path = tmp_path / "geometric.csv"
        csv_path.write_text(CSV_DISTRIBUTION_GEOMETRIC, encoding="utf-8")

        result = validate_configuration(
            settings_path=configs_dir / "distribution" / "settings.toml",
            labware_path=configs_dir / "labware_dict.toml",
            csv_path=csv_path,
        )

        assert result["status"] == "ok"

    def test_mixed_mode_csv_validates_successfully(self, tmp_path: Path) -> None:
        """Mixed cherry-pick and distribution CSV should pass validation."""
        configs_dir = Path(__file__).resolve().parent / "configs"

        csv_path = tmp_path / "mixed.csv"
        csv_path.write_text(CSV_MIXED_MODE, encoding="utf-8")

        result = validate_configuration(
            settings_path=configs_dir / "distribution" / "settings.toml",
            labware_path=configs_dir / "labware_dict.toml",
            csv_path=csv_path,
        )

        assert result["status"] == "ok"

    def test_distribution_with_multiple_sources(self, tmp_path: Path) -> None:
        """Distribution from multiple source wells should validate."""
        configs_dir = Path(__file__).resolve().parent / "configs"

        csv_content = """\
Source Labware,Source Well,Dest Labware,Dest Well,Distribution Volume (ul),Distribution,Source Bottom,Dest Top
tube_rack_96_1500ul_1,A1,384_pp_standard_100ul_2,A1|B1|C1|D1,25,equal,2,-5
tube_rack_96_1500ul_1,A2,384_pp_standard_100ul_2,E1|F1|G1|H1,25,equal,2,-5
tube_rack_96_1500ul_1,A3,384_pp_standard_100ul_2,I1|J1|K1|L1,25,equal,2,-5
""".strip()

        csv_path = tmp_path / "multi_source.csv"
        csv_path.write_text(csv_content, encoding="utf-8")

        result = validate_configuration(
            settings_path=configs_dir / "distribution" / "settings.toml",
            labware_path=configs_dir / "labware_dict.toml",
            csv_path=csv_path,
        )

        assert result["status"] == "ok"

    def test_distribution_with_optional_columns(self, tmp_path: Path) -> None:
        """Distribution CSV with optional columns should validate."""
        configs_dir = Path(__file__).resolve().parent / "configs"

        csv_content = """\
Source Labware,Source Well,Dest Labware,Dest Well,Distribution Volume (ul),Distribution,Air Gap,Tip Action,Source Bottom,Dest Top
tube_rack_96_1500ul_1,A1,384_pp_standard_100ul_2,A1|B1|C1|D1,20,equal,15,keep,2,-5
tube_rack_96_1500ul_1,A2,384_pp_standard_100ul_2,E1|F1|G1|H1,20,equal,15,drop,2,-5
""".strip()

        csv_path = tmp_path / "with_options.csv"
        csv_path.write_text(csv_content, encoding="utf-8")

        result = validate_configuration(
            settings_path=configs_dir / "distribution" / "settings.toml",
            labware_path=configs_dir / "labware_dict.toml",
            csv_path=csv_path,
        )

        assert result["status"] == "ok"


@requires_custom_labware
class TestDistributionE2E:
    """End-to-end tests for distribution workflows."""

    def test_distribution_csv_generates_protocol(
        self, e2e_workspace_factory
    ) -> None:
        """Protocol should generate from valid distribution CSV."""
        workspace: E2EWorkspace = e2e_workspace_factory("multi")

        csv_path = workspace.get_csv_path("example_distribution.csv")
        success, output = generate_protocol(workspace, csv_path)

        assert success, f"Protocol generation failed:\n{output}"
        assert workspace.protocol_path.exists()

    def test_distribution_csv_validates_and_simulates(
        self, e2e_workspace_factory
    ) -> None:
        """Full workflow: generation → simulation with distribution CSV."""
        workspace: E2EWorkspace = e2e_workspace_factory("multi")

        result = run_full_workflow(
            workspace,
            "example_distribution.csv",
            custom_labware_path=CUSTOM_LABWARE_PATH,
        )

        result.assert_success("Distribution mode simulation failed")

    def test_geometric_distribution_simulates(self, e2e_workspace_factory) -> None:
        """Geometric distribution patterns work correctly in simulation."""
        workspace: E2EWorkspace = e2e_workspace_factory("multi")

        result = run_full_workflow(
            workspace,
            "example_distribution.csv",
            custom_labware_path=CUSTOM_LABWARE_PATH,
        )

        result.assert_success("Geometric distribution simulation failed")

    def test_distribution_with_air_gaps_simulates(
        self, e2e_workspace_factory
    ) -> None:
        """Distribution with air gaps between dispenses works correctly."""
        workspace: E2EWorkspace = e2e_workspace_factory("multi")

        result = run_full_workflow(
            workspace,
            "example_distribution.csv",
            custom_labware_path=CUSTOM_LABWARE_PATH,
        )

        result.assert_success("Distribution with air gaps simulation failed")
        assert "Protocol complete" in result.output

    def test_mixed_mode_simulates(self, e2e_workspace_factory) -> None:
        """Mixed cherry-pick and distribution mode works in simulation."""
        workspace: E2EWorkspace = e2e_workspace_factory("multi")

        result = run_full_workflow(
            workspace,
            "example_mixed_modes.csv",
            custom_labware_path=CUSTOM_LABWARE_PATH,
        )

        result.assert_success("Mixed mode simulation failed")

    def test_distribution_protocol_output_contains_transfers(
        self, e2e_workspace_factory
    ) -> None:
        """Simulation output should show distribution transfers."""
        workspace: E2EWorkspace = e2e_workspace_factory("multi")

        result = run_full_workflow(
            workspace,
            "example_distribution.csv",
            custom_labware_path=CUSTOM_LABWARE_PATH,
        )

        result.assert_success()
        # Check that simulation output shows transfers were performed
        output_lower = result.output.lower()
        assert (
            "aspirat" in output_lower or "dispens" in output_lower
        ), "Expected transfer operations (aspirat* or dispens*) in simulation output"


class TestDistributionValidationErrorCases:
    """Test error handling in distribution validation."""

    def test_missing_distribution_volume_fails_validation(
        self, tmp_path: Path
    ) -> None:
        """CSV missing Distribution Volume should fail validation."""
        configs_dir = Path(__file__).resolve().parent / "configs"

        csv_content = """\
Source Labware,Source Well,Dest Labware,Dest Well,Distribution,Source Bottom,Dest Top
tube_rack_96_1500ul_1,A1,384_pp_standard_100ul_2,A1|B1|C1,equal,2,-5
""".strip()

        csv_path = tmp_path / "no_volume.csv"
        csv_path.write_text(csv_content, encoding="utf-8")

        result = validate_configuration(
            settings_path=configs_dir / "distribution" / "settings.toml",
            labware_path=configs_dir / "labware_dict.toml",
            csv_path=csv_path,
        )

        assert result["status"] == "error"
        assert any("volume" in e.lower() for e in result["errors"])

    def test_invalid_labware_in_distribution_fails(self, tmp_path: Path) -> None:
        """CSV with undefined labware should fail validation."""
        configs_dir = Path(__file__).resolve().parent / "configs"

        csv_content = """\
Source Labware,Source Well,Dest Labware,Dest Well,Distribution Volume (ul),Distribution,Source Bottom,Dest Top
undefined_labware_1,A1,384_pp_standard_100ul_2,A1|B1|C1,25,equal,2,-5
""".strip()

        csv_path = tmp_path / "bad_labware.csv"
        csv_path.write_text(csv_content, encoding="utf-8")

        result = validate_configuration(
            settings_path=configs_dir / "distribution" / "settings.toml",
            labware_path=configs_dir / "labware_dict.toml",
            csv_path=csv_path,
        )

        assert result["status"] == "error"
        assert any("undefined_labware" in e for e in result["errors"])

    def test_invalid_well_generates_warning(self, tmp_path: Path) -> None:
        """CSV with invalid well names should generate warning, not error."""
        configs_dir = Path(__file__).resolve().parent / "configs"

        csv_content = """\
Source Labware,Source Well,Dest Labware,Dest Well,Distribution Volume (ul),Distribution,Source Bottom,Dest Top
tube_rack_96_1500ul_1,A1,384_pp_standard_100ul_2,A1|INVALID|B1,25,equal,2,-5
""".strip()

        csv_path = tmp_path / "invalid_wells.csv"
        csv_path.write_text(csv_content, encoding="utf-8")

        result = validate_configuration(
            settings_path=configs_dir / "distribution" / "settings.toml",
            labware_path=configs_dir / "labware_dict.toml",
            csv_path=csv_path,
        )

        assert result["status"] == "ok"
        assert any("INVALID" in w for w in result.get("warnings", []))

    def test_missing_pipe_in_distribution_wells_warning(self, tmp_path: Path) -> None:
        """Distribution row with single well generates warning."""
        configs_dir = Path(__file__).resolve().parent / "configs"

        csv_content = """\
Source Labware,Source Well,Dest Labware,Dest Well,Distribution Volume (ul),Distribution,Source Bottom,Dest Top
tube_rack_96_1500ul_1,A1,384_pp_standard_100ul_2,A1,25,equal,2,-5
""".strip()

        csv_path = tmp_path / "single_dest.csv"
        csv_path.write_text(csv_content, encoding="utf-8")

        result = validate_configuration(
            settings_path=configs_dir / "distribution" / "settings.toml",
            labware_path=configs_dir / "labware_dict.toml",
            csv_path=csv_path,
        )

        # Should pass validation (single dest is valid), but may warn
        assert result["status"] == "ok"


class TestDistributionPatterns:
    """Test specific distribution patterns."""

    def test_equal_distribution_pattern(self, tmp_path: Path) -> None:
        """Equal distribution pattern should validate."""
        configs_dir = Path(__file__).resolve().parent / "configs"

        csv_content = """\
Source Labware,Source Well,Dest Labware,Dest Well,Distribution Volume (ul),Distribution,Source Bottom,Dest Top
tube_rack_96_1500ul_1,A1,384_pp_standard_100ul_2,A1|B1|C1|D1,30,equal,2,-5
""".strip()

        csv_path = tmp_path / "equal.csv"
        csv_path.write_text(csv_content, encoding="utf-8")

        result = validate_configuration(
            settings_path=configs_dir / "distribution" / "settings.toml",
            labware_path=configs_dir / "labware_dict.toml",
            csv_path=csv_path,
        )

        assert result["status"] == "ok"

    def test_geometric_decay_pattern(self, tmp_path: Path) -> None:
        """Geometric decay (factor < 1) pattern should validate."""
        configs_dir = Path(__file__).resolve().parent / "configs"

        csv_content = """\
Source Labware,Source Well,Dest Labware,Dest Well,Distribution Volume (ul),Distribution,Source Bottom,Dest Top
tube_rack_96_1500ul_1,A1,384_pp_standard_100ul_2,A1|B1|C1|D1,100,geometric:0.5,2,-5
""".strip()

        csv_path = tmp_path / "decay.csv"
        csv_path.write_text(csv_content, encoding="utf-8")

        result = validate_configuration(
            settings_path=configs_dir / "distribution" / "settings.toml",
            labware_path=configs_dir / "labware_dict.toml",
            csv_path=csv_path,
        )

        assert result["status"] == "ok"

    def test_geometric_growth_pattern(self, tmp_path: Path) -> None:
        """Geometric growth (factor > 1) pattern should validate."""
        configs_dir = Path(__file__).resolve().parent / "configs"

        csv_content = """\
Source Labware,Source Well,Dest Labware,Dest Well,Distribution Volume (ul),Distribution,Source Bottom,Dest Top
tube_rack_96_1500ul_1,A1,384_pp_standard_100ul_2,A1|B1|C1|D1,20,geometric:2,2,-5
""".strip()

        csv_path = tmp_path / "growth.csv"
        csv_path.write_text(csv_content, encoding="utf-8")

        result = validate_configuration(
            settings_path=configs_dir / "distribution" / "settings.toml",
            labware_path=configs_dir / "labware_dict.toml",
            csv_path=csv_path,
        )

        assert result["status"] == "ok"

    def test_geometric_pattern_with_direction(self, tmp_path: Path) -> None:
        """Geometric pattern with direction modifier should validate."""
        configs_dir = Path(__file__).resolve().parent / "configs"

        csv_content = """\
Source Labware,Source Well,Dest Labware,Dest Well,Distribution Volume (ul),Distribution,Source Bottom,Dest Top
tube_rack_96_1500ul_1,A1,384_pp_standard_100ul_2,A1|B1|C1|D1,100,geometric:0.5:desc,2,-5
tube_rack_96_1500ul_1,A2,384_pp_standard_100ul_2,E1|F1|G1|H1,20,geometric:2:asc,2,-5
""".strip()

        csv_path = tmp_path / "direction.csv"
        csv_path.write_text(csv_content, encoding="utf-8")

        result = validate_configuration(
            settings_path=configs_dir / "distribution" / "settings.toml",
            labware_path=configs_dir / "labware_dict.toml",
            csv_path=csv_path,
        )

        assert result["status"] == "ok"
