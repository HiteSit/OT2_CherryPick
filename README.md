# OT2-CherryPick

[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)](https://ghcr.io/hitesit/ot2-cherrypick)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://python.org)
[![License: GPL-3.0](https://img.shields.io/badge/License-GPL--3.0-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/Version-1.5.0-blue.svg)](https://github.com/HiteSit/OT2_CherryPick)

**A zero-install, data-driven cherry-picking platform for the Opentrons OT-2** that bridges the gap between Protocol Designer's accessibility and custom Python scripting's flexibility.

Existing tools for the OT-2 present researchers with a dichotomy: graphical interfaces offer accessibility but lack flexibility for complex workflows, while code-based solutions require programming expertise that excludes many wet-lab scientists. OT2-CherryPick resolves this by combining a browser-based GUI, CSV-driven transfer specification, and comprehensive liquid handling control into a single zero-install platform. All configuration compiles into self-contained protocol files requiring no external dependencies at runtime.

The platform architecture also exposes all operations through the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/), enabling AI-assisted workflow automation -- to our knowledge, the first application of MCP in laboratory robotics.

![Graphical Abstract](docs/imgs/graphical_abstract.png)

## Features

- **Zero-install deployment** -- `docker compose up` provides complete functionality in any browser
- **Configuration as embedded data** -- TOML + CSV compile into a single self-contained Python protocol
- **4-step web GUI** -- Visual deck editor, liquid handling configuration, spreadsheet-style transfer map, and one-click execution
- **AI-native MCP server** -- Protocol generation via Claude Code or Claude Desktop through structured tool invocations
- **Liquid handling presets** -- Pre-configured profiles for aqueous, viscous, and volatile liquids with full scientific parametrization
- **Multi-pipette modes** -- Single-channel, 8-channel single-tip, full 8-channel, and dual-pipette
- **Distribution mode** -- One source to multiple destinations with equal or geometric volume patterns
- **Heater-shaker module support** -- Temperature and shaking control during protocols
- **Simulation-first workflow** -- Validate every protocol with `opentrons_simulate` before touching real samples
- **Auto-UUID deployment** -- Deploy protocols to the Opentrons App with automatic UUID directory creation and analysis generation; no manual protocol directory management required
- **Calibration offset database** -- Per-labware, per-slot offset tracking for reproducible positioning

## Quick Start with Docker (Recommended)

```bash
cd docker
cp .env.example .env
```

Edit `.env` with your Opentrons paths:

```env
OPENTRONS_DIR_HOST=/mnt/c/Users/YOUR_USERNAME/AppData/Roaming/Opentrons
OPENTRONS_DIR_MOUNT=/mnt/c/Users/YOUR_USERNAME/AppData/Roaming/Opentrons
```

> **Why `_HOST` and `_MOUNT`?** The pair maps a single Docker volume for the entire Opentrons App data directory: `HOST` is the path on your machine, `MOUNT` is the path inside the container. Labware and protocol subdirectories are auto-derived from this root. On WSL they are typically identical, but separating them allows different host OS configurations (e.g., native Linux) while the container always sees the expected path.

Start the application:

```bash
docker compose up -d
```

Open [http://localhost](http://localhost) to access the GUI. No port number is needed because the frontend defaults to port 80, the standard HTTP port. To use a different port, set `HOST_PORT` in `.env` (e.g., `HOST_PORT=8080`) and access `http://localhost:8080`.

## Alternative: Local Development Setup

Requires [uv](https://docs.astral.sh/uv/) and Python 3.12+.

```bash
git clone https://github.com/HiteSit/OT2_CherryPick.git
cd OT2_CherryPick
uv sync
```

Run the GUI backend and frontend separately, or use the MCP server for AI-assisted workflows.

## MCP Server Configuration

The MCP server exposes the full protocol workflow through AI-native tools.

<details>
<summary><strong>Claude Code</strong></summary>

```bash
claude mcp add ot2-cherrypick \
  --scope user \
  --transport stdio \
  -e OPENTRONS_DIR=/mnt/c/Users/YOUR_USERNAME/AppData/Roaming/Opentrons \
  -- uv --directory /path/to/OT2_CherryPick run ot2-mcp-server
```

`--scope user` registers the server globally (available in every project directory).
Use `--scope project` instead to write to `.mcp.json` (shared via version control).

</details>

<details>
<summary><strong>Claude Desktop</strong></summary>

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "ot2-cherrypick": {
      "command": "uv",
      "args": ["--directory", "/path/to/OT2_CherryPick", "run", "ot2-mcp-server"],
      "env": {
        "OPENTRONS_DIR": "/mnt/c/Users/YOUR_USERNAME/AppData/Roaming/Opentrons"
      }
    }
  }
}
```

</details>

**Environment variables:**
- `OPENTRONS_DIR` (required) -- Root Opentrons App data directory; labware and protocol subdirectories are auto-derived
- `OT2_PROJECT_DIR` (optional) -- Persistent workspace directory

## How It Works

The system follows a three-file workflow:

```
settings.toml + labware_dict.toml + CSVs/*.csv
              |
              v
      helper_cherry_pick.py
              |
              v
    CherryPick_OT2.py (self-contained protocol with embedded JSON)
```

1. **Define transfers** in a CSV file (source wells, dest wells, volumes, heights)
2. **Configure deck layout and liquid handling** in `settings.toml`
3. **Compile and simulate** -- the helper compiles everything into a single Python protocol

The generated protocol embeds all configuration as JSON, requiring no external files at runtime on the OT-2.

## Documentation

| Guide | Description |
|-------|-------------|
| [GUI Guide](docs/gui_guide.md) | 4-step wizard walkthrough for the web interface |
| [Configuration Reference](docs/configuration_reference.md) | Complete settings.toml, labware, CSV format reference |
| [Liquid Handling Guide](docs/liquid_handling_guide.md) | Presets, parameters, and scientific rationale |
| [MCP Tools Reference](docs/mcp_tools_reference.md) | Full MCP tool, resource, and prompt catalog |

## Troubleshooting

| Error | Fix |
|-------|-----|
| Labware not found | Verify `labware_id` matches Opentrons load name |
| Slot conflict | Ensure unique `position_rack` values in settings.toml |
| No tips available | Add tip racks or check `connection` field |
| Multi mode incompatible | Multi mode requires 96 or 384-well plates |
| Volume warnings | Check pipette `volume_range` in labware_dict.toml |
| Both height columns set | Use EITHER `Bottom` OR `Top` per source/dest, not both |

## Citation

If you use OT2-CherryPick in your research, please cite:

```bibtex
@article{OT2CherryPick2021,
  title   = {OT2-CherryPick: A Zero-Install Web Platform for Orchestrating
             Complex Liquid Handling on the Opentrons OT-2},
  year    = {2021},
  journal = {ChemRxiv},
  doi     = {10.26434/chemrxiv.15000637},
  url     = {https://chemrxiv.org/doi/full/10.26434/chemrxiv.15000637/v1}
}
```


## Contributing

Contributions are welcome. Please open an issue or pull request on [GitHub](https://github.com/HiteSit/OT2_CherryPick).

## License

[GPL-3.0-or-later](LICENSE)
