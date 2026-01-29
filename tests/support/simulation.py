"""Shared parser setup and fixture normalization helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from tests.unit.simulation_logs import expectations as expectations_module
from tests.unit.simulation_logs.expectations import ExpectedTransfer
from tests.unit.simulation_logs import parse as parse_module
from tests.unit.simulation_logs.models import ParseResult
from tests.unit.simulation_logs.normalize import load_settings
from tests.support import fixtures as fixtures_module
from tests.support import paths as support_paths

FixtureEntry = fixtures_module.FixtureEntry


def load_settings_profile(profile: str) -> dict:
    settings_path = support_paths.settings_profile_path(profile)
    return load_settings(settings_path)


def resolve_fixture_csv(entry: FixtureEntry) -> Path:
    return support_paths.repo_root() / entry.csv_path


def build_expected_transfers_for_entry(entry: FixtureEntry) -> Sequence[ExpectedTransfer]:
    csv_path = resolve_fixture_csv(entry)
    settings = load_settings_profile(entry.settings_profile)
    return expectations_module.build_expected_transfers(csv_path, settings)


def parse_fixture_entry(entry: FixtureEntry) -> ParseResult:
    return parse_module.parse_fixture(entry.fixture_id)


def build_fixture_context(
    entry: FixtureEntry,
) -> tuple[Sequence[ExpectedTransfer], ParseResult, Path, dict]:
    expected_transfers = build_expected_transfers_for_entry(entry)
    parsed_result = parse_fixture_entry(entry)
    csv_path = resolve_fixture_csv(entry)
    settings = load_settings_profile(entry.settings_profile)
    return expected_transfers, parsed_result, csv_path, settings


__all__ = [
    "build_expected_transfers_for_entry",
    "build_fixture_context",
    "load_settings_profile",
    "parse_fixture_entry",
    "resolve_fixture_csv",
]
