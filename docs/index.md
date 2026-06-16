# OT2-CherryPick

OT2-CherryPick is a data-driven protocol generator for Opentrons OT-2 cherry-picking workflows. It turns a human-readable project definition into a self-contained Python protocol:

```text
settings.toml + labware_dict.toml + CSVs/*.csv
              |
              v
      helper_cherry_pick.py
              |
              v
    CherryPick_OT2.py
```

The generated protocol embeds its configuration as JSON, so the OT-2 runtime does not need the original TOML or CSV files.

![Graphical Abstract](imgs/graphical_abstract.png)

## Manual structure

This documentation is organized as a practical software manual:

- [Installation](installation.md) covers Docker Compose startup, environment variables, logs, shutdown, and where the Opentrons App path fits.
- [GUI Guide](gui_guide.md) walks through the 4-step browser wizard and includes screenshot captions for each screen.
- [Configuration Reference](configuration_reference.md) documents the TOML files, CSV transfer maps, labware references, offsets, modules, and distribution rows.
- [Liquid Handling Guide](liquid_handling_guide.md) explains presets and tunable pipetting behavior.
- [MCP Tools Reference](mcp_tools_reference.md) lists the MCP tools, resources, and prompts exposed by the automation server.

## Build outputs

The same Markdown source can be published as a browsable MkDocs site or exported as a PDF manual.

```bash
uv run mkdocs build
ENABLE_PDF_EXPORT=1 uv run mkdocs build
```

The PDF is written to:

```text
site/pdf/OT2-CherryPick-Manual.pdf
```
