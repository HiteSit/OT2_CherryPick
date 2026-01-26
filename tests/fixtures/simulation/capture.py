"""
Simulation fixture capture helpers.

Captures stdout/stderr from simulate_protocol.sh runs and stores metadata
for repeatable test baselines.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class FixtureEntry:
    fixture_id: str
    csv_path: str
    settings_profile: str
    expect_failure: bool


FIXTURES_DIR = Path(__file__).resolve().parent
MANIFEST_PATH = FIXTURES_DIR / "manifest.json"


def _find_repo_root() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "pyproject.toml").exists():
            return parent
    raise FileNotFoundError("Unable to locate repo root (pyproject.toml not found)")


def load_manifest(path: Path = MANIFEST_PATH) -> list[FixtureEntry]:
    data = json.loads(path.read_text(encoding="utf-8"))
    fixtures = data.get("fixtures", [])
    if not isinstance(fixtures, list):
        raise ValueError("Manifest must contain a list under 'fixtures'")
    entries: list[FixtureEntry] = []
    for item in fixtures:
        entries.append(
            FixtureEntry(
                fixture_id=item["fixture_id"],
                csv_path=item["csv_path"],
                settings_profile=item["settings_profile"],
                expect_failure=bool(item["expect_failure"]),
            )
        )
    return entries


def _parse_machine_config(script_text: str) -> str:
    match = re.search(r'^MACHINE_CONFIG="(?P<config>[^"]+)"', script_text, re.MULTILINE)
    if not match:
        raise ValueError("simulate_protocol.sh missing MACHINE_CONFIG")
    return match.group("config")


def _parse_labware_path_win(script_text: str, machine_config: str) -> str:
    in_case = False
    in_block = False
    for line in script_text.splitlines():
        stripped = line.strip()
        if stripped.startswith('case "$MACHINE_CONFIG" in'):
            in_case = True
            continue
        if in_case:
            if re.match(rf'^"?{re.escape(machine_config)}"?\)', stripped):
                in_block = True
                continue
            if in_block and stripped.startswith("LABWARE_PATH_WIN="):
                value = stripped.split("=", 1)[1].strip().strip('"')
                return value
            if in_block and stripped.startswith(";;"):
                in_block = False
    raise ValueError(f"LABWARE_PATH_WIN not found for machine config '{machine_config}'")


def _resolve_labware_path(simulate_script: Path) -> tuple[str, Path]:
    script_text = simulate_script.read_text(encoding="utf-8")
    machine_config = _parse_machine_config(script_text)
    labware_path_win = _parse_labware_path_win(script_text, machine_config)
    override = os.environ.get("LABWARE_PATH_WIN_OVERRIDE")
    if override:
        labware_path_win = override
    labware_path = _convert_windows_path(labware_path_win)
    return labware_path_win, labware_path


def _convert_windows_path(path_value: str) -> Path:
    if shutil.which("wslpath"):
        result = subprocess.run(
            ["wslpath", path_value],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            return Path(result.stdout.strip())
    match = re.match(r"^([A-Za-z]):\\", path_value)
    if match:
        drive = match.group(1).lower()
        path_value = f"/mnt/{drive}/" + path_value[3:]
    return Path(path_value.replace("\\", "/"))


def _validate_labware_path(labware_path: Path) -> None:
    if not labware_path.exists() or not labware_path.is_dir():
        raise FileNotFoundError(f"Labware directory not found: {labware_path}")
    if not any(labware_path.glob("*.json")):
        raise FileNotFoundError(
            f"Labware directory contains no JSON files: {labware_path}"
        )


def _get_simulator_version() -> str:
    result = subprocess.run(
        ["opentrons_simulate", "-v"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"opentrons_simulate -v failed: {result.stderr.strip()}")
    return result.stdout.strip()


@contextmanager
def swap_settings_profile(repo_root: Path, profile: str) -> Iterable[None]:
    settings_path = repo_root / "settings.toml"
    profile_path = repo_root / "tests" / "e2e" / "configs" / profile / "settings.toml"
    if not profile_path.exists():
        raise FileNotFoundError(f"Settings profile not found: {profile_path}")
    if not settings_path.exists():
        raise FileNotFoundError(f"settings.toml not found: {settings_path}")

    backup_path = settings_path.with_suffix(".toml.backup")
    shutil.copy2(settings_path, backup_path)
    shutil.copy2(profile_path, settings_path)
    try:
        yield
    finally:
        shutil.copy2(backup_path, settings_path)
        backup_path.unlink(missing_ok=True)


def capture_fixture(entry: FixtureEntry) -> Path:
    repo_root = _find_repo_root()
    simulate_script = repo_root / "simulate_protocol.sh"
    csv_path = repo_root / entry.csv_path
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    labware_path_win, labware_path = _resolve_labware_path(simulate_script)
    _validate_labware_path(labware_path)
    simulator_version = _get_simulator_version()

    fixture_dir = FIXTURES_DIR / entry.fixture_id
    fixture_dir.mkdir(parents=True, exist_ok=True)
    stdout_path = fixture_dir / "stdout.txt"
    stderr_path = fixture_dir / "stderr.txt"
    metadata_path = fixture_dir / "metadata.json"

    command = ["bash", "simulate_protocol.sh", str(csv_path)]
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    stdout = ""
    stderr = ""
    returncode: int | None = None
    error_message: str | None = None

    try:
        with swap_settings_profile(repo_root, entry.settings_profile):
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                cwd=repo_root,
            )
        stdout = result.stdout
        stderr = result.stderr
        returncode = result.returncode
    except Exception as exc:
        error_message = str(exc)
        stderr = (stderr + "\n" + error_message).strip()
    finally:
        stdout_path.write_text(stdout, encoding="utf-8")
        stderr_path.write_text(stderr, encoding="utf-8")
        metadata = {
            "fixture_id": entry.fixture_id,
            "csv": entry.csv_path,
            "settings_profile": entry.settings_profile,
            "simulator_version": simulator_version,
            "labware_path": str(labware_path),
            "labware_path_win": labware_path_win,
            "command": command,
            "returncode": returncode,
            "timestamp": timestamp,
        }
        if error_message:
            metadata["error"] = error_message
        metadata_path.write_text(
            json.dumps(metadata, indent=2, ensure_ascii=True),
            encoding="utf-8",
        )

    if error_message:
        raise RuntimeError(error_message)

    return fixture_dir
