from __future__ import annotations

import json
from pathlib import Path
from typing import Callable, List

from tests.simulation_logs.adapters import v8_7_0
from tests.simulation_logs.models import ParseResult, ParseWarning, RawEvent
from tests.simulation_logs.normalize import load_settings, normalize_events

DEFAULT_SIMULATOR_VERSION = "opentrons_simulate 8.7.0"
ADAPTERS: dict[str, Callable[[str, str], ParseResult]] = {
    "opentrons_simulate 8.7.0": v8_7_0.parse_text,
}

FIXTURE_ROOT = Path(__file__).resolve().parents[1] / "fixtures" / "simulation"
SETTINGS_ROOT = Path(__file__).resolve().parents[1] / "e2e" / "configs"


def select_adapter(metadata: dict[str, object]) -> Callable[[str, str], ParseResult]:
    version = str(metadata.get("simulator_version", "") or "")
    if not version:
        return ADAPTERS[DEFAULT_SIMULATOR_VERSION]
    if version in ADAPTERS:
        return ADAPTERS[version]
    return ADAPTERS[DEFAULT_SIMULATOR_VERSION]


def parse_fixture(fixture_id: str) -> ParseResult:
    fixture_dir = FIXTURE_ROOT / fixture_id
    metadata_path = fixture_dir / "metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

    warnings: List[ParseWarning] = []
    version = str(metadata.get("simulator_version", "") or "")
    if version and version not in ADAPTERS:
        warnings.append(
            ParseWarning(line=0, reason=f"Unknown simulator_version: {version}")
        )
        return ParseResult(events=[], warnings=warnings)

    adapter = select_adapter(metadata)

    stdout_path = fixture_dir / "stdout.txt"
    stderr_path = fixture_dir / "stderr.txt"
    stdout_text = stdout_path.read_text(encoding="utf-8") if stdout_path.exists() else ""
    stderr_text = stderr_path.read_text(encoding="utf-8") if stderr_path.exists() else ""

    stdout_result = adapter(stdout_text, source="stdout")
    stderr_result = adapter(stderr_text, source="stderr")

    raw_events: List[RawEvent] = [*stdout_result.events, *stderr_result.events]
    warnings.extend(stdout_result.warnings)
    warnings.extend(stderr_result.warnings)

    settings_profile = metadata.get("settings_profile")
    if not settings_profile:
        raise ValueError(f"Fixture metadata missing settings_profile: {fixture_id}")

    settings_path = SETTINGS_ROOT / str(settings_profile) / "settings.toml"
    settings = load_settings(settings_path)
    normalized = normalize_events(raw_events, settings)

    return ParseResult(events=normalized, warnings=warnings)
