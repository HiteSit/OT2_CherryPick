"""Tests for UUID reuse behavior in deploy_to_opentrons_dir()."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from ot2_cherrypick_mcp.core.deployment import (
    _extract_protocol_name,
    _find_existing_protocol_uuid,
    deploy_to_opentrons_dir,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_fake_protocol(opentrons_dir: Path, uuid_str: str, protocol_name: str) -> Path:
    """Create a minimal protocol file inside a fake Opentrons directory structure."""
    src_dir = opentrons_dir / "protocols" / uuid_str / "src"
    src_dir.mkdir(parents=True)
    (opentrons_dir / "protocols" / uuid_str / "analysis").mkdir(parents=True)
    protocol_file = src_dir / "CherryPick_OT2.py"
    protocol_file.write_text(
        f"metadata = {{\n    'protocolName': '{protocol_name}',\n}}\n"
    )
    return protocol_file


def _create_source_protocol(tmp_path: Path, protocol_name: str) -> Path:
    """Create a source protocol file to deploy."""
    protocol = tmp_path / "source" / "CherryPick_OT2.py"
    protocol.parent.mkdir(parents=True, exist_ok=True)
    protocol.write_text(
        f"metadata = {{\n    'protocolName': '{protocol_name}',\n}}\n"
    )
    return protocol


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def mock_analysis(monkeypatch):
    """Disable protocol analysis which requires opentrons.cli."""
    monkeypatch.setattr(
        "ot2_cherrypick_mcp.core.deployment._run_protocol_analysis",
        lambda protocol_path, analysis_dir, labware_dir, **kw: None,
    )


@pytest.fixture()
def opentrons_dir(tmp_path: Path) -> Path:
    """Create a fake Opentrons root directory."""
    ot_dir = tmp_path / "Opentrons"
    ot_dir.mkdir()
    (ot_dir / "protocols").mkdir()
    return ot_dir


# ---------------------------------------------------------------------------
# Unit tests for _extract_protocol_name
# ---------------------------------------------------------------------------

class TestExtractProtocolName:

    def test_extracts_name_from_file(self, tmp_path: Path) -> None:
        protocol = tmp_path / "proto.py"
        protocol.write_text("metadata = {\n    'protocolName': 'My Experiment',\n}\n")
        assert _extract_protocol_name(protocol) == "My Experiment"

    def test_returns_none_when_missing(self, tmp_path: Path) -> None:
        protocol = tmp_path / "proto.py"
        protocol.write_text("metadata = {\n    'apiLevel': '2.15',\n}\n")
        assert _extract_protocol_name(protocol) is None

    def test_returns_none_for_nonexistent_file(self, tmp_path: Path) -> None:
        assert _extract_protocol_name(tmp_path / "nonexistent.py") is None


# ---------------------------------------------------------------------------
# Unit tests for _find_existing_protocol_uuid
# ---------------------------------------------------------------------------

class TestFindExistingProtocolUuid:

    def test_finds_matching_uuid(self, opentrons_dir: Path) -> None:
        _create_fake_protocol(opentrons_dir, "aaaa-bbbb-cccc", "TestProtocol")
        result = _find_existing_protocol_uuid(opentrons_dir, "TestProtocol")
        assert result == "aaaa-bbbb-cccc"

    def test_returns_none_when_no_match(self, opentrons_dir: Path) -> None:
        _create_fake_protocol(opentrons_dir, "aaaa-bbbb-cccc", "OtherProtocol")
        result = _find_existing_protocol_uuid(opentrons_dir, "TestProtocol")
        assert result is None

    def test_multiple_matches_uses_newest(self, opentrons_dir: Path) -> None:
        old_file = _create_fake_protocol(opentrons_dir, "old-uuid-0001", "SameName")
        # Ensure different mtimes by back-dating the old file
        old_mtime = time.time() - 100
        import os
        os.utime(old_file, (old_mtime, old_mtime))

        _create_fake_protocol(opentrons_dir, "new-uuid-0002", "SameName")

        result = _find_existing_protocol_uuid(opentrons_dir, "SameName")
        assert result == "new-uuid-0002"


# ---------------------------------------------------------------------------
# Integration tests for deploy_to_opentrons_dir
# ---------------------------------------------------------------------------

class TestDeployToOpentronsDirUuidReuse:

    def test_reuses_existing_uuid(self, tmp_path: Path, opentrons_dir: Path) -> None:
        _create_fake_protocol(opentrons_dir, "existing-uuid-1234", "MyProtocol")
        source = _create_source_protocol(tmp_path, "MyProtocol")

        result = deploy_to_opentrons_dir(source, opentrons_dir)

        assert result["uuid"] == "existing-uuid-1234"
        assert result["reused"] is True
        assert Path(result["deployed_path"]).exists()

    def test_creates_new_uuid_for_different_name(self, tmp_path: Path, opentrons_dir: Path) -> None:
        _create_fake_protocol(opentrons_dir, "existing-uuid-1234", "ProtocolA")
        source = _create_source_protocol(tmp_path, "ProtocolB")

        result = deploy_to_opentrons_dir(source, opentrons_dir)

        assert result["uuid"] != "existing-uuid-1234"
        assert result["reused"] is False
        assert Path(result["deployed_path"]).exists()

    def test_no_name_creates_new_uuid(self, tmp_path: Path, opentrons_dir: Path) -> None:
        _create_fake_protocol(opentrons_dir, "existing-uuid-1234", "SomeProtocol")

        # Source protocol without protocolName
        source = tmp_path / "source" / "CherryPick_OT2.py"
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text("metadata = {\n    'apiLevel': '2.15',\n}\n")

        result = deploy_to_opentrons_dir(source, opentrons_dir)

        assert result["uuid"] != "existing-uuid-1234"
        assert result["reused"] is False

    def test_deploy_creates_expected_directory_structure(self, tmp_path: Path, opentrons_dir: Path) -> None:
        source = _create_source_protocol(tmp_path, "StructureTest")

        result = deploy_to_opentrons_dir(source, opentrons_dir)

        deployed = Path(result["deployed_path"])
        uuid_dir = deployed.parent.parent
        assert (uuid_dir / "src").is_dir()
        assert (uuid_dir / "analysis").is_dir()
        assert deployed.name == "CherryPick_OT2.py"
