"""Shared filesystem path helpers for tests."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def repo_root() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "pyproject.toml").exists():
            return parent
    raise FileNotFoundError("Unable to locate repo root (pyproject.toml not found)")


def tests_root() -> Path:
    return repo_root() / "tests"


def simulation_fixtures_root() -> Path:
    return tests_root() / "integration" / "simulation_logs" / "fixtures"


def simulation_manifest_path() -> Path:
    """Return path to unified manifest.json in tests/support/.

    This is the single source of truth for all test scenario definitions.
    The legacy manifest at integration/simulation_logs/fixtures/manifest.json
    is no longer used.
    """
    return tests_root() / "support" / "manifest.json"


def simulation_baselines_root() -> Path:
    """Return path to captured simulation baseline fixtures.

    Baselines (stdout.txt, stderr.txt, metadata.json) are stored here.
    Only fixtures with has_baseline=true in manifest.json have baselines.
    """
    return tests_root() / "integration" / "simulation_logs" / "fixtures"


def settings_profiles_root() -> Path:
    return tests_root() / "e2e" / "configs"


def settings_profile_path(profile: str) -> Path:
    return settings_profiles_root() / profile / "settings.toml"
