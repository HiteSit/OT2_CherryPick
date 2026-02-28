"""Tests verifying HEALTHCHECK directives exist in project Dockerfiles."""

from pathlib import Path

import pytest

DOCKER_DIR = Path(__file__).resolve().parents[2] / "docker"


def _read_dockerfile(name: str) -> str:
    """Read a Dockerfile from the docker/ directory and return its text."""
    path = DOCKER_DIR / name
    assert path.exists(), f"{path} not found"
    return path.read_text()


class TestBackendDockerfileHealthcheck:
    """Verify the backend Dockerfile contains a valid HEALTHCHECK."""

    @pytest.fixture(autouse=True)
    def _load(self) -> None:
        self.content = _read_dockerfile("Dockerfile.backend")

    def test_healthcheck_directive_exists(self) -> None:
        assert "HEALTHCHECK" in self.content

    def test_healthcheck_references_port_8000(self) -> None:
        assert "localhost:8000" in self.content

    def test_healthcheck_before_cmd(self) -> None:
        hc_pos = self.content.index("HEALTHCHECK")
        cmd_pos = self.content.index("\nCMD ")
        assert hc_pos < cmd_pos, "HEALTHCHECK must appear before CMD"


class TestFrontendDockerfileHealthcheck:
    """Sanity-check that the frontend Dockerfile also has a HEALTHCHECK."""

    def test_healthcheck_directive_exists(self) -> None:
        content = _read_dockerfile("Dockerfile.frontend")
        assert "HEALTHCHECK" in content
