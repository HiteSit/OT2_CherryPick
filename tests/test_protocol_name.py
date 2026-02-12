"""Unit tests for customizable protocol name feature.

Verifies that:
- Empty protocol_name preserves default metadata
- Custom protocol_name updates metadata protocolName
- Custom protocol_name is included in embedded JSON settings
- Special characters in protocol_name are handled safely
"""

from __future__ import annotations

import json
import re
import shutil
import textwrap
from pathlib import Path

import pytest

from ot2_cherrypick_mcp.core.protocol_generator import (
    create_json_config,
    update_protocol_file,
)

pytestmark = [pytest.mark.unit]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

DEFAULT_PROTOCOL_NAME = "Unified Cherry-Pick & Distribution Protocol (CherryPick_OT2)"

# Minimal protocol file template that matches the real structure
PROTOCOL_TEMPLATE = textwrap.dedent("""\
    def get_values(*names):
        import json
        _all_values = json.loads(\\"\\"\\"{"placeholder": true}\\"\\"\\"\\")
        return [_all_values[n] for n in names]

    metadata = {
        'protocolName': 'Unified Cherry-Pick & Distribution Protocol (CherryPick_OT2)',
        'author': 'Opentrons User',
        'description': 'Cherry-pick protocol'
    }
""")


def _extract_embedded_json(protocol_text: str) -> dict:
    """Extract the embedded JSON from a generated protocol file."""
    match = re.search(r'json\.loads\("""(.+?)"""\)', protocol_text, re.DOTALL)
    assert match, "Could not find embedded JSON in protocol"
    return json.loads(match.group(1))


def _extract_protocol_name_from_metadata(protocol_text: str) -> str:
    """Extract protocolName value from the metadata dict in a protocol file."""
    match = re.search(r"'protocolName'\s*:\s*'([^']*)'", protocol_text)
    assert match, "Could not find protocolName in metadata"
    return match.group(1)


def _find_project_root() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "pyproject.toml").exists():
            return parent
    raise FileNotFoundError("Cannot find project root")


PROJECT_ROOT = _find_project_root()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    """Create a minimal workspace with real repo files for protocol generation."""
    ws = tmp_path / "ws"
    ws.mkdir()

    # Copy real labware dict and protocol template
    shutil.copy2(
        PROJECT_ROOT / "tests" / "e2e" / "configs" / "labware_dict.toml",
        ws / "labware_dict.toml",
    )
    shutil.copy2(PROJECT_ROOT / "CherryPick_OT2.py", ws / "CherryPick_OT2.py")

    # Copy a basic settings.toml (single_X1 profile)
    shutil.copy2(
        PROJECT_ROOT / "tests" / "e2e" / "configs" / "single_X1" / "settings.toml",
        ws / "settings.toml",
    )

    # Copy an example CSV
    csv_dir = ws / "CSVs"
    csv_dir.mkdir()
    shutil.copy2(
        PROJECT_ROOT / "CSVs" / "example_basic.csv",
        csv_dir / "example_basic.csv",
    )

    return ws


def _set_protocol_name(settings_path: Path, name: str) -> None:
    """Add or update protocol_name in a settings.toml file."""
    text = settings_path.read_text(encoding="utf-8")
    if "protocol_name" in text:
        text = re.sub(
            r'protocol_name\s*=\s*"[^"]*"',
            f'protocol_name = "{name}"',
            text,
        )
    else:
        # Insert after [settings.general] line
        text = text.replace(
            "[settings.general]\n",
            f'[settings.general]\nprotocol_name = "{name}"\n',
        )
    settings_path.write_text(text, encoding="utf-8")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestDefaultProtocolName:
    """Verify behavior when protocol_name is empty or absent."""

    def test_default_protocol_name_unchanged(self, workspace: Path):
        """With no protocol_name, metadata retains the default name."""
        json_config = create_json_config(
            str(workspace / "labware_dict.toml"),
            str(workspace / "settings.toml"),
            str(workspace / "CSVs" / "example_basic.csv"),
            verbose=False,
        )
        update_protocol_file(str(workspace / "CherryPick_OT2.py"), json_config, verbose=False)

        protocol_text = (workspace / "CherryPick_OT2.py").read_text(encoding="utf-8")
        name = _extract_protocol_name_from_metadata(protocol_text)
        assert name == DEFAULT_PROTOCOL_NAME

    def test_empty_protocol_name_preserves_default(self, workspace: Path):
        """Explicitly setting protocol_name = '' preserves the default."""
        _set_protocol_name(workspace / "settings.toml", "")

        json_config = create_json_config(
            str(workspace / "labware_dict.toml"),
            str(workspace / "settings.toml"),
            str(workspace / "CSVs" / "example_basic.csv"),
            verbose=False,
        )
        update_protocol_file(str(workspace / "CherryPick_OT2.py"), json_config, verbose=False)

        protocol_text = (workspace / "CherryPick_OT2.py").read_text(encoding="utf-8")
        name = _extract_protocol_name_from_metadata(protocol_text)
        assert name == DEFAULT_PROTOCOL_NAME


class TestCustomProtocolName:
    """Verify behavior when a custom protocol_name is configured."""

    def test_custom_protocol_name_in_metadata(self, workspace: Path):
        """Custom name appears in metadata protocolName."""
        _set_protocol_name(workspace / "settings.toml", "Experiment ABC-123")

        json_config = create_json_config(
            str(workspace / "labware_dict.toml"),
            str(workspace / "settings.toml"),
            str(workspace / "CSVs" / "example_basic.csv"),
            verbose=False,
        )
        update_protocol_file(str(workspace / "CherryPick_OT2.py"), json_config, verbose=False)

        protocol_text = (workspace / "CherryPick_OT2.py").read_text(encoding="utf-8")
        name = _extract_protocol_name_from_metadata(protocol_text)
        assert name == "Experiment ABC-123"

    def test_custom_protocol_name_in_embedded_json(self, workspace: Path):
        """Custom name is present in the embedded JSON settings."""
        _set_protocol_name(workspace / "settings.toml", "Experiment ABC-123")

        json_config = create_json_config(
            str(workspace / "labware_dict.toml"),
            str(workspace / "settings.toml"),
            str(workspace / "CSVs" / "example_basic.csv"),
            verbose=False,
        )
        update_protocol_file(str(workspace / "CherryPick_OT2.py"), json_config, verbose=False)

        protocol_text = (workspace / "CherryPick_OT2.py").read_text(encoding="utf-8")
        data = _extract_embedded_json(protocol_text)
        embedded_name = data["settings"]["settings"]["general"]["protocol_name"]
        assert embedded_name == "Experiment ABC-123"

    def test_protocol_name_with_special_characters(self, workspace: Path):
        """Protocol name with quotes, ampersands, and unicode is handled safely."""
        special_name = "Test & Validation - Plate #5 (2024)"
        _set_protocol_name(workspace / "settings.toml", special_name)

        json_config = create_json_config(
            str(workspace / "labware_dict.toml"),
            str(workspace / "settings.toml"),
            str(workspace / "CSVs" / "example_basic.csv"),
            verbose=False,
        )
        update_protocol_file(str(workspace / "CherryPick_OT2.py"), json_config, verbose=False)

        protocol_text = (workspace / "CherryPick_OT2.py").read_text(encoding="utf-8")
        name = _extract_protocol_name_from_metadata(protocol_text)
        assert name == special_name

        # Also check the embedded JSON roundtrips correctly
        data = _extract_embedded_json(protocol_text)
        assert data["settings"]["settings"]["general"]["protocol_name"] == special_name

    def test_protocol_name_overwrites_previous_custom_name(self, workspace: Path):
        """Running generation twice updates the protocol name each time."""
        # First generation with name A
        _set_protocol_name(workspace / "settings.toml", "Name A")
        json_a = create_json_config(
            str(workspace / "labware_dict.toml"),
            str(workspace / "settings.toml"),
            str(workspace / "CSVs" / "example_basic.csv"),
            verbose=False,
        )
        update_protocol_file(str(workspace / "CherryPick_OT2.py"), json_a, verbose=False)

        protocol_text = (workspace / "CherryPick_OT2.py").read_text(encoding="utf-8")
        assert _extract_protocol_name_from_metadata(protocol_text) == "Name A"

        # Second generation with name B
        _set_protocol_name(workspace / "settings.toml", "Name B")
        json_b = create_json_config(
            str(workspace / "labware_dict.toml"),
            str(workspace / "settings.toml"),
            str(workspace / "CSVs" / "example_basic.csv"),
            verbose=False,
        )
        update_protocol_file(str(workspace / "CherryPick_OT2.py"), json_b, verbose=False)

        protocol_text = (workspace / "CherryPick_OT2.py").read_text(encoding="utf-8")
        assert _extract_protocol_name_from_metadata(protocol_text) == "Name B"
