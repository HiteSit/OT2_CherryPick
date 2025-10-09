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

**FastMCP** is the modern, production-ready approach:

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("opentron-cherry-pick")

@mcp.tool()
async def my_tool(param: str) -> str:
    """Tool description from docstring"""
    return result

@mcp.resource("resource://my-data")
async def my_resource() -> str:
    """Resource description"""
    return data

@mcp.prompt()
async def my_prompt() -> str:
    """Prompt template"""
    return template
```

### Critical Implementation Rules

1. **Never write to stdout** - Corrupts JSON-RPC messages (use stderr or files)
2. **Agent-friendly errors** - Return actionable guidance, not just failure messages
3. **STDIO transport** - Preferred for development and local MCP servers
4. **Type hints + docstrings** - FastMCP auto-generates schemas from these
5. **Logging discipline** - Use logging library configured for stderr
6. **Idempotency** - Tools should handle repeated calls safely

---

## Proposed MCP Server Design for OpenTron

### Tool Definitions

#### 1. `generate_protocol`
**Purpose**: Generate CherryPick_OT2.py from TOML + CSV inputs

```python
@mcp.tool()
async def generate_protocol(
    csv_file_path: str,
    settings_toml_path: str = "settings.toml",
    labware_toml_path: str = "labware_dict.toml",
    output_protocol_path: str = "CherryPick_OT2.py"
) -> dict:
    """
    Generate OT-2 protocol by compiling TOML and CSV into embedded JSON.
    
    Args:
        csv_file_path: Path to CSV transfer definition file
        settings_toml_path: Path to settings TOML (default: settings.toml)
        labware_toml_path: Path to labware dictionary (default: labware_dict.toml)
        output_protocol_path: Output protocol file (default: CherryPick_OT2.py)
    
    Returns:
        dict: {
            "success": bool,
            "protocol_path": str,
            "json_size": int,
            "message": str
        }
    """
```

**Implementation**: Wraps `helper_cherry_pick.py` functions

---

#### 2. `simulate_protocol`
**Purpose**: Run Opentrons simulation to validate protocol

```python
@mcp.tool()
async def simulate_protocol(
    protocol_path: str = "CherryPick_OT2.py",
    custom_labware_path: str | None = None
) -> dict:
    """
    Simulate OT-2 protocol using opentrons_simulate.
    
    Args:
        protocol_path: Path to protocol file to simulate
        custom_labware_path: Path to custom labware directory (auto-detected if None)
    
    Returns:
        dict: {
            "success": bool,
            "output": str,  # Simulation log
            "errors": list[str],  # Any errors encountered
            "warnings": list[str]  # Any warnings
        }
    """
```

**Implementation**: Executes `opentrons_simulate` command via subprocess

---

#### 3. `validate_configuration`
**Purpose**: Pre-flight validation of TOML + CSV without full generation

```python
@mcp.tool()
async def validate_configuration(
    csv_file_path: str,
    settings_toml_path: str = "settings.toml",
    labware_toml_path: str = "labware_dict.toml"
) -> dict:
    """
    Validate TOML and CSV files for correctness before protocol generation.
    
    Checks:
    - TOML syntax validity
    - Required fields present
    - Labware references in CSV match definitions
    - Deck slot conflicts
    - Volume ranges compatible with pipettes
    - Multi-mode plate compatibility
    
    Returns:
        dict: {
            "valid": bool,
            "errors": list[str],
            "warnings": list[str],
            "statistics": {
                "transfer_count": int,
                "unique_labware": list[str],
                "estimated_tips": int
            }
        }
    """
```

---

#### 4. `update_settings`
**Purpose**: Programmatic modification of settings.toml

```python
@mcp.tool()
async def update_settings(
    setting_path: str,
    value: str | int | float | bool,
    settings_file: str = "settings.toml"
) -> dict:
    """
    Update specific setting in settings.toml.
    
    Args:
        setting_path: Dot-notation path (e.g., "general.tip_reuse", "liquid_handling.push_out.enabled")
        value: New value to set
        settings_file: Path to settings file
    
    Returns:
        dict: {
            "success": bool,
            "old_value": any,
            "new_value": any,
            "message": str
        }
    """
```

---

#### 5. `apply_liquid_preset`
**Purpose**: Apply predefined liquid handling presets

```python
@mcp.tool()
async def apply_liquid_preset(
    preset_name: str,  # "standard", "viscous", "slippery", "minimal", "aggressive"
    settings_file: str = "settings.toml"
) -> dict:
    """
    Apply a liquid handling preset from settings.toml presets section.
    
    Copies preset configuration to active liquid_handling section.
    
    Args:
        preset_name: Name of preset (standard/viscous/slippery/minimal/aggressive)
        settings_file: Path to settings file
    
    Returns:
        dict: {
            "success": bool,
            "applied_preset": str,
            "changes": dict  # What changed
        }
    """
```

---

#### 6. `add_labware_definition`
**Purpose**: Add new labware type to labware_dict.toml

```python
@mcp.tool()
async def add_labware_definition(
    labware_id: str,
    category: str,  # "plate", "tube_rack", "tip_rack", "reservoir"
    well_count: int,
    well_volume: int,
    offset_x: float = 0.0,
    offset_y: float = 0.0,
    offset_z: float = 0.0,
    labware_file: str = "labware_dict.toml"
) -> dict:
    """
    Add new labware definition to labware dictionary.
    
    Args:
        labware_id: Unique identifier for labware type
        category: Labware category
        well_count: Number of wells
        well_volume: Well volume in µL
        offset_x/y/z: Calibration offsets in mm
        labware_file: Path to labware dictionary
    
    Returns:
        dict: {
            "success": bool,
            "labware_id": str,
            "message": str
        }
    """
```

---

#### 7. `create_csv_template`
**Purpose**: Generate CSV template for specific labware configuration

```python
@mcp.tool()
async def create_csv_template(
    source_labware: str,  # e.g., "tube_rack_96_1500ul_4"
    dest_labware: str,    # e.g., "384_ppv_55ul_2"
    num_transfers: int,
    output_path: str,
    include_optional_columns: bool = False
) -> dict:
    """
    Generate CSV template file for transfers between specified labware.
    
    Args:
        source_labware: Source labware ID + slot (e.g., "tube_rack_96_1500ul_4")
        dest_labware: Destination labware ID + slot
        num_transfers: Number of transfer rows to generate
        output_path: Output CSV file path
        include_optional_columns: Include Mix Volume, Flow rates, etc.
    
    Returns:
        dict: {
            "success": bool,
            "csv_path": str,
            "row_count": int
        }
    """
```

---

#### 8. `deploy_to_opentrons`
**Purpose**: Copy protocol to Opentrons App directory

```python
@mcp.tool()
async def deploy_to_opentrons(
    protocol_path: str = "CherryPick_OT2.py",
    machine_config: str = "local"  # "local" or "remote"
) -> dict:
    """
    Deploy protocol to Opentrons App directory for specific machine configuration.
    
    Reads TARGET_PROTOCOL_SRC from simulate_protocol.sh configuration.
    
    Args:
        protocol_path: Source protocol file
        machine_config: Machine configuration name ("local" or "remote")
    
    Returns:
        dict: {
            "success": bool,
            "target_path": str,
            "message": str
        }
    """
```

---

#### 9. `full_workflow`
**Purpose**: End-to-end orchestration (generate → simulate → optional deploy)

```python
@mcp.tool()
async def full_workflow(
    csv_file_path: str,
    deploy: bool = False,
    machine_config: str = "local"
) -> dict:
    """
    Execute complete workflow: validate → generate → simulate → [deploy].
    
    This is the high-level tool that chains the entire process.
    
    Args:
        csv_file_path: Path to CSV transfer file
        deploy: Whether to deploy to Opentrons App after successful simulation
        machine_config: Target machine ("local" or "remote")
    
    Returns:
        dict: {
            "success": bool,
            "stages": {
                "validation": dict,
                "generation": dict,
                "simulation": dict,
                "deployment": dict | None
            },
            "protocol_ready": bool
        }
    """
```

---

### Resource Definitions

Resources expose configuration and state as read-only data.

#### 1. `config://settings`
```python
@mcp.resource("config://settings")
async def get_settings() -> str:
    """Current settings.toml configuration"""
    with open("settings.toml", "r") as f:
        return f.read()
```

#### 2. `config://labware`
```python
@mcp.resource("config://labware")
async def get_labware_dict() -> str:
    """Current labware_dict.toml definitions"""
    with open("labware_dict.toml", "r") as f:
        return f.read()
```

#### 3. `status://deck-layout`
```python
@mcp.resource("status://deck-layout")
async def get_deck_layout() -> str:
    """
    Current deck layout visualization and slot assignments.
    
    Returns formatted representation of deck configuration.
    """
    # Parse settings.toml and return formatted deck layout
```

#### 4. `status://liquid-handling-config`
```python
@mcp.resource("status://liquid-handling-config")
async def get_liquid_handling() -> str:
    """Current liquid handling parameters"""
    # Parse and return liquid handling settings in readable format
```

#### 5. `files://csvs`
```python
@mcp.resource("files://csvs")
async def list_csv_files() -> str:
    """List available CSV transfer files in CSVs/ directory"""
    # Return list of CSV files with metadata (size, modified date)
```

#### 6. `logs://last-simulation`
```python
@mcp.resource("logs://last-simulation")
async def get_last_simulation_log() -> str:
    """Output from most recent protocol simulation"""
    # Return cached simulation output
```

---

### Prompt Definitions

Prompts guide the LLM through complex workflows.

#### 1. `setup_new_experiment`
```python
@mcp.prompt()
async def setup_new_experiment() -> str:
    """
    Guide user through setting up a new cherry-pick experiment.
    
    Workflow:
    1. Ask about liquid type (aqueous/viscous/slippery)
    2. Recommend liquid handling preset
    3. Configure deck layout (source/dest labware)
    4. Create CSV template
    5. Validate configuration
    """
    return """
    I'll help you set up a new cherry-pick experiment for the OT-2.
    
    First, tell me:
    1. What type of liquid are you transferring? (aqueous/DMSO-like/hydrophobic)
    2. What source labware will you use? (e.g., tube_rack_96_1500ul)
    3. What destination labware? (e.g., 384_ppv_55ul)
    4. Which deck slots for each? (see deck diagram)
    5. How many transfers?
    
    I'll configure the optimal settings and generate a CSV template.
    """
```

#### 2. `add_new_labware_type`
```python
@mcp.prompt()
async def add_new_labware_type() -> str:
    """
    Guide user through adding a new labware type with calibration.
    
    Workflow:
    1. Collect labware specifications
    2. Add to labware_dict.toml
    3. Recommend calibration procedure
    4. Test with dry run protocol
    """
```

#### 3. `troubleshoot_simulation_error`
```python
@mcp.prompt()
async def troubleshoot_simulation_error() -> str:
    """
    Help diagnose and fix common simulation errors.
    
    Analyzes last simulation log and suggests fixes.
    """
```

#### 4. `optimize_liquid_handling`
```python
@mcp.prompt()
async def optimize_liquid_handling() -> str:
    """
    Interactive guide to tune liquid handling parameters.
    
    Asks about observed issues (dripping, inaccuracy, splashing)
    and recommends parameter adjustments.
    """
```

---

## Implementation Architecture

### File Structure

```
opentron_cherry_pick_mcp/
├── src/
│   ├── __init__.py
│   ├── server.py              # Main MCP server with FastMCP
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── protocol_tools.py  # generate, simulate, validate
│   │   ├── config_tools.py    # update_settings, apply_preset
│   │   └── labware_tools.py   # add_labware, create_csv_template
│   ├── resources/
│   │   ├── __init__.py
│   │   ├── config_resources.py
│   │   └── status_resources.py
│   ├── prompts/
│   │   ├── __init__.py
│   │   └── workflow_prompts.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── validation.py      # Configuration validation logic
│   │   ├── toml_handler.py    # TOML read/write utilities
│   │   └── simulation.py      # Simulation execution wrapper
│   └── utils/
│       ├── __init__.py
│       ├── logging_config.py  # Stderr logging setup
│       └── errors.py          # Custom exception types
├── tests/
│   ├── test_tools.py
│   ├── test_resources.py
│   └── test_integration.py
├── pyproject.toml
├── README.md
└── config.json                # MCP server configuration for Claude Desktop
```

### Server Entry Point (server.py)

```python
"""
OpenTron Cherry-Pick MCP Server

Provides MCP interface to the OpenTron OT-2 cherry-pick protocol generation system.
"""

import logging
import sys
from pathlib import Path
from mcp.server.fastmcp import FastMCP

# Configure logging to stderr ONLY
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)

logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("opentron-cherry-pick")

# Set working directory to repository root
REPO_ROOT = Path(__file__).parent.parent.parent
mcp.settings.base_directory = str(REPO_ROOT)

# Import and register all tools
from .tools import protocol_tools, config_tools, labware_tools
from .resources import config_resources, status_resources
from .prompts import workflow_prompts

def main():
    """Entry point for MCP server"""
    logger.info("Starting OpenTron Cherry-Pick MCP Server")
    logger.info(f"Working directory: {REPO_ROOT}")
    
    # Run server with STDIO transport
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
```

### Claude Desktop Configuration

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "opentron-cherry-pick": {
      "command": "uv",
      "args": [
        "--directory",
        "/mnt/d/Amadteus_Main/OpenTron/OT2_CherryPick/opentron_cherry_pick_mcp",
        "run",
        "opentron-mcp-server"
      ],
      "env": {
        "LABWARE_PATH": "/mnt/c/Users/ricca/AppData/Roaming/Opentrons/labware"
      }
    }
  }
}
```

---

## Development Phases

### Phase 1: Core Protocol Tools (MVP)
- `generate_protocol`
- `simulate_protocol`
- `validate_configuration`
- Basic resources: `config://settings`, `config://labware`
- Simple logging and error handling

**Goal**: Basic protocol generation and validation via MCP

### Phase 2: Configuration Management
- `update_settings`
- `apply_liquid_preset`
- `add_labware_definition`
- Additional resources: `status://deck-layout`, `status://liquid-handling-config`

**Goal**: Programmatic configuration without manual TOML editing

### Phase 3: Workflow Orchestration
- `full_workflow`
- `deploy_to_opentrons`
- `create_csv_template`
- Workflow prompts: `setup_new_experiment`

**Goal**: End-to-end automation with guided workflows

### Phase 4: Advanced Features
- CSV validation and linting
- Troubleshooting prompts
- Simulation log analysis
- Integration with Opentrons API for robot status

**Goal**: Production-ready system with comprehensive diagnostics

---

## Key Design Principles

### 1. High-Level Abstractions
Tools should represent **tasks**, not low-level operations. For example:
- ✅ `full_workflow(csv_file)` - Complete protocol generation
- ❌ `read_toml()`, `write_json()` - Too granular

### 2. Stateless Operations
Each tool call should be independent and idempotent:
- Generate protocol with same inputs → same output
- Simulate multiple times → consistent results
- Safe to retry on failure

### 3. Agent-Friendly Errors
Don't just report failures - provide actionable guidance:

**Bad**: `"Error: Labware not found"`

**Good**: `"Labware 'tube_rack_96_1500ul_4' not found in settings.toml. Available labware in labware_dict.toml: ['tube_rack_96_1500ul', 'tube_rack_96_2000ul', ...]. Did you forget to add slot number (e.g., _4)?"`

### 4. Configuration as Resources
Expose config files as resources so LLM can read them before making decisions:
```python
# LLM can first read config://settings to understand current state
# Then call update_settings() with informed changes
```

### 5. Prompts for Complexity
Use prompts to chain operations and guide users through multi-step workflows:
- New experiment setup
- Troubleshooting
- Optimization

### 6. Robust Validation
Validate early and often:
- Pre-flight checks before generation
- Schema validation on TOML/CSV
- Simulation before deployment

---

## Security and Safety Considerations

### 1. Path Validation
- All file paths must be within repository root
- Prevent path traversal attacks (`../../`)
- Validate file extensions

### 2. Subprocess Safety
- Use `subprocess.run()` with shell=False
- Validate command arguments
- Set timeouts to prevent hanging

### 3. TOML/CSV Parsing
- Use safe parsing libraries (toml, csv)
- Catch and report malformed input gracefully
- Limit file sizes

### 4. No Sensitive Data
- Don't log API keys or credentials
- Redact paths containing usernames in error messages

### 5. Read-Only by Default
- Most operations should be read-only or create new files
- Require explicit confirmation for destructive operations
- Backup configs before modification

---

## Testing Strategy

### Unit Tests
- Individual tool functions
- TOML/CSV parsing and validation
- Error handling and edge cases

### Integration Tests
- Full workflow execution
- Resource retrieval
- Prompt rendering

### Simulation Tests
- Generate and simulate various protocol configurations
- Test multi-mode compatibility checks
- Volume range validation

### MCP Protocol Tests
- JSON-RPC message formatting
- STDIO communication
- Error propagation

---

## Benefits of MCP Integration

### For Users
1. **Natural language interface** - Describe experiment, get configured protocol
2. **Guided workflows** - Step-by-step setup with intelligent defaults
3. **Automated validation** - Catch errors before hardware run
4. **Configuration discovery** - Ask "what presets are available?" and get answers
5. **Troubleshooting assistance** - AI analyzes errors and suggests fixes

### For Development
1. **Standardized interface** - MCP protocol for all AI interactions
2. **Reusable across clients** - Works with Claude Desktop, VS Code, custom apps
3. **Version controlled** - Server code in git alongside protocol code
4. **Extensible** - Easy to add new tools as system evolves

### For Reproducibility
1. **Programmatic configuration** - No manual editing, fewer mistakes
2. **Audit trail** - Log all MCP calls for experiment provenance
3. **Consistent formatting** - AI generates valid TOML/CSV every time

---

## Next Steps

1. **Proof of Concept** (1-2 days)
   - Create basic FastMCP server with 3 core tools
   - Test with Claude Desktop
   - Validate STDIO communication

2. **Core Implementation** (1 week)
   - Implement Phase 1 tools and resources
   - Add comprehensive error handling
   - Write unit tests

3. **User Testing** (ongoing)
   - Test with real experiment workflows
   - Gather feedback on tool design
   - Refine prompts and error messages

4. **Documentation** (parallel)
   - API documentation for all tools/resources
   - Example workflows
   - Troubleshooting guide

---

## References

### MCP Documentation
- Official MCP Docs: https://modelcontextprotocol.io/
- Python SDK: https://github.com/modelcontextprotocol/python-sdk
- FastMCP Framework: https://github.com/jlowin/fastmcp

### Implementation Examples
- Weather server: https://github.com/jalateras/weather
- Filesystem server: https://github.com/punkpeye/mcp-filesystem-python
- Official examples: https://github.com/modelcontextprotocol/servers

### Best Practices
- DigitalOcean MCP Guide: https://www.digitalocean.com/community/tutorials/mcp-server-python
- Production Best Practices: https://thenewstack.io/15-best-practices-for-building-mcp-servers-in-production/

---

## Conclusion

Integrating the OpenTron cherry-pick system with MCP will transform it from a script-based tool into an AI-native system where users can express experimental intent in natural language and receive validated, optimized protocols. The key is designing high-level, task-oriented tools that abstract away implementation details while providing the LLM with sufficient context through resources to make intelligent decisions.

The phased implementation approach ensures we deliver value quickly (Phase 1 MVP) while building toward a comprehensive, production-ready system (Phases 2-4).
