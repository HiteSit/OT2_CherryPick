# Project Overview

Purpose:
- OT-2 Cherry-Pick protocol generator with MCP server integration for configuring, validating, simulating, and deploying OT-2 liquid handling protocols.
- Configuration-as-data workflow: TOML + CSV -> JSON embedded in `CherryPick_OT2.py` (self-contained protocol).

Primary Capabilities:
- MCP tools to update settings, manage labware/CSV, generate protocol, simulate, deploy.
- GUI + FastAPI for interactive workflow (optional).

Tech Stack:
- Python 3.12 (uv-managed environment)
- FastMCP / MCP server (`src/ot2_cherrypick_mcp`)
- FastAPI + Uvicorn (GUI backend)
- React/Vite frontend (via `npm run dev:full` in scripts)
- Testing: pytest (unit + integration)
- Data: pandas, numpy, toml/tomlkit
