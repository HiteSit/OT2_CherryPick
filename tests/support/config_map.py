"""
CSV to Configuration Profile Mapping

Maps CSV files to their compatible settings.toml profiles for parametrized testing.
This module loads configuration from the unified manifest.json and provides
backward-compatible accessors for the E2E test suite.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pytest

from tests.support.fixtures import load_manifest


# ============ Manifest-Based Config Map ============

# Profiles that represent special test cases (not standard CSV + profile combos)
# These are excluded from the E2E CSV_CONFIG_MAP but included in integration tests
_SPECIAL_PROFILES = frozenset({"liquid_extreme"})

# Special CSVs that are only for error testing, not standard E2E runs
_SPECIAL_CSV_PATTERNS = frozenset({"tests/fixtures/", "invalid"})


def _is_special_entry(csv_path: str, profile: str) -> bool:
    """Check if an entry is a special test case (not for E2E CSV_CONFIG_MAP)."""
    if profile in _SPECIAL_PROFILES:
        return True
    return any(pattern in csv_path for pattern in _SPECIAL_CSV_PATTERNS)


@lru_cache(maxsize=1)
def _build_csv_config_map() -> dict[str, list[str]]:
    """Build CSV_CONFIG_MAP from unified manifest.json.

    Returns:
        Dict mapping CSV filename to list of compatible settings profiles.
        E.g., {"example_basic.csv": ["single_X1", "multi_X1"]}

    Note:
        Special test cases (liquid_extreme profile, error test CSVs) are
        excluded from this map. They are only used in integration tests.
    """
    entries = load_manifest()
    csv_profiles: dict[str, list[str]] = {}

    for entry in entries:
        # Skip special test cases
        if _is_special_entry(entry.csv_path, entry.settings_profile):
            continue

        # Extract CSV filename from path (e.g., "CSVs/example_basic.csv" -> "example_basic.csv")
        csv_name = Path(entry.csv_path).name

        if csv_name not in csv_profiles:
            csv_profiles[csv_name] = []

        if entry.settings_profile not in csv_profiles[csv_name]:
            csv_profiles[csv_name].append(entry.settings_profile)

    return csv_profiles


# For backward compatibility: expose as module-level variable
# This is dynamically computed on first access
def _get_csv_config_map() -> dict[str, list[str]]:
    """Get the CSV config map (lazy-loaded from manifest)."""
    return _build_csv_config_map()


# Create a proxy class that acts like a dict but loads lazily
class _LazyConfigMap:
    """Lazy-loading dict proxy for CSV_CONFIG_MAP.

    This allows the manifest to be loaded only when actually accessed,
    avoiding import-time file I/O.
    """

    _map: dict[str, list[str]] | None = None

    @classmethod
    def _ensure_loaded(cls) -> dict[str, list[str]]:
        if cls._map is None:
            cls._map = _build_csv_config_map()
        return cls._map

    def __getitem__(self, key: str) -> list[str]:
        return self._ensure_loaded()[key]

    def __contains__(self, key: object) -> bool:
        return key in self._ensure_loaded()

    def __iter__(self):
        return iter(self._ensure_loaded())

    def __len__(self) -> int:
        return len(self._ensure_loaded())

    def get(self, key: str, default: list[str] | None = None) -> list[str] | None:
        return self._ensure_loaded().get(key, default)

    def keys(self):
        return self._ensure_loaded().keys()

    def values(self):
        return self._ensure_loaded().values()

    def items(self):
        return self._ensure_loaded().items()

    def __repr__(self) -> str:
        return repr(self._ensure_loaded())


# Module-level variable for backward compatibility
CSV_CONFIG_MAP: dict[str, list[str]] = _LazyConfigMap()  # type: ignore[assignment]


# ============ Parametrization Helpers ============

def get_compatible_profiles(csv_name: str) -> list[str]:
    """Return list of compatible config profiles for a CSV.

    Args:
        csv_name: CSV filename (e.g., "example_basic.csv")

    Returns:
        List of compatible profile names (e.g., ["single_X1", "multi_X1"])
    """
    return CSV_CONFIG_MAP.get(csv_name) or []


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
    # Note: This is kept as static categorization since it represents
    # logical test groupings, not just CSV/profile compatibility
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
        "home_control": [
            "example_home_control.csv",
        ],
    }


__all__ = [
    "CSV_CONFIG_MAP",
    "get_compatible_profiles",
    "csv_config_combinations",
    "get_csvs_by_category",
]
