# Suggested Commands

## Package Management (uv)
All Python commands must use `uv run`:

```bash
# Run helper script
uv run python helper_cherry_pick.py -l labware_dict.toml -s settings.toml -c CSVs/example_basic.csv -p CherryPick_OT2.py

# Run simulation
uv run opentrons_simulate --custom-labware $LABWARE_PATH CherryPick_OT2.py

# Run tests
uv run pytest tests/

# Add a package
uv add package-name
```

## Protocol Workflow

```bash
# Simulate protocol (quick validation)
./simulate_protocol.sh CSVs/your_file.csv

# Simulate and deploy to Opentrons App
./simulate_protocol.sh CSVs/your_file.csv --send-to-opentrons
```

## MCP Server

```bash
# Start MCP server (STDIO transport)
uv run ot2-mcp-server

# Run MCP integration tests
uv run pytest tests/test_mcp_integration.py
```

## Testing

```bash
# Run all tests
uv run pytest tests/

# Run specific test file
uv run pytest tests/test_mcp_integration.py

# Run with verbose output
uv run pytest tests/ -v
```

## Git (Windows/WSL)
Standard git commands work in WSL:
```bash
git status
git add .
git commit -m "message"
git push
```

## Windows Path Conversion
Paths are auto-converted from Windows to WSL format:
- `C:\Users\...` → `/mnt/c/Users/...`
