"""Tests for TOML handler utilities."""

from __future__ import annotations

from pathlib import Path

import pytest

from ot2_cherrypick_mcp.utils.errors import ConfigurationError
from ot2_cherrypick_mcp.utils.toml import TomlHandler


def _copy_settings(tmp_path: Path) -> Path:
    repo_root = Path(__file__).resolve().parents[1]
    source = repo_root / "settings.toml"
    destination = tmp_path / "settings.toml"
    destination.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    return destination


def test_toml_handler_gets_scalar_value(tmp_path: Path, monkeypatch) -> None:
    """Expect dotted-path lookup to return scalar values."""
    settings_copy = _copy_settings(tmp_path)
    monkeypatch.setenv("OT2_PROJECT_DIR", str(tmp_path))
    handler = TomlHandler("settings.toml")
    assert handler.get_value("settings.general.mode") == "multi"


def test_toml_handler_handles_array_indices(tmp_path: Path, monkeypatch) -> None:
    """Array notation should resolve to nested values."""
    settings_copy = _copy_settings(tmp_path)
    monkeypatch.setenv("OT2_PROJECT_DIR", str(tmp_path))
    handler = TomlHandler("settings.toml")
    assert handler.get_value("settings.working_plate[0].type") == "module"


def test_toml_handler_invalid_path_raises(tmp_path: Path, monkeypatch) -> None:
    """Invalid paths raise configuration errors."""
    settings_copy = _copy_settings(tmp_path)
    monkeypatch.setenv("OT2_PROJECT_DIR", str(tmp_path))
    handler = TomlHandler("settings.toml")
    with pytest.raises(ConfigurationError):
        handler.get_value("settings.missing.section")


def test_toml_handler_set_value_updates_file(tmp_path: Path) -> None:
    """Setting a value writes the file and produces a backup."""

    settings_copy = _copy_settings(tmp_path)
    handler = TomlHandler(settings_copy)

    old_value, new_value = handler.set_value("settings.general.mode", "single_X1")

    assert old_value == "multi"
    assert new_value == "single_X1"

    content = settings_copy.read_text(encoding="utf-8")
    assert 'mode = "single_X1"' in content

    backup = settings_copy.with_suffix(settings_copy.suffix + ".backup")
    assert backup.exists()
    backup_content = backup.read_text(encoding="utf-8")
    assert 'mode = "multi"' in backup_content


def test_toml_handler_set_value_missing_path_raises(tmp_path: Path) -> None:
    """Setting a non-existent path surfaces configuration errors."""

    settings_copy = _copy_settings(tmp_path)
    handler = TomlHandler(settings_copy)

    with pytest.raises(ConfigurationError):
        handler.set_value("settings.general.does_not_exist", "value")
