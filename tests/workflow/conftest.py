"""Workflow test configuration and fixtures.

This module provides pytest configuration and fixtures specific to the
unified workflow tests in tests/workflow/.
"""

from __future__ import annotations

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
from tests.support.fixtures import (
    FixtureEntry,
    load_manifest,
    load_fixtures_with_baselines,
)


# Re-export for backward compatibility and convenience
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
    # From fixtures module
    "FixtureEntry",
    "load_manifest",
    "load_fixtures_with_baselines",
]


# Note: The main test fixture (workflow_workspace) is defined in
# test_protocol_workflow.py to keep all test logic in one file.
