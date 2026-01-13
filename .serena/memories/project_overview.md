# OpenTron Cherry-Pick Protocol System

## Purpose
Self-contained protocol generator for Opentrons OT-2 liquid handling robot. Core philosophy: **configuration as embedded data**.

```
TOML configuration + CSV transfer maps → compiled JSON → embedded in self-contained Python protocol
```

## Key Benefits
- Define liquid transfers in simple CSV files
- Configure deck layout in human-readable TOML files
- Generate complete protocols that run directly on OT-2 with no runtime file dependencies
- Test everything with simulation before touching real samples

## Tech Stack
- **Python 3.12** with uv package manager
- **FastMCP** for MCP server integration
- **TOML/CSV** for configuration
- **React + Vite** for GUI (optional)
- **FastAPI** for backend API

## Core Files
- `CherryPick_OT2.py` - Executable OT-2 protocol (auto-generated)
- `helper_cherry_pick.py` - Configuration compiler
- `settings.toml` - Protocol execution parameters
- `labware_dict.toml` - Hardware definitions
- `CSVs/` - Transfer definition files
- `simulate_protocol.sh` - Automation script

## MCP Server
Located in `src/ot2_cherrypick_mcp/`:
- 9 tool categories (project, protocol, config, csv, deployment, labware, simulation, validation, workflow)
- 4 resource types (config, file, log, status)
- Workflow prompts for guided AI interactions
