"""
E2E Workspace and Simulation Helpers

Provides isolated workspace management and protocol simulation utilities
for end-to-end testing of OT-2 protocols.
"""

from __future__ import annotations

import glob
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from ot2_cherrypick_mcp.core.protocol_generator import generate_protocol as generate_protocol_core


# ============ Path Constants ============

def _find_project_root() -> Path:
    """Find project root by looking for pyproject.toml."""
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "pyproject.toml").exists():
            return parent
    raise FileNotFoundError("Unable to locate repo root (pyproject.toml not found)")


PROJECT_ROOT = _find_project_root()
E2E_DIR = PROJECT_ROOT / "tests" / "e2e"
CONFIGS_DIR = E2E_DIR / "configs"
CSV_DIR = PROJECT_ROOT / "CSVs"
LABWARE_DICT_PATH = CONFIGS_DIR / "labware_dict.toml"


def _find_custom_labware_path() -> Path | None:
    """
    Find custom labware definitions directory.

    Searches in order:
    1. OPENTRONS_DIR environment variable (appends /labware)
    2. LABWARE_PATH environment variable (legacy fallback)
    3. Windows Opentrons App location via WSL path
    4. Linux default locations
    """
    # Check OPENTRONS_DIR first (new canonical env var)
    opentrons_dir = os.environ.get("OPENTRONS_DIR")
    if opentrons_dir:
        path = Path(opentrons_dir) / "labware"
        if path.exists():
            return path

    # Legacy fallback
    env_path = os.environ.get("LABWARE_PATH")
    if env_path:
        path = Path(env_path)
        if path.exists():
            return path

    # Check common Windows locations via WSL
    windows_locations = [
        Path("/mnt/c/Users/*/AppData/Roaming/Opentrons/labware"),
    ]

    for location in windows_locations:
        if "*" in str(location):
            # Expand glob pattern
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


# ============ Data Classes ============

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


# ============ Workflow Functions ============

def generate_protocol(
    workspace: E2EWorkspace,
    csv_path: Path,
    *,
    verbose: bool = False,
) -> tuple[bool, str]:
    """
    Generate protocol from CSV using the same core path as the app.

    Returns:
        tuple: (success, output)
    """
    try:
        result = generate_protocol_core(
            str(workspace.labware_dict_path),
            str(workspace.settings_path),
            str(csv_path),
            str(workspace.protocol_path),
            verbose=verbose,
        )
    except Exception as exc:
        return False, str(exc)

    return True, str(result)


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


__all__ = [
    # Path constants
    "PROJECT_ROOT",
    "E2E_DIR",
    "CONFIGS_DIR",
    "CSV_DIR",
    "LABWARE_DICT_PATH",
    "CUSTOM_LABWARE_PATH",
    # Data classes
    "SimulationResult",
    "E2EWorkspace",
    # Functions
    "generate_protocol",
    "simulate_protocol",
    "run_full_workflow",
]
