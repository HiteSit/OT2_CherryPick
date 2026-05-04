"""Pytest fixtures shared across MCP integration tests."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any, Dict

import pytest
from langchain_mistralai import ChatMistralAI
from mcp_use import MCPAgent, MCPClient

from .helpers import AgentRunner, ProjectSetup
from .test_data import CSV_BASIC


class _AllowedLicenseDecision:
    mode = "normal-mode"


@pytest.fixture(autouse=True)
def allow_protocol_generation_license(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep ordinary tests off the live license Worker."""

    from ot2_cherrypick_mcp.core import protocol_generator

    monkeypatch.setattr(
        protocol_generator,
        "check_generation_license",
        lambda: _AllowedLicenseDecision(),
    )


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Return the repository root used as a template for test projects."""

    return Path(__file__).resolve().parents[1]


@pytest.fixture
def project_setup(project_root: Path) -> ProjectSetup:
    """Provide a ProjectSetup helper bound to the repository root."""

    return ProjectSetup(project_root=project_root)


@pytest.fixture
def project_dir(tmp_path: Path, project_setup: ProjectSetup) -> Path:
    """Provision a standard project directory with template assets."""

    project = project_setup.create_standard_project(tmp_path)
    _log_fixture_paths("project_dir", project)
    return project


@pytest.fixture
def empty_project_dir(tmp_path: Path, project_setup: ProjectSetup) -> Path:
    """Provide an empty project directory for initialize_project tests."""

    project = project_setup.create_empty_project(tmp_path)
    _log_fixture_paths("empty_project_dir", project, include_existing=False)
    return project


@pytest.fixture
def build_mcp_config(project_root: Path) -> Callable[[Path], Dict[str, Any]]:
    """Factory producing MCP configuration dictionaries for a given project."""

    def _build(project_dir: Path) -> Dict[str, Any]:
        return {
            "mcpServers": {
                "ot2-cherrypick": {
                    "command": "uv",
                    "args": [
                        "--directory", str(project_root),
                        "run",
                        "ot2-mcp-server",
                    ],
                    "env": {
                        "OPENTRONS_DIR": str(project_root),
                        "OT2_PROJECT_DIR": str(project_dir),
                    },
                }
            }
        }

    return _build


@pytest.fixture
def agent_factory(
    build_mcp_config: Callable[[Path], Dict[str, Any]]
) -> Callable[..., AgentRunner]:
    """Factory for creating AgentRunner instances bound to specific projects."""

    def _factory(project_dir: Path, *, max_steps: int = 20) -> AgentRunner:
        def builder(max_steps_override: int | None) -> tuple[MCPAgent, MCPClient]:
            config = build_mcp_config(project_dir)
            client = MCPClient(config=config)
            llm = ChatMistralAI(model="mistral-small-2506")
            agent = MCPAgent(
                llm=llm,
                client=client,
                max_steps=max_steps_override if max_steps_override is not None else max_steps,
            )
            return agent, client

        return AgentRunner(builder)

    return _factory


@pytest.fixture
def agent_runner(project_dir: Path, agent_factory: Callable[..., AgentRunner]) -> AgentRunner:
    """AgentRunner instance bound to the standard project directory."""

    return agent_factory(project_dir)


@pytest.fixture
def project_with_csv(tmp_path: Path, project_setup: ProjectSetup) -> Path:
    """Project directory pre-populated with a CSV transfer map."""

    project = project_setup.create_with_csv(tmp_path, CSV_BASIC, filename="test.csv")
    _log_fixture_paths("project_with_csv", project)
    return project


@pytest.fixture
def project_with_protocol(tmp_path: Path, project_setup: ProjectSetup) -> Path:
    """Project directory that already contains the protocol template."""

    project = project_setup.create_with_protocol(tmp_path)
    _log_fixture_paths("project_with_protocol", project)
    return project


def _log_fixture_paths(label: str, project_dir: Path, *, include_existing: bool = True) -> None:
    """Emit helpful debugging information about the generated project directory."""

    if include_existing:
        files = ", ".join(sorted(p.name for p in project_dir.iterdir()))
    else:
        files = "(empty)"
    print(
        f"[{label}] project_dir={project_dir} contents={files}",
        flush=True,
    )
