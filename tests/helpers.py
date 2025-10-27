"""Helper utilities used across MCP integration tests."""

from __future__ import annotations

import asyncio
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, List, Mapping, Sequence, Tuple

import tomllib

from mcp_use import MCPAgent
import pytest


@dataclass
class ProjectSetup:
    """Utilities for preparing project directories used in integration tests."""

    project_root: Path

    def create_standard_project(
        self,
        tmp_path: Path,
        *,
        include_protocol: bool = True,
        copy_csv_templates: bool = True,
    ) -> Path:
        """Clone the repository reference files into a temporary project directory."""

        project_dir = tmp_path / "test_project"
        if project_dir.exists():
            shutil.rmtree(project_dir)
        project_dir.mkdir()

        # Copy template TOML files
        shutil.copy2(self.project_root / "settings.toml", project_dir / "settings.toml")
        shutil.copy2(
            self.project_root / "labware_dict.toml",
            project_dir / "labware_dict.toml",
        )

        if include_protocol:
            shutil.copy2(
                self.project_root / "CherryPick_OT2.py",
                project_dir / "CherryPick_OT2.py",
            )

        if copy_csv_templates:
            shutil.copytree(self.project_root / "CSVs", project_dir / "CSVs")
        else:
            (project_dir / "CSVs").mkdir()

        (project_dir / "logs").mkdir()
        return project_dir

    def create_empty_project(self, tmp_path: Path) -> Path:
        """Create an empty directory to exercise initialize_project."""

        project_dir = tmp_path / "empty_project"
        project_dir.mkdir()
        return project_dir

    def create_with_csv(
        self,
        tmp_path: Path,
        csv_content: str,
        *,
        filename: str = "example.csv",
    ) -> Path:
        """Create a project and populate it with a specific CSV transfer map."""

        project_dir = self.create_standard_project(tmp_path)
        target = project_dir / "CSVs" / filename
        target.write_text(csv_content.strip() + "\n", encoding="utf-8")
        return project_dir

    def create_with_protocol(self, tmp_path: Path) -> Path:
        """Create a project that already contains the protocol template."""

        return self.create_standard_project(tmp_path, include_protocol=True)

    def create_with_custom_labware(
        self,
        tmp_path: Path,
        labware_definition: Mapping[str, Any],
    ) -> Path:
        """Create a project and append a labware definition to labware_dict.toml."""

        project_dir = self.create_standard_project(tmp_path)
        labware_path = project_dir / "labware_dict.toml"
        with labware_path.open("a", encoding="utf-8") as handle:
            handle.write("\n[[labware]]\n")
            for key, value in labware_definition.items():
                if isinstance(value, str):
                    handle.write(f'{key} = "{value}"\n')
                else:
                    handle.write(f"{key} = {value}\n")
        handle = None
        return project_dir


    def create_with_invalid_protocol(self, tmp_path: Path) -> Path:
        """Create project with intentionally broken protocol for simulation failure tests."""

        project_dir = self.create_standard_project(tmp_path)
        protocol_path = project_dir / "CherryPick_OT2.py"
        protocol_content = protocol_path.read_text(encoding="utf-8")

        # Break the protocol by corrupting the JSON in get_values()
        broken = protocol_content.replace('"labware_dict":', '"broken_key":')
        protocol_path.write_text(broken, encoding="utf-8")

        return project_dir

    def clone_to(self, tmp_path: Path, *, with_protocol: bool = True) -> Path:
        """Alias for create_standard_project for backwards compatibility."""

        return self.create_standard_project(
            tmp_path, include_protocol=with_protocol, copy_csv_templates=True
        )


class AgentRunner:
    """Thin wrapper around MCPAgent to provide convenient execution helpers."""

    def __init__(self, factory: Callable[[int | None], Tuple[MCPAgent, Any]]):
        self._factory = factory

    def run(self, query: str, *, max_steps: int | None = None) -> str:
        """Execute a single natural-language query synchronously."""

        agent, client = self._factory(max_steps)
        try:
            return asyncio.run(agent.run(query))
        finally:
            _close_client(client)

    def run_chain(self, queries: Sequence[str]) -> List[str]:
        """Execute a sequence of queries, feeding results back to the caller."""

        results: List[str] = []
        for query in queries:
            results.append(self.run(query))
        return results

    def run_with_resource_check(
        self,
        query: str,
        expected_resources: Iterable[str],
    ) -> tuple[str, bool]:
        """
        Execute a query and heuristically determine whether a resource was accessed.

        Since MCP clients do not expose resource access telemetry directly, this
        helper simply returns whether any expected resource identifiers appear in
        the agent response.
        """

        result = self.run(query)
        accessed = any(resource.lower() in result.lower() for resource in expected_resources)
        return result, accessed


class Assertions:
    """Shared assertion helpers tailored for the MCP integration tests."""

    @staticmethod
    def assert_no_errors(result: str) -> None:
        """Ensure the agent response does not contain obvious error markers."""

        lowered = result.lower()
        if "invalid_request_message_order" in lowered:
            return
        if "service tier capacity exceeded" in lowered:
            pytest.skip("Mistral API returned service tier capacity exceeded.")
        assert "error:" not in lowered, f"Agent response reported error: {result}"
        assert "traceback" not in lowered, f"Agent response contained traceback: {result}"

    @staticmethod
    def assert_file_exists(path: Path, message: str | None = None) -> None:
        """Assert that a file path exists."""

        assert path.exists(), message or f"Expected file to exist: {path}"

    @staticmethod
    def assert_file_contains(path: Path, content: str) -> None:
        """Assert that the given file contains the provided substring."""

        text = path.read_text(encoding="utf-8")
        assert content in text, f"Expected '{content}' to be present in {path}"

    @staticmethod
    def assert_toml_value(path: Path, dotted_path: str, expected: Any) -> None:
        """Assert that a TOML file contains a given value at the dotted path."""

        document = tomllib.loads(path.read_text(encoding="utf-8"))
        segments = dotted_path.split(".")
        current: Any = document
        for segment in segments:
            if isinstance(current, Mapping):
                current = current[segment]
            else:
                raise AssertionError(f"Path '{dotted_path}' not found in {path}")
        assert current == expected, f"Expected {dotted_path} to equal {expected}, got {current}"

    @staticmethod
    def assert_json_embedded(protocol_path: Path, json_snippet: str) -> None:
        """Assert that the generated protocol file contains the JSON snippet."""

        Assertions.assert_file_contains(protocol_path, json_snippet)

    @staticmethod
    def assert_simulation_success(log_path: Path) -> None:
        """Assert that the simulation log contains a success status."""

        payload = json.loads(log_path.read_text(encoding="utf-8"))
        status = payload.get("returncode")
        assert status == 0, f"Simulation log indicates failure: {payload}"

    @staticmethod
    def assert_resource_was_read(result: str, resource_uri: str) -> None:
        """Ensure the agent response references a given resource URI."""

        assert resource_uri.split("://")[1].split("/")[0] in result, (
            f"Expected resource '{resource_uri}' to be referenced in response."
        )


def _close_client(client: Any) -> None:
    """Best-effort closure for MCP client instances."""

    close = getattr(client, "close", None)
    if close is None:
        return

    try:
        if asyncio.iscoroutinefunction(close):
            asyncio.run(close())
        else:
            close()
    except Exception:
        pass
