# Testing Patterns

**Analysis Date:** 2026-01-20

## Test Framework

**Runner:**
- pytest 8.4.2
- No explicit config file (`pytest.ini` or `pyproject.toml [tool.pytest]`)
- Tests discovered automatically via `test_*.py` naming

**Assertion Library:**
- pytest's built-in assertions
- Custom `Assertions` helper class in `tests/helpers.py`

**Run Commands:**
```bash
uv run pytest tests/                    # Run all tests
uv run pytest tests/ -v                 # Verbose output
uv run pytest tests/ -k "test_name"     # Filter by name
uv run pytest tests/test_tools.py       # Specific file
uv run pytest tests/ --cov              # Coverage (if configured)
```

## Test File Organization

**Location:**
- Separate `tests/` directory at repository root
- Co-located with source code via relative imports

**Naming:**
- `test_<module_name>.py` matches source module names
- Test functions: `test_<scenario_description>()`

**Structure:**
```
tests/
  __init__.py               # Enables package imports
  conftest.py               # Shared fixtures
  helpers.py                # Test utilities (ProjectSetup, AgentRunner, Assertions)
  test_data.py              # Centralized test data and scenarios
  test_toml_handler.py      # Unit tests for TomlHandler
  test_validation.py        # Unit tests for validation module
  test_config_tools.py      # Unit tests for config_tools
  test_tools.py             # Unit tests for protocol_tools
  test_mcp_integration.py   # Integration tests with MCP agents
  test_workflow_tools.py    # Workflow tool tests
  test_simulation_tools.py  # Simulation tool tests
  test_deployment_tools.py  # Deployment tool tests
  test_labware_tools.py     # Labware tool tests
  test_csv_tools.py         # CSV tool tests
  test_prompts.py           # Prompt tests
  test_resources.py         # Resource tests
  test_home_control.py      # HOME control row tests
  test_formatters.py        # Output formatter tests
  test_project_tools.py     # Project initialization tests
  e2e/                      # End-to-end tests
  fastapi/                  # FastAPI backend tests
```

## Test Structure

**Suite Organization:**
```python
"""Tests for TOML handler utilities."""

from __future__ import annotations

from pathlib import Path

import pytest

from ot2_cherrypick_mcp.utils.errors import ConfigurationError
from ot2_cherrypick_mcp.utils.toml import TomlHandler


def _copy_settings(tmp_path: Path) -> Path:
    """Helper to copy settings.toml to temp directory."""
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
    assert handler.get_value("settings.general.tip_reuse") == "always"


def test_toml_handler_invalid_path_raises(tmp_path: Path, monkeypatch) -> None:
    """Invalid paths raise configuration errors."""
    settings_copy = _copy_settings(tmp_path)
    monkeypatch.setenv("OT2_PROJECT_DIR", str(tmp_path))
    handler = TomlHandler("settings.toml")
    with pytest.raises(ConfigurationError):
        handler.get_value("settings.missing.section")
```

**Patterns:**
- Docstrings describe expected behavior
- Local helper functions prefixed with underscore: `_copy_settings()`, `_setup_inputs()`
- Each test isolates to `tmp_path` fixture
- `monkeypatch` used for environment variables

## Fixtures (conftest.py)

**Shared Fixtures:**
```python
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
def agent_factory(
    build_mcp_config: Callable[[Path], Dict[str, Any]]
) -> Callable[..., AgentRunner]:
    """Factory for creating AgentRunner instances bound to specific projects."""
    def _factory(project_dir: Path, *, max_steps: int = 20) -> AgentRunner:
        # ...build agent with MCP client
        return AgentRunner(builder)
    return _factory
```

**Fixture Patterns:**
- `scope="session"` for expensive setup (project_root)
- Factory fixtures return callables for flexible instantiation
- Logging helpers for debugging: `_log_fixture_paths()`

## Mocking

**Framework:** pytest's built-in `monkeypatch` fixture

**Patterns:**
```python
def test_update_settings_value_overrides_scalar(tmp_path: Path) -> None:
    """Updating a scalar value writes the new content and backup."""
    settings_copy = _copy_settings(tmp_path)
    result = update_settings_value(
        path="settings.general.tip_reuse",
        value='"never"',
        settings_path=str(settings_copy),
    )
    assert result["old_value"] == "always"
    assert result["new_value"] == "never"
```

**Environment Mocking:**
```python
def test_toml_handler_handles_array_indices(tmp_path: Path, monkeypatch) -> None:
    settings_copy = _copy_settings(tmp_path)
    monkeypatch.setenv("OT2_PROJECT_DIR", str(tmp_path))
    handler = TomlHandler("settings.toml")
    assert handler.get_value("settings.working_plate[0].type") == "source"
```

**What to Mock:**
- Environment variables (`OT2_PROJECT_DIR`, `LABWARE_PATH`)
- File system via `tmp_path` fixture (pytest built-in)
- External API calls (MCP client initialization)

**What NOT to Mock:**
- Actual TOML/CSV parsing (tested against real files)
- Validation logic (core business logic under test)
- File writes (verified by reading back)

## Test Data (test_data.py)

**Test Data Centralization:**
```python
CSV_BASIC = """\
Source Labware,Source Well,Volume (ul),Dest Labware,Dest Well,Source Height,Dest Top
tube_rack_96_1500ul_4,A1,100,384_ppv_55ul_2,B1,2,-5
tube_rack_96_1500ul_4,A2,50,384_ppv_55ul_2,B2,2,-5
""".strip()

CSV_WITH_MIXING = """\
Source Labware,Source Well,Volume (ul),Dest Labware,Dest Well,Source Height,Dest Top,Mix Before,Mix After
tube_rack_96_1500ul_4,A1,120,custom_384_pcr_2,B1,2,-5,Yes,Yes
""".strip()

UPDATE_SETTINGS_SCENARIOS: List[Tuple[str, str, str, str]] = [
    (
        "settings.general.tip_reuse",
        "never",
        'tip_reuse = "never"',
        "Use the update_settings tool to set path 'settings.general.tip_reuse' to 'never'",
    ),
    # ... more scenarios
]

LIQUID_PRESET_SCENARIOS: List[Tuple[str, Dict[str, Any]]] = [
    ("standard", {"delays.post_aspirate": 0, "push_out.enabled": False}),
    ("viscous", {"delays.post_aspirate": 2.0, "push_out.enabled": True}),
]
```

**Location:**
- `tests/test_data.py` for shared test data

## Parametrized Tests

**Pattern:**
```python
@pytest.mark.parametrize("path,value,expected,prompt", UPDATE_SETTINGS_SCENARIOS)
def test_agent_updates_settings(
    tmp_path: Path,
    project_setup: ProjectSetup,
    agent_factory: Callable[..., AgentRunner],
    path: str,
    value: str,
    expected: str,
    prompt: str,
) -> None:
    """Test that agent can update settings via natural language."""
    project_dir: Path = project_setup.create_standard_project(tmp_path)
    runner: AgentRunner = agent_factory(project_dir, max_steps=8)

    query = f"{prompt} in the settings file"
    result = runner.run(query)
    Assertions.assert_no_errors(result)

    settings_file = project_dir / "settings.toml"
    updated = settings_file.read_text(encoding="utf-8")
    assert expected in updated
```

## Coverage

**Requirements:** No formal coverage target enforced

**View Coverage:**
```bash
uv run pytest tests/ --cov=src/ot2_cherrypick_mcp --cov-report=term-missing
```

**Coverage Gaps:**
- MCP tool wrapper functions use `# pragma: no cover` (tested via integration)
- External simulation calls (require OT-2 environment)

## Test Types

**Unit Tests:**
- Direct function calls with controlled inputs
- Test files: `test_toml_handler.py`, `test_validation.py`, `test_config_tools.py`
- Isolate to `tmp_path` with copied config files
- Fast execution, no external dependencies

**Integration Tests:**
- MCP agent interactions via `mcp-use` library
- Test file: `test_mcp_integration.py`
- Use Mistral LLM (`mistral-small-2506`) for natural language processing
- Marked with `@pytest.mark.slow` for optional skipping

**E2E Tests:**
- Full workflow from configuration to protocol generation
- Located in `tests/e2e/` directory
- Marked with `@pytest.mark.pipeline_test`

## Test Markers

**Custom Markers:**
```python
@pytest.mark.slow                    # Long-running tests
@pytest.mark.requires_simulation     # Requires opentrons_simulate
@pytest.mark.pipeline_test           # Full workflow tests
@pytest.mark.resource_test           # MCP resource tests
@pytest.mark.error_scenario          # Tests expected failure paths
```

## Helper Classes (helpers.py)

**ProjectSetup:**
```python
@dataclass
class ProjectSetup:
    """Utilities for preparing project directories used in integration tests."""

    project_root: Path

    def create_standard_project(self, tmp_path: Path, ...) -> Path:
        """Clone the repository reference files into a temporary project directory."""

    def create_empty_project(self, tmp_path: Path) -> Path:
        """Create an empty directory to exercise initialize_project."""

    def create_with_csv(self, tmp_path: Path, csv_content: str, ...) -> Path:
        """Create a project and populate it with a specific CSV transfer map."""

    def create_with_invalid_protocol(self, tmp_path: Path) -> Path:
        """Create project with intentionally broken protocol for simulation failure tests."""
```

**AgentRunner:**
```python
class AgentRunner:
    """Thin wrapper around MCPAgent to provide convenient execution helpers."""

    def run(self, query: str, *, max_steps: int | None = None) -> str:
        """Execute a single natural-language query synchronously."""

    def run_chain(self, queries: Sequence[str]) -> List[str]:
        """Execute a sequence of queries, feeding results back to the caller."""
```

**Assertions:**
```python
class Assertions:
    """Shared assertion helpers tailored for the MCP integration tests."""

    @staticmethod
    def assert_no_errors(result: str) -> None:
        """Ensure the agent response does not contain obvious error markers."""
        lowered = result.lower()
        assert "error:" not in lowered
        assert "traceback" not in lowered

    @staticmethod
    def assert_file_exists(path: Path, message: str | None = None) -> None:
        assert path.exists(), message or f"Expected file to exist: {path}"

    @staticmethod
    def assert_file_contains(path: Path, content: str) -> None:
        text = path.read_text(encoding="utf-8")
        assert content in text

    @staticmethod
    def assert_toml_value(path: Path, dotted_path: str, expected: Any) -> None:
        """Assert that a TOML file contains a given value at the dotted path."""
```

## Common Patterns

**Async Testing:**
```python
def run(self, query: str, *, max_steps: int | None = None) -> str:
    """Execute a single natural-language query synchronously."""
    agent, client = self._factory(max_steps)
    try:
        return asyncio.run(agent.run(query))  # Sync wrapper around async
    finally:
        _close_client(client)
```

**Error Testing:**
```python
def test_update_settings_invalid_path_errors(tmp_path: Path) -> None:
    """Invalid dotted paths raise configuration errors."""
    settings_copy = _copy_settings(tmp_path)
    with pytest.raises(ConfigurationError):
        update_settings_value(
            path="settings.missing.section",
            value="false",
            settings_path=str(settings_copy),
        )
```

**File Verification:**
```python
def test_toml_handler_set_value_updates_file(tmp_path: Path) -> None:
    """Setting a value writes the file and produces a backup."""
    settings_copy = _copy_settings(tmp_path)
    handler = TomlHandler(settings_copy)

    old_value, new_value = handler.set_value("settings.general.tip_reuse", "never")

    assert old_value == "always"
    assert new_value == "never"

    content = settings_copy.read_text(encoding="utf-8")
    assert "tip_reuse = \"never\"" in content

    backup = settings_copy.with_suffix(settings_copy.suffix + ".backup")
    assert backup.exists()
```

**MCP Integration Testing:**
```python
def test_agent_runs_workflow_from_string(project_dir: Path, agent_runner: AgentRunner) -> None:
    """Test that agent can upload CSV and run workflow."""
    csv_dir = project_dir / "CSVs"
    tmp_target = csv_dir / "tmp_uploaded.csv"
    tmp_target.unlink(missing_ok=True)

    query = (
        "I have some transfer data in CSV format that I'd like you to save to "
        "'CSVs/tmp_uploaded.csv'. After saving it, please generate and validate the protocol "
        "(but skip the simulation step). Here's the CSV data:\n\n"
        f"{CSV_BASIC}\n\n"
        "Let me know if everything worked correctly."
    )

    result = agent_runner.run(query)
    Assertions.assert_no_errors(result)
    Assertions.assert_file_exists(tmp_target)
```

## Test Configuration

**MCP Client Config:**
```python
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
                    "LABWARE_PATH": str(project_root),
                    "OT2_PROJECT_DIR": str(project_dir),
                },
            }
        }
    }
```

**LLM Configuration:**
```python
llm = ChatMistralAI(model="mistral-small-2506")
agent = MCPAgent(llm=llm, client=client, max_steps=max_steps)
```

---

*Testing analysis: 2026-01-20*
