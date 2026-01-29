"""
CSV to Configuration Profile Mapping

Maps CSV files to their compatible settings.toml profiles for parametrized testing.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pytest


# ============ CSV -> Config Mapping ============
# Maps each CSV to the list of compatible config profiles
CSV_CONFIG_MAP: dict[str, list[str]] = {
    # Basic cherry-pick CSVs work with single_X1 or multi_X1
    "example_basic.csv": ["single_X1", "multi_X1"],
    "example_basic_volumes.csv": ["single_X1"],  # Uses volumes > 300uL, needs P1000
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

    # HOME control row feature
    "example_home_control.csv": ["single_X1", "multi_X1"],
}


# ============ Parametrization Helpers ============

def get_compatible_profiles(csv_name: str) -> list[str]:
    """Return list of compatible config profiles for a CSV."""
    return CSV_CONFIG_MAP.get(csv_name, [])


def csv_config_combinations() -> list:
    """
    Generate all (csv_name, config_profile) combinations for parametrization.

    Returns:
        List of pytest.param objects with descriptive IDs
    """
    import pytest

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


__all__ = [
    "CSV_CONFIG_MAP",
    "get_compatible_profiles",
    "csv_config_combinations",
    "get_csvs_by_category",
]
