# MCP Project-Based Workspace Architecture

## Overview
The MCP server now requires a **project directory** separate from the codebase installation. Each project is self-contained with its own configuration files. The `OT2_PROJECT_DIR` environment variable is **mandatory** in MCP configuration.

## Core Requirements
- `OT2_PROJECT_DIR` environment variable is **REQUIRED** (not optional)
- Each project directory is self-contained (settings.toml, labware_dict.toml, CSVs/, logs/)
- No backward compatibility - force migration to project-based architecture
- Server startup validates project directory and required files

## New Tool: initialize_project

**Location**: Create `src/ot2_cherrypick_mcp/tools/project_tools.py`

**Function signature**: No directory parameter - reads from `OT2_PROJECT_DIR` env var

**Implementation logic**:
1. Read `OT2_PROJECT_DIR` from `os.environ` (required, raise if missing)
2. Create directory structure if doesn't exist
3. Get source repo root using existing `get_repo_root()` (where code is installed)
4. Copy template files from repo root to project directory:
   - `settings.toml` → `{project_dir}/settings.toml`
   - `labware_dict.toml` → `{project_dir}/labware_dict.toml`
   - `CSVs/` → `{project_dir}/CSVs/` (entire directory, all CSV files)
5. Create empty directories: `{project_dir}/logs/`
6. Return success message listing created files and structure

**Registration**: Add to `src/ot2_cherrypick_mcp/tools/__init__.py`:
- Import `register_project_tools` from `.project_tools`
- Call `register_project_tools(mcp)` in `register_tools()` function

## Path Resolution Changes

**File**: `src/ot2_cherrypick_mcp/utils/paths.py`

**Add new function**: `get_project_root()`
- Read `OT2_PROJECT_DIR` from environment
- If not set: `raise ValueError("OT2_PROJECT_DIR environment variable is required")`
- Convert to Path object
- If directory doesn't exist: `raise ValueError(f"Project directory does not exist: {path}")`
- Return Path object

**Keep existing**: `get_repo_root()` - still needed for initialize_project to find template files

**Global replacement**: Search entire `src/ot2_cherrypick_mcp/` codebase and replace all `get_repo_root()` calls with `get_project_root()` EXCEPT:
- In `project_tools.py` (needs repo root to copy templates)
- In `server.py` initial validation (uses both)

**Files requiring path replacement** (use `get_project_root()` instead of `get_repo_root()`):
- All 8 tool modules: protocol_tools.py, config_tools.py, csv_tools.py, labware_tools.py, simulation_tools.py, validation_tools.py, deployment_tools.py, workflow_tools.py
- All 4 resource modules: config_resources.py, file_resources.py, log_resources.py, status_resources.py
- Core modules: validation.py, simulation.py, deployment.py, toml_handler.py

## Server Startup Validation

**File**: `src/ot2_cherrypick_mcp/server.py`

**Update `main()` function**:
1. After `configure_logging()`, validate project directory:
   - Check `OT2_PROJECT_DIR` env var is set
   - Call `get_project_root()` to validate directory exists
   - Check required files exist: `settings.toml`, `labware_dict.toml`
   - If missing files: raise error with message: "Project directory not initialized. Use 'initialize_project' tool or manually create required files."
2. Change working directory: `os.chdir(get_project_root())`
3. Run server as normal

**Remove unused variables**: Lines 49-52 (transport, host, port, path) are unused since `.run()` takes no parameters

## MCP Configuration Template

**File**: `utils/mcp_use_config.json`

**Update**: Add `OT2_PROJECT_DIR` to env section (required):
```json
{
  "mcpServers": {
    "ot2-cherrypick": {
      "command": "pixi",
      "args": ["run", "--manifest-path", "{manifest_path}", "python", "-m", "ot2_cherrypick_mcp.server"],
      "env": {
        "LABWARE_PATH": "{labware_path}",
        "OT2_PROJECT_DIR": "{project_directory}"
      }
    }
  }
}
```

## Test Updates

**File**: `tests/test_mcp_integration.py`

**Update `_build_config()` function**:
- Accept `project_dir: Path` parameter
- Add `OT2_PROJECT_DIR` to env section pointing to project_dir

**Update test functions**:
- Each test receives `tmp_path` fixture
- Create project structure in tmp_path before running agent:
  - Copy settings.toml, labware_dict.toml from PROJECT_ROOT
  - Create CSVs/ directory, copy necessary CSV files
  - Create logs/ directory
- Pass tmp_path to `_build_config(project_dir=tmp_path)`

**Alternative approach**: Create shared fixture that initializes project structure in tmp_path and returns configured client

## Project Directory Structure

**Template files** (copied from repo root):
- settings.toml
- labware_dict.toml
- CSVs/ (entire directory with all CSV examples)

**Generated directories** (created empty):
- logs/

**Generated files** (created by tools during workflow):
- CherryPick_OT2.py (by generate_protocol tool)
- logs/last_simulation.json (by simulate_protocol tool)
- Any additional CSV files (by upload_csv_content or generate_csv_template tools)

## Documentation Updates

**CLAUDE.md**:
- Update "MCP Server Architecture" section with project directory requirement
- Update "Integration with Claude Desktop" example to show OT2_PROJECT_DIR
- Add subsection explaining initialize_project workflow
- Update "Development Workflow" to mention project setup as first step

**README.md**:
- Update "Running the Server" section to require OT2_PROJECT_DIR
- Add section on project initialization before workflow examples
- Update mcp-use example to show OT2_PROJECT_DIR in config

**docs/mcp_tools_guide.md**:
- Add documentation for initialize_project tool
- Update all tool descriptions that mention file paths to clarify they operate in project directory
- Add "Getting Started" section mentioning project initialization as prerequisite

## Breaking Changes

- `OT2_PROJECT_DIR` environment variable is now **mandatory**
- Server will not start without valid project directory
- Project directory must contain settings.toml and labware_dict.toml
- No fallback to repo root - project-based architecture is enforced
- Force migration: existing STDIO configurations must be updated

## User Workflow

1. **Configure Claude Desktop** with MCP server and `OT2_PROJECT_DIR` pointing to desired project location (can be non-existent initially)
2. **Start Claude Desktop** (server may fail if project not initialized - this is expected)
3. **Call initialize_project tool** - creates project structure and copies templates
4. **Restart Claude Desktop** - server now works with initialized project
5. **All operations** work in project directory (protocol generation, CSV management, simulation, etc.)

## Implementation Order

1. Create `project_tools.py` with `initialize_project` tool
2. Add `get_project_root()` to `utils/paths.py`
3. Update `server.py` main() with validation logic
4. Global search/replace: `get_repo_root()` → `get_project_root()` in all tools/resources/core modules (except project_tools.py)
5. Register project_tools in `tools/__init__.py`
6. Update `utils/mcp_use_config.json` template
7. Update test suite to use tmp project directories
8. Update all documentation (CLAUDE.md, README.md, mcp_tools_guide.md)
9. Test end-to-end workflow with real Claude Desktop configuration