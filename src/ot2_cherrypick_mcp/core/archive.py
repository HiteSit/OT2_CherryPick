"""Workspace archiving helpers."""

from __future__ import annotations

import base64
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, Tuple
from zipfile import ZIP_DEFLATED, ZipFile

from ..utils.paths import project_directory_info

__all__ = ["create_project_archive"]


def create_project_archive(
    *,
    as_base64: bool = False,
    skip_existing_archives: bool = True,
    retention: int = 5,
) -> Dict[str, object]:
    """Create (and optionally encode) an archive of the current project workspace."""

    info = project_directory_info()
    root: Path = info["path"]
    archives_dir = root / "archives"
    archives_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    archive_path = archives_dir / f"ot2_project_{timestamp}.zip"

    with ZipFile(archive_path, "w", ZIP_DEFLATED) as archive:
        for file_path, arcname in _iter_archive_entries(root, skip_existing_archives):
            archive.write(file_path, arcname=str(arcname))

    _enforce_retention(archives_dir, retention)

    result: Dict[str, object] = {
        "archive_path": str(archive_path),
        "auto_created_workspace": bool(info["auto_created"]),
    }

    if as_base64:
        encoded = base64.b64encode(archive_path.read_bytes()).decode("ascii")
        result["archive_base64"] = encoded

    return result


def _iter_archive_entries(
    root: Path,
    skip_existing_archives: bool,
) -> Iterable[Tuple[Path, Path]]:
    """Yield (absolute_path, archive_relative_path) pairs for zip creation."""
    archives_dir = root / "archives"
    for path in root.rglob("*"):
        if path.is_dir():
            continue
        rel_path = path.relative_to(root)
        if skip_existing_archives and rel_path.parts and rel_path.parts[0] == "archives":
            continue
        yield path, rel_path


def _enforce_retention(archives_dir: Path, retention: int) -> None:
    """Keep only the most recent `retention` archives."""
    if retention <= 0 or not archives_dir.exists():
        return

    archives = sorted(
        (path.stat().st_mtime, path)
        for path in archives_dir.glob("*.zip")
        if path.is_file()
    )
    if len(archives) <= retention:
        return

    for _, path in archives[: len(archives) - retention]:
        try:
            path.unlink()
        except OSError:
            # Ignore failures – best effort retention.
            pass
