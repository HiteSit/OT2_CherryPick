# Architecture

**Analysis Date:** 2026-01-20

## Pattern Overview

**Overall:** Configuration-as-Code with Embedded Data Protocol Generation

**Key Characteristics:**
- Three-file input workflow: TOML configuration + CSV transfer maps compile into self-contained Python protocol
- Multi-interface design: CLI, MCP server, and Web GUI all consume the same core logic
- Protocol runtime isolation: Generated protocol embeds all config as JSON, requires no external files on OT-2

## Layers

**Configuration Layer:**
- Purpose: Define hardware layout, pipette settings, and liquid handling parameters
- Location: `settings.toml`, `labware_dict.toml`
- Contains: TOML configuration for deck layout, pipette modes, liquid handling presets
- Depends on: Nothing
- Used by: Protocol Generator, Validation, MCP Tools, GUI Backend

**Transfer Definition Layer:**
- Purpose: Specify individual liquid transfers (source, dest, volume, tip actions)
- Location: `CSVs/*.csv`
- Contains: CSV files with cherry-pick or distribution transfer specifications
- Depends on: Configuration Layer (labware references must match settings)
- Used by: Protocol Generator, Validation

**Protocol Generator Layer:**
- Purpose: Compile TOML + CSV into embedded JSON and patch protocol file
- Location: `src/ot2_cherrypick_mcp/core/protocol_generator.py`
- Contains: `read_toml_file()`, `read_csv_file()`, `create_json_config()`, `update_protocol_file()`, `generate_protocol()`
- Depends on: Configuration Layer, Transfer Definition Layer
- Used by: CLI Helper, MCP Tools, GUI Backend

**Protocol Execution Layer:**
- Purpose: Execute liquid transfers on OT-2 hardware
- Location: `CherryPick_OT2.py`
- Contains: `get_values()` (embedded JSON), `run()` main protocol, transfer execution functions
- Depends on: Opentrons API, embedded configuration
- Used by: Opentrons robot/simulator

**MCP Server Layer:**
- Purpose: Expose protocol generation workflow via Model Context Protocol for AI interaction
- Location: `src/ot2_cherrypick_mcp/`
- Contains: FastMCP server, tools, resources, prompts
- Depends on: Protocol Generator Layer, Validation
- Used by: Claude Desktop, mcp-use clients

**GUI Backend Layer:**
- Purpose: REST API for web-based configuration editing and workflow execution
- Location: `src/gui/backend/`
- Contains: FastAPI routes, FileStateStore workspace manager
- Depends on: Protocol Generator Layer, Simulation, Deployment
- Used by: GUI Frontend

**GUI Frontend Layer:**
- Purpose: React-based configuration editor and workflow runner
- Location: `src/gui/frontend/`
- Contains: Vite/React app with wizard components
- Depends on: GUI Backend API
- Used by: End users via browser

## Data Flow

**Protocol Generation Flow:**

1. User edits `settings.toml` (deck layout), `labware_dict.toml` (hardware catalog), `CSVs/*.csv` (transfers)
2. `protocol_generator.py` reads TOML files via `read_toml_file()` and CSV via `read_csv_file()`
3. `create_json_config()` merges labware_dict + settings + csv_data into single JSON string
4. `update_protocol_file()` patches `CherryPick_OT2.py` with embedded JSON in `get_values()` function
5. Generated protocol is self-contained, ready for simulation or execution

**Simulation Flow:**

1. `simulate_protocol()` in `src/ot2_cherrypick_mcp/core/simulation.py` invokes `opentrons_simulate`
2. Custom labware path resolved from environment or shell settings
3. Subprocess captures stdout/stderr, logs to `logs/last_simulation.json`
4. Returns structured result with success/error status

**State Management:**
- MCP Server: Uses filesystem as state via `utils/paths.py` (project directory pattern)
- GUI Backend: `FileStateStore` class maintains workspace in `gui_state/` directory
- Both support auto-copying templates from repo root to workspace on first access

## Key Abstractions

**TomlHandler:**
- Purpose: Format-preserving TOML editing that maintains comments and whitespace
- Examples: `src/ot2_cherrypick_mcp/utils/toml.py`, `src/ot2_cherrypick_mcp/core/toml_handler.py`
- Pattern: Read via tomlkit, modify in-place, write back preserving formatting

**FileStateStore:**
- Purpose: Workspace isolation for GUI - edits happen in `gui_state/` not repo root
- Examples: `src/gui/backend/state.py`
- Pattern: Singleton state manager with bootstrap, patch, and reset operations

**MCP Tool Registration:**
- Purpose: Modular tool registration for FastMCP server
- Examples: `src/ot2_cherrypick_mcp/tools/__init__.py` aggregates all tool modules
- Pattern: Each tool module exports `register_X_tools(mcp)` function

**Transfer Execution Functions:**
- Purpose: Encapsulate complex pipetting logic (tip management, liquid handling, mixing)
- Examples: `determine_tip_action()`, `execute_tip_action()`, `perform_liquid_contact()`, `perform_distribution()` in `CherryPick_OT2.py`
- Pattern: Pure functions taking transfer dict + pipette + config, returning action results

## Entry Points

**CLI Entry (`helper_cherry_pick.py`):**
- Location: `helper_cherry_pick.py`
- Triggers: Direct Python execution with `-l`, `-s`, `-c`, `-p` arguments
- Responsibilities: Parse args, call `generate_protocol()`, print status

**MCP Server Entry (`server.py`):**
- Location: `src/ot2_cherrypick_mcp/server.py`
- Triggers: `uv run ot2-mcp-server` or Claude Desktop MCP config
- Responsibilities: Create FastMCP app, register tools/resources/prompts, run STDIO transport

**GUI Backend Entry (`main.py`):**
- Location: `src/gui/backend/main.py`
- Triggers: `uvicorn src.gui.backend.main:app`
- Responsibilities: Create FastAPI app, register routes, configure CORS

**Protocol Entry (`CherryPick_OT2.py`):**
- Location: `CherryPick_OT2.py` `run()` function
- Triggers: Opentrons robot execution or `opentrons_simulate`
- Responsibilities: Parse embedded JSON, load labware/pipettes, execute all transfers

**Shell Script Entry (`simulate_protocol.sh`):**
- Location: `simulate_protocol.sh`
- Triggers: Bash execution with CSV path argument
- Responsibilities: Call helper, run simulation, copy to clipboard, optional deployment

## Error Handling

**Strategy:** Exception-based with structured error types

**Patterns:**
- `ConfigurationError`: Invalid TOML/CSV structure, missing files, labware mismatches
- `SimulationError`: Non-zero exit from opentrons_simulate, timeout
- `ValueError`: Invalid configuration values (well format, volume ranges, mode incompatibility)
- HTTP exceptions in GUI backend via FastAPI `HTTPException` with status codes

## Cross-Cutting Concerns

**Logging:**
- MCP server uses `utils/logging_config.py` for structured logging
- Simulation results logged to `logs/last_simulation.json`
- Protocol execution uses `protocol.comment()` for OT-2 log output

**Validation:**
- Pre-flight validation in `src/ot2_cherrypick_mcp/core/validation.py`
- Runtime validation in `CherryPick_OT2.py` (labware match, mode compatibility, volume ranges)
- CSV column validation with required/optional field patterns

**Path Resolution:**
- `utils/paths.py` provides `get_repo_root()`, `get_project_root()`, `resolve_project_path()`
- Supports both persistent workspace (`OT2_PROJECT_DIR` env var) and auto-created temp directories
- Windows-to-WSL path conversion in `FileStateStore._windows_to_wsl()`

---

*Architecture analysis: 2026-01-20*
