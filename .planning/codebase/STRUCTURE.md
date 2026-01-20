# Codebase Structure

**Analysis Date:** 2026-01-20

## Directory Layout

```
OT2_CherryPick/
├── src/                        # Source packages
│   ├── ot2_cherrypick_mcp/     # MCP server package
│   │   ├── core/               # Core business logic
│   │   ├── tools/              # MCP tool definitions
│   │   ├── resources/          # MCP resource providers
│   │   ├── prompts/            # MCP workflow prompts
│   │   └── utils/              # Shared utilities
│   └── gui/                    # Web GUI package
│       ├── backend/            # FastAPI backend
│       │   └── routes/         # API route handlers
│       └── frontend/           # React/Vite frontend
│           └── src/            # Frontend source
│               ├── api/        # API client
│               └── components/ # React components
├── CSVs/                       # Transfer CSV files
├── tests/                      # Test suite
│   ├── e2e/                    # End-to-end tests
│   └── fastapi/                # FastAPI-specific tests
├── gui_state/                  # GUI workspace (isolated edits)
│   └── CSVs/                   # Workspace CSV copies
├── projects/                   # Archived experiment projects
├── notebooks/                  # Jupyter notebooks
├── docs/                       # Documentation
├── docker/                     # Docker configurations
├── scripts/                    # Utility scripts
├── logs/                       # Generated log files
├── CherryPick_OT2.py           # Generated OT-2 protocol
├── helper_cherry_pick.py       # CLI protocol generator
├── settings.toml               # Protocol settings
├── labware_dict.toml           # Labware catalog
├── simulate_protocol.sh        # Shell automation script
└── pyproject.toml              # Package manifest
```

## Directory Purposes

**`src/ot2_cherrypick_mcp/`:**
- Purpose: MCP server package for AI-native protocol generation
- Contains: FastMCP server, tool modules, resource providers, prompts
- Key files: `server.py` (entry point), `__init__.py`

**`src/ot2_cherrypick_mcp/core/`:**
- Purpose: Core business logic shared across interfaces
- Contains: Protocol generation, simulation, validation, deployment
- Key files: `protocol_generator.py`, `simulation.py`, `validation.py`, `deployment.py`

**`src/ot2_cherrypick_mcp/tools/`:**
- Purpose: MCP tool definitions (9 categories)
- Contains: One module per tool category with `register_X_tools()` functions
- Key files: `config_tools.py`, `csv_tools.py`, `protocol_tools.py`, `simulation_tools.py`, `workflow_tools.py`

**`src/ot2_cherrypick_mcp/resources/`:**
- Purpose: MCP resource providers (read-only data access)
- Contains: Config, file, log, and status resources
- Key files: `config_resources.py`, `status_resources.py`, `log_resources.py`, `file_resources.py`

**`src/ot2_cherrypick_mcp/utils/`:**
- Purpose: Shared utilities for MCP server
- Contains: Path resolution, TOML handling, error types, logging, formatters
- Key files: `paths.py`, `toml.py`, `errors.py`, `logging_config.py`

**`src/gui/backend/`:**
- Purpose: FastAPI REST API for web GUI
- Contains: Main app, state manager, route handlers, schemas
- Key files: `main.py` (app factory), `state.py` (FileStateStore), `dependencies.py`

**`src/gui/backend/routes/`:**
- Purpose: API route handlers organized by domain
- Contains: Settings, labware, CSV, workflow, system routes
- Key files: `settings.py`, `labware.py`, `csvs.py`, `workflow.py`, `system.py`

**`src/gui/frontend/`:**
- Purpose: Vite + React web application
- Contains: Configuration editor wizard, workflow runner
- Key files: `src/App.tsx`, `src/main.tsx`

**`CSVs/`:**
- Purpose: Transfer definition CSV files (cherry-pick and distribution)
- Contains: Example CSVs and user-created transfer files
- Key files: `example_basic.csv`, `example_distribution.csv`, `example_home_control.csv`

**`gui_state/`:**
- Purpose: Isolated workspace for GUI edits (does not touch repo root configs)
- Contains: Working copies of settings.toml, labware_dict.toml, CherryPick_OT2.py
- Key files: `settings.toml`, `labware_dict.toml`, `shell_settings.json`

**`tests/`:**
- Purpose: Pytest test suite
- Contains: Unit tests, integration tests, end-to-end tests
- Key files: `conftest.py` (fixtures), `test_mcp_integration.py`, `test_validation.py`

**`projects/`:**
- Purpose: Archived experiment projects with full provenance
- Contains: Past experiments with CSVs, notebooks, figures
- Key files: Varies by project

## Key File Locations

**Entry Points:**
- `src/ot2_cherrypick_mcp/server.py`: MCP server entry (run via `ot2-mcp-server`)
- `src/gui/backend/main.py`: FastAPI entry (run via uvicorn)
- `helper_cherry_pick.py`: CLI entry for protocol generation
- `simulate_protocol.sh`: Shell script for simulation workflow
- `CherryPick_OT2.py`: Protocol entry (`run()` function for OT-2)

**Configuration:**
- `settings.toml`: Deck layout, pipette mode, liquid handling parameters
- `labware_dict.toml`: Labware catalog with calibration offsets
- `pyproject.toml`: Package dependencies, scripts, build config
- `.mcp.json`: MCP server configuration for IDE integration
- `gui_state/shell_settings.json`: GUI shell runner paths

**Core Logic:**
- `src/ot2_cherrypick_mcp/core/protocol_generator.py`: TOML+CSV to JSON compilation
- `src/ot2_cherrypick_mcp/core/simulation.py`: opentrons_simulate wrapper
- `src/ot2_cherrypick_mcp/core/validation.py`: Pre-flight config validation
- `src/ot2_cherrypick_mcp/core/deployment.py`: Protocol copy/clipboard operations

**Testing:**
- `tests/conftest.py`: Shared pytest fixtures
- `tests/test_mcp_integration.py`: End-to-end MCP tests with mcp-use
- `tests/test_validation.py`: Configuration validation tests
- `tests/test_home_control.py`: HOME control row feature tests

## Naming Conventions

**Files:**
- Python modules: `snake_case.py` (e.g., `protocol_generator.py`, `config_tools.py`)
- TOML config: `snake_case.toml` (e.g., `settings.toml`, `labware_dict.toml`)
- CSV files: `snake_case.csv` (e.g., `example_basic.csv`)
- Test files: `test_<module>.py` (e.g., `test_validation.py`)

**Directories:**
- Packages: `snake_case` (e.g., `ot2_cherrypick_mcp`, `gui_state`)
- Route directories: Plural nouns (`routes/`, `tools/`, `resources/`)

**Functions/Classes:**
- Functions: `snake_case` (e.g., `generate_protocol()`, `simulate_protocol()`)
- Classes: `PascalCase` (e.g., `FileStateStore`, `TomlHandler`)
- MCP tool functions: `snake_case` matching tool name (e.g., `update_settings()`)

## Where to Add New Code

**New MCP Tool:**
- Create `src/ot2_cherrypick_mcp/tools/<tool_name>_tools.py`
- Export `register_<tool_name>_tools(mcp: FastMCP)` function
- Add import and call in `src/ot2_cherrypick_mcp/tools/__init__.py`

**New MCP Resource:**
- Create `src/ot2_cherrypick_mcp/resources/<resource_name>_resources.py`
- Export `register_<resource_name>_resources(mcp: FastMCP)` function
- Add import and call in `src/ot2_cherrypick_mcp/resources/__init__.py`

**New Core Business Logic:**
- Add to existing module in `src/ot2_cherrypick_mcp/core/` or create new module
- Import in relevant tools/resources that need it

**New GUI API Route:**
- Create `src/gui/backend/routes/<domain>.py`
- Define FastAPI router with endpoints
- Register router in `src/gui/backend/main.py`

**New Protocol Feature:**
- Add function in `CherryPick_OT2.py` (helper functions before `run()`)
- Call from `run()` during transfer execution
- Update validation in `src/ot2_cherrypick_mcp/core/validation.py`

**New Test:**
- Create `tests/test_<feature>.py`
- Use fixtures from `tests/conftest.py`
- Follow naming pattern `test_<function_or_feature>()`

**New CSV Example:**
- Add to `CSVs/` directory with descriptive name
- Use `example_` prefix for documentation examples
- Use `test_` prefix for test-specific files

## Special Directories

**`.venv/`:**
- Purpose: uv-managed Python virtual environment
- Generated: Yes (by uv)
- Committed: No (in .gitignore)

**`logs/`:**
- Purpose: Simulation output logs
- Generated: Yes (by simulate_protocol)
- Committed: No (transient outputs)

**`gui_state/`:**
- Purpose: GUI workspace isolation
- Generated: Yes (on first GUI use)
- Committed: Partial (shell_settings.json template)

**`__pycache__/`:**
- Purpose: Python bytecode cache
- Generated: Yes (by Python)
- Committed: No (in .gitignore)

**`.planning/`:**
- Purpose: GSD planning documents
- Generated: Yes (by GSD commands)
- Committed: Yes (planning artifacts)

---

*Structure analysis: 2026-01-20*
