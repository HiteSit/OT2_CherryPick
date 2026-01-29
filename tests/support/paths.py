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
    return simulation_fixtures_root() / "manifest.json"


def settings_profiles_root() -> Path:
    return tests_root() / "e2e" / "configs"


def settings_profile_path(profile: str) -> Path:
    return settings_profiles_root() / profile / "settings.toml"
