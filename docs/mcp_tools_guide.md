# OT-2 CherryPick MCP Server Guide

## Overview

The OT-2 CherryPick MCP Server exposes the OpenTron protocol generation system through the Model Context Protocol (MCP), enabling AI assistants like Claude to programmatically configure, generate, validate, and deploy OT-2 liquid handling protocols.

**Implementation Location:** `src/ot2_cherrypick_mcp/`

## Architecture

The MCP server is organized into four main categories:

1. **Tools** - Executable functions that perform actions
2. **Resources** - URI-addressable read-only data sources
3. **Prompts** - Reusable workflow templates
4. **Core Modules** - Shared utilities (TOML handling, validation, simulation, deployment)

## MCP Tools

Tools are registered via `@mcp.tool()` decorators and provide high-level task-oriented operations.

### 1. Protocol Generation

**File:** `src/ot2_cherrypick_mcp/tools/protocol_tools.py`

#### `generate_protocol`

Compiles TOML configuration and CSV transfer file into a self-contained OT-2 protocol.

**Parameters:**
- `csv_path` (str, required) - Path to transfer CSV definition
- `settings_path` (str, default: "settings.toml") - Protocol settings
- `labware_path` (str, default: "labware_dict.toml") - Labware catalog
- `protocol_path` (str, default: "CherryPick_OT2.py") - Output protocol file
- `verbose` (bool, default: False) - Enable verbose logging

**Returns:** Dict with:
- `success` (bool) - Generation status
- `protocol_path` (str) - Path to generated protocol
- `message` (str) - Status message

**Prompt Location:** Inline in function decorator

**Example Use:**
```python
generate_protocol(
    csv_path="CSVs/experiment_2025.csv",
    settings_path="settings.toml",
    verbose=False
)
```

---

### 2. Configuration Management

**File:** `src/ot2_cherrypick_mcp/tools/config_tools.py`

#### `update_settings`

Modifies specific values in settings.toml using dot-notation paths while preserving file formatting and comments.

**Parameters:**
- `path` (str, required) - Dot-notation path (e.g., "settings.general.tip_reuse")
- `value` (str, required) - New value to set
- `settings_path` (str, default: "settings.toml") - Settings file path

**Returns:** Dict with:
- `success` (bool) - Update status
- `path` (str) - Path that was updated
- `old_value` (any) - Previous value
- `new_value` (any) - New value
- `message` (str) - Status message

**Editable Sections:**
- `settings.general.*` - Core behavior (tip_reuse, mode, starting_tip_well, head_speed)
- `settings.liquid_handling.*` - Physical parameters (pre-aspirate, wicking, delays, push-out)
- `settings.working_plate[N].*` - Deck layout entries

**Prompt Location:** Inline in function decorator

**Example Use:**
```python
update_settings(
    path="settings.general.tip_reuse",
    value="never"
)
```

#### `apply_liquid_preset`

Applies a complete liquid handling preset configuration from settings.toml presets section.

**Parameters:**
- `preset_name` (str, required) - Preset identifier (e.g., "standard", "viscous", "slippery")
- `settings_path` (str, default: "settings.toml") - Settings file path

**Returns:** Dict with:
- `success` (bool) - Application status
- `preset_name` (str) - Preset that was applied
- `changes` (list) - List of all configuration changes made
- `message` (str) - Status message

**Available Presets:**
- `standard` - Default parameters for aqueous buffers
- `viscous` - For DMSO, glycerol, oils (slower speeds, longer delays)
- `slippery` - For volatile solvents (reduced speed to prevent dripping)
- `minimal` - Bare minimum handling (no contact, no wicking)
- `aggressive` - Maximum mixing and contact (for difficult liquids)

**Prompt Location:** Inline in function decorator

**Example Use:**
```python
apply_liquid_preset(
    preset_name="viscous"
)
```

---

### 3. CSV Template Generation

**File:** `src/ot2_cherrypick_mcp/tools/csv_tools.py`

#### `generate_csv_template`

Creates a CSV template file in CSVs/ directory with proper column structure.

**Parameters:**
- `filename` (str, required) - Output filename (e.g., "experiment_2025.csv")
- `transfers` (int, required) - Number of transfer rows to generate
- `source_labware` (str, required) - Source labware identifier
- `dest_labware` (str, required) - Destination labware identifier
- `default_volume` (float, default: 0.0) - Default volume for all transfers
- `source_height` (float, optional) - Source height from bottom (mm)
- `dest_top` (float, optional) - Destination offset from top (mm, negative goes down)

**Returns:** Dict with:
- `success` (bool) - Generation status
- `csv_path` (str) - Path to generated CSV file
- `transfers` (int) - Number of rows created
- `message` (str) - Status message

**Generated Columns:**
- Source Labware, Source Well, Volume (ul), Dest Labware, Dest Well
- Source Height OR Source Top (mutually exclusive)
- Dest Height OR Dest Top (mutually exclusive)
- Optional: Mix Volume, Mix Height, Flow Aspirate, Flow Dispense, Air Gap, Air Gap Rate, Tip Action

**Prompt Location:** Inline in function decorator

**Example Use:**
```python
generate_csv_template(
    filename="cherry_pick_384.csv",
    transfers=96,
    source_labware="tube_rack_96_1500ul_4",
    dest_labware="384_ppv_55ul_2",
    default_volume=50.0,
    source_height=2.0,
    dest_top=-3.0
)
```

#### `upload_csv_content`

Writes provided CSV text to disk so subsequent tools can operate on it.

**Parameters:**
- `csv_content` (str, required) – Raw CSV string including the header row.
- `filename` (str, required) – Desired output filename (e.g., `tmp_uploaded.csv`).
- `output_dir` (str, default: `CSVs/`) – Directory where the file will be saved.

**Returns:** Dict with:
- `csv_file` (str) – Path to the saved CSV file.

**Example Use:**
```python
upload_csv_content(
    csv_content="Source Labware,Source Well,Volume (ul),Dest Labware,Dest Well,Source Height,Dest Top\n",
    filename="tmp_uploaded.csv",
)
```

---

### 4. Labware Catalog Management

**File:** `src/ot2_cherrypick_mcp/tools/labware_tools.py`

#### `add_labware_definition`

Appends a new labware entry to labware_dict.toml with optional calibration offsets.

**Parameters:**
- `labware_id` (str, required) - Unique labware identifier
- `category` (str, required) - Labware category ("plate", "tube_rack", "reservoir", etc.)
- `well_count` (int, required) - Total number of wells
- `well_volume` (int, required) - Maximum well volume (µL)
- `offset_x` (float, optional) - X-axis calibration offset (mm)
- `offset_y` (float, optional) - Y-axis calibration offset (mm)
- `offset_z` (float, optional) - Z-axis calibration offset (mm)
- `labware_path` (str, default: "labware_dict.toml") - Labware catalog file

**Returns:** Dict with:
- `success` (bool) - Addition status
- `labware_id` (str) - ID of added labware
- `message` (str) - Status message

**Editable Properties:**
All fields in the `[[labware]]` array can be added. Each entry must have:
- `labware_id` - Unique identifier
- `category` - Type classification
- `well_count` - Number of wells
- `well_volume` - Max volume per well
- Optionally: `offset_x`, `offset_y`, `offset_z` for calibration

**Prompt Location:** Inline in function decorator

**Example Use:**
```python
add_labware_definition(
    labware_id="custom_96_plate",
    category="plate",
    well_count=96,
    well_volume=200,
    offset_x=-0.5,
    offset_y=0.8,
    offset_z=-0.3
)
```

---

### 5. Protocol Simulation

**File:** `src/ot2_cherrypick_mcp/tools/simulation_tools.py`

#### `simulate_protocol`

Runs opentrons_simulate to validate the generated protocol without hardware.

**Parameters:**
- `protocol_path` (str, default: "CherryPick_OT2.py") - Protocol file to simulate
- `labware_path` (str, optional) - Custom labware directory path
- `timeout` (int, default: 180) - Simulation timeout in seconds
- `log_file` (str, default: "simulation_log.txt") - Output log file path

**Returns:** Dict with:
- `success` (bool) - Simulation status
- `protocol_path` (str) - Simulated protocol path
- `output` (str) - Simulation output/errors
- `log_file` (str) - Path to saved log
- `message` (str) - Status message

**Prompt Location:** Inline in function decorator

**Example Use:**
```python
simulate_protocol(
    protocol_path="CherryPick_OT2.py",
    labware_path="/path/to/custom/labware",
    timeout=180
)
```

---

### 6. Protocol Deployment

**File:** `src/ot2_cherrypick_mcp/tools/deployment_tools.py`

#### `deploy_to_opentrons`

Copies the generated protocol to a target path and optionally to system clipboard.

**Parameters:**
- `protocol_path` (str, default: "CherryPick_OT2.py") - Protocol to deploy
- `target_path` (str, optional) - Destination directory path
- `copy_to_clipboard` (bool, default: False) - Also copy to clipboard
- `clipboard_command` (str, optional) - Custom clipboard command (e.g., "clip.exe", "pbcopy")

**Returns:** Dict with:
- `success` (bool) - Deployment status
- `protocol_path` (str) - Source protocol
- `target_path` (str) - Destination path (if applicable)
- `clipboard` (bool) - Whether copied to clipboard
- `message` (str) - Status message

**Prompt Location:** Inline in function decorator

**Example Use:**
```python
deploy_to_opentrons(
    protocol_path="CherryPick_OT2.py",
    target_path="/path/to/opentrons/protocols/",
    copy_to_clipboard=True,
    clipboard_command="clip.exe"
)
```

---

### 7. Configuration Validation

**File:** `src/ot2_cherrypick_mcp/tools/validation_tools.py`

#### `validate_configuration`

Pre-flight validation of TOML and CSV inputs before protocol generation.

**Parameters:**
- `csv_path` (str, required) - Transfer CSV to validate
- `settings_path` (str, default: "settings.toml") - Settings file
- `labware_path` (str, default: "labware_dict.toml") - Labware catalog

**Returns:** Dict with:
- `valid` (bool) - Overall validation status
- `errors` (list) - List of validation errors
- `warnings` (list) - List of validation warnings
- `message` (str) - Summary message

**Checks Performed:**
- TOML syntax validation
- Labware reference consistency
- Deck slot conflicts
- Volume range validation
- CSV column structure
- Height specification consistency

**Prompt Location:** Inline in function decorator

**Example Use:**
```python
validate_configuration(
    csv_path="CSVs/experiment.csv",
    settings_path="settings.toml",
    labware_path="labware_dict.toml"
)
```

---

### 8. Full Workflow Orchestration

**File:** `src/ot2_cherrypick_mcp/tools/workflow_tools.py`

#### `full_workflow`

End-to-end orchestration: validation → generation → simulation → optional deployment.

**Parameters:**
- `csv_path` (str, required) - Transfer CSV file
- `settings_path` (str, default: "settings.toml") - Settings file
- `labware_path` (str, default: "labware_dict.toml") - Labware catalog
- `protocol_path` (str, default: "CherryPick_OT2.py") - Output protocol
- `simulate` (bool, default: True) - Run simulation after generation
- `labware_env_path` (str, optional) - Custom labware directory for simulation
- `deploy` (bool, default: False) - Deploy after successful simulation
- `deployment_target` (str, optional) - Deployment destination path
- `copy_to_clipboard` (bool, default: False) - Copy to clipboard after deployment
- `clipboard_command` (str, optional) - Custom clipboard command

**Returns:** Dict with:
- `success` (bool) - Overall workflow status
- `validation` (dict) - Validation results
- `generation` (dict) - Generation results
- `simulation` (dict) - Simulation results (if enabled)
- `deployment` (dict) - Deployment results (if enabled)
- `message` (str) - Summary message

**Prompt Location:** Inline in function decorator

**Example Use:**
```python
full_workflow(
    csv_path="CSVs/experiment.csv",
    simulate=True,
    deploy=True,
    deployment_target="/path/to/opentrons/",
    copy_to_clipboard=True
)
```

---

## MCP Resources

Resources are read-only data sources registered via `@mcp.resource()` decorators.

### 1. Configuration Resources

**File:** `src/ot2_cherrypick_mcp/resources/config_resources.py`

#### `config://settings`

Returns the complete settings.toml file content.

**Description:** "settings.toml configuration file"

**Returns:** String containing TOML content or error message

**Example Use:** Query this resource to understand current protocol configuration before making changes.

#### `config://labware`

Returns the complete labware_dict.toml file content.

**Description:** "labware_dict.toml catalog file"

**Returns:** String containing TOML content or error message

**Example Use:** Query to see available labware definitions and calibration offsets.

---

### 2. File Resources

**File:** `src/ot2_cherrypick_mcp/resources/file_resources.py`

#### `files://csvs`

Lists all CSV files in the CSVs/ directory.

**Description:** "List of available CSV transfer files"

**Returns:** Newline-separated list of CSV filenames

**Example Use:** Query to see what transfer definitions are available before selecting one for protocol generation.

---

### 3. Log Resources

**File:** `src/ot2_cherrypick_mcp/resources/log_resources.py`

#### `logs://last-simulation`

Returns the most recent simulation log entry.

**Description:** "Most recent simulation log entry"

**Returns:** String containing log content or empty string if no log exists

**Example Use:** Query after a failed simulation to understand errors.

---

### 4. Status Resources

**File:** `src/ot2_cherrypick_mcp/resources/status_resources.py`

#### `status://deck-layout`

Provides a human-readable summary of the current deck configuration from settings.toml.

**Description:** "Summary of current deck configuration"

**Returns:** Formatted string showing:
```
Deck Layout:
- Slot 4: tube_rack_96_1500ul [source]
- Slot 2: 384_ppv_55ul [destination]
- Slot 5: opentrons_96_tiprack_300ul [tip]
```

**Example Use:** Query to visualize deck setup before configuring an experiment.

#### `status://liquid-handling-config`

Shows active liquid handling parameters from settings.toml.

**Description:** "Active liquid handling parameters from settings.toml"

**Returns:** Formatted string showing:
```
Liquid Handling Configuration:
- pre_aspirate_contact: {...}
- post_aspirate_wick: {...}
- delays: {...}
- push_out: {...}
```

**Example Use:** Query to understand current liquid handling behavior before applying presets.

---

## MCP Prompts

Prompts are reusable workflow templates registered via `@mcp.prompt` decorators.

**File:** `src/ot2_cherrypick_mcp/prompts/workflow_prompts.py`

### 1. `setup_new_experiment`

Guides an AI agent through configuring a new cherry-pick experiment.

**Prompt Text:**
```
Goal: configure a new cherry-pick run.

1. Inspect current configuration via config://settings and status://deck-layout.
2. Apply liquid handling presets with the apply_liquid_preset tool if appropriate.
3. Use update_settings to adjust parameters such as tip reuse or head speed.
4. Generate a CSV template with generate_csv_template or review existing files via files://csvs.
5. Validate, generate, and simulate using the full_workflow tool, enabling deployment if needed.
```

**Use Case:** Starting a new experiment from scratch with guided steps.

**Example Invocation:** "Follow the setup_new_experiment prompt to configure a protocol for viscous liquids."

---

### 2. `troubleshoot_simulation_error`

Guides troubleshooting of failed protocol simulations.

**Prompt Text:**
```
When a simulation fails:
- Read logs://last-simulation to understand the failure.
- Re-check deck layout via status://deck-layout and ensure labware IDs match labware_dict.toml.
- Validate inputs with validate_configuration; address any errors.
- Re-run full_workflow after fixing issues, and report concrete changes made.
```

**Use Case:** Debugging simulation failures systematically.

**Example Invocation:** "Use the troubleshoot_simulation_error prompt to diagnose why my simulation failed."

---

## Core Modules

### TOML Handler

**File:** `src/ot2_cherrypick_mcp/utils/toml.py`

Provides format-preserving TOML editing capabilities using `tomlkit`.

**Key Features:**
- Preserves comments, formatting, and whitespace
- Dot-notation path access (e.g., "settings.general.tip_reuse")
- Automatic backup creation (`.toml.backup` files)
- Atomic write operations

**Main Class:** `TomlHandler`

**Methods:**
- `read_text()` - Get raw TOML content
- `read_document()` - Parse into TOMLDocument
- `get_value(dotted_path)` - Retrieve value via path
- `set_value(dotted_path, value)` - Update value with backup
- `set_values(updates)` - Batch update multiple values

**Example:**
```python
from ot2_cherrypick_mcp.utils.toml import TomlHandler

handler = TomlHandler("settings.toml")
old, new = handler.set_value("settings.general.tip_reuse", "never")
```

---

### Validation Module

**File:** `src/ot2_cherrypick_mcp/core/validation.py`

Implements pre-flight checks for protocol generation.

**Key Function:** `validate_configuration(settings_path, labware_path, csv_path)`

**Validation Logic:**
- TOML syntax parsing
- Labware reference existence
- Deck slot uniqueness
- Volume within pipette range
- CSV column structure
- Height specification rules

---

### Simulation Module

**File:** `src/ot2_cherrypick_mcp/core/simulation.py`

Wraps opentrons_simulate execution with proper environment handling.

**Key Function:** `run_simulation(protocol_path, labware_path, timeout, log_file)`

**Features:**
- Subprocess execution with timeout
- Custom labware path injection via environment variable
- Output capture and logging
- Error parsing

---

### Deployment Module

**File:** `src/ot2_cherrypick_mcp/core/deployment.py`

Handles protocol file deployment to target locations.

**Key Function:** `run_deployment(protocol_path, target_path, copy_to_clipboard, clipboard_command)`

**Features:**
- File copying with validation
- Clipboard integration (Windows/Linux/macOS)
- Configurable clipboard command
- Path resolution and safety checks

---

## Editable Configuration Summary

### settings.toml Editable Sections

**Via `update_settings` tool:**

1. **settings.general** - Core protocol behavior
   - `tip_reuse` - "always", "never", "per_source"
   - `mode` - "single_X1", "multi_X1", "multi"
   - `starting_tip_well` - Initial tip position (e.g., "A1")
   - `head_speed.speed` - Movement speed (mm/min)

2. **settings.liquid_handling** - Physical parameters
   - `pre_aspirate_contact.enabled` - Pre-wet tip behavior
   - `pre_aspirate_contact.position_offset_percent` - Contact depth
   - `pre_aspirate_contact.aspirate_volume` - Pre-wet volume
   - `post_aspirate_wick.enabled` - Tip wicking behavior
   - `post_aspirate_wick.radius` - Touch radius
   - `post_aspirate_wick.v_offset_mm` - Vertical offset
   - `post_aspirate_wick.speed` - Touch speed
   - `delays.post_aspirate` - Wait after aspirate (seconds)
   - `push_out.enabled` - Push-out behavior
   - `push_out.volume_ul` - Extra air volume

3. **settings.working_plate** - Deck layout (array modification)
   - Array entries with: `type`, `labware_id`, `position_rack`, `connection`

**Via `apply_liquid_preset` tool:**
- Applies entire preset configuration atomically
- Presets defined under `settings.liquid_handling.presets`

### labware_dict.toml Editable Sections

**Via `add_labware_definition` tool:**

1. **[[labware]]** array - Labware definitions
   - `labware_id` - Unique identifier
   - `category` - Type (plate, tube_rack, reservoir, etc.)
   - `well_count` - Number of wells
   - `well_volume` - Max volume per well (µL)
   - `offset_x` - X calibration offset (mm)
   - `offset_y` - Y calibration offset (mm)
   - `offset_z` - Z calibration offset (mm)

---

## Usage Examples

### Example 1: Configure and Generate Protocol

```python
# 1. Check current configuration
config = read_resource("config://settings")
deck = read_resource("status://deck-layout")

# 2. Apply viscous liquid preset
result = apply_liquid_preset(preset_name="viscous")

# 3. Set tip reuse strategy
update_settings(path="settings.general.tip_reuse", value="per_source")

# 4. Generate and simulate
workflow = full_workflow(
    csv_path="CSVs/cherry_pick_384.csv",
    simulate=True,
    deploy=False
)
```

### Example 2: Add New Labware and Use It

```python
# 1. Add custom labware to catalog
add_labware_definition(
    labware_id="custom_384_pcr",
    category="plate",
    well_count=384,
    well_volume=50,
    offset_x=-0.3,
    offset_y=0.5,
    offset_z=-0.2
)

# 2. Generate CSV template using new labware
generate_csv_template(
    filename="custom_protocol.csv",
    transfers=96,
    source_labware="tube_rack_96_1500ul_4",
    dest_labware="custom_384_pcr_2",
    default_volume=25.0
)

# 3. Validate and generate
full_workflow(csv_path="CSVs/custom_protocol.csv")
```

### Example 3: Troubleshoot Simulation Failure

```python
# 1. Run workflow and capture failure
result = full_workflow(csv_path="CSVs/test.csv")

# 2. Check simulation log
log = read_resource("logs://last-simulation")

# 3. Validate configuration
validation = validate_configuration(
    csv_path="CSVs/test.csv",
    settings_path="settings.toml",
    labware_path="labware_dict.toml"
)

# 4. Fix issues based on validation errors
# ... apply fixes ...

# 5. Re-run workflow
result = full_workflow(csv_path="CSVs/test.csv")
```

---

## Implementation Status

### Completed Features (Phase 1-3)

✅ Core protocol generation tools
✅ Configuration management (update_settings, apply_liquid_preset)
✅ CSV template generation
✅ Labware catalog management
✅ Protocol simulation
✅ Deployment tools
✅ Full workflow orchestration
✅ Configuration resources (settings, labware)
✅ File resources (CSV listing)
✅ Log resources (simulation logs)
✅ Status resources (deck layout, liquid handling)
✅ Workflow prompts (setup, troubleshooting)
✅ TOML handler with format preservation
✅ Validation module
✅ Simulation wrapper
✅ Deployment module

### Not Yet Implemented

- Robot HTTP API integration (Phase 4)
- Advanced diagnostic tools (Phase 4)
- CSV linting with specific error reporting (Phase 4)
- AI-powered log analysis (Phase 4)

---

## Server Entry Point

**File:** `src/ot2_cherrypick_mcp/server.py`

**Main Function:** `main()`

**Execution:**
```bash
# Via pixi task (recommended)
pixi run ot2-mcp-server

# Direct Python execution
pixi run python -m ot2_cherrypick_mcp.server
```

**Server Configuration:**
- Name: "ot2-cherrypick"
- Transport: STDIO (stdin/stdout)
- Working Directory: Repository root
- Logging: stderr only (to avoid corrupting JSON-RPC)

---

## Testing

The MCP server can be tested using `mcp-use` library with Mistral LLM.

**Example Test Script:**
```python
from mcp_use import MCPClient
from langchain_mistralai import ChatMistralAI
from mcp_use.agents import MCPAgent

# Initialize client and LLM
client = MCPClient.from_config("test_config.json")
llm = ChatMistralAI(model="mistral-large-latest")

# Create agent with access to MCP tools
agent = MCPAgent(llm=llm, client=client, max_steps=10)

# Execute test query
response = await agent.ainvoke("What is the current tip reuse setting?")
print(response)
```

**Test Documentation:** See `docs/readme_mcp_use.md` for detailed testing instructions.

---

## Summary

The MCP server provides **8 tools**, **6 resources**, and **2 prompts** that expose the complete OT-2 CherryPick protocol generation workflow to AI assistants. The implementation follows the design document closely, with all Phase 1-3 features completed and ready for use. The server enables natural language interaction with complex liquid handling protocol configuration while maintaining the human-readable TOML/CSV source-of-truth files.
