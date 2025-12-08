# Brief-In: OT-2 CherryPick Protocol System

Load codebase context for the specified mode: **$ARGUMENTS**

Valid modes: `SCIENCE`, `MCP`, `GUI`, `ALL`

---

## Instructions

1. Parse `$ARGUMENTS` to determine scope
2. Read files for the applicable mode(s)
3. Internalize the key concepts listed
4. Output: "Ready to help with **[MODE]**. Context loaded for: [layers]."

---

## SCIENCE Mode (always included)

**Read these files:**
- `CherryPick_OT2.py` - Main protocol logic (~1500 lines, embedded JSON config)
- `settings.toml` - Protocol settings (mode, tip reuse, liquid handling, deck layout)
- `labware_dict.toml` - Hardware definitions (pipettes, labware catalog)
- `docs/readme_opetrons_api.md` - Opentrons API v2.24 reference

**Key concepts:**
- **Three-file workflow**: TOML + CSV → compiled JSON → self-contained Python protocol
- **Pipette modes**: `single_X1` (single-channel), `multi_X1` (8-channel single-tip), `multi` (8-channel full), `dual` (both pipettes)
- **Tip management**: CSV column `Tip Action` with values `new`, `keep`, `drop`
- **Liquid handling params**: pre-aspirate contact, tip wicking, post-aspirate delays, push-out volume
- **Volume splitting**: `split_volume_into_chunks()` for multi-trip transfers exceeding pipette capacity
- **Distribution mode**: One-to-many with `|` delimiter in Dest Well, supports `equal` and `geometric:factor` patterns
- **Deck layout**: Slots 1-11 (trash at 12), configured in `[[settings.working_plate]]` arrays
- **CSV columns**: Required (Source/Dest Labware, Source/Dest Well, Volume) + Optional (Heights, Mix, Flow rates, Air Gap)

---

## MCP Mode (if $ARGUMENTS = MCP or ALL)

**Read these files:**
- `src/ot2_cherrypick_mcp/server.py` - FastMCP entry point
- `src/ot2_cherrypick_mcp/tools/__init__.py` - Tool registration
- `src/ot2_cherrypick_mcp/core/protocol_generator.py` - Generation logic
- `src/ot2_cherrypick_mcp/core/simulation.py` - Simulation runner
- `src/ot2_cherrypick_mcp/utils/toml.py` - TomlHandler class

**Key concepts:**
- **FastMCP server**: STDIO transport, entry point `ot2-mcp-server`
- **9 tool categories**: project, protocol, config, csv, labware, simulation, validation, deployment, workflow
- **4 resource categories**: config://, status://, files://, logs://
- **TomlHandler**: Format-preserving TOML editing via tomlkit, dot-notation paths
- **Workspace modes**: Temporary (auto-created) vs persistent (`OT2_PROJECT_DIR` env var)
- **Core functions**: `generate_protocol()`, `simulate_protocol()`, `deploy_protocol()`
- **Tool naming**: All tools prefixed with `ot2_` (e.g., `ot2_generate_protocol`)

---

## GUI Mode (if $ARGUMENTS = GUI or ALL)

**Read these files:**
- `src/gui/backend/main.py` - FastAPI app entry
- `src/gui/backend/state.py` - FileStateStore (critical)
- `src/gui/backend/routes/workflow.py` - Workflow execution
- `src/gui/frontend/src/App.tsx` - React entry
- `src/gui/frontend/src/components/wizard/WizardContext.tsx` - State management

**Key concepts:**
- **Stack**: FastAPI backend (port 8000) + React/Vite frontend (port 5173) + Mantine UI
- **FileStateStore**: Workspace isolation in `gui_state/` directory
- **4-step wizard**: Deck Setup → Configuration → Transfer Map → Review & Execute
- **Workspace isolation**: Edits in `gui_state/` don't affect repo root configs
- **shell_settings.json**: Windows paths for labware and deployment target
- **Path conversion**: Auto Windows→WSL via `wslpath` utility
- **API routes**: `/settings`, `/labware`, `/csvs`, `/workflow/generate`

---

## Mode Resolution

| $ARGUMENTS | Layers Loaded |
|------------|---------------|
| `SCIENCE`  | SCIENCE only |
| `MCP`      | SCIENCE + MCP |
| `GUI`      | SCIENCE + GUI |
| `ALL`      | SCIENCE + MCP + GUI |

---

## Output Format

After reading and internalizing, respond with:

> Ready to help with **[MODE]**. Context loaded for: [comma-separated layers].

Example: "Ready to help with **MCP**. Context loaded for: SCIENCE, MCP."
