"""Shared test support utilities."""

# Re-export commonly used items for convenience
from tests.support.paths import (
    repo_root,
    tests_root,
    simulation_fixtures_root,  # Legacy alias, use simulation_baselines_root
    simulation_baselines_root,
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

from tests.support.fixtures import (
    FixtureEntry,
    load_manifest,
    load_fixtures_with_baselines,
    load_fixture_metadata,
    assert_settings_profile_parity,
    capture_fixture,
    swap_settings_profile,
)

from tests.support.simulation import (
    build_expected_transfers_for_entry,
    build_fixture_context,
    load_settings_profile,
    parse_fixture_entry,
    resolve_fixture_csv,
)

__all__ = [
    # paths
    "repo_root",
    "tests_root",
    "simulation_fixtures_root",  # Legacy alias
    "simulation_baselines_root",
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
    # fixtures
    "FixtureEntry",
    "load_manifest",
    "load_fixtures_with_baselines",
    "load_fixture_metadata",
    "assert_settings_profile_parity",
    "capture_fixture",
    "swap_settings_profile",
    # simulation
    "build_expected_transfers_for_entry",
    "build_fixture_context",
    "load_settings_profile",
    "parse_fixture_entry",
    "resolve_fixture_csv",
]
