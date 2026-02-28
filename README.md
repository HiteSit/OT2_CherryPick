# OT2-CherryPick

[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)](https://ghcr.io/hitesit/ot2-cherrypick)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/Version-1.0.0-blue.svg)](https://github.com/HiteSit/OT2_CherryPick)

**A zero-install, data-driven cherry-picking platform for the Opentrons OT-2** that bridges the gap between Protocol Designer's accessibility and custom Python scripting's flexibility.

Existing tools for the OT-2 present researchers with a dichotomy: graphical interfaces offer accessibility but lack flexibility for complex workflows, while code-based solutions require programming expertise that excludes many wet-lab scientists. OT2-CherryPick resolves this by combining a browser-based GUI, CSV-driven transfer specification, and comprehensive liquid handling control into a single zero-install platform. All configuration compiles into self-contained protocol files requiring no external dependencies at runtime.

The platform architecture also exposes all operations through the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/), enabling AI-assisted workflow automation -- to our knowledge, the first application of MCP in laboratory robotics.

![Graphical Abstract](docs/graphical_abstract.png)

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
- **Calibration offset database** -- Per-labware, per-slot offset tracking for reproducible positioning

## Quick Start with Docker (Recommended)

```bash
cd docker
cp .env.example .env
```

Edit `.env` with your Opentrons paths:

```env
LABWARE_PATH_HOST=/mnt/c/Users/YOUR_USERNAME/AppData/Roaming/Opentrons/labware
LABWARE_PATH_MOUNT=/mnt/c/Users/YOUR_USERNAME/AppData/Roaming/Opentrons/labware
PROTOCOLS_DIR_HOST=/mnt/c/Users/YOUR_USERNAME/AppData/Roaming/Opentrons/protocols
PROTOCOLS_DIR_MOUNT=/mnt/c/Users/YOUR_USERNAME/AppData/Roaming/Opentrons/protocols
```

Start the application:

```bash
docker compose up -d
```

Open [http://localhost](http://localhost) to access the GUI.

## Alternative: Local Development Setup

Requires [uv](https://docs.astral.sh/uv/) and Python 3.12+.

```bash
git clone https://github.com/HiteSit/OT2_CherryPick.git
cd OT2_CherryPick
uv sync
```

Run the GUI backend and frontend separately, or use the CLI workflow:

```bash
# CLI: compile and simulate a protocol
./simulate_protocol.sh CSVs/example_basic.csv

# CLI: simulate and deploy to Opentrons App
./simulate_protocol.sh CSVs/example_basic.csv --send-to-opentrons
```

## MCP Server Configuration

The MCP server exposes the full protocol workflow through AI-native tools.

<details>
<summary><strong>Claude Code (.mcp.json)</strong></summary>

```json
{
  "mcpServers": {
    "ot2-cherrypick": {
      "type": "stdio",
      "command": "uv",
      "args": ["--directory", "/path/to/OT2_CherryPick", "run", "--no-sync", "ot2-mcp-server"],
      "env": {
        "LABWARE_PATH": "/mnt/c/Users/YOUR_USERNAME/AppData/Roaming/Opentrons/labware"
      }
    }
  }
}
```

</details>

<details>
<summary><strong>Claude Desktop (claude_desktop_config.json)</strong></summary>

```json
{
  "mcpServers": {
    "ot2-cherrypick": {
      "command": "uv",
      "args": ["--directory", "/path/to/OT2_CherryPick", "run", "ot2-mcp-server"],
      "env": {
        "LABWARE_PATH": "/path/to/opentrons/labware",
        "OT2_PROJECT_DIR": "/path/to/your/project"
      }
    }
  }
}
```

</details>

**Environment variables:**
- `LABWARE_PATH` (required) -- Path to custom labware JSON files for simulation
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
| Both height columns set | Use EITHER `Height` OR `Top` per source/dest, not both |

## Citation

If you use OT2-CherryPick in your research, please cite:

> OT2-CherryPick: a web-based platform for data-driven liquid handling automation with AI-native Model Context Protocol integration. *Manuscript in preparation.*

<!-- TODO: Update with DOI once published on ChemRxiv / Digital Discovery -->

## Contributing

Contributions are welcome. Please open an issue or pull request on [GitHub](https://github.com/HiteSit/OT2_CherryPick).

## License

[MIT](LICENSE)
