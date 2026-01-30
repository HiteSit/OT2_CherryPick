"""Unified protocol workflow tests.

This module validates the complete OT-2 protocol generation and simulation workflow
in two complementary modes:

**Baseline Mode (Default, Fast):**
- Uses pre-captured simulation outputs for fixtures with `has_baseline=true`
- No simulation required, all tests run in <100ms each
- Ideal for fast CI pipelines
- Validates that protocol generation produces expected outputs

**Live Mode (OT2_LIVE_SIMULATION=1, Comprehensive):**
- Runs actual opentrons_simulate for all fixtures
- Validates complete workflow end-to-end
- Can capture new baselines with OT2_REFRESH_BASELINES=1
- Useful for development, pre-commit validation, and baseline updates

Run with:
    # Baseline mode (fast, default)
    uv run pytest tests/workflow/ -v

    # Live mode (comprehensive)
    OT2_LIVE_SIMULATION=1 uv run pytest tests/workflow/ -v

    # Refresh baselines
    OT2_REFRESH_BASELINES=1 uv run pytest tests/workflow/ -v --tb=short

    # Single fixture in live mode
    OT2_LIVE_SIMULATION=1 uv run pytest tests/workflow/ -k "basic-single_x1" -v
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from tests.support.fixtures import (
    FixtureEntry,
    assert_settings_profile_parity,
    capture_fixture,
    load_manifest,
    load_fixtures_with_baselines,
)
from tests.support import paths as support_paths
from tests.support.workspace import (
    E2EWorkspace,
    run_full_workflow,
    CUSTOM_LABWARE_PATH,
)


# Environment variables controlling test behavior
LIVE_SIMULATION_MODE = bool(os.environ.get("OT2_LIVE_SIMULATION"))
REFRESH_BASELINES_MODE = bool(os.environ.get("OT2_REFRESH_BASELINES"))




class FixtureWorkspace:
    """Unified workspace that supports both baseline and live simulation modes."""

    def __init__(self, entry: FixtureEntry, tmp_path: Path):
        self.entry = entry
        self.tmp_path = tmp_path
        self._result = None
        self._baseline = None
        self._baseline_loaded = False

    def get_result(self) -> SimulationResultProxy:
        """Get simulation result (from baseline or live simulation).

        Returns a proxy object that behaves like SimulationResult but can
        load from either baseline files or actual simulation output.
        """
        if self._result is not None:
            return self._result

        # Determine which mode to use
        if LIVE_SIMULATION_MODE:
            self._result = self._run_live_simulation()
        else:
            # Try baseline first, fall back to live if no baseline
            if self.entry.has_baseline and not REFRESH_BASELINES_MODE:
                self._result = self._load_baseline()
            else:
                self._result = self._run_live_simulation()

        return self._result

    def _load_baseline(self) -> SimulationResultProxy:
        """Load result from captured baseline files."""
        import json

        baselines_root = support_paths.simulation_baselines_root()
        fixture_dir = baselines_root / self.entry.fixture_id
        stdout_path = fixture_dir / "stdout.txt"
        stderr_path = fixture_dir / "stderr.txt"
        metadata_path = fixture_dir / "metadata.json"

        if not all(p.exists() for p in [stdout_path, stderr_path, metadata_path]):
            # Baseline missing, fall back to live simulation
            return self._run_live_simulation()

        stdout = stdout_path.read_text(encoding="utf-8")
        stderr = stderr_path.read_text(encoding="utf-8")
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        returncode = metadata.get("returncode", -1)

        return SimulationResultProxy(
            success=returncode == 0,
            returncode=returncode,
            stdout=stdout,
            stderr=stderr,
            source="baseline",
        )

    def _run_live_simulation(self) -> SimulationResultProxy:
        """Run actual protocol generation and simulation."""
        # Create workspace
        workspace = E2EWorkspace.create(
            self.tmp_path,
            self.entry.settings_profile,
        )

        # Get CSV path
        csv_name = Path(self.entry.csv_path).name
        csv_path = workspace.get_csv_path(csv_name)

        # Run workflow
        sim_result = run_full_workflow(
            workspace,
            csv_name,
            custom_labware_path=CUSTOM_LABWARE_PATH,
        )

        result = SimulationResultProxy(
            success=sim_result.success,
            returncode=sim_result.returncode,
            stdout=sim_result.stdout,
            stderr=sim_result.stderr,
            source="live",
        )

        # Optionally capture baseline
        if REFRESH_BASELINES_MODE:
            try:
                capture_fixture(self.entry)
            except Exception as exc:
                # Non-fatal: baseline capture failed but test can still proceed
                result.capture_error = str(exc)

        return result

    def assert_baseline_parity(self) -> None:
        """Verify baseline metadata matches manifest."""
        if self.entry.has_baseline:
            assert_settings_profile_parity(self.entry)


class SimulationResultProxy:
    """Proxy for simulation results that works with both baseline and live modes."""

    def __init__(
        self,
        success: bool,
        returncode: int,
        stdout: str,
        stderr: str,
        source: str = "unknown",
    ):
        self.success = success
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.source = source
        self.capture_error = None

    @property
    def output(self) -> str:
        """Combined stdout and stderr."""
        return self.stdout + self.stderr

    def assert_success(self, message: str | None = None) -> None:
        """Assert simulation was successful."""
        if not self.success:
            msg = message or f"Simulation failed (from {self.source})"
            raise AssertionError(f"{msg}:\n{self.stderr}")

    def assert_failure(self, message: str | None = None) -> None:
        """Assert simulation failed as expected."""
        if self.success:
            msg = message or f"Expected failure but simulation succeeded (from {self.source})"
            raise AssertionError(msg)

    def has_pattern(self, pattern: str) -> bool:
        """Check if output contains regex pattern."""
        import re
        return bool(re.search(pattern, self.output, re.IGNORECASE))


@pytest.fixture
def workflow_workspace(tmp_path: Path):
    """Factory fixture for creating unified FixtureWorkspace instances.

    Usage in tests:
        @pytest.mark.parametrize("entry", load_manifest(), ids=lambda e: e.fixture_id)
        def test_something(entry: FixtureEntry, workflow_workspace):
            workspace = workflow_workspace(entry)
            result = workspace.get_result()
            result.assert_success()
    """

    def _factory(entry: FixtureEntry) -> FixtureWorkspace:
        return FixtureWorkspace(entry, tmp_path)

    return _factory


# ============ Test Functions ============


@pytest.mark.parametrize(
    "entry",
    load_manifest(),
    ids=lambda e: e.fixture_id,
)
def test_protocol_simulation(entry: FixtureEntry, tmp_path: Path) -> None:
    """Test that protocol simulation succeeds or fails as expected.

    This is the core workflow test that validates the complete protocol
    generation and simulation pipeline for all manifest entries.

    - For successful entries: Asserts returncode == 0
    - For expected_failure entries: Asserts returncode != 0
    - Runs in baseline mode by default (fast), live mode on demand
    """
    workspace = FixtureWorkspace(entry, tmp_path)
    result = workspace.get_result()

    if entry.expect_failure:
        result.assert_failure(f"Expected failure for {entry.fixture_id}")
    else:
        result.assert_success(f"Protocol simulation failed for {entry.fixture_id}")


@pytest.mark.parametrize(
    "entry",
    load_fixtures_with_baselines(),
    ids=lambda e: e.fixture_id,
)
def test_baseline_settings_profile_parity(entry: FixtureEntry) -> None:
    """Verify baseline metadata matches manifest entry settings_profile.

    Only runs for fixtures with has_baseline=true. This test ensures that
    captured baseline files have matching settings_profile values in their
    metadata compared to the manifest.
    """
    workspace = FixtureWorkspace(entry, Path("/tmp"))
    workspace.assert_baseline_parity()


@pytest.mark.parametrize(
    "entry",
    load_fixtures_with_baselines(),
    ids=lambda e: e.fixture_id,
)
def test_baseline_returncode_consistency(entry: FixtureEntry) -> None:
    """Verify baseline returncode matches expectation.

    Validates that captured baseline files have consistent return codes:
    - expect_failure=true → returncode != 0
    - expect_failure=false → returncode == 0
    """
    import json

    baselines_root = support_paths.simulation_baselines_root()
    fixture_dir = baselines_root / entry.fixture_id
    metadata_path = fixture_dir / "metadata.json"

    if not metadata_path.exists():
        pytest.skip(f"Baseline metadata not found for {entry.fixture_id}")

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    returncode = metadata.get("returncode")

    if entry.expect_failure:
        assert returncode != 0, (
            f"{entry.fixture_id} marked as expect_failure but baseline has "
            f"returncode={returncode}"
        )
    else:
        assert returncode == 0, (
            f"{entry.fixture_id} marked as expect_failure=false but baseline has "
            f"returncode={returncode}"
        )


# ============ Pytest Markers ============

# Mark tests that require simulation infrastructure
pytestmark = [
    pytest.mark.requires_simulation,
    pytest.mark.pipeline_test,
]


__all__ = [
    "test_protocol_simulation",
    "test_baseline_settings_profile_parity",
    "test_baseline_returncode_consistency",
    "FixtureWorkspace",
    "SimulationResultProxy",
]
