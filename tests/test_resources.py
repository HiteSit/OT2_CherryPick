"""Tests for configuration resources."""

from __future__ import annotations

import asyncio
from pathlib import Path

from ot2_cherrypick_mcp.server import create_mcp_app
from ot2_cherrypick_mcp.core.simulation import DEFAULT_LOG_FILE
from ot2_cherrypick_mcp.utils.toml import TomlHandler as RealTomlHandler


def test_settings_resource_registered_and_readable() -> None:
    """Settings resource should be available and return TOML text."""
    app = create_mcp_app()
    resources = asyncio.run(app.get_resources())
    assert "config://settings" in resources
    content = resources["config://settings"].fn()
    assert "settings.general" in content


def test_labware_resource_registered_and_readable() -> None:
    """Labware resource should be available and return TOML text."""
    app = create_mcp_app()
    resources = asyncio.run(app.get_resources())
    assert "config://labware" in resources
    content = resources["config://labware"].fn()
    assert "[[labware]]" in content


def test_csv_file_resource_lists_files(tmp_path: Path, monkeypatch) -> None:
    """CSV resource should list available files."""

    csv_dir = tmp_path / "CSVs"
    csv_dir.mkdir()
    (csv_dir / "b.csv").write_text("", encoding="utf-8")
    (csv_dir / "a.csv").write_text("", encoding="utf-8")

    monkeypatch.setattr(
        "ot2_cherrypick_mcp.resources.file_resources.DEFAULT_CSV_DIR",
        csv_dir,
    )

    app = create_mcp_app()
    resources = asyncio.run(app.get_resources())
    content = resources["files://csvs"].fn()
    assert "a.csv" in content.splitlines()[0]
def test_last_simulation_resource(tmp_path: Path, monkeypatch) -> None:
    """Log resource should serve latest simulation entry."""

    log_path = tmp_path / "logs" / "last_simulation.json"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text("{\"status\": \"ok\"}", encoding="utf-8")

    monkeypatch.setattr(
        "ot2_cherrypick_mcp.core.simulation.DEFAULT_LOG_FILE",
        log_path,
        raising=False,
    )
    monkeypatch.setattr(
        "ot2_cherrypick_mcp.resources.log_resources.DEFAULT_LOG_FILE",
        log_path,
        raising=False,
    )

    app = create_mcp_app()
    resources = asyncio.run(app.get_resources())
    content = resources["logs://last-simulation"].fn()
    assert "\"status\"" in content


def test_status_resources(tmp_path: Path, monkeypatch) -> None:
    settings_copy = tmp_path / "settings.toml"
    settings_copy.write_text(
        """
[settings]
  [[settings.working_plate]]
  type = "source"
  labware_id = "plate_a"
  position_rack = "1"

  [settings.liquid_handling]
  mode = "test"
""",
        encoding="utf-8",
    )

    class FakeTomlHandler(RealTomlHandler):
        def __init__(self, path):  # type: ignore[super-init-not-called]
            super().__init__(settings_copy)

    monkeypatch.setattr("ot2_cherrypick_mcp.resources.status_resources.TomlHandler", FakeTomlHandler)

    app = create_mcp_app()
    resources = asyncio.run(app.get_resources())
    deck = resources["status://deck-layout"].fn()
    liquid = resources["status://liquid-handling-config"].fn()

    assert "plate_a" in deck
    assert "Liquid Handling Configuration" in liquid
