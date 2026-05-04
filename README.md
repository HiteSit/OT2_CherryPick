# OT2-CherryPick

[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)](https://ghcr.io/hitesit/ot2-cherrypick)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://python.org)
[![License: GPL-3.0](https://img.shields.io/badge/License-GPL--3.0-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/Version-1.6.0-blue.svg)](https://github.com/HiteSit/OT2_CherryPick)

**A zero-install, data-driven cherry-picking platform for the Opentrons OT-2** that bridges the gap between Protocol Designer's accessibility and custom Python scripting's flexibility.

Existing tools for the OT-2 present researchers with a dichotomy: graphical interfaces offer accessibility but lack flexibility for complex workflows, while code-based solutions require programming expertise that excludes many wet-lab scientists. OT2-CherryPick resolves this by combining a browser-based GUI, CSV-driven transfer specification, and comprehensive liquid handling control into a single zero-install platform. All configuration compiles into self-contained protocol files requiring no external dependencies at runtime.

![Graphical Abstract](docs/imgs/graphical_abstract.png)

## Features

- **Liquid handling presets** -- Pre-configured profiles for aqueous, viscous, and volatile liquids with full scientific parametrization
- **Multi-pipette modes** -- Single-channel, 8-channel single-tip, full 8-channel, and dual-pipette
- **Distribution mode** -- One source to multiple destinations with equal or geometric volume patterns
- **Heater-shaker module support** -- Temperature and shaking control during protocols
- **Simulation-first workflow** -- Validate every protocol with `opentrons_simulate` before touching real samples
- **Auto-UUID deployment** -- Deploy protocols to the Opentrons App with automatic UUID directory creation and analysis generation
- **Calibration offset database** -- Per-labware, per-slot offset tracking for reproducible positioning

## Quick Start with Docker (Recommended)

Copy the example env file in `docker/` and add the main path to your Opentrons directory. Then bring up the stack with `docker compose`.

Open the GUI in a browser once the stack is running.

## MCP Server Integration

The platform architecture exposes all operations through the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/), enabling AI-assisted workflow automation. The MCP server surfaces the full protocol workflow (project setup, deck configuration, liquid handling presets, CSV management, simulation, deployment) as structured tool invocations, allowing natural-language orchestration of complex pipetting experiments while preserving the TOML/CSV files as the source of truth.

<details>
<summary><strong>Configuration</strong></summary>

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
