# Suggested Commands

Environment:
- `uv run <command>` for all Python commands (uv manages local .venv)

MCP Server:
- `uv run ot2-mcp-server`

Simulation / Protocol generation:
- `uv run python helper_cherry_pick.py -l labware_dict.toml -s settings.toml -c CSVs/example_basic.csv -p CherryPick_OT2.py`
- `./simulate_protocol.sh CSVs/example_basic.csv`
- `./simulate_protocol.sh CSVs/example_basic.csv --send-to-opentrons`

Testing:
- `uv run pytest` (full suite)
- `uv run pytest tests/test_mcp_integration.py` (MCP integration)

GUI Dev:
- `./scripts/run_gui_dev.sh` (FastAPI 8000 + React 5173)

Utilities:
- `git status`, `git diff`, `git log` for VCS
