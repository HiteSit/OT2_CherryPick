# MCP Server Integration Design for OpenTron Cherry-Pick System

## Executive Summary

This document outlines the design and implementation strategy for integrating the OpenTron OT-2 cherry-pick protocol system into a Model Context Protocol (MCP) server, enabling Claude Desktop and other MCP clients to interact programmatically with the protocol generation workflow.

---

## Current System Architecture Analysis

### Workflow Overview

The system follows a three-stage compilation pipeline:

```
TOML Configuration + CSV Transfers → JSON Compilation → Self-Contained Python Protocol
```

**Key Components:**
1. **labware_dict.toml** - Hardware catalog (pipettes, labware, calibration offsets)
2. **settings.toml** - Protocol parameters (deck layout, liquid handling, tip management)
3. **CSV files** - Transfer definitions (source/dest wells, volumes, heights)
4. **helper_cherry_pick.py** - Compiler that generates JSON and embeds it into protocol
5. **CherryPick_OT2.py** - Executable OT-2 protocol with embedded JSON in `get_values()`
6. **simulate_protocol.sh** - Orchestration script (helper → simulation → clipboard → optional deployment)

### User Interaction Points

**High-Frequency Edits** (per experiment):
- Creating/modifying CSV transfer files
- Adjusting settings.toml (deck layout, pipette mode, liquid handling presets)

**Low-Frequency Edits** (occasional):
- Adding new labware to labware_dict.toml
- Defining calibration offsets
- Configuring new liquid handling presets

**Execution**:
- Running `./simulate_protocol.sh CSVs/file.csv [--send-to-opentrons]`

---

## ⚠️ CRITICAL: TOML File Editing Requirement

### The Source of Truth Problem

**TOML files are the source of truth.** The current workflow is:

```
1. User manually edits TOML files (settings.toml, labware_dict.toml)
2. helper_cherry_pick.py READS TOML files
3. TOML data → compiled to JSON
4. JSON → embedded in CherryPick_OT2.py
```

**Therefore, MCP tools MUST be able to:**
1. **READ** TOML files (parse structure)
2. **MODIFY** specific values programmatically
3. **WRITE** back to disk while preserving:
   - Comments
   - Formatting
   - Section order
   - Human readability

### TOML Editing Implementation Strategy

#### Library Choice: `tomlkit` (Recommended)

**Why `tomlkit` over standard `toml`?**

| Feature | `toml` (stdlib) | `tomlkit` |
|---------|-----------------|-----------|
| Parse TOML | ✅ | ✅ |
| Write TOML | ✅ | ✅ |
| Preserve comments | ❌ | ✅ |
| Preserve formatting | ❌ | ✅ |
| Preserve whitespace | ❌ | ✅ |
| Style-preserving edits | ❌ | ✅ |

**Installation:**
```bash
pip install tomlkit
```

#### Core TOML Handler Design Pattern

The TOML handler should provide a structured API for reading, modifying, and writing TOML files while preserving the original document structure. Key architectural components:

**File: `src/core/toml_handler.py`**

The handler should encapsulate:
- Document loading with encoding safety
- Path-based value access (dot notation like "settings.general.tip_reuse")
- Atomic write operations with automatic backup creation
- Table and array manipulation for TOML structures
- Error handling with detailed context

**Core Operations Needed:**
- `read()` - Load TOML document from file
- `write()` - Persist document with backup creation
- `get_value(path)` - Navigate nested structures via dot notation
- `set_value(path, value)` - Update values while preserving structure
- `add_table(path, content)` - Create new configuration sections
- `append_array_item(path, item)` - Add to arrays like [[labware]] or [[settings.working_plate]]

**Backup Strategy:**
Before any write operation, create `.toml.backup` files to enable rollback if needed.

#### Helper Functions for Common Operations

**Settings Management:**
Function to update individual settings values:
- Input: settings file path, dot-notation path, new value
- Output: success status, old/new values, descriptive message
- Should handle validation errors gracefully

**Preset Application:**
Function to apply liquid handling presets:
- Read preset configuration from settings.toml presets section
- Copy all preset values to active liquid_handling configuration
- Track what changed for audit purposes
- Return comprehensive change report

**Labware Definition Management:**
Function to add new labware types:
- Accept labware specifications (ID, category, dimensions, offsets)
- Check for duplicate IDs before insertion
- Append to labware array with proper formatting
- Return success status with new labware details

#### Integration with MCP Tools

MCP tools should expose these helper functions through clean interfaces:

**Tool: update_settings**
- Purpose: Programmatic modification of settings.toml values
- Parameters: setting path (dot notation), new value, optional file path
- Returns: Change confirmation with old/new values
- Example use: "update_settings('general.tip_reuse', 'never')"

**Tool: apply_liquid_preset**
- Purpose: Apply predefined liquid handling configurations
- Parameters: preset name (standard/viscous/slippery/minimal/aggressive)
- Returns: List of all configuration changes applied
- Example use: "apply_liquid_preset('viscous')" for DMSO-like liquids

**Tool: add_labware_definition**
- Purpose: Register new labware type in catalog
- Parameters: labware specifications including calibration offsets
- Returns: Confirmation with labware ID
- Example use: Add custom tube rack or plate definition

### Why TOML Editing is Critical

**Data Flow with TOML Editing:**

```
1. LLM reads config://settings resource → understands current state
2. LLM calls update_settings() → TOML file modified in place
3. User (or LLM) runs generate_protocol() → helper reads updated TOML
4. TOML → JSON → embedded in protocol
5. Protocol ready for simulation/deployment
```

**Without TOML Editing:**
- User must manually edit files (defeats purpose of MCP)
- No programmatic configuration
- Can't have automated workflows

**With TOML Editing:**
- ✅ LLM can configure experiments autonomously
- ✅ Guided setup workflows work correctly
- ✅ Settings preserved with comments/formatting
- ✅ Full audit trail of changes

### Critical Implementation Notes

1. **Always create backups** before writing (`.toml.backup` files)
2. **Validate inputs** before modifying TOML
3. **Log all changes** for audit trail
4. **Test with edge cases**: nested tables, arrays, inline tables
5. **Handle concurrent access**: File locking if needed

---

## MCP Server Testing Strategy with mcp-use

### Overview of mcp-use

**mcp-use** is a Python library that enables testing and integration of MCP servers by connecting any LangChain-compatible LLM to any MCP server. It's essential for validating that our MCP server works correctly before deploying to Claude Desktop.

**Why use mcp-use for testing:**
- Test server functionality without Claude Desktop
- Automate integration tests
- Validate tool schemas and responses
- Verify resource access patterns
- Debug server behavior in isolation

### Installation and Setup

```bash
pip install mcp-use
```

### Basic Testing Pattern

The testing workflow involves creating an MCP client that connects to your server, pairing it with an LLM, and creating an agent that exercises the server's tools:

**Key Components:**
1. **MCPClient** - Connects to your MCP server via config
2. **LLM** - Any LangChain-compatible model (OpenAI, Anthropic, Mistral, etc.)
3. **MCPAgent** - Orchestrates LLM calls with server tools

### Configuration for Testing

Create a test configuration file (e.g., `test_config.json`) that points to your MCP server:

```json
{
  "mcpServers": {
    "ot2-cherrypick": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/ot2_cherrypick_mcp",
        "run",
        "ot2-mcp-server"
      ],
      "env": {
        "LABWARE_PATH": "/path/to/labware/directory"
      }
    }
  }
}
```

### Testing Architecture

**Test Script Structure:**

The test script should:
- Load MCP server configuration
- Initialize LLM client (Mistral, OpenAI, etc.)
- Create agent with access to server tools
- Run test queries that exercise server functionality
- Validate responses and tool execution

**Example Test Scenarios:**

1. **Configuration Reading Test**
   - Query: "What is the current tip reuse setting?"
   - Validates: Resource access (config://settings)
   - Expected: Agent reads and reports setting correctly

2. **Configuration Modification Test**
   - Query: "Set tip reuse to 'never'"
   - Validates: update_settings tool execution
   - Expected: TOML file updated, backup created

3. **Preset Application Test**
   - Query: "Apply viscous liquid handling preset"
   - Validates: apply_liquid_preset tool
   - Expected: Multiple settings changed atomically

4. **Protocol Generation Test**
   - Query: "Generate protocol for CSV file X"
   - Validates: generate_protocol tool execution
   - Expected: Protocol file created with embedded JSON

5. **End-to-End Workflow Test**
   - Query: "Set up experiment with viscous liquid, generate and simulate protocol"
   - Validates: Tool chaining and workflow orchestration
   - Expected: Configuration → generation → simulation succeeds

### Test Execution Example

Reference implementation at `mcp-use_example.py` shows the basic pattern:
- Async execution via asyncio
- MCPClient initialization from config
- LLM setup (Mistral in this case, but any LangChain LLM works)
- Agent creation with max_steps control
- Natural language query execution

**The agent automatically:**
- Discovers available tools from the MCP server
- Selects appropriate tools based on query
- Executes tools in logical sequence
- Synthesizes responses from tool results

### Testing Best Practices

1. **Isolation Testing**
   - Test individual tools before integration
   - Verify resource access patterns
   - Validate error handling

2. **Integration Testing**
   - Test tool chaining and workflows
   - Verify state consistency across operations
   - Test with realistic queries

3. **Regression Testing**
   - Maintain suite of test queries
   - Run after any server changes
   - Compare outputs for consistency

4. **LLM Model Testing**
   - Test with different LLMs (GPT-4, Claude, Mistral)
   - Verify tool selection is consistent
   - Validate response quality

5. **Error Scenario Testing**
   - Invalid TOML paths
   - Missing files
   - Malformed CSV data
   - Concurrent access conflicts

### Continuous Testing During Development

**Development Workflow:**
1. Implement new MCP tool
2. Write mcp-use test for tool functionality
3. Run test with `python test_script.py`
4. Iterate based on results
5. Add test to regression suite

**Benefits:**
- Faster iteration than manual Claude Desktop testing
- Automated validation of tool behavior
- Clear debugging output
- Reproducible test scenarios

### Integration with CI/CD

mcp-use enables automated testing in continuous integration:
- Run test suite on every commit
- Validate server functionality before deployment
- Catch breaking changes early
- Ensure cross-LLM compatibility

---

## MCP Server Architecture Fundamentals

### Core Primitives

**1. Tools** - Executable functions that perform actions
- LLM can call these to execute operations
- Should be high-level and task-oriented, not simple API wrappers
- Must be idempotent (safe for retries/parallelization)
- Return agent-friendly error messages

**2. Resources** - Read-only data exposed as URIs
- Application-controlled (client explicitly fetches)
- Provides contextual data without side effects
- Ideal for configuration files, logs, status info
- URI-addressable (e.g., `file://settings`, `config://deck-layout`)

**3. Prompts** - Reusable workflow templates
- Chain multiple tools/operations
- Act like macros for common tasks
- Guide LLM through complex workflows
- Reduce need for users to know internal details

### Python Implementation Framework

**FastMCP** is the modern, production-ready approach for implementing MCP servers in Python. It provides decorators and automatic schema generation from Python type hints and docstrings.

### Critical Implementation Rules

1. **Never write to stdout** - Corrupts JSON-RPC messages (use stderr or files)
2. **Agent-friendly errors** - Return actionable guidance, not just failure messages
3. **STDIO transport** - Preferred for development and local MCP servers
4. **Type hints + docstrings** - FastMCP auto-generates schemas from these
5. **Logging discipline** - Use logging library configured for stderr
6. **Idempotency** - Tools should handle repeated calls safely

---

## Proposed MCP Server Design for OpenTron

### Tool Categories and Design Philosophy

Tools should represent **complete tasks** rather than low-level operations. Design tools around user intentions, not implementation details.

#### 1. Protocol Generation Tools

**generate_protocol**
- Purpose: Compile TOML + CSV into executable protocol
- Input: Paths to configuration files
- Output: Success status, protocol path, embedded JSON size
- Implementation: Wraps helper_cherry_pick.py compilation logic

**simulate_protocol**
- Purpose: Validate protocol through OT-2 simulation
- Input: Protocol file path, optional labware directory
- Output: Simulation results, errors, warnings
- Implementation: Execute opentrons_simulate via subprocess

**validate_configuration**
- Purpose: Pre-flight checks before generation
- Input: Configuration file paths
- Output: Validation results with specific issues identified
- Checks: TOML syntax, labware references, deck conflicts, volume ranges

#### 2. Configuration Management Tools

**update_settings**
- Purpose: Modify settings.toml values programmatically
- Input: Dot-notation path, new value
- Output: Change confirmation with old/new values
- Implementation: Uses TOML handler with backup creation

**apply_liquid_preset**
- Purpose: Apply predefined liquid handling configurations
- Input: Preset name
- Output: List of all configuration changes
- Implementation: Copy preset values to active config

**add_labware_definition**
- Purpose: Register new labware type in catalog
- Input: Labware specifications with calibration offsets
- Output: Success confirmation
- Implementation: Append to labware array in labware_dict.toml

#### 3. Workflow Orchestration Tools

**full_workflow**
- Purpose: End-to-end protocol generation pipeline
- Input: CSV file, optional deployment flag
- Output: Comprehensive workflow results
- Stages: Validation → Generation → Simulation → Optional Deployment
- Philosophy: Single command for complete protocol preparation

**create_csv_template**
- Purpose: Generate CSV skeleton for specific labware
- Input: Source/dest labware, transfer count
- Output: CSV file with proper columns and structure
- Philosophy: Reduce manual CSV creation errors

**deploy_to_opentrons**
- Purpose: Copy protocol to Opentrons App directory
- Input: Protocol path, machine configuration
- Output: Deployment confirmation
- Implementation: Reads config from simulate_protocol.sh settings

---

### Resource Definitions

Resources expose system state as read-only URI-addressable data.

**Configuration Resources:**
- `config://settings` - Current settings.toml content
- `config://labware` - Labware dictionary definitions

**Status Resources:**
- `status://deck-layout` - Visual representation of current deck configuration
- `status://liquid-handling-config` - Active liquid handling parameters

**File Resources:**
- `files://csvs` - List of available CSV transfer files

**Log Resources:**
- `logs://last-simulation` - Most recent simulation output

---

### Prompt Definitions

Prompts guide users through multi-step workflows using natural language templates.

**setup_new_experiment**
- Purpose: Interactive experiment configuration
- Flow: Liquid type → Preset recommendation → Deck layout → CSV generation → Validation

**add_new_labware_type**
- Purpose: Guided labware registration
- Flow: Specifications → TOML update → Calibration guidance → Dry run testing

**troubleshoot_simulation_error**
- Purpose: Error diagnosis and resolution
- Flow: Parse simulation log → Identify issues → Suggest fixes

**optimize_liquid_handling**
- Purpose: Parameter tuning for specific liquids
- Flow: Describe issues → Analyze parameters → Recommend adjustments

---

## Implementation Architecture

### Directory Structure

```
ot2_cherrypick_mcp/
├── src/
│   ├── __init__.py
│   ├── server.py              # FastMCP server entry point
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── protocol_tools.py  # Protocol generation and simulation
│   │   ├── config_tools.py    # Settings and configuration management
│   │   └── labware_tools.py   # Labware and CSV operations
│   ├── resources/
│   │   ├── __init__.py
│   │   ├── config_resources.py
│   │   └── status_resources.py
│   ├── prompts/
│   │   ├── __init__.py
│   │   └── workflow_prompts.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── validation.py      # Configuration validation
│   │   ├── toml_handler.py    # TOML read/write with preservation
│   │   └── simulation.py      # Simulation execution wrapper
│   └── utils/
│       ├── __init__.py
│       ├── logging_config.py  # Stderr logging setup
│       └── errors.py          # Custom exceptions
├── tests/
│   ├── test_tools.py
│   ├── test_resources.py
│   ├── test_toml_handler.py   # TOML preservation tests
│   ├── test_mcp_use_integration.py  # mcp-use based tests
│   └── test_integration.py
├── pyproject.toml
├── README.md
└── config.json                # MCP server configuration
```

### Server Entry Point Design

The main server should:
- Configure stderr-only logging
- Initialize FastMCP instance
- Set working directory to repository root
- Import and register all tools, resources, and prompts
- Run STDIO transport

### Dependencies Philosophy

Minimal, focused dependencies:
- `mcp` - MCP protocol implementation
- `tomlkit` - Format-preserving TOML editing (CRITICAL)
- `toml` - Compatibility with existing helper code

Development dependencies:
- `mcp-use` - For testing and validation
- Standard testing frameworks

### Claude Desktop Integration

Configuration should specify:
- Command to launch server (via `uv` or `python`)
- Working directory (repository root)
- Environment variables (labware paths, etc.)

---

## Development Phases with Codebase Transformation

### Current State (Pre-MCP)

**Repository Structure:**
```
OT2_CherryPick/
├── .gitignore
├── .serena/                   # Serena MCP tool metadata
├── AGENTS.md                  # Documentation
├── CLAUDE.md                  # Project instructions
├── CherryPick_OT2.py         # Executable protocol (auto-generated)
├── CSVs/                      # Transfer definitions
│   ├── example_advanced.csv
│   ├── example_basic.csv
│   └── example_multi_mode.csv
├── copy_essentials.sh         # Utility script
├── helper_cherry_pick.py      # Core compiler
├── labware_dict.toml          # Hardware catalog
├── notebooks/                 # Analysis notebooks
├── OT2_UserGuide/            # Documentation
├── scripts_library/           # Utility scripts
├── settings.toml              # Protocol parameters
└── simulate_protocol.sh       # Orchestration script
```

**User Workflow:**
1. Manually edit `settings.toml` and `labware_dict.toml`
2. Create/edit CSV files in `CSVs/`
3. Run: `./simulate_protocol.sh CSVs/file.csv [--send-to-opentrons]`
4. Script executes: helper → opentrons_simulate → clipboard/deploy

---

### Phase 1: Core Protocol Tools (MVP) - Foundation Build

**Goal**: Establish MCP server with essential protocol generation and validation

#### New Files Created
```
ot2_cherrypick_mcp/                # NEW: MCP server package
├── pyproject.toml                 # NEW: Package definition
├── README.md                      # NEW: MCP server documentation
├── src/
│   ├── server.py                  # NEW: FastMCP server
│   ├── core/
│   │   ├── toml_handler.py        # NEW: CRITICAL - TOML editor
│   │   ├── validation.py          # NEW: Config validation
│   │   └── simulation.py          # NEW: Simulation wrapper
│   ├── tools/
│   │   └── protocol_tools.py      # NEW: Core protocol operations
│   ├── resources/
│   │   └── config_resources.py    # NEW: Config exposure
│   └── utils/
│       ├── logging_config.py      # NEW: Logging setup
│       └── errors.py              # NEW: Error types
└── tests/
    ├── test_tools.py              # NEW: Tool tests
    ├── test_toml_handler.py       # NEW: TOML preservation tests
    ├── test_mcp_use_basic.py      # NEW: Basic mcp-use integration tests
    └── test_validation.py         # NEW: Validation tests
```

#### Existing Files Modified
- **helper_cherry_pick.py** - Refactored for MCP tool import
- **CLAUDE.md** - Add MCP setup instructions

#### Files Preserved Unchanged
- ✅ All core protocol system files
- ✅ Configuration files (settings.toml, labware_dict.toml)
- ✅ CSV examples
- ✅ Simulation script
- ✅ Documentation

#### Phase 1 End State
Parallel operation: Original script-based workflow + new MCP interface

**Key Capabilities Unlocked:**
- ✅ LLM can read TOML configurations
- ✅ LLM can generate protocols programmatically
- ✅ LLM can simulate and validate
- ✅ TOML editing foundation established
- ✅ Basic mcp-use testing framework in place

**Testing Strategy:**
- Unit tests for each tool
- TOML preservation tests (comment/format retention)
- mcp-use integration tests for basic queries

---

### Phase 2: Configuration Management - Programmatic Control

**Goal**: Enable AI-driven configuration without manual TOML editing

#### New Files Created
```
ot2_cherrypick_mcp/
├── src/
│   ├── tools/
│   │   ├── config_tools.py        # NEW: Settings management
│   │   └── labware_tools.py       # NEW: Labware operations
│   └── resources/
│       └── status_resources.py    # NEW: Status visualization
└── tests/
    ├── test_config_tools.py       # NEW: Config tool tests
    └── test_mcp_use_config.py     # NEW: Config management tests via mcp-use
```

#### Existing Files Enhanced
- **settings.toml** - Automatic `.toml.backup` creation
- **labware_dict.toml** - Automatic backup mechanism

#### Phase 2 End State
TOML files become programmatically modifiable with full preservation

**Key Capabilities Unlocked:**
- ✅ LLM can modify settings programmatically
- ✅ LLM can apply liquid handling presets
- ✅ LLM can add labware definitions
- ✅ Backup/rollback capability
- ✅ Audit trail of changes

**Testing Strategy:**
- TOML modification tests with format verification
- mcp-use tests for preset application
- mcp-use tests for configuration workflows

**Workflow Evolution:**
- Before: "Edit settings.toml manually, then run script"
- Now: "Claude, set tip reuse to 'never' and apply viscous preset"

---

### Phase 3: Workflow Orchestration - End-to-End Automation

**Goal**: Complete workflows guided by AI with minimal user input

#### New Files Created
```
ot2_cherrypick_mcp/
├── src/
│   ├── tools/
│   │   ├── workflow_tools.py      # NEW: full_workflow, deploy
│   │   └── csv_tools.py           # NEW: CSV generation
│   ├── prompts/
│   │   └── workflow_prompts.py    # NEW: Guided workflows
│   └── resources/
│       └── file_resources.py      # NEW: File listing
└── tests/
    ├── test_workflow_tools.py     # NEW: Workflow integration
    ├── test_prompts.py            # NEW: Prompt rendering
    └── test_mcp_use_e2e.py        # NEW: End-to-end mcp-use tests
```

#### Existing Files Modified
- **simulate_protocol.sh** - Logic extraction for deployment tool
- **CLAUDE.md** - Workflow examples

#### Phase 3 End State
Full automation: natural language → validated protocol

**Key Capabilities Unlocked:**
- ✅ End-to-end workflows (validate → generate → simulate → deploy)
- ✅ CSV template generation
- ✅ Guided experiment setup
- ✅ Automated deployment
- ✅ Multi-step AI orchestration

**Testing Strategy:**
- Complete workflow tests via mcp-use
- Multi-tool chaining validation
- Error recovery testing

**Workflow Revolution:**
- Before: Multi-step manual process
- Now: "Claude, set up cherry-pick with viscous liquid, 384-well dest"
- Result: Full configuration + CSV + validated protocol

---

### Phase 4: Advanced Features - Production Polish

**Goal**: Comprehensive diagnostics, troubleshooting, and robot integration

#### New Files Created
```
ot2_cherrypick_mcp/
├── src/
│   ├── tools/
│   │   ├── diagnostic_tools.py    # NEW: Linting and analysis
│   │   └── robot_tools.py         # NEW: HTTP API integration
│   ├── prompts/
│   │   └── troubleshooting_prompts.py  # NEW: Error diagnosis
│   ├── resources/
│   │   └── log_resources.py       # NEW: Log access
│   └── core/
│       ├── csv_validator.py       # NEW: CSV validation
│       └── robot_client.py        # NEW: OT-2 HTTP client
├── docs/
│   ├── API.md                     # NEW: API documentation
│   ├── WORKFLOWS.md               # NEW: Example workflows
│   └── TROUBLESHOOTING.md         # NEW: Common issues
└── tests/
    ├── test_diagnostics.py        # NEW: Diagnostic tests
    ├── test_robot_integration.py  # NEW: Robot API tests
    └── test_mcp_use_comprehensive.py  # NEW: Full test suite
```

#### Files Potentially Archived
- `simulate_protocol.sh` → `archived_scripts/`
- `copy_essentials.sh` → `archived_scripts/`

#### Phase 4 End State
Production-ready MCP server with comprehensive capabilities

**Key Capabilities Unlocked:**
- ✅ CSV linting with specific errors
- ✅ Simulation log AI analysis
- ✅ Robot status monitoring
- ✅ Intelligent troubleshooting
- ✅ Performance optimization
- ✅ Complete audit trails

**Testing Strategy:**
- Comprehensive mcp-use regression suite
- Cross-LLM compatibility testing
- Error scenario coverage
- Performance benchmarking

**Production Workflow:**
Natural language → AI configuration → validation → simulation → deployment → monitoring

---

## Testing Strategy Evolution

### Unit Testing
- Individual tool functions
- TOML editing with format preservation (CRITICAL)
- Configuration validation
- Error handling

### mcp-use Integration Testing
- Tool execution via agent
- Resource access patterns
- Multi-tool workflows
- Error scenarios

### Regression Testing
- Test query suite maintained across development
- Run on every change
- Validate consistency across LLMs

### Cross-LLM Testing
Test with multiple models via mcp-use:
- OpenAI GPT-4
- Anthropic Claude
- Mistral Large
- Verify tool selection and execution consistency

---

## Key Design Principles

### 1. High-Level Abstractions
Tools represent **tasks**, not operations:
- ✅ `full_workflow(csv_file)` - Complete process
- ❌ `read_toml()`, `write_json()` - Too granular

### 2. Stateless Operations
Each tool call is independent and idempotent:
- Generate with same inputs → same output
- Simulate multiple times → consistent results
- Safe to retry on failure

### 3. Agent-Friendly Errors
Provide actionable guidance, not just failure messages:

**Bad**: `"Error: Labware not found"`

**Good**: `"Labware 'tube_rack_96_1500ul_4' not found. Available labware: ['tube_rack_96_1500ul', ...]. Did you forget slot number (e.g., _4)?"`

### 4. Configuration as Resources
Expose configs as resources for LLM context:
- LLM reads `config://settings` to understand state
- Then calls `update_settings()` with informed changes

### 5. Prompts for Complexity
Chain operations and guide multi-step workflows:
- New experiment setup
- Troubleshooting
- Optimization

### 6. Robust Validation
Validate early and often:
- Pre-flight checks before generation
- Schema validation
- Simulation before deployment

---

## Security and Safety Considerations

### Path Validation
- Restrict operations to repository root
- Prevent path traversal attacks
- Validate file extensions

### Subprocess Safety
- Use `subprocess.run()` with `shell=False`
- Validate arguments
- Set timeouts

### TOML/CSV Parsing
- Safe parsing libraries
- Graceful error handling
- File size limits

### Data Protection
- No logging of sensitive data
- Redact paths in errors
- Secure backup handling

### Read-Only by Default
- Most operations read-only or create new files
- Explicit confirmation for destructive operations
- **Always backup configs before modification**

---

## Benefits of MCP Integration

### For Users
1. **Natural language interface** - Describe experiment, get protocol
2. **Guided workflows** - Step-by-step with intelligent defaults
3. **Automated validation** - Catch errors pre-hardware
4. **Configuration discovery** - Query available options
5. **AI troubleshooting** - Analyze errors, suggest fixes

### For Development
1. **Standardized interface** - MCP protocol for AI interactions
2. **Reusable across clients** - Claude Desktop, VS Code, custom apps
3. **Version controlled** - Server code alongside protocol code
4. **Extensible** - Easy to add capabilities
5. **Testable** - mcp-use enables automated testing

### For Reproducibility
1. **Programmatic configuration** - Fewer manual errors
2. **Audit trail** - Log all MCP operations
3. **Consistent formatting** - AI generates valid configs
4. **Format preservation** - Human-readable TOML maintained

---

## Codebase Transformation Summary

### File Lifecycle Across Phases

#### Preserved Throughout (Core Protocol System)
- ✅ `CherryPick_OT2.py` - Always auto-generated
- ✅ `helper_cherry_pick.py` - Refactored but not removed
- ✅ `settings.toml` - Enhanced with backup mechanism
- ✅ `labware_dict.toml` - Enhanced with backup mechanism
- ✅ `CSVs/` - Continues to accumulate
- ✅ `CLAUDE.md` - Updated with MCP instructions
- ✅ `OT2_UserGuide/` - Reference documentation

#### Evolved/Enhanced
- 🔄 `helper_cherry_pick.py` - Functions extracted for MCP (Phase 1)
- 🔄 `settings.toml` - Backup files created (Phase 2)
- 🔄 `labware_dict.toml` - Backup files created (Phase 2)

#### Deprecated/Archived (Phase 4)
- ⚠️ `simulate_protocol.sh` → `archived_scripts/`
- ⚠️ `copy_essentials.sh` → `archived_scripts/`

#### Created (MCP Server)
- ✨ `ot2_cherrypick_mcp/` - Entire MCP server package
  - Phase 1: Core tools + TOML handler + mcp-use tests
  - Phase 2: Configuration management
  - Phase 3: Workflow orchestration
  - Phase 4: Advanced diagnostics

### Migration Path for Users

**Phase 1:** Dual-mode (script OR MCP)
**Phase 2:** MCP preferred for config
**Phase 3:** MCP handles full workflows
**Phase 4:** Script-based workflow deprecated, mcp-use test suite complete

---

## Next Steps

1. **Proof of Concept** (1-2 days)
   - Install `tomlkit` and `mcp-use`
   - Test TOML editing preservation
   - Create basic FastMCP server with TOML handler
   - Implement 3 core tools
   - Write mcp-use test script
   - Validate STDIO communication

2. **Core Implementation** (1 week)
   - Implement Phase 1 tools and resources
   - Comprehensive error handling
   - Unit tests + TOML preservation tests
   - mcp-use integration test suite

3. **User Testing** (ongoing)
   - Real experiment workflows
   - mcp-use automated regression tests
   - Feedback on tool design
   - Refine prompts and errors

4. **Documentation** (parallel)
   - API documentation
   - Workflow examples
   - Troubleshooting guide
   - mcp-use testing guide

---

## References

### MCP Documentation
- Official MCP Docs: https://modelcontextprotocol.io/
- Python SDK: https://github.com/modelcontextprotocol/python-sdk
- FastMCP Framework: https://github.com/jlowin/fastmcp

### Testing Tools
- mcp-use GitHub: https://github.com/mcp-use/mcp-use
- mcp-use documentation for integration testing

### TOML Libraries
- tomlkit documentation: https://tomlkit.readthedocs.io/
- tomlkit GitHub: https://github.com/sdispater/tomlkit

### Implementation Examples
- Weather server: https://github.com/jalateras/weather
- Filesystem server: https://github.com/punkpeye/mcp-filesystem-python
- Official examples: https://github.com/modelcontextprotocol/servers

---

## Conclusion

Integrating the OpenTron cherry-pick system with MCP transforms it from a script-based tool into an AI-native system where users express experimental intent in natural language and receive validated, optimized protocols.

**Critical Success Factors:**

1. **TOML Editing with `tomlkit`** - Enables programmatic configuration while preserving human readability
2. **Testing with `mcp-use`** - Ensures server quality through automated testing with real LLMs
3. **High-Level Tool Design** - Task-oriented abstractions rather than low-level operations
4. **Phased Implementation** - Deliver value quickly (Phase 1) while building toward comprehensive system (Phases 2-4)
5. **Backward Compatibility** - Original workflows remain functional throughout evolution

The phased approach ensures continuous value delivery while maintaining system stability. Each phase is independently testable via mcp-use, enabling confident iteration toward the full production system.