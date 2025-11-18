# MCP Response Format Implementation Analysis

## Executive Summary

The MCP tool implementation currently returns **unformatted dictionaries** that are appropriate for LLM processing but lack structure for different use cases (JSON export, markdown rendering, concise vs detailed summaries). All return types are `Dict[str, Any]` or `Dict[str, object]`.

**Key Finding:** There is NO existing formatting layer - all tools return raw data dictionaries that need formatting.

## Current Return Patterns Across Tools

### 1. Protocol Generation Tool
**File:** `src/ot2_cherrypick_mcp/tools/protocol_tools.py:run_generate_protocol()`

**Current Return:**
```python
{
    "protocol_file": str,      # Path to generated protocol
    "json_size": int,          # Embedded JSON size in characters
    "message": str,            # Success message
}
```

**Source:** Wraps result from `core/protocol_generator.py:generate_protocol()` which returns `{'protocol_file', 'json_size', 'message'}`

**JSON Format:** Already dict-serializable, minimal processing needed
**Markdown Format:** Single sentence summary with file path and size
**Concise:** Just message + protocol_file
**Detailed:** Add json_size + timestamp + success confirmation

---

### 2. Simulation Tool
**File:** `src/ot2_cherrypick_mcp/tools/simulation_tools.py:run_simulation()`

**Current Return:**
```python
{
    "command": list[str],      # Full opentrons_simulate command
    "stdout": str,             # Simulation output (multiline)
    "stderr": str,             # Error output (multiline)
    "returncode": int,         # Exit code (0 = success)
    "log_file": str | None,    # Path to log file if created
}
```

**Source:** Wraps result from `core/simulation.py:simulate_protocol()` which adds "protocol_path" and "labware_path" fields

**JSON Format:** Direct dict serialization works (multiline strings as-is)
**Markdown Format:** Complex - needs:
  - Collapsible sections for stdout/stderr (they're long)
  - Command as code block
  - Success/failure indication based on returncode
  - Highlight key lines from output

**Concise:** returncode + 1-line summary ("Simulation PASSED" or "FAILED: <error>")
**Detailed:** Full stdout + stderr + command + paths + returncode

---

### 3. Configuration Management Tool
**File:** `src/ot2_cherrypick_mcp/tools/config_tools.py:list_settings_values()`

**Current Return:**
```python
{
    "settings_file": str,           # Path to settings.toml
    "entries": [
        {"path": str, "value": object},  # Flattened key-value entries
        ...
    ],
    "data": Dict,                   # Full nested structure
    "total_entries": int,           # Count of flattened entries
    "message": str,                 # Success message
}
```

**Also returns (update_settings_value):**
```python
{
    "settings_file": str,
    "path": str,                    # Dot-notation path (e.g., "settings.general.tip_reuse")
    "old_value": object,
    "new_value": object,
    "backup_file": str,             # Path to .toml.backup
}
```

**JSON Format:** Dict serialization works, but "data" field can be deeply nested
**Markdown Format:** 
  - list_settings_values: Hierarchical tree view or table of entries
  - update_settings_value: Before/after diff format, mention backup creation

**Concise:** Just "total_entries" count + top-level settings keys
**Detailed:** Full nested "data" structure + all flattened "entries" + file paths

---

### 4. Validation Tool
**File:** `src/ot2_cherrypick_mcp/tools/validation_tools.py:run_validation()`

**Current Return:** (from `core/validation.py:_result()`)
```python
{
    "status": "ok" | "error",
    "errors": List[str],            # Critical issues preventing generation
    "warnings": List[str],          # Non-fatal issues to be aware of
}
```

**JSON Format:** Simple list of strings, direct serialization works
**Markdown Format:** 
  - Status as prominent badge: "✓ OK" or "✗ ERROR"
  - Error list with bullet points (red/bold)
  - Warning list with bullet points (yellow/warning style)
  - Show count summary

**Concise:** Just status + count ("✓ OK: 0 errors, 0 warnings")
**Detailed:** Full error + warning lists with context

---

### 5. CSV Management Tool
**File:** `src/ot2_cherrypick_mcp/tools/csv_tools.py:generate_csv_template()`

**Current Return:**
```python
{
    "csv_file": str,                # Path to created CSV
    "transfers": int,               # Number of transfer rows
    "source_labware": str,
    "dest_labware": str,
}
```

Also `list_csv_files()` returns: `List[str]` (list of file paths)

**JSON Format:** Already serializable (except list_csv_files which is just a list)
**Markdown Format:** 
  - generate_csv_template: Creation confirmation with file path
  - list_csv_files: Bulleted list or table of available CSVs

**Concise:** Just csv_file path + transfer count
**Detailed:** Add source/dest labware info + CSV preview (first few rows?)

---

### 6. Labware Tool
**File:** `src/ot2_cherrypick_mcp/tools/labware_tools.py:add_labware_definition()`

**Returns (based on pattern):**
```python
{
    "labware_file": str,            # Path to labware_dict.toml
    "labware_id": str,
    "category": str,
    "well_count": int,
    "well_volume": float,
    "offsets": {
        "x": float, "y": float, "z": float
    },
    "backup_file": str,             # .toml.backup path
}
```

**JSON Format:** Nested dict, serializable
**Markdown Format:** Before/after view of added labware entry with specs
**Concise:** labware_id + (category, well_count, well_volume)
**Detailed:** Full offset values + backup file location

---

### 7. Workflow Tool
**File:** `src/ot2_cherrypick_mcp/tools/workflow_tools.py:run_full_workflow()`

**Current Return:**
```python
{
    "validation": {...},            # From validation tool
    "generation": {...},            # From protocol generation tool (or error dict)
    "simulation": {...},            # From simulation tool (or error dict or None)
    "deployment": {...},            # From deployment tool (or error dict or None)
    "status": "ok" | "error",       # Overall workflow status
}
```

**Composite structure** - combines outputs from multiple tools

**JSON Format:** Nested dicts, fully serializable
**Markdown Format:** Pipeline view showing each stage's status/results in sequence
**Concise:** Overall status + success count of stages
**Detailed:** Expandable sections for each stage's full output

---

### 8. Deployment Tool
**File:** `src/ot2_cherrypick_mcp/tools/deployment_tools.py:run_deployment()`

**Current Return:** (from `core/deployment.py:deploy_protocol()`)
```python
{
    "protocol_file": str,           # Original protocol path
    "copies": List[str],            # List of copied destination paths
    "clipboard": {
        "success": bool,            # Was clipboard operation successful?
        "message": str,             # Clipboard status message
    } | None,                       # None if not attempted
}
```

**JSON Format:** Nested dict with lists, serializable
**Markdown Format:** Deployment summary showing copy destinations + clipboard status
**Concise:** Number of copies + clipboard success (Y/N)
**Detailed:** List of full destination paths + clipboard command output

---

## Patterns Identified

### Return Type Consistency
- ALL tools return: `Dict[str, object]` or `Dict[str, Any]`
- No tools return primitives (except list_csv_files → List[str])
- No tools return tuples or custom objects

### Data Structure Patterns

| Tool Type | Has Status Field | Has Errors | Has Warnings | Has File Path | Has Nested Data |
|-----------|-----------------|-----------|-------------|---------------|-----------------|
| Protocol Gen | No | No | No | Yes (protocol_file) | No (flat) |
| Simulation | No | No (has returncode) | No | Yes (log_file) | No (multiline strings) |
| Config | No | No | No | Yes (settings_file) | Yes (nested "data") |
| Validation | Yes | Yes | Yes | No | No (lists of strings) |
| CSV | No | No | No | Yes (csv_file) | No (flat) |
| Labware | No | No | No | Yes (labware_file) | Yes (offsets dict) |
| Deployment | No | No | No | Yes (copies list) | Yes (clipboard dict) |
| Workflow | Yes | No | No | No | Yes (combines 4 sub-dicts) |

### Error Handling Patterns
- **Validation tool:** Returns status="error" + error list (non-exception)
- **Generation/Simulation/Deployment tools:** Catch exceptions and wrap in error dict or re-raise
- **Workflow tool:** Catches exceptions, wraps in {"error": str} within response dict

---

## Proposed Response Format Strategy

### Option 1: Format at Tool Level (Minimal Refactoring)
- Add optional `format: Literal["json", "markdown", "concise"]` parameter to each tool
- Keep existing return dict for "json" format
- Generate markdown/concise strings on-demand
- Return: Either dict (for json) or str (for markdown/concise)

**Pros:** Each tool controls its formatting
**Cons:** Inconsistent return types, lots of duplication, harder for clients

### Option 2: Format at Wrapper Level (Recommended)
- Create `src/ot2_cherrypick_mcp/utils/formatters.py` module
- Each tool returns unchanged dict
- Create formatter functions: `format_as_json()`, `format_as_markdown()`, `format_as_concise()`
- Register tools with MCP in ORIGINAL form (returns dicts)
- Clients can post-process if needed (Claude will handle this)

**Pros:** 
  - Zero changes to existing tools
  - Single formatting logic per response type
  - Extensible (easy to add new formats)
  - Clear separation of concerns

**Cons:** Formatting happens outside MCP (in client code or wrapper)

### Option 3: Hybrid - MCP Tools + Formatter Utilities (Best for This Project)
- Keep tools unchanged (return dicts as-is)
- Create utility formatters for use by Claude through a dedicated formatting tool
- Add MCP `format_response` tool that takes tool output + format preference
- Client passes response dict through formatter

**Structure:**
```
src/ot2_cherrypick_mcp/
├── utils/
│   ├── formatters.py           # Format conversion logic
│   │   ├── ResponseFormatter (class)
│   │   ├── JsonFormatter
│   │   ├── MarkdownFormatter
│   │   └── ConciseFormatter
│   └── ...
└── tools/
    ├── formatting_tools.py      # MCP tool exposing formatters
    │   └── format_response()    # MCP tool
    └── ...
```

---

## Detailed Formatting Specifications

### JSON Format
**Definition:** Return the dict as-is, suitable for API/programmatic use
**Tool Return:** `Dict[str, object]` (unchanged)
**Markdown Equivalent:** Code block with pretty-printed JSON

### Markdown Format
**Definition:** Human-readable text with formatting, suitable for documentation/logs

**By Tool Type:**

#### Simple Success Response (Protocol Gen, CSV)
```markdown
# Protocol Generation

✓ **Success**

- **File:** `/path/to/CherryPick_OT2.py`
- **JSON Size:** 12,345 characters
- **Status:** Protocol embedded with configuration

**Next Step:** Run simulation to validate protocol
```

#### Complex Multiline Output (Simulation)
```markdown
# Simulation Results

## Status
✓ **PASSED** (exit code: 0)

## Command
\`\`\`bash
opentrons_simulate --custom-labware /path/to/labware /path/to/protocol.py
\`\`\`

## Output
<details>
<summary>Simulation Output (click to expand)</summary>

\`\`\`
[simulation stdout here...]
\`\`\`

</details>

## Log
- **Log File:** `/path/to/last_simulation.json`
```

#### Status with Lists (Validation)
```markdown
# Configuration Validation

## Status
✓ **OK** - Ready to generate protocol

## Summary
- **Errors:** 0
- **Warnings:** 1

## Warnings
- Row 5: well 'A13' has unexpected format for column 'Source Well'

---
```

#### Hierarchical Data (Settings)
```markdown
# Settings Configuration

**File:** `/path/to/settings.toml`

## Settings Structure

- **general**
  - tip_reuse: `always`
  - mode: `single_X1`
  - head_speed: 400
- **liquid_handling**
  - post_aspirate_wick: `true`
  - push_out_volume: 5
- **working_plate** (3 entries)
  - [0] source plate in slot 4
  - [1] dest plate in slot 2
  - [2] tip rack in slot 5

**Total Entries:** 12
```

#### Diff Format (Settings Update)
```markdown
# Settings Updated

**File:** `/path/to/settings.toml`

**Path:** `settings.general.tip_reuse`

### Change
```diff
- old_value: "never"
+ new_value: "always"
```

**Backup:** `/path/to/settings.toml.backup`

---
```

#### Pipeline/Sequential (Workflow)
```markdown
# Full Workflow Execution

## Pipeline Status: ✓ COMPLETE

### 1. Validation
✓ PASSED
- Errors: 0
- Warnings: 1

### 2. Generation
✓ PASSED
- Protocol: `/path/to/CherryPick_OT2.py`
- Size: 12,345 chars

### 3. Simulation
✓ PASSED
- Exit code: 0
- Log: `/path/to/last_simulation.json`

### 4. Deployment
✓ PASSED
- Copies: 1
  - `/target/CherryPick_OT2.py`
- Clipboard: ✓ copied

---
```

### Concise Format
**Definition:** Single line or very short summary, suitable for CLI output or progress indicators

**Rules:**
- Single line preferred, maximum 2 lines
- No file paths unless critical
- Status emoji + key metric + status word
- Format: `[emoji] [metric]: [status]`

**Examples by Tool:**

| Tool | Response | Concise Format |
|------|----------|----------------|
| Protocol Gen | {...} | "✓ Protocol generated (12,345 chars)" |
| Simulation | returncode=0 | "✓ Simulation passed" |
| Simulation | returncode=1 | "✗ Simulation failed - see details for error output" |
| Validation | 0 errors, 1 warning | "✓ Valid (1 warning)" |
| Validation | 2 errors | "✗ Invalid (2 errors)" |
| CSV Gen | 100 transfers | "✓ Template created (100 transfers)" |
| Settings List | 12 entries | "✓ Settings loaded (12 entries)" |
| Settings Update | old→new | "✓ Updated (old → new)" |
| Labware Add | {...} | "✓ Labware added (96-well, 1500µL)" |
| Deployment | 1 copy, clipboard | "✓ Deployed (1 file, clipboard)" |
| Workflow | 4/4 stages | "✓ Workflow complete (validation → generation → simulation → deployment)" |

---

## Implementation Plan

### Phase 1: Create Formatter Utility Module
**File:** `src/ot2_cherrypick_mcp/utils/formatters.py`

```python
# Pseudo-structure (placeholder)
class ResponseFormatter:
    """Base formatter with common utilities."""
    
    @staticmethod
    def format_as_json(data: Dict) -> str
    @staticmethod
    def format_as_markdown(tool_type: str, data: Dict) -> str
    @staticmethod
    def format_as_concise(tool_type: str, data: Dict) -> str

# Subclasses or factory functions:
# - format_protocol_generation()
# - format_simulation()
# - format_validation()
# - format_settings()
# - format_csv()
# - format_labware()
# - format_deployment()
# - format_workflow()
```

### Phase 2: Add Formatting Tool (Optional)
**File:** Extend `src/ot2_cherrypick_mcp/tools/formatting_tools.py` (new file)

```python
def format_response_tool(response: Dict, response_type: str, format: str = "markdown") -> str:
    """MCP tool to format any tool's response."""
```

### Phase 3: Documentation
- Update CLAUDE.md with response format examples
- Add reference guide to docs/mcp_response_formats.md

---

## Test Coverage Needed

1. **JSON Format Tests:**
   - Verify all tool outputs are JSON-serializable
   - Test with json.dumps()

2. **Markdown Format Tests:**
   - Each tool type produces valid markdown
   - Headers, lists, code blocks are properly formatted
   - Status emojis render correctly

3. **Concise Format Tests:**
   - Always ≤ 2 lines
   - Contains status emoji + key metric
   - Accurate metric extraction

---

## Where to Add Formatting Logic

### Best Location: Tool-Agnostic Utility Module
- **Create:** `src/ot2_cherrypick_mcp/utils/formatters.py`
- **Use:** ImportedHere in any tool or as standalone module
- **Responsibility:** Convert dicts → formatted strings
- **Test:** Independent tests for each formatter

### Why NOT tool-level:
- Tools should focus on functionality, not presentation
- Duplication across 9 different files
- Harder to maintain consistent style
- Clients might want different formats for same output

### Why NOT core-level:
- Core modules (validation, simulation, etc.) should return data
- Core shouldn't depend on presentation logic
- These modules are imported by both CLI and MCP (different needs)

---

## Existing Formatting Utilities to Leverage

**Current Status:** NO formatting utilities currently exist

**Can leverage:**
- Python standard library: `json.dumps()`, `textwrap`, `pprint`
- For markdown: No external deps, use string concatenation
- For emojis: Python 3.12 supports native emoji in strings

---

## Summary Table: Format Implementation by Tool

| Tool | Tool Type | JSON Ready | MD Template | Concise Pattern | Priority |
|------|-----------|-----------|-----------|-----------------|----------|
| protocol_tools | Generation | Yes | Simple success | "✓ generated (N chars)" | High |
| simulation_tools | Output parsing | Yes | Details+collapsible | "✓/✗ simulation" | High |
| config_tools | Hierarchical data | Yes | Tree/table | "✓ loaded (N entries)" | Medium |
| validation_tools | Status+lists | Yes | Status badge | "✓/✗ valid (N errors)" | High |
| csv_tools | Generation | Yes | Simple list | "✓ created (N transfers)" | Low |
| labware_tools | Config update | Yes | Diff format | "✓ added (type, volume)" | Low |
| deployment_tools | Status+results | Yes | Pipeline | "✓ deployed (N files)" | Medium |
| workflow_tools | Composite | Yes | Pipeline stages | "✓ complete (4/4 stages)" | High |
