"""Tests verifying HEALTHCHECK directives exist in project Dockerfiles."""

import re
import subprocess
from pathlib import Path

import pytest

DOCKER_DIR = Path(__file__).resolve().parents[2] / "docker"
ENTRYPOINT_SCRIPT = DOCKER_DIR / "backend-entrypoint.sh"


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

    def test_backend_entrypoint_configured(self) -> None:
        assert 'ENTRYPOINT ["/app/docker/backend-entrypoint.sh"]' in self.content
        assert "chmod +x docker/backend-entrypoint.sh" in self.content

    def test_activation_marker_not_required_at_build_time(self) -> None:
        assert not re.search(r"(?m)^COPY\s+\.activation\.needs\b", self.content)
        assert not re.search(r"(?m)^ADD\s+\.activation\.needs\b", self.content)


class TestFrontendDockerfileHealthcheck:
    """Sanity-check that the frontend Dockerfile also has a HEALTHCHECK."""

    def test_healthcheck_directive_exists(self) -> None:
        content = _read_dockerfile("Dockerfile.frontend")
        assert "HEALTHCHECK" in content

    def test_healthcheck_uses_ipv4_loopback(self) -> None:
        content = _read_dockerfile("Dockerfile.frontend")
        assert "http://127.0.0.1/health" in content
        assert "http://localhost/health" not in content


class TestBackendDockerLicenseWiring:
    """Verify Docker passes the backend license identity."""

    def test_compose_passes_machine_identity_to_backend(self) -> None:
        content = (DOCKER_DIR / "docker-compose.yml").read_text()
        assert "COMPUTER_ID: ${COMPUTER_ID}" in content

    def test_env_example_defines_machine_identity_and_env_stays_local(self) -> None:
        example = (DOCKER_DIR / ".env.example").read_text()
        gitignore = (DOCKER_DIR.parent / ".gitignore").read_text()

        assert "docker/.env\n" in gitignore
        assert "docker/.env.example" not in gitignore
        assert "COMPUTER_ID=YOUR_MACHINE_NAME" in example

    def test_entrypoint_does_not_materialize_activation_marker(self) -> None:
        content = ENTRYPOINT_SCRIPT.read_text()
        assert ".activation.needs" not in content
        assert 'exec "$@"' in content

    def test_entrypoint_smoke_execs_command(self) -> None:
        result = subprocess.run(
            ["sh", str(ENTRYPOINT_SCRIPT), "true"],
            text=True,
            capture_output=True,
            check=False,
        )

        assert result.returncode == 0, result.stderr
