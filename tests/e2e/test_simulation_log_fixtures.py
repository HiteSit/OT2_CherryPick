"""Baseline fixture capture for opentrons_simulate logs."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

import pytest

from tests.fixtures.simulation import FixtureEntry, capture_fixture, load_manifest


pytestmark = [pytest.mark.requires_simulation, pytest.mark.pipeline_test]

FIXTURES_ROOT = Path(__file__).resolve().parents[1] / "fixtures" / "simulation"


def _load_fixture_outputs(entry: FixtureEntry) -> tuple[str, str, dict[str, object]]:
    fixture_dir = FIXTURES_ROOT / entry.fixture_id
    stdout_path = fixture_dir / "stdout.txt"
    stderr_path = fixture_dir / "stderr.txt"
    metadata_path = fixture_dir / "metadata.json"

    refresh = bool(os.environ.get("OT2_REFRESH_SIM_FIXTURES"))
    if not refresh and stdout_path.exists() and stderr_path.exists() and metadata_path.exists():
        return (
            stdout_path.read_text(encoding="utf-8"),
            stderr_path.read_text(encoding="utf-8"),
            json.loads(metadata_path.read_text(encoding="utf-8")),
        )

    capture_fixture(entry)
    return (
        stdout_path.read_text(encoding="utf-8"),
        stderr_path.read_text(encoding="utf-8"),
        json.loads(metadata_path.read_text(encoding="utf-8")),
    )


def _excerpt(text: str, *, max_lines: int = 20, max_chars: int = 800) -> str:
    lines = text.splitlines()
    excerpt = "\n".join(lines[:max_lines])
    if len(excerpt) > max_chars:
        return excerpt[:max_chars] + "..."
    return excerpt


def _assert_no_markers(entry: FixtureEntry, label: str, output: str) -> None:
    if re.search(r"\b(warning|error)\b", output, re.IGNORECASE):
        raise AssertionError(
            f"{entry.fixture_id} {label} contains warning/error output:\n"
            f"{_excerpt(output)}"
        )


@pytest.mark.parametrize("entry", load_manifest(), ids=lambda entry: entry.fixture_id)
def test_simulation_log_fixtures(entry: FixtureEntry) -> None:
    stdout, stderr, metadata = _load_fixture_outputs(entry)
    returncode = metadata.get("returncode")

    if entry.expect_failure:
        assert returncode != 0, (
            f"{entry.fixture_id} expected failure but returned success.\n"
            f"stdout:\n{_excerpt(stdout)}\n"
            f"stderr:\n{_excerpt(stderr)}"
        )
        return

    assert returncode == 0, (
        f"{entry.fixture_id} simulation failed with return code {returncode}.\n"
        f"stdout:\n{_excerpt(stdout)}\n"
        f"stderr:\n{_excerpt(stderr)}"
    )
    _assert_no_markers(entry, "stdout", stdout)
    _assert_no_markers(entry, "stderr", stderr)
