"""
E2E Test Fixtures and Configuration

This module provides pytest fixtures for end-to-end simulation testing of OT-2 protocols.
It matches CSV files with their required settings.toml configurations and runs actual
opentrons_simulate validation.
"""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest


# ============ Path Constants ============
E2E_DIR = Path(__file__).parent
CONFIGS_DIR = E2E_DIR / "configs"
PROJECT_ROOT = E2E_DIR.parent.parent
CSV_DIR = PROJECT_ROOT / "CSVs"
LABWARE_DICT_PATH = CONFIGS_DIR / "labware_dict.toml"


def _find_custom_labware_path() -> Path | None:
    """
    Find custom labware definitions directory.

    Searches in order:
    1. LABWARE_PATH environment variable
    2. Windows Opentrons App location via WSL path
    3. Linux default locations
    """
    import os

    # Check environment variable first
    env_path = os.environ.get("LABWARE_PATH")
    if env_path:
        path = Path(env_path)
        if path.exists():
            return path

    # Check common Windows locations via WSL
    windows_locations = [
        Path("/mnt/c/Users/ricca/AppData/Roaming/Opentrons/labware"),
        Path("/mnt/c/Users/*/AppData/Roaming/Opentrons/labware"),
    ]

    for location in windows_locations:
        if "*" in str(location):
            # Expand glob pattern
            import glob
            matches = glob.glob(str(location))
            for match in matches:
                match_path = Path(match)
                if match_path.exists() and match_path.is_dir():
                    return match_path
        elif location.exists() and location.is_dir():
            return location

    # Check Linux default locations
    linux_locations = [
        Path.home() / ".opentrons" / "labware",
        Path("/opt/opentrons/labware"),
    ]

    for location in linux_locations:
        if location.exists() and location.is_dir():
            return location

    return None


# Auto-detect custom labware path
CUSTOM_LABWARE_PATH = _find_custom_labware_path()


# ============ CSV → Config Mapping ============
# Maps each CSV to the list of compatible config profiles
CSV_CONFIG_MAP: dict[str, list[str]] = {
    # Basic cherry-pick CSVs work with single_X1 or multi_X1
    "example_basic.csv": ["single_X1", "multi_X1"],
    "example_basic_volumes.csv": ["single_X1"],  # Uses volumes > 300µL, needs P1000
    # example_advanced.csv has Tip Action=keep which conflicts with multi_X1's no-return-tip limitation
    "example_advanced.csv": ["single_X1"],

    # Multi mode requires full 8-channel
    "example_multi_mode.csv": ["multi"],

    # Distribution CSVs - work with multi mode ONLY if each distribution uses consistent row letters
    # (e.g., A1|A2|A3 or B1|B2|B3, NOT A1|B2|A3 which mixes interleaving patterns)
    # Both CSVs use consistent row letters per distribution, so they're multi-compatible
    "example_distribution.csv": ["multi", "single_X1", "multi_X1"],
    "example_mixed_modes.csv": ["multi", "single_X1", "multi_X1"],

    # Dual-pipette mode CSVs
    "test_dual_all_three_modes.csv": ["dual"],
    "test_dual_single_multi.csv": ["dual"],
    "test_dual_single_multi_X1.csv": ["dual"],

    # Custom deck layout
    "fill_analytics_plate.csv": ["fill_analytics"],
}


@dataclass
class SimulationResult:
    """Result of a protocol simulation."""

    success: bool
    returncode: int
    stdout: str
    stderr: str

    @property
    def output(self) -> str:
        """Combined stdout and stderr."""
        return self.stdout + self.stderr

    def assert_success(self, message: str | None = None) -> None:
        """Assert simulation was successful."""
        if not self.success:
            msg = message or "Simulation failed"
            raise AssertionError(f"{msg}:\n{self.stderr}")


@dataclass
class E2EWorkspace:
    """Isolated workspace for e2e test execution."""

    workspace_dir: Path
    settings_path: Path
    labware_dict_path: Path
    protocol_path: Path
    csv_dir: Path

    @classmethod
    def create(cls, tmp_path: Path, config_profile: str) -> "E2EWorkspace":
        """Create a new isolated workspace with the specified config profile."""
        workspace = tmp_path / "e2e_workspace"
        workspace.mkdir(exist_ok=True)

        # Copy settings.toml for the profile
        settings_src = CONFIGS_DIR / config_profile / "settings.toml"
        settings_dst = workspace / "settings.toml"
        shutil.copy2(settings_src, settings_dst)

        # Copy shared labware_dict.toml
        labware_dst = workspace / "labware_dict.toml"
        shutil.copy2(LABWARE_DICT_PATH, labware_dst)

        # Copy protocol template
        protocol_dst = workspace / "CherryPick_OT2.py"
        shutil.copy2(PROJECT_ROOT / "CherryPick_OT2.py", protocol_dst)

        # Create CSVs directory and copy all CSVs
        csv_dst = workspace / "CSVs"
        if CSV_DIR.exists():
            shutil.copytree(CSV_DIR, csv_dst)
        else:
            csv_dst.mkdir()

        return cls(
            workspace_dir=workspace,
            settings_path=settings_dst,
            labware_dict_path=labware_dst,
            protocol_path=protocol_dst,
            csv_dir=csv_dst,
        )

    def get_csv_path(self, csv_name: str) -> Path:
        """Get the path to a CSV file in the workspace."""
        return self.csv_dir / csv_name


def generate_protocol(
    workspace: E2EWorkspace,
    csv_path: Path,
    *,
    verbose: bool = False,
) -> tuple[bool, str]:
    """
    Run helper_cherry_pick.py to generate protocol from CSV.

    Returns:
        tuple: (success, output)
    """
    cmd = [
        "uv", "run", "python", str(PROJECT_ROOT / "helper_cherry_pick.py"),
        "-l", str(workspace.labware_dict_path),
        "-s", str(workspace.settings_path),
        "-c", str(csv_path),
        "-p", str(workspace.protocol_path),
    ]

    if verbose:
        cmd.append("-v")

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
        timeout=60,
    )

    success = result.returncode == 0
    output = result.stdout + result.stderr
    return success, output


def simulate_protocol(
    protocol_path: Path,
    *,
    custom_labware_path: Path | None = None,
    timeout: int = 120,
) -> SimulationResult:
    """
    Run opentrons_simulate on a protocol file.

    Returns:
        SimulationResult with success status and output
    """
    cmd = ["uv", "run", "opentrons_simulate"]

    if custom_labware_path and custom_labware_path.exists():
        cmd.extend(["--custom-labware", str(custom_labware_path)])

    cmd.append(str(protocol_path))

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
        timeout=timeout,
    )

    return SimulationResult(
        success=result.returncode == 0,
        returncode=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr,
    )


def run_full_workflow(
    workspace: E2EWorkspace,
    csv_name: str,
    *,
    custom_labware_path: Path | None = None,
) -> SimulationResult:
    """
    Execute the full workflow: generate protocol then simulate.

    Args:
        workspace: E2EWorkspace instance
        csv_name: Name of CSV file
        custom_labware_path: Optional path to custom labware definitions.
                            If None, uses auto-detected CUSTOM_LABWARE_PATH.

    Returns:
        SimulationResult from the simulation
    """
    csv_path = workspace.get_csv_path(csv_name)

    # Generate protocol
    gen_success, gen_output = generate_protocol(workspace, csv_path)
    if not gen_success:
        return SimulationResult(
            success=False,
            returncode=1,
            stdout="",
            stderr=f"Protocol generation failed:\n{gen_output}",
        )

    # Use auto-detected labware path if not provided
    labware_path = custom_labware_path if custom_labware_path is not None else CUSTOM_LABWARE_PATH

    # Simulate protocol
    return simulate_protocol(
        workspace.protocol_path,
        custom_labware_path=labware_path,
    )


# ============ Fixtures ============

@pytest.fixture(scope="session")
def project_root() -> Path:
    """Return the project root directory."""
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def csv_dir() -> Path:
    """Return the CSV directory."""
    return CSV_DIR


@pytest.fixture(scope="session")
def custom_labware_path() -> Path | None:
    """Return the custom labware path, or None if not found."""
    return CUSTOM_LABWARE_PATH


@pytest.fixture
def e2e_workspace_factory(tmp_path: Path):
    """Factory fixture to create E2E workspaces with specific config profiles."""
    def _factory(config_profile: str) -> E2EWorkspace:
        return E2EWorkspace.create(tmp_path, config_profile)
    return _factory


# Skip marker for tests requiring custom labware
requires_custom_labware = pytest.mark.skipif(
    CUSTOM_LABWARE_PATH is None,
    reason="Custom labware path not found. Set LABWARE_PATH environment variable."
)


# ============ Parametrization Helpers ============

def get_compatible_profiles(csv_name: str) -> list[str]:
    """Return list of compatible config profiles for a CSV."""
    return CSV_CONFIG_MAP.get(csv_name, [])


def csv_config_combinations() -> list[tuple[str, str]]:
    """
    Generate all (csv_name, config_profile) combinations for parametrization.

    Returns:
        List of pytest.param objects with descriptive IDs
    """
    combinations = []
    for csv_name, profiles in CSV_CONFIG_MAP.items():
        for profile in profiles:
            combinations.append(
                pytest.param(
                    csv_name,
                    profile,
                    id=f"{csv_name.replace('.csv', '')}-{profile}",
                )
            )
    return combinations


def get_csvs_by_category() -> dict[str, list[str]]:
    """
    Group CSV files by test category.

    Returns:
        Dict mapping category names to lists of CSV filenames
    """
    return {
        "basic": [
            "example_basic.csv",
            "example_basic_volumes.csv",
        ],
        "advanced": [
            "example_advanced.csv",
        ],
        "multi_channel": [
            "example_multi_mode.csv",
        ],
        "distribution": [
            "example_distribution.csv",
            "example_mixed_modes.csv",
        ],
        "dual_pipette": [
            "test_dual_all_three_modes.csv",
            "test_dual_single_multi.csv",
            "test_dual_single_multi_X1.csv",
        ],
        "real_world": [
            "fill_analytics_plate.csv",
        ],
    }
