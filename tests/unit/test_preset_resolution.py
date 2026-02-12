"""Tests for liquid handling preset resolution logic.

Tests cover:
- Preset resolution as performed in CherryPick_OT2.py run()
- The MCP apply_liquid_preset tool from config_tools
"""

from __future__ import annotations

import copy
from pathlib import Path

import pytest

from ot2_cherrypick_mcp.tools.config_tools import apply_liquid_preset
from ot2_cherrypick_mcp.utils.errors import ConfigurationError


# ---------------------------------------------------------------------------
# Helpers: simulate the preset resolution logic from CherryPick_OT2.py run()
# ---------------------------------------------------------------------------

# Canonical preset definitions matching settings.toml
STANDARD_PRESET = {
    "pre_aspirate_contact": {"enabled": True, "position_offset_percent": 20, "aspirate_volume": 0},
    "post_aspirate_wick": {"enabled": True, "radius": 0.8, "v_offset_mm": -1.5, "speed": 20},
    "delays": {"post_aspirate": 0},
    "push_out": {"enabled": False},
    "mixing": {"enabled": True, "location": "destination", "repetitions": 3, "source_remixing": "once"},
}

VISCOUS_PRESET = {
    "pre_aspirate_contact": {"enabled": True, "position_offset_percent": 20, "aspirate_volume": 0},
    "post_aspirate_wick": {"enabled": True, "radius": 0.8, "v_offset_mm": -1.5, "speed": 20},
    "delays": {"post_aspirate": 2.0},
    "push_out": {"enabled": True, "volume_ul": 5},
    "mixing": {"enabled": True, "location": "destination", "repetitions": 5, "source_remixing": "once"},
}

# Base individual settings (before any preset is applied)
BASE_INDIVIDUAL_SETTINGS = {
    "active_preset": "",
    "pre_aspirate_contact": {"enabled": False, "position_offset_percent": 20, "aspirate_volume": 20},
    "post_aspirate_wick": {"enabled": False, "radius": 1, "v_offset_mm": -1.5, "speed": 20},
    "delays": {"post_aspirate": 0},
    "push_out": {"enabled": True, "volume_ul": 20},
    "mixing": {"enabled": False, "location": "destination", "repetitions": 2, "source_remixing": "once"},
    "presets": {
        "standard": STANDARD_PRESET,
        "viscous": VISCOUS_PRESET,
    },
}


def resolve_presets(liquid_handling: dict) -> dict:
    """Simulate preset resolution as done in CherryPick_OT2.py run()."""
    active_preset = liquid_handling.get("active_preset", "")
    if active_preset:
        presets = liquid_handling.get("presets", {})
        if active_preset not in presets:
            raise ValueError(
                f"Unknown liquid handling preset: '{active_preset}'. "
                f"Available: {list(presets.keys())}"
            )
        preset_values = presets[active_preset]
        for key in ("pre_aspirate_contact", "post_aspirate_wick", "delays", "push_out", "mixing"):
            if key in preset_values:
                liquid_handling[key] = preset_values[key]
    return liquid_handling


# ---------------------------------------------------------------------------
# Unit tests: preset resolution logic
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestPresetResolution:
    """Tests for the runtime preset resolution logic."""

    def test_standard_preset_resolves_correctly(self) -> None:
        """active_preset='standard' resolves all 5 keys to standard preset values."""
        lh = copy.deepcopy(BASE_INDIVIDUAL_SETTINGS)
        lh["active_preset"] = "standard"

        resolved = resolve_presets(lh)

        assert resolved["pre_aspirate_contact"] == STANDARD_PRESET["pre_aspirate_contact"]
        assert resolved["post_aspirate_wick"] == STANDARD_PRESET["post_aspirate_wick"]
        assert resolved["delays"] == STANDARD_PRESET["delays"]
        assert resolved["push_out"] == STANDARD_PRESET["push_out"]
        assert resolved["mixing"] == STANDARD_PRESET["mixing"]

    def test_viscous_preset_resolves_correctly(self) -> None:
        """active_preset='viscous' resolves to viscous preset values."""
        lh = copy.deepcopy(BASE_INDIVIDUAL_SETTINGS)
        lh["active_preset"] = "viscous"

        resolved = resolve_presets(lh)

        assert resolved["delays"]["post_aspirate"] == 2.0
        assert resolved["push_out"]["enabled"] is True
        assert resolved["push_out"]["volume_ul"] == 5
        assert resolved["pre_aspirate_contact"]["enabled"] is True
        assert resolved["post_aspirate_wick"]["radius"] == 0.8
        assert resolved["mixing"]["repetitions"] == 5

    def test_no_preset_uses_individual_settings(self) -> None:
        """Empty active_preset leaves individual settings unchanged."""
        lh = copy.deepcopy(BASE_INDIVIDUAL_SETTINGS)
        lh["active_preset"] = ""
        original = copy.deepcopy(lh)

        resolved = resolve_presets(lh)

        # All individual settings should be unchanged
        assert resolved["pre_aspirate_contact"] == original["pre_aspirate_contact"]
        assert resolved["post_aspirate_wick"] == original["post_aspirate_wick"]
        assert resolved["delays"] == original["delays"]
        assert resolved["push_out"] == original["push_out"]
        assert resolved["mixing"] == original["mixing"]

    def test_missing_preset_key_uses_individual_settings(self) -> None:
        """Missing active_preset key (not in dict at all) uses individual settings."""
        lh = copy.deepcopy(BASE_INDIVIDUAL_SETTINGS)
        del lh["active_preset"]
        original_push_out = copy.deepcopy(lh["push_out"])

        resolved = resolve_presets(lh)

        assert resolved["push_out"] == original_push_out

    def test_invalid_preset_raises_error(self) -> None:
        """Nonexistent preset name raises ValueError with helpful message."""
        lh = copy.deepcopy(BASE_INDIVIDUAL_SETTINGS)
        lh["active_preset"] = "nonexistent"

        with pytest.raises(ValueError, match="Unknown liquid handling preset: 'nonexistent'"):
            resolve_presets(lh)

    def test_preset_overrides_individual_settings(self) -> None:
        """Preset values take precedence over conflicting individual settings."""
        lh = copy.deepcopy(BASE_INDIVIDUAL_SETTINGS)
        # Individual: push_out.enabled=True, volume_ul=20
        assert lh["push_out"]["enabled"] is True
        assert lh["push_out"]["volume_ul"] == 20

        # Standard preset: push_out.enabled=False (no volume_ul key)
        lh["active_preset"] = "standard"
        resolved = resolve_presets(lh)

        # Preset should win
        assert resolved["push_out"]["enabled"] is False

    def test_preset_does_not_modify_presets_dict(self) -> None:
        """Resolving a preset does not alter the presets definitions themselves."""
        lh = copy.deepcopy(BASE_INDIVIDUAL_SETTINGS)
        lh["active_preset"] = "viscous"

        resolve_presets(lh)

        # The presets dict should still contain the original definitions
        assert lh["presets"]["viscous"] == VISCOUS_PRESET
        assert lh["presets"]["standard"] == STANDARD_PRESET


# ---------------------------------------------------------------------------
# Unit tests: MCP apply_liquid_preset tool
# ---------------------------------------------------------------------------

def _copy_settings(tmp_path: Path) -> Path:
    """Copy repo-root settings.toml to a temp directory."""
    repo_root = Path(__file__).resolve().parents[2]
    source = repo_root / "settings.toml"
    destination = tmp_path / "settings.toml"
    destination.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    return destination


@pytest.mark.unit
class TestApplyLiquidPresetTool:
    """Tests for the MCP apply_liquid_preset tool from config_tools."""

    def test_apply_preset_sets_active_settings(self, tmp_path: Path) -> None:
        """Applying viscous preset writes viscous values into active settings."""
        settings_copy = _copy_settings(tmp_path)

        result = apply_liquid_preset(
            preset_name="viscous",
            settings_path=str(settings_copy),
        )

        assert result["preset"] == "viscous"
        change_paths = {c["path"] for c in result["changes"]}
        assert "settings.liquid_handling.delays" in change_paths
        assert "settings.liquid_handling.push_out" in change_paths

        # Verify the file was actually updated
        text = settings_copy.read_text(encoding="utf-8")
        assert "post_aspirate = 2.0" in text

    def test_apply_standard_preset(self, tmp_path: Path) -> None:
        """Applying standard preset disables push_out and sets contact+wick."""
        settings_copy = _copy_settings(tmp_path)

        result = apply_liquid_preset(
            preset_name="standard",
            settings_path=str(settings_copy),
        )

        assert result["preset"] == "standard"

        text = settings_copy.read_text(encoding="utf-8")
        # Standard preset has push_out.enabled = false
        assert "enabled = false" in text

    def test_apply_preset_creates_backup(self, tmp_path: Path) -> None:
        """Applying a preset creates a backup file."""
        settings_copy = _copy_settings(tmp_path)

        result = apply_liquid_preset(
            preset_name="standard",
            settings_path=str(settings_copy),
        )

        backup_path = Path(result["backup_file"])
        assert backup_path.exists()

    def test_apply_invalid_preset_errors(self, tmp_path: Path) -> None:
        """Unknown preset name raises ConfigurationError."""
        settings_copy = _copy_settings(tmp_path)

        with pytest.raises(ConfigurationError, match="not found"):
            apply_liquid_preset(
                preset_name="does_not_exist",
                settings_path=str(settings_copy),
            )
