"""
File-backed configuration state manager for the GUI backend.
"""

from __future__ import annotations

import os
import shutil
import tomllib
from pathlib import Path
from typing import Any, Iterable, List

import tomlkit
from fastapi import HTTPException, status

from ot2_cherrypick_mcp.core.deployment import deploy_protocol
from ot2_cherrypick_mcp.core.protocol_generator import generate_protocol
from ot2_cherrypick_mcp.core.simulation import simulate_protocol
from ot2_cherrypick_mcp.utils.paths import get_repo_root


class FileStateStore:
    """
    Maintain editable copies of configuration files for the GUI workflow.

    All edits happen inside ``projects/gui_state`` so that the repository's
    canonical configuration stays untouched until the user explicitly
    generates a protocol.
    """
    def __init__(self, workspace_name: str | None = None) -> None:
        if workspace_name is None:
            workspace_name = os.getenv("OT2_GUI_WORKSPACE", "gui_state")
        self.repo_root = get_repo_root()
        self.workspace_dir = self.repo_root / "projects" / workspace_name
        self.workspace_dir.mkdir(parents=True, exist_ok=True)

        self.settings_path = self.workspace_dir / "settings.toml"
        self.labware_path = self.workspace_dir / "labware_dict.toml"
        self.csv_dir = self.workspace_dir / "CSVs"
        self.csv_dir.mkdir(parents=True, exist_ok=True)

        self.protocol_output = self.repo_root / "CherryPick_OT2.py"

        self._bootstrap_file(self.repo_root / "settings.toml", self.settings_path)
        self._bootstrap_file(self.repo_root / "labware_dict.toml", self.labware_path)

    # ------------------------------------------------------------------ #
    # Public accessors
    # ------------------------------------------------------------------ #

    def get_settings(self) -> dict[str, Any]:
        return self._doc_to_plain(self._read_doc(self.settings_path))

    def write_settings(self, payload: dict[str, Any]) -> dict[str, Any]:
        doc = tomlkit.parse(tomlkit.dumps(payload))
        self._write_doc(self.settings_path, doc)
        return self.get_settings()

    def patch_settings(self, path: str, value: Any) -> dict[str, Any]:
        doc = self._read_doc(self.settings_path)
        self._apply_patch(doc, path, value)
        self._write_doc(self.settings_path, doc)
        return self._doc_to_plain(doc)

    def reset_settings(self) -> dict[str, Any]:
        self._bootstrap_file(self.repo_root / "settings.toml", self.settings_path, force=True)
        return self.get_settings()

    def get_labware(self) -> dict[str, Any]:
        return self._doc_to_plain(self._read_doc(self.labware_path))

    def write_labware(self, payload: dict[str, Any]) -> dict[str, Any]:
        doc = tomlkit.parse(tomlkit.dumps(payload))
        self._write_doc(self.labware_path, doc)
        return self.get_labware()

    def patch_labware(self, path: str, value: Any) -> dict[str, Any]:
        doc = self._read_doc(self.labware_path)
        self._apply_patch(doc, path, value)
        self._write_doc(self.labware_path, doc)
        return self._doc_to_plain(doc)

    def reset_labware(self) -> dict[str, Any]:
        self._bootstrap_file(self.repo_root / "labware_dict.toml", self.labware_path, force=True)
        return self.get_labware()

    def reset_workspace(self) -> dict[str, Any]:
        """
        Reset both configuration files.
        """

        self.reset_settings()
        self.reset_labware()
        return {"settings": self.get_settings(), "labware": self.get_labware()}

    # ------------------------------------------------------------------ #
    # CSV helpers
    # ------------------------------------------------------------------ #

    def list_csv_files(self) -> list[str]:
        return sorted(file.name for file in self.csv_dir.glob("*.csv"))

    def save_csv(self, name: str, content: str) -> str:
        target = self._validate_csv_name(name)
        target.write_text(content.strip() + ("\n" if not content.endswith("\n") else ""), encoding="utf-8")
        return target.name

    def load_csv(self, name: str) -> str:
        target = self._validate_csv_name(name)
        if not target.exists():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CSV file not found")
        return target.read_text(encoding="utf-8")

    def delete_csv(self, name: str) -> None:
        target = self._validate_csv_name(name)
        if not target.exists():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CSV file not found")
        target.unlink()

    def resolve_csv_path(self, name_or_path: str) -> Path:
        candidate = Path(name_or_path)
        if candidate.is_absolute():
            return candidate
        local = self.csv_dir / candidate.name
        if local.exists():
            return local
        repo_relative = self.repo_root / candidate
        if repo_relative.exists():
            return repo_relative
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"CSV '{name_or_path}' not found in workspace or repository.",
        )

    # ------------------------------------------------------------------ #
    # Workflow helpers
    # ------------------------------------------------------------------ #

    def run_generate_protocol(self, csv_path: Path | str, protocol_path: Path | str | None = None) -> dict[str, Any]:
        csv_file = Path(csv_path)
        if not csv_file.exists():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"CSV file missing: {csv_file}")

        protocol_file = Path(protocol_path) if protocol_path else self.protocol_output

        try:
            result = generate_protocol(
                str(self.labware_path),
                str(self.settings_path),
                str(csv_file),
                str(protocol_file),
                verbose=False,
            )
        except Exception as exc:  # pragma: no cover - bubbled up to API
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc

        return result

    def run_simulation(self, protocol_path: Path | str | None = None) -> dict[str, Any]:
        protocol_file = Path(protocol_path) if protocol_path else self.protocol_output
        try:
            result = simulate_protocol(str(protocol_file))
        except Exception as exc:  # pragma: no cover - bubbled up to API
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
        return result

    def deploy_protocol(
        self,
        protocol_path: Path | str | None = None,
        *,
        target_path: Path | str | None = None,
        copy_to_clipboard: bool = False,
    ) -> dict[str, Any]:
        protocol_file = Path(protocol_path) if protocol_path else self.protocol_output
        try:
            result = deploy_protocol(
                str(protocol_file),
                target_path=str(target_path) if target_path is not None else None,
                copy_to_clipboard=copy_to_clipboard,
            )
        except Exception as exc:  # pragma: no cover - bubbled up to API
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
        return result

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #

    def _bootstrap_file(self, source: Path, destination: Path, *, force: bool = False) -> None:
        if destination.exists() and not force:
            return
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)

    def _read_doc(self, path: Path) -> tomlkit.TOMLDocument:
        return tomlkit.parse(path.read_text(encoding="utf-8"))

    def _write_doc(self, path: Path, doc: tomlkit.TOMLDocument) -> None:
        path.write_text(tomlkit.dumps(doc), encoding="utf-8")

    def _doc_to_plain(self, doc: tomlkit.TOMLDocument) -> dict[str, Any]:
        # Round-trip through tomllib for a JSON-compatible dict (drops comments intentionally).
        return tomllib.loads(tomlkit.dumps(doc))

    def _apply_patch(self, doc: tomlkit.TOMLDocument, path: str, value: Any) -> None:
        keys = self._explode_path(path)
        if not keys:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty path is not allowed.")

        cursor = doc
        for key in keys[:-1]:
            cursor = self._descend(cursor, key)

        last_key = keys[-1]
        if isinstance(last_key, int):
            if not isinstance(cursor, list):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="List index used on non-list item.")
            try:
                cursor[last_key] = value
            except IndexError as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail=f"Index {last_key} out of range."
                ) from exc
        else:
            cursor[last_key] = value

    def _descend(self, cursor: Any, key: str | int) -> Any:
        if isinstance(key, int):
            if not isinstance(cursor, list):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="List index used on non-list item.")
            try:
                return cursor[key]
            except IndexError as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail=f"Index {key} out of range."
                ) from exc

        if key not in cursor:
            cursor[key] = tomlkit.table()
        return cursor[key]

    def _explode_path(self, dotted_path: str) -> List[str | int]:
        segments: List[str | int] = []
        for raw_segment in dotted_path.split("."):
            segments.extend(self._expand_segment(raw_segment))
        return segments

    def _expand_segment(self, segment: str) -> Iterable[str | int]:
        tokens: List[str | int] = []
        buffer = ""
        i = 0
        while i < len(segment):
            char = segment[i]
            if char == "[":
                if buffer:
                    tokens.append(buffer)
                    buffer = ""
                close_idx = segment.find("]", i)
                if close_idx == -1:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unmatched '[' in segment '{segment}'"
                    )
                index_str = segment[i + 1 : close_idx]
                if not index_str.isdigit():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid list index '{index_str}'"
                    )
                tokens.append(int(index_str))
                i = close_idx
            else:
                buffer += char
            i += 1
        if buffer:
            tokens.append(buffer)
        return tokens

    def _validate_csv_name(self, name: str) -> Path:
        candidate = Path(name)
        if candidate.name != name or candidate.suffix != ".csv":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CSV name must be a simple filename ending with .csv",
            )
        return self.csv_dir / candidate.name


__all__ = ["FileStateStore"]
