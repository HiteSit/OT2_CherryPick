"""
File-backed configuration state manager for the GUI backend.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tomllib
from pathlib import Path
from typing import Any, Iterable, List

import tomlkit
from fastapi import HTTPException, status

from ot2_cherrypick_mcp.core.deployment import deploy_protocol
from ot2_cherrypick_mcp.core.protocol_generator import generate_protocol
from ot2_cherrypick_mcp.core.simulation import DEFAULT_LOG_FILE, simulate_protocol
from ot2_cherrypick_mcp.utils.errors import SimulationError
from ot2_cherrypick_mcp.utils.paths import get_repo_root, resolve_project_path


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
        self.workspace_dir = self.repo_root / workspace_name
        self.workspace_dir.mkdir(parents=True, exist_ok=True)

        self.settings_path = self.workspace_dir / "settings.toml"
        self.labware_path = self.workspace_dir / "labware_dict.toml"
        self.csv_dir = self.workspace_dir / "CSVs"
        self.csv_dir.mkdir(parents=True, exist_ok=True)

        self.protocol_output = self.workspace_dir / "CherryPick_OT2.py"
        self.shell_settings_path = self.workspace_dir / "shell_settings.json"

        self._bootstrap_file(self.repo_root / "settings.toml", self.settings_path)
        self._bootstrap_file(self.repo_root / "labware_dict.toml", self.labware_path)
        self._bootstrap_file(self.repo_root / "CherryPick_OT2.py", self.protocol_output)
        self._ensure_shell_settings()

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

    def add_working_plate_entry(self, payload: dict[str, Any]) -> dict[str, Any]:
        current = self.get_settings()
        plates = current.setdefault("settings", {}).setdefault("working_plate", [])
        if not isinstance(plates, list):
            plates = []
            current["settings"]["working_plate"] = plates
        plates.append(payload)
        return self.write_settings(current)

    def remove_working_plate_entry(self, index: int) -> dict[str, Any]:
        current = self.get_settings()
        plate_list = current.get("settings", {}).get("working_plate")
        if not isinstance(plate_list, list):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No working_plate entries to remove.")
        if index < 0 or index >= len(plate_list):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Working plate index out of range.")
        del plate_list[index]
        return self.write_settings(current)

    def move_working_plate_entry(self, index: int, target_index: int) -> dict[str, Any]:
        current = self.get_settings()
        plate_list = current.get("settings", {}).get("working_plate")
        if not isinstance(plate_list, list):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No working_plate entries to move.")
        if index < 0 or index >= len(plate_list):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Working plate index out of range.")
        target = max(0, min(target_index, len(plate_list) - 1))
        entry = plate_list.pop(index)
        plate_list.insert(target, entry)
        return self.write_settings(current)

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
    # Shell runner configuration
    # ------------------------------------------------------------------ #

    def get_shell_settings(self) -> dict[str, Any]:
        return self._load_shell_settings()

    def update_shell_settings(
        self,
        *,
        target_protocol_src_win: str | None = None,
        labware_path_win: str | None = None,
    ) -> dict[str, Any]:
        data = self._load_shell_settings()
        if target_protocol_src_win is not None:
            data["target_protocol_src_win"] = target_protocol_src_win.strip()
        if labware_path_win is not None:
            data["labware_path_win"] = labware_path_win.strip()
        self._write_shell_settings(data)
        return data

    def browse_and_update_shell_settings(self, field: str) -> dict[str, Any]:
        if field not in {"target_protocol_src_win", "labware_path_win"}:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid shell setting field.")
        title = "Select Opentrons protocol folder" if field == "target_protocol_src_win" else "Select custom labware folder"
        selection = self._prompt_for_directory(title)
        kwargs: dict[str, Any] = {field: selection}
        return self.update_shell_settings(**kwargs)

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

    def run_generate_protocol(
        self,
        csv_path: Path | str,
        protocol_path: Path | str | None = None,
    ) -> tuple[dict[str, Any], list[str]]:
        csv_file = Path(csv_path)
        if not csv_file.exists():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"CSV file missing: {csv_file}")

        protocol_file = Path(protocol_path) if protocol_path else self.protocol_output

        log_lines = [
            "=== Step 1: Updating protocol with helper ===",
            f"Labware TOML: {self.labware_path}",
            f"Settings TOML: {self.settings_path}",
            f"CSV file: {csv_file}",
        ]

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

        log_lines.append("✓ Protocol generated successfully")
        log_lines.append(f"Output: {result['protocol_file']}")
        return result, log_lines

    def run_simulation(
        self,
        protocol_path: Path | str | None = None,
    ) -> tuple[dict[str, Any], list[str]]:
        protocol_file = Path(protocol_path) if protocol_path else self.protocol_output
        labware_override = self._resolve_labware_path()
        log_lines = [
            "=== Step 2: Running protocol simulation ===",
            f"Protocol: {protocol_file}",
        ]
        if labware_override:
            log_lines.append(f"Custom labware dir: {labware_override}")
        try:
            result = simulate_protocol(str(protocol_file), labware_path=labware_override)
            result["success"] = True
            stdout = (result.get("stdout") or "").strip()
            stderr = (result.get("stderr") or "").strip()
            if stdout:
                log_lines.append("--- opentrons_simulate stdout ---")
                log_lines.append(stdout)
            if stderr:
                log_lines.append("--- opentrons_simulate stderr ---")
                log_lines.append(stderr)
            log_lines.append("✓ Simulation completed successfully")
            return result, log_lines
        except SimulationError as exc:
            payload = self._read_simulation_log()
            stdout = payload.get("stdout", "")
            stderr = payload.get("stderr", "")
            result = {
                "success": False,
                "error": str(exc),
                "stdout": stdout,
                "stderr": stderr,
                "returncode": payload.get("returncode"),
            }
            if stdout:
                log_lines.append("--- opentrons_simulate stdout ---")
                log_lines.append(stdout)
            if stderr:
                log_lines.append("--- opentrons_simulate stderr ---")
                log_lines.append(stderr)
            log_lines.append(f"✗ Simulation failed: {exc}")
            return result, log_lines
        except Exception as exc:  # pragma: no cover - defensive
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc

    def deploy_protocol(
        self,
        protocol_path: Path | str | None = None,
        *,
        target_path: Path | str | None = None,
        copy_to_clipboard: bool = False,
    ) -> tuple[dict[str, Any], list[str]]:
        protocol_file = Path(protocol_path) if protocol_path else self.protocol_output
        log_lines = [
            "=== Step 3: Deployment ===",
            f"Source protocol: {protocol_file}",
        ]
        
        # Auto-convert Windows paths to WSL format for deployment
        resolved_target: str | None = None
        if target_path is not None:
            target_str = str(target_path)
            # Check if Windows path (C:\... or D:\... etc.)
            import re
            if re.match(r'^[A-Za-z]:', target_str):
                resolved_target = self._windows_to_wsl(target_str)
                log_lines.append(f"Converted Windows path: {target_str} -> {resolved_target}")
            else:
                resolved_target = target_str
        
        try:
            result = deploy_protocol(
                str(protocol_file),
                target_path=resolved_target,
                copy_to_clipboard=copy_to_clipboard,
            )
        except Exception as exc:  # pragma: no cover - bubbled up to API
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
        if result.get("copies"):
            log_lines.append(f"Copied to: {', '.join(result['copies'])}")
        if copy_to_clipboard:
            if result.get("clipboard"):
                log_lines.append("Clipboard updated.")
            else:
                log_lines.append("Clipboard update requested but returned no result.")
        log_lines.append("✓ Deployment complete")
        return result, log_lines

    def run_shell_script(self, csv_path: Path, send_to_opentrons: bool) -> tuple[dict[str, Any], list[str]]:
        command = ["bash", "simulate_protocol.sh", str(csv_path)]
        if send_to_opentrons:
            command.append("--send-to-opentrons")

        backups = self._sync_repo_configs()
        env = os.environ.copy()
        shell_settings = self._load_shell_settings()
        target_override = shell_settings.get("target_protocol_src_win")
        if target_override:
            env["TARGET_PROTOCOL_SRC_WIN_OVERRIDE"] = target_override
        labware_override = shell_settings.get("labware_path_win")
        if labware_override:
            env["LABWARE_PATH_WIN_OVERRIDE"] = labware_override
        log_lines = ["=== simulate_protocol.sh ===", f"Command: {' '.join(command)}"]
        try:
            completed = subprocess.run(
                command,
                cwd=self.repo_root,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
        finally:
            self._restore_repo_configs(backups)

        stdout = completed.stdout or ""
        stderr = completed.stderr or ""
        if stdout:
            log_lines.append("--- stdout ---")
            log_lines.extend(stdout.splitlines())
        if stderr:
            log_lines.append("--- stderr ---")
            log_lines.extend(stderr.splitlines())
        log_lines.append(f"Return code: {completed.returncode}")

        result = {
            "command": command,
            "stdout": stdout,
            "stderr": stderr,
            "returncode": completed.returncode,
            "success": completed.returncode == 0,
        }
        return result, log_lines

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

    def _ensure_shell_settings(self) -> None:
        if self.shell_settings_path.exists():
            return
        self.shell_settings_path.write_text(
            json.dumps({"target_protocol_src_win": "", "labware_path_win": ""}, indent=2),
            encoding="utf-8",
        )

    def _load_shell_settings(self) -> dict[str, Any]:
        self._ensure_shell_settings()
        raw = self.shell_settings_path.read_text(encoding="utf-8")
        try:
            data = json.loads(raw) if raw.strip() else {}
        except json.JSONDecodeError:
            data = {}
        if "target_protocol_src_win" not in data:
            data["target_protocol_src_win"] = ""
        if "labware_path_win" not in data:
            data["labware_path_win"] = ""
        return data

    def _write_shell_settings(self, payload: dict[str, Any]) -> None:
        self.shell_settings_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _prompt_for_directory(self, dialog_title: str) -> str:
        try:
            import tkinter as tk
            from tkinter import filedialog
        except Exception as exc:  # pragma: no cover - GUI dependency
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Folder dialog is unavailable on this environment.",
            ) from exc

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        selected = filedialog.askdirectory(title=dialog_title)
        root.destroy()

        if not selected:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Folder selection canceled.")
        return selected

    def _resolve_labware_path(self) -> str | None:
        # First, check environment variable (Docker volume mount)
        env_path = os.getenv("LABWARE_PATH")
        if env_path:
            return env_path.strip()

        # Fallback to shell_settings.json
        data = self._load_shell_settings()
        raw = (data.get("labware_path_win") or "").strip()
        if not raw:
            return None
        return self._windows_to_wsl(raw)

    def _windows_to_wsl(self, path: str) -> str:
        if not path or path.startswith("/"):
            return path
        try:
            completed = subprocess.run(
                ["wslpath", path],
                capture_output=True,
                text=True,
                check=True,
            )
            candidate = completed.stdout.strip()
            if candidate:
                return candidate
        except (FileNotFoundError, subprocess.CalledProcessError):  # pragma: no cover - best effort fallback
            pass
        sanitized = path.replace("\\", "/")
        if ":" in sanitized:
            drive, rest = sanitized.split(":", 1)
            rest = rest.lstrip("/")
            return f"/mnt/{drive.lower()}/{rest}"
        return sanitized

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
                if value is None:
                    cursor.pop(last_key)
                else:
                    cursor[last_key] = value
            except IndexError as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail=f"Index {last_key} out of range."
                ) from exc
        else:
            if value is None:
                if isinstance(cursor, dict) and last_key in cursor:
                    del cursor[last_key]
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

    def _read_simulation_log(self) -> dict[str, Any]:
        log_path = Path(DEFAULT_LOG_FILE)
        if not log_path.is_absolute():
            try:
                log_path = resolve_project_path(log_path)
            except Exception:
                # Fall back to workspace dir, then repo root
                workspace_candidate = self.workspace_dir / log_path
                log_path = workspace_candidate if workspace_candidate.exists() else self.repo_root / log_path
        if log_path.exists():
            try:
                return json.loads(log_path.read_text(encoding="utf-8"))
            except Exception:  # pragma: no cover - best effort
                return {}
        return {}

    def _sync_repo_configs(self) -> dict[str, str | None]:
        backups: dict[str, str | None] = {}
        for filename, workspace_path in (
            ("settings.toml", self.settings_path),
            ("labware_dict.toml", self.labware_path),
            ("CherryPick_OT2.py", self.protocol_output),
        ):
            dest = self.repo_root / filename
            backups[filename] = dest.read_text(encoding="utf-8") if dest.exists() else None
            shutil.copy2(workspace_path, dest)
        return backups

    def _restore_repo_configs(self, backups: dict[str, str | None]) -> None:
        # Preserve the script's CherryPick output by copying it back into workspace before restore
        protocol_src = self.repo_root / "CherryPick_OT2.py"
        if protocol_src.exists():
            shutil.copy2(protocol_src, self.protocol_output)

        for filename, content in backups.items():
            dest = self.repo_root / filename
            if content is None:
                if dest.exists():
                    dest.unlink()
            else:
                dest.write_text(content, encoding="utf-8")


__all__ = ["FileStateStore"]
