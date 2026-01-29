"""
E2E Test Fixtures and Configuration

This module provides pytest fixtures for end-to-end simulation testing of OT-2 protocols.
It matches CSV files with their required settings.toml configurations and runs actual
opentrons_simulate validation.
"""

from __future__ import annotations

from pathlib import Path

import pytest

# Import shared utilities from support modules
from tests.support.workspace import (
    PROJECT_ROOT,
    CSV_DIR,
    CUSTOM_LABWARE_PATH,
    E2EWorkspace,
    SimulationResult,
    generate_protocol,
    simulate_protocol,
    run_full_workflow,
)
from tests.support.config_map import (
    CSV_CONFIG_MAP,
    get_compatible_profiles,
    csv_config_combinations,
    get_csvs_by_category,
)


# Re-export for backward compatibility
__all__ = [
    # From workspace module
    "PROJECT_ROOT",
    "CSV_DIR",
    "CUSTOM_LABWARE_PATH",
    "E2EWorkspace",
    "SimulationResult",
    "generate_protocol",
    "simulate_protocol",
    "run_full_workflow",
    # From config_map module
    "CSV_CONFIG_MAP",
    "get_compatible_profiles",
    "csv_config_combinations",
    "get_csvs_by_category",
    # Fixtures
    "project_root",
    "csv_dir",
    "custom_labware_path",
    "e2e_workspace_factory",
    "requires_custom_labware",
]


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
