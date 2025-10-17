"""Helpers for running OT-2 protocol simulations."""

from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Mapping, MutableMapping, Sequence

from ..utils.errors import ConfigurationError, SimulationError
from ..utils.paths import resolve_project_path


def _default_runner(
    command: Sequence[str],
    *,
    env: Mapping[str, str] | None,
    timeout: int,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # type: ignore[return-value]
        command,
        capture_output=True,
        text=True,
        env=dict(env) if env is not None else None,
        timeout=timeout,
        check=False,
    )


DEFAULT_LOG_FILE = Path("logs") / "last_simulation.json"


def simulate_protocol(
    protocol_path: str | Path,
    *,
    labware_path: str | Path | None = None,
    extra_env: Mapping[str, str] | None = None,
    timeout: int = 120,
    runner: Callable[..., subprocess.CompletedProcess[str]] | None = None,
    log_file: str | Path | None = DEFAULT_LOG_FILE,
) -> dict[str, object]:
    """Run `opentrons_simulate` for the given protocol file.

    Args:
        protocol_path: Path to the protocol file to simulate.
        labware_path: Optional path to a custom labware directory. If ``None``, the
            function will look for the ``LABWARE_PATH`` environment variable.
            Must be a directory containing Opentrons JSON labware definitions, NOT a TOML file.
            If invalid or not set, simulation runs without custom labware.
        extra_env: Optional mapping of additional environment variables for the
            subprocess invocation.
        timeout: Timeout in seconds for simulation execution.
        runner: Injectable runner for testing. Defaults to ``subprocess.run``.

    Returns:
        Dictionary containing stdout/stderr/command/returncode.

    Raises:
        ConfigurationError: If inputs are missing or invalid.
        SimulationError: If the simulator returns a non-zero exit code.
    """

    protocol_file = resolve_project_path(protocol_path)
    if not protocol_file.exists():
        raise ConfigurationError(f"Protocol file not found at {protocol_file}")

    labware_dir: Path | None = None
    if labware_path is None:
        raw_labware = os.getenv("LABWARE_PATH")
        if raw_labware:
            try:
                candidate = resolve_project_path(raw_labware)
                # Validate it's a directory, not a file
                if candidate.exists() and candidate.is_dir():
                    labware_dir = candidate
            except Exception:
                # If resolution fails, skip custom labware
                pass
    else:
        try:
            candidate = resolve_project_path(labware_path)
            if candidate.exists() and candidate.is_dir():
                labware_dir = candidate
            elif candidate.exists() and not candidate.is_dir():
                raise ConfigurationError(
                    f"labware_path must be a directory containing JSON labware definitions, "
                    f"not a file: {candidate}"
                )
        except ConfigurationError:
            raise  # Re-raise explicit configuration errors
        except Exception:
            # For other errors, skip custom labware
            pass

    command: list[str] = ["opentrons_simulate"]
    if labware_dir is not None:
        command.extend(["--custom-labware", str(labware_dir)])
    command.append(str(protocol_file))

    # Always inherit current environment to ensure LABWARE_PATH and other vars are available
    env = dict(os.environ)
    if extra_env is not None:
        env.update(extra_env)

    runner_fn = runner or (lambda cmd: _default_runner(cmd, env=env, timeout=timeout))
    try:
        completed = runner_fn(command)
    except subprocess.TimeoutExpired as exc:  # pragma: no cover - defensive
        raise SimulationError(f"Simulation timed out after {timeout} seconds") from exc

    result = {
        "command": command,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "returncode": completed.returncode,
        "protocol_path": str(protocol_file),
        "labware_path": str(labware_dir) if labware_dir is not None else None,
    }

    if log_file is not None:
        _write_simulation_log(log_file, result)

    if completed.returncode != 0:
        raise SimulationError(
            "opentrons_simulate returned non-zero exit status",
        )

    return result


def _write_simulation_log(log_file: str | Path, payload: Mapping[str, object]) -> None:
    """Persist simulation details for consumption via resources."""

    log_path = resolve_project_path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    entry = dict(payload)
    entry["timestamp"] = datetime.now(timezone.utc).isoformat()

    with log_path.open("w", encoding="utf-8") as handle:
        json.dump(entry, handle, indent=2)


__all__ = ["simulate_protocol", "DEFAULT_LOG_FILE"]
