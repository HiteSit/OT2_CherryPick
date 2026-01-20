# Coding Conventions

**Analysis Date:** 2026-01-20

## Naming Patterns

**Files:**
- `snake_case.py` for all Python modules
- Test files: `test_<module_name>.py` pattern in `tests/` directory
- Configuration: lowercase with underscores (`settings.toml`, `labware_dict.toml`)
- Protocol files: `PascalCase_OT2.py` (e.g., `CherryPick_OT2.py`)

**Functions:**
- `snake_case` for all functions and methods
- Private helpers prefixed with underscore: `_parse_value()`, `_load_toml()`, `_is_home_control_row()`
- Public API functions without prefix: `validate_configuration()`, `generate_protocol()`

**Variables:**
- `snake_case` for local variables and parameters
- `SCREAMING_SNAKE_CASE` for module-level constants: `CSV_BASE_REQUIRED`, `WELL_PATTERN`, `APP_NAME`
- Type aliases use `_PascalCase` with underscore: `_PathLike = Union[str, Path]`

**Classes:**
- `PascalCase` for class names: `TomlHandler`, `ProjectSetup`, `AgentRunner`, `Assertions`
- Dataclasses preferred for simple data containers
- Exception classes suffixed with `Error`: `MCPServerError`, `ConfigurationError`

**Types:**
- Type hints used throughout via `from __future__ import annotations`
- Return types explicitly annotated: `def get_value(self, dotted_path: str) -> object:`
- `Dict`, `List`, `Tuple` from typing module for complex types

## Code Style

**Formatting:**
- No explicit formatter configuration (no `.prettierrc`, `black.toml`, or `ruff.toml`)
- Follows PEP 8 conventions by convention
- 4-space indentation throughout
- Line length appears to be ~100-120 characters max

**Linting:**
- No explicit linting configuration detected
- Type checking via inline `# type: ignore` comments where needed
- `# pragma: no cover` for code paths exercised via MCP tool wrappers

**Docstrings:**
- Module-level docstrings explain purpose
- Function docstrings use Google-style format:
```python
def generate_protocol(labware_toml_path: str, ...) -> Dict[str, Any]:
    """
    High-level orchestration function for MCP usage.

    Args:
        labware_toml_path: Path to labware dictionary TOML file
        settings_toml_path: Path to settings TOML file
        ...

    Returns:
        dict: {
            'protocol_file': str - Path to updated protocol file
            'json_size': int - Size of embedded JSON config
            ...
        }

    Raises:
        FileNotFoundError: If any input file is missing
        ValueError: If validation or embedding fails
    """
```

## Import Organization

**Order:**
1. Future imports: `from __future__ import annotations`
2. Standard library: `os`, `json`, `re`, `csv`, `shutil`, `asyncio`
3. Third-party packages: `pytest`, `tomlkit`, `tomllib`, `fastmcp`
4. Local imports: relative imports within package

**Pattern example from `config_tools.py`:**
```python
from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date, datetime, time
from pathlib import Path
from typing import Any, Dict, List

import tomlkit
from fastmcp import FastMCP

try:  # Python 3.11+
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

from ..utils.errors import ConfigurationError
from ..utils.paths import resolve_project_path
from ..utils.toml import TomlHandler
```

**Path Aliases:**
- Relative imports within `src/ot2_cherrypick_mcp/` package: `from ..utils.errors import ConfigurationError`
- Direct imports for top-level scripts: `from src.ot2_cherrypick_mcp.core.protocol_generator import ...`

## Error Handling

**Custom Exception Hierarchy:**
```python
# src/ot2_cherrypick_mcp/utils/errors.py
class MCPServerError(Exception):
    """Base error for MCP server issues."""

class ConfigurationError(MCPServerError):
    """Raised when configuration files are invalid or missing."""

class ProtocolGenerationError(MCPServerError):
    """Raised when protocol compilation fails."""

class SimulationError(MCPServerError):
    """Raised when OT-2 protocol simulation fails."""

class DeploymentError(MCPServerError):
    """Raised when protocol deployment fails."""
```

**Error Pattern:**
- Catch specific exceptions, re-raise with context:
```python
try:
    preset_values = handler.get_value(preset_path)
except ConfigurationError as exc:
    raise ConfigurationError(f"Preset '{preset_name}' not found: {exc}") from exc
```

- Use `from exc` to chain exceptions and preserve traceback
- Validate early, fail fast with descriptive messages
- Include file paths and line numbers in error messages when possible

**Validation Pattern:**
- Collect all errors before returning (don't fail on first error)
- Return structured result with status, errors, warnings:
```python
def _result(errors: List[str], warnings: List[str]) -> Dict[str, object]:
    status = "error" if errors else "ok"
    return {"status": status, "errors": errors, "warnings": warnings}
```

## Logging

**Framework:** Standard `print()` for progress feedback

**Patterns:**
- Use `verbose` flag for optional output:
```python
def create_json_config(..., verbose: bool = True) -> str:
    if verbose:
        print(f"Reading configuration files...")
        print(f"  - Labware TOML: {labware_toml}")
```
- CLI scripts default `verbose=True`, library functions default `verbose=False`
- Progress indicators use checkmarks: `print("Successfully read all configuration files")`
- Flush output for real-time visibility in test logs: `print(..., flush=True)`

## Comments

**When to Comment:**
- Complex regex patterns get inline explanations
- Non-obvious business logic (e.g., OT-2 firmware requirements)
- Compatibility considerations:
```python
try:  # Python 3.11+
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib
```

**Pragma Comments:**
- `# pragma: no cover` - exclude from coverage (wrapper functions tested via integration)
- `# type: ignore` - suppress type checker warnings

**Block Comments:**
- Multi-line docstrings for module and function documentation
- Single-line `#` comments for implementation notes

## Function Design

**Size Guidelines:**
- Functions typically 10-40 lines
- Complex validation functions may reach 100+ lines but are well-structured
- Helper functions extracted for reusability

**Parameters:**
- Use keyword-only arguments for public APIs: `def validate_configuration(*, settings_path, labware_path, csv_path):`
- Default values for optional configuration: `verbose: bool = True`
- Path parameters accept `str | Path` for flexibility

**Return Values:**
- Return `Dict[str, object]` for MCP tool results (JSON-serializable)
- Include `message` field for human-readable status
- Include relevant metadata: file paths, sizes, counts
```python
return {
    "settings_file": str(handler.path),
    "path": path,
    "old_value": old_value,
    "new_value": new_value,
    "backup_file": str(handler.path.with_suffix(handler.path.suffix + ".backup")),
}
```

## Module Design

**Exports:**
- Explicit `__all__` lists in modules:
```python
__all__ = [
    "validate_configuration",
    "CSV_BASE_REQUIRED",
    "CSV_VOLUME_COLUMNS",
    "WELL_PATTERN",
]
```

**Barrel Files:**
- `__init__.py` files re-export public APIs from submodules
- Registration functions exposed: `register_tools()`, `register_config_resources()`

**Package Structure:**
```
src/ot2_cherrypick_mcp/
  __init__.py           # Package entry point
  server.py             # FastMCP server factory
  core/                 # Business logic
    validation.py
    protocol_generator.py
    simulation.py
    deployment.py
  tools/                # MCP tool definitions
    __init__.py         # Registers all tools
    config_tools.py
    protocol_tools.py
    ...
  resources/            # MCP resource definitions
  prompts/              # MCP prompt definitions
  utils/                # Shared utilities
    errors.py
    paths.py
    toml.py
```

## Type Annotations

**Style:**
- Use `from __future__ import annotations` for forward references
- Prefer `|` union syntax for Python 3.10+ (but maintain `Union` for compatibility)
- Use `object` for dynamically typed values (vs `Any`)

**Common Patterns:**
```python
_PathLike = Union[str, Path]
_Token = Union[str, int]

def get_value(self, dotted_path: str) -> object:
def set_value(self, dotted_path: str, value: object) -> Tuple[object, object]:
def run(self, query: str, *, max_steps: int | None = None) -> str:
```

## MCP Tool Conventions

**Tool Registration:**
```python
@mcp.tool(
    name="ot2_update_settings",
    description="""Detailed description with examples...""",
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
def update_settings_tool(path: str, value: str, ...) -> Dict[str, object]:
    ...
```

**Naming:**
- Tool names prefixed with `ot2_` for namespacing
- Underlying functions without prefix (testable directly)

**Return Format:**
- Always return `Dict[str, object]` for JSON serialization
- Include `message` field for user feedback
- Include `_file` suffix for path fields: `settings_file`, `backup_file`

---

*Convention analysis: 2026-01-20*
