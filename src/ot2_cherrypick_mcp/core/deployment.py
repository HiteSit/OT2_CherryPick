"""Helpers for deploying generated protocols."""

from __future__ import annotations

import glob
import logging
import shutil
import subprocess
import time
import uuid
from pathlib import Path
from typing import Callable, Sequence

from ..utils.errors import ConfigurationError, DeploymentError
from ..utils.paths import resolve_project_path

DEFAULT_CLIP_COMMAND = ["/mnt/c/Windows/System32/clip.exe"]

__all__ = ["deploy_protocol", "deploy_to_opentrons_dir", "DEFAULT_CLIP_COMMAND"]

logger = logging.getLogger(__name__)


def _find_opentrons_python() -> str | None:
    """Discover the pipx-managed Python interpreter for the opentrons package.

    Strategy: locate the ``opentrons_simulate`` script via ``shutil.which``,
    then read its shebang line to find the Python interpreter.  Falls back to
    well-known pipx virtual-environment paths if the shebang approach fails.

    Returns:
        Absolute path to the Python interpreter, or ``None`` if it cannot be
        determined.
    """
    simulate_path = shutil.which("opentrons_simulate")
    if simulate_path is not None:
        try:
            with open(simulate_path, "r", encoding="utf-8") as fh:
                first_line = fh.readline().strip()
            if first_line.startswith("#!"):
                python_path = first_line[2:].strip()
                if Path(python_path).is_file():
                    return python_path
        except OSError:
            pass

    # Fallback: check common pipx virtual-environment locations.
    candidates = [
        Path.home() / ".local" / "pipx" / "venvs" / "opentrons" / "bin" / "python",
        Path("/root/.local/pipx/venvs/opentrons/bin/python"),
    ]
    for candidate in candidates:
        if candidate.is_file():
            return str(candidate)

    return None


def _run_protocol_analysis(
    protocol_path: Path,
    analysis_dir: Path,
    labware_dir: Path | None,
    *,
    timeout: int = 120,
) -> str | None:
    """Run ``opentrons.cli analyze`` to produce the analysis JSON.

    Args:
        protocol_path: Absolute path to the deployed protocol file.
        analysis_dir: Directory where the analysis JSON should be written.
        labware_dir: Directory containing custom labware ``.json`` files.
            If ``None`` or non-existent, no labware files are passed.
        timeout: Maximum seconds to wait for the analysis subprocess.

    Returns:
        The absolute path to the generated analysis JSON file, or ``None``
        if the analysis could not be completed.
    """
    python_exe = _find_opentrons_python()
    if python_exe is None:
        logger.warning(
            "Could not locate the pipx opentrons Python interpreter; "
            "skipping protocol analysis."
        )
        return None

    timestamp_ms = int(time.time() * 1000)
    output_file = analysis_dir / f"{timestamp_ms}.json"

    cmd: list[str] = [
        python_exe,
        "-m",
        "opentrons.cli",
        "analyze",
        f"--json-output={output_file}",
        str(protocol_path),
    ]

    # Append custom labware JSON files as positional arguments.
    if labware_dir is not None and labware_dir.is_dir():
        labware_files = sorted(glob.glob(str(labware_dir / "*.json")))
        cmd.extend(labware_files)

    logger.info("Running protocol analysis: %s", " ".join(cmd))

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )
        if result.returncode != 0:
            logger.warning(
                "Protocol analysis exited with code %d.\nstdout: %s\nstderr: %s",
                result.returncode,
                result.stdout,
                result.stderr,
            )
            return None
    except subprocess.TimeoutExpired:
        logger.warning(
            "Protocol analysis timed out after %d seconds.", timeout
        )
        return None
    except OSError as exc:
        logger.warning("Failed to run protocol analysis: %s", exc)
        return None

    if output_file.is_file():
        logger.info("Analysis written to %s", output_file)
        return str(output_file)

    logger.warning("Analysis command succeeded but output file not found: %s", output_file)
    return None


def deploy_protocol(
    protocol_path: str | Path,
    *,
    target_path: str | Path | None = None,
    copy_to_clipboard: bool = False,
    clipboard_command: Sequence[str] | None = DEFAULT_CLIP_COMMAND,
    clipboard_runner: ClipboardRunner | None = None,
) -> dict[str, object]:
    """Deploy the compiled protocol by copying and/or putting it on the clipboard."""

    protocol_file = resolve_project_path(protocol_path)
    if not protocol_file.exists():
        raise ConfigurationError(f"Protocol file not found at {protocol_file}")

    copies: list[str] = []
    if target_path is not None:
        destination = _resolve_destination(target_path, protocol_file.name)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(protocol_file, destination)
        copies.append(str(destination))

    clipboard_result: dict[str, object] | None = None
    if copy_to_clipboard:
        clipboard_result = _send_to_clipboard(
            protocol_file=protocol_file,
            command=clipboard_command,
            runner=clipboard_runner,
        )

    return {
        "protocol_file": str(protocol_file),
        "copies": copies,
        "clipboard": clipboard_result,
    }


def deploy_to_opentrons_dir(
    protocol_path: str | Path,
    opentrons_dir: str | Path,
    *,
    copy_to_clipboard: bool = False,
    clipboard_command: Sequence[str] | None = DEFAULT_CLIP_COMMAND,
    clipboard_runner: ClipboardRunner | None = None,
) -> dict[str, object]:
    """Deploy the protocol into a new UUID-based folder under the Opentrons directory.

    Creates ``{opentrons_dir}/protocols/{uuid}/src/`` and
    ``{opentrons_dir}/protocols/{uuid}/analysis/``, then copies the protocol file
    into the ``src/`` sub-directory.  After deployment, runs
    ``opentrons.cli analyze`` to generate the analysis JSON that the Opentrons
    App expects.

    Args:
        protocol_path: Path to the compiled protocol file.
        opentrons_dir: Root Opentrons App data directory
            (e.g. ``/mnt/c/Users/.../AppData/Roaming/Opentrons``).
        copy_to_clipboard: Whether to also copy the protocol content to the clipboard.
        clipboard_command: Command used to pipe data to the clipboard.
        clipboard_runner: Injectable callable for testing.

    Returns:
        Dictionary with ``protocol_file``, ``uuid``, ``deployed_path``, ``copies``,
        ``clipboard``, and ``analysis_path`` keys.
    """
    protocol_file = resolve_project_path(protocol_path)
    if not protocol_file.exists():
        raise ConfigurationError(f"Protocol file not found at {protocol_file}")

    ot_dir = Path(opentrons_dir)
    if not ot_dir.is_dir():
        raise ConfigurationError(f"Opentrons directory not found: {ot_dir}")

    protocol_uuid = str(uuid.uuid4())
    src_dir = ot_dir / "protocols" / protocol_uuid / "src"
    analysis_dir = ot_dir / "protocols" / protocol_uuid / "analysis"
    src_dir.mkdir(parents=True, exist_ok=True)
    analysis_dir.mkdir(parents=True, exist_ok=True)

    destination = src_dir / protocol_file.name
    shutil.copy2(protocol_file, destination)

    # Verify the deployed file exists and resolves correctly
    if not destination.exists():
        raise DeploymentError(
            f"Post-deploy verification failed: file not found at {destination}"
        )

    # Run protocol analysis (non-fatal on failure).
    labware_dir = ot_dir / "labware"
    analysis_path = _run_protocol_analysis(
        protocol_path=destination,
        analysis_dir=analysis_dir,
        labware_dir=labware_dir,
    )

    clipboard_result: dict[str, object] | None = None
    if copy_to_clipboard:
        clipboard_result = _send_to_clipboard(
            protocol_file=protocol_file,
            command=clipboard_command,
            runner=clipboard_runner,
        )

    return {
        "protocol_file": str(protocol_file),
        "uuid": protocol_uuid,
        "deployed_path": str(destination),
        "copies": [str(destination)],
        "clipboard": clipboard_result,
        "analysis_path": analysis_path,
    }


def _resolve_destination(target: str | Path, filename: str) -> Path:
    dest = resolve_project_path(target)

    if dest.exists() and dest.is_dir():
        return dest / filename

    if str(target).endswith(("/", "\\")):
        return dest / filename

    return dest


ClipboardRunner = Callable[[Sequence[str], str], subprocess.CompletedProcess[str]]


def _send_to_clipboard(
    *,
    protocol_file: Path,
    command: Sequence[str] | None,
    runner: ClipboardRunner | None,
) -> dict[str, object]:
    if not command:
        raise ConfigurationError("clipboard_command must be provided when copy_to_clipboard is True")

    executable = command[0]
    if not shutil.which(executable):
        raise DeploymentError(f"Clipboard command not found: {executable}")

    clip_runner = runner or _default_clipboard_runner
    try:
        completed = clip_runner(
            command,
            protocol_file.read_text(encoding="utf-8"),
        )
    except subprocess.CalledProcessError as exc:  # pragma: no cover - defensive
        raise DeploymentError(f"Clipboard command failed: {exc}") from exc
    except OSError as exc:
        raise DeploymentError(f"Clipboard command could not be executed: {exc}") from exc

    if completed.returncode != 0:
        raise DeploymentError(
            f"Clipboard command returned non-zero exit status {completed.returncode}: {completed.stderr}"
        )

    return {
        "command": list(command),
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def _default_clipboard_runner(
    command: Sequence[str],
    data: str,
    timeout: int = 10,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # type: ignore[return-value]
        command,
        input=data,
        text=True,
        capture_output=True,
        check=False,
        timeout=timeout,
    )
