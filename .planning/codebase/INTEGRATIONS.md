# External Integrations

**Analysis Date:** 2025-01-20

## APIs & External Services

**Opentrons OT-2 Robot:**
- Purpose: Liquid handling automation (cherry-picking, distribution protocols)
- SDK: `opentrons` package (API level 2.24)
- Integration: Protocols compiled to self-contained Python files with embedded JSON config
- Simulation: `opentrons_simulate` CLI tool validates protocols without hardware
- Location: `CherryPick_OT2.py`, `src/ot2_cherrypick_mcp/core/simulation.py`

**Model Context Protocol (MCP):**
- Purpose: AI-native tool exposure for protocol generation
- SDK: `fastmcp>=2.3.0`, `mcp>=1.8.0`
- Transport: STDIO (for Claude Desktop integration)
- Server: `src/ot2_cherrypick_mcp/server.py`
- Tools exposed: 9 categories (config, csv, deployment, labware, project, protocol, simulation, validation, workflow)

**Mistral AI (Testing Only):**
- Purpose: LLM integration for MCP agent testing
- SDK: `langchain-mistralai>=0.2.12`
- Model: `mistral-medium-2508`
- Auth: `MISTRAL_API_KEY` environment variable
- Location: `tests/conftest.py`, `tests/test_mcp_integration.py`

**External MCP Servers (Development):**
- Configuration: `.mcp.json`
- Servers:
  - `git` - Git operations via `mcp-server-git`
  - `serena_jetbrains` - IDE-powered semantic code navigation
  - `mermaid-mcp` - Diagram generation (SSE at `https://mcp.mermaid.ai/sse`)
  - `playwright` - Browser automation for testing

## Data Storage

**Databases:**
- None - File-based configuration only

**File Storage:**
- TOML configuration: `settings.toml`, `labware_dict.toml`
- CSV transfer maps: `CSVs/` directory
- Generated protocols: `CherryPick_OT2.py`
- GUI workspace: `gui_state/` directory (isolated configuration copies)
- Simulation logs: `logs/last_simulation.json`
- Custom labware: Opentrons JSON definitions (external path via `LABWARE_PATH`)

**Caching:**
- None - Stateless protocol generation

## Authentication & Identity

**Auth Provider:**
- None required for core functionality
- Mistral API key for testing only (`MISTRAL_API_KEY`)

**Implementation:**
- No user authentication
- CORS wide-open for local development (`allow_origins=["*"]`)

## Monitoring & Observability

**Error Tracking:**
- Custom exception classes in `src/ot2_cherrypick_mcp/utils/errors.py`
  - `ConfigurationError`
  - `SimulationError`
  - `DeploymentError`
  - `ValidationError`

**Logs:**
- Simulation output stored in `logs/last_simulation.json`
- Structured JSON format with timestamp, command, stdout, stderr, returncode
- MCP resource: `logs://last-simulation`
- Python logging configured in `src/ot2_cherrypick_mcp/utils/logging_config.py`

## CI/CD & Deployment

**Hosting:**
- Docker Compose deployment (self-hosted)
- Local development via WSL2

**CI Pipeline:**
- Not detected (no GitHub Actions, CircleCI, etc.)
- Manual testing via `pytest` and simulation

**Docker Services:**
- Backend: FastAPI + opentrons_simulate
- Frontend: Nginx + React (Vite build)
- Network: `ot2-network` bridge

## Environment Configuration

**Required env vars:**
- `LABWARE_PATH` or `LABWARE_PATH_MOUNT` - Path to custom Opentrons labware JSON definitions (required for simulation with custom labware)

**Optional env vars:**
- `OT2_PROJECT_DIR` - Override project root detection
- `OT2_GUI_WORKSPACE` - GUI state directory (default: `gui_state`)
- `MISTRAL_API_KEY` - For MCP integration tests only

**Docker env vars (in `.env`):**
- `OT2_GUI_WORKSPACE` - Workspace path inside container
- `OT2_PROJECT_DIR` - Project directory
- `LABWARE_PATH_HOST` / `LABWARE_PATH_MOUNT` - Labware volume mount
- `PROTOCOLS_DIR_HOST` / `PROTOCOLS_DIR_MOUNT` - Protocol deployment path
- `HOST_PORT` - External port (default: 80)

**Secrets location:**
- Environment variables only
- No secrets file detected
- Docker `.env` file for local configuration

## Webhooks & Callbacks

**Incoming:**
- None

**Outgoing:**
- None

## Clipboard Integration

**Windows Clipboard (WSL):**
- Purpose: Copy generated protocol to clipboard for easy pasting
- Command: `/mnt/c/Windows/System32/clip.exe`
- Location: `src/ot2_cherrypick_mcp/core/deployment.py`
- Configurable via `clipboard_command` parameter

## Opentrons App Integration

**Protocol Deployment:**
- Target: `C:\Users\<user>\AppData\Roaming\Opentrons\protocols\<UUID>\src`
- Method: File copy to Opentrons App protocol directory
- Location: `src/ot2_cherrypick_mcp/core/deployment.py`

**Custom Labware:**
- Source: `C:\Users\<user>\AppData\Roaming\Opentrons\labware`
- Format: Opentrons JSON labware definitions
- Used by: `opentrons_simulate --custom-labware <path>`

## Path Translation (WSL)

**Windows to WSL:**
- `C:\Users\...` to `/mnt/c/Users/...`
- Handled automatically by GUI backend for simulation and deployment
- Shell script uses `wslpath` for conversion

## REST API Endpoints

**Backend API (`src/gui/backend/`):**
- `/settings` - Configuration management
- `/labware` - Labware catalog
- `/csvs` - CSV file management
- `/workflow` - Protocol generation workflow
- `/system` - System information

## MCP Resources (Read-Only Data)

**Configuration:**
- `config://settings` - Current settings.toml content
- `config://labware` - Labware catalog definitions

**Status:**
- `status://deck-layout` - Visual deck configuration
- `status://liquid-handling-config` - Active liquid handling parameters

**Files:**
- `files://csvs` - List of available CSV transfer files

**Logs:**
- `logs://last-simulation` - Most recent simulation output

---

*Integration audit: 2025-01-20*
