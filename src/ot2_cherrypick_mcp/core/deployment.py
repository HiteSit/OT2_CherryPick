"""Helpers for deploying generated protocols."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Callable, Sequence

from ..utils.errors import ConfigurationError, DeploymentError
from ..utils.paths import resolve_repo_path

DEFAULT_CLIP_COMMAND = ["/mnt/c/Windows/System32/clip.exe"]

__all__ = ["deploy_protocol", "DEFAULT_CLIP_COMMAND"]


def deploy_protocol(
    protocol_path: str | Path,
    *,
    target_path: str | Path | None = None,
    copy_to_clipboard: bool = False,
    clipboard_command: Sequence[str] | None = DEFAULT_CLIP_COMMAND,
    clipboard_runner: ClipboardRunner | None = None,
) -> dict[str, object]:
    """Deploy the compiled protocol by copying and/or putting it on the clipboard."""

    protocol_file = resolve_repo_path(protocol_path)
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


def _resolve_destination(target: str | Path, filename: str) -> Path:
    dest = resolve_repo_path(target)

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
