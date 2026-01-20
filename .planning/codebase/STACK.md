# Technology Stack

**Analysis Date:** 2025-01-20

## Languages

**Primary:**
- Python 3.12 - Backend, MCP server, protocol generation, CLI tools
- TypeScript 5.9 - Frontend React application

**Secondary:**
- Bash - Shell automation scripts (`simulate_protocol.sh`)
- TOML - Configuration files (`settings.toml`, `labware_dict.toml`)
- JSON - Labware definitions, MCP configuration

## Runtime

**Environment:**
- Python 3.12 (strict: `>=3.12,<3.13`)
- Node.js (via npm for frontend)

**Package Manager:**
- uv (Astral) - Python dependency management
- npm - Frontend package management
- Lockfile: `uv.lock` (present), `package-lock.json` (present)

## Frameworks

**Core:**
- FastMCP 2.3+ - Model Context Protocol server framework (`src/ot2_cherrypick_mcp/server.py`)
- FastAPI 0.121+ - REST API backend for GUI (`src/gui/backend/main.py`)
- React 19.2 - Frontend UI framework (`src/gui/frontend/`)
- Opentrons API 2.24 - OT-2 robot protocol interface (`CherryPick_OT2.py`)

**Testing:**
- pytest 8.4+ - Test runner and fixtures
- mcp-use 1.3+ - MCP agent testing framework
- langchain-mistralai 0.2+ - LLM integration for MCP tests

**Build/Dev:**
- Vite 7.2 - Frontend build tool and dev server
- Hatchling - Python package build backend
- uvicorn 0.38+ - ASGI server for FastAPI
- concurrently - Parallel script runner for frontend dev

## Key Dependencies

**Critical:**
- `opentrons` - OT-2 robot SDK (installed via pipx for simulation)
- `fastmcp>=2.3.0` - MCP server implementation
- `mcp>=1.8.0` - Model Context Protocol base library
- `tomlkit>=0.13.3` - Format-preserving TOML editing
- `pandas>=2.3.3` - Data manipulation for CSV processing

**Infrastructure:**
- `uvicorn>=0.38.0` - ASGI server
- `fastapi>=0.121.1` - REST API framework
- `axios` - HTTP client (frontend)
- `@tanstack/react-query` - Data fetching (frontend)

**Scientific Computing:**
- `numpy>=1.20.0` - Numerical operations
- `rdkit>=2025.9.1` - Cheminformatics library
- `datamol>=0.12.5` - Molecular data processing
- `seaborn>=0.13.2` - Statistical visualization
- `mols2grid>=2.0.0` - Molecular grid visualization

**Frontend UI:**
- `@mantine/core>=8.3.7` - Component library
- `@mantine/hooks>=8.3.7` - React hooks
- `@mantine/notifications>=8.3.7` - Toast notifications
- `@tabler/icons-react>=3.35.0` - Icon library
- `@dnd-kit/core`, `@dnd-kit/sortable` - Drag-and-drop
- `react-spreadsheet` - CSV editing
- `papaparse` - CSV parsing

## Configuration

**Environment:**
- `OT2_PROJECT_DIR` - Project root directory (optional, auto-detected)
- `OT2_GUI_WORKSPACE` - GUI state workspace (default: `gui_state`)
- `LABWARE_PATH` - Path to custom Opentrons labware JSON definitions
- Configuration via TOML files:
  - `settings.toml` - Protocol execution parameters
  - `labware_dict.toml` - Hardware definitions catalog

**Build:**
- `pyproject.toml` - Python package manifest (hatchling build)
- `vite.config.ts` - Vite configuration for frontend
- `tsconfig.json` - TypeScript configuration
- `.mcp.json` - MCP server configuration for development

## Platform Requirements

**Development:**
- WSL2 (Windows Subsystem for Linux) - Primary development environment
- Windows with WSL path translation (e.g., `C:\` to `/mnt/c/`)
- clip.exe available at `/mnt/c/Windows/System32/clip.exe` for clipboard

**Production:**
- Docker with docker-compose 3.9
- Python 3.12-slim-bookworm base image
- Nginx reverse proxy for frontend
- Port 80 (frontend), Port 8000 (backend internal)

## Console Entry Points

**Defined in `pyproject.toml`:**
- `ot2-mcp-server` - Start MCP server via STDIO transport

**Shell Scripts:**
- `simulate_protocol.sh` - CLI wrapper for protocol generation and simulation

## Docker Configuration

**Backend (`docker/Dockerfile.backend`):**
- Base: `python:3.12-slim-bookworm`
- uv installed from `ghcr.io/astral-sh/uv:latest`
- opentrons_simulate via pipx
- uvicorn ASGI server

**Frontend (`docker/Dockerfile.frontend`):**
- Nginx serving built React app
- Reverse proxy to backend `/api`

**Volumes:**
- `gui_state` - Persistent workspace configuration
- `logs` - Application logs
- Host mounts for labware and protocol directories

---

*Stack analysis: 2025-01-20*
