# Codebase Structure

Top-level:
- `src/ot2_cherrypick_mcp/`: MCP server, tools, resources, prompts, core helpers
- `tests/`: unit + integration tests (incl. MCP integration)
- `CSVs/`, `settings.toml`, `labware_dict.toml`: protocol inputs
- `CherryPick_OT2.py`: generated OT-2 protocol (do not hand-edit)
- `helper_cherry_pick.py`: config compiler and protocol generator
- `simulate_protocol.sh`: CLI workflow for simulation + deployment
- `gui_state/`: GUI workspace configs
- `scripts/run_gui_dev.sh`: run GUI dev servers (FastAPI + React)
- `docs/`: MCP tools guide and documentation
