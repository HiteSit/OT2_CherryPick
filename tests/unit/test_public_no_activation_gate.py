from __future__ import annotations

import subprocess
from pathlib import Path

from ot2_cherrypick_mcp.utils import paths


def test_runtime_startup_does_not_require_activation_marker(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(paths, "get_repo_root", lambda: tmp_path)

    assert paths.ensure_runtime_ready() == tmp_path


def test_runtime_code_does_not_reference_activation_marker_file() -> None:
    root = Path(__file__).resolve().parents[2]
    tracked_files = subprocess.check_output(
        ["git", "ls-files", "src", "docker", ".gitignore"],
        cwd=root,
        text=True,
    ).splitlines()

    offenders: list[str] = []
    for relative_path in tracked_files:
        if b".activation.needs" in (root / relative_path).read_bytes():
            offenders.append(relative_path)

    assert offenders == []
