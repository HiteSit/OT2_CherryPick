# Completion Steps

After implementing changes:
- Run `./simulate_protocol.sh <csv>` for protocol-related changes
- Run `uv run pytest` for test updates or MCP/tool changes
- For GUI changes, validate via `./scripts/run_gui_dev.sh`

Notes:
- Ensure `LABWARE_PATH` is set when simulating or running MCP workflows
- Do not hand-edit `CherryPick_OT2.py` embedded JSON; regenerate via helper
