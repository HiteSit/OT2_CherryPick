"""Shared test support utilities."""

# Re-export commonly used items for convenience
from tests.support.paths import (
    repo_root,
    tests_root,
    simulation_fixtures_root,
    simulation_manifest_path,
    settings_profiles_root,
    settings_profile_path,
)

from tests.support.workspace import (
    PROJECT_ROOT,
    E2E_DIR,
    CONFIGS_DIR,
    CSV_DIR,
    LABWARE_DICT_PATH,
    CUSTOM_LABWARE_PATH,
    SimulationResult,
    E2EWorkspace,
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

__all__ = [
    # paths
    "repo_root",
    "tests_root",
    "simulation_fixtures_root",
    "simulation_manifest_path",
    "settings_profiles_root",
    "settings_profile_path",
    # workspace
    "PROJECT_ROOT",
    "E2E_DIR",
    "CONFIGS_DIR",
    "CSV_DIR",
    "LABWARE_DICT_PATH",
    "CUSTOM_LABWARE_PATH",
    "SimulationResult",
    "E2EWorkspace",
    "generate_protocol",
    "simulate_protocol",
    "run_full_workflow",
    # config_map
    "CSV_CONFIG_MAP",
    "get_compatible_profiles",
    "csv_config_combinations",
    "get_csvs_by_category",
]
