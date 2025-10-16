# OT-2 Cherry-Pick MCP Server

The OpenTron cherry-picking workflow can now be orchestrated through the Model Context Protocol (MCP). This repository pairs the existing protocol generation scripts with a FastMCP server so agents (e.g., in Claude Desktop or via `mcp-use`) can configure experiments, validate inputs, generate protocols, simulate, and deploy them end-to-end.

## Capabilities at a Glance

### Tools
- `generate_protocol` – compile TOML + CSV into `CherryPick_OT2.py`
- `validate_configuration` – run pre-flight checks on TOML and CSV
- `simulate_protocol` – execute `opentrons_simulate` and capture logs
- `deploy_to_opentrons` – copy the protocol to a target path and/or clipboard
- `full_workflow` – chain validation → generation → optional simulation/deployment
- Configuration helpers: `update_settings`, `apply_liquid_preset`
- Labware utilities: `add_labware_definition`
- CSV utilities: `generate_csv_template`, `upload_csv_content`

### Resources
- `config://settings`, `config://labware` – raw TOML
- `status://deck-layout`, `status://liquid-handling-config` – summaries derived from settings
- `files://csvs` – available transfer maps
- `logs://last-simulation` – most recent simulation output

### Prompts
- `setup_new_experiment` – step-by-step guidance to plan a new run
- `troubleshoot_simulation_error` – recommendations for resolving failed simulations

## Running the Server

Always launch the server through uv to guarantee the correct environment:

```bash
uv run ot2-mcp-server
```

Ensure the `LABWARE_PATH` environment variable points to any custom labware directory required for simulation.

## Using `mcp-use`

`mcp-use` lets you connect an LLM to the server. The integration tests (`tests/test_mcp_integration.py`) show a fully working setup that runs an agent with Mistral and verifies tool usage.

### Minimal Client Example

```python
import asyncio
from langchain_mistralai import ChatMistralAI
from mcp_use import MCPAgent, MCPClient

CONFIG = {
    "mcpServers": {
        "ot2-cherrypick": {
            "command": "uv",
            "args": [
                "run",
                "ot2-mcp-server",
            ],
            "env": {
                "LABWARE_PATH": "/absolute/path/to/labware",
                "OT2_PROJECT_DIR": "/absolute/path/to/your/project",
            },
            "cwd": "/absolute/path/to/OT2_CherryPick",
        }
    }
}

async def main():
    client = MCPClient(config=CONFIG)
    llm = ChatMistralAI(model="mistral-medium-2508")
    agent = MCPAgent(llm=llm, client=client, max_steps=20)
    response = await agent.run(
        "Use full_workflow on CSVs/example_basic.csv and summarize the results."
    )
    print(response)

if __name__ == "__main__":
    asyncio.run(main())
```

### Sample Agent Prompts
- "List the available tools on the OT-2 cherry-pick server."
- "Apply the viscous preset and report the updated liquid-handling configuration."
- "Troubleshoot the latest simulation error and provide recommended fixes."
- "Run full_workflow on /path/to/example_basic.csv with deployment enabled; save the protocol to /tmp/CherryPick_OT2.py and copy it to the clipboard."
- "Given this CSV text <paste>, use upload_csv_content to save it and then run full_workflow on the saved file."

## Logs & Status Resources

- Simulation runs persist their JSON payload to `logs/last_simulation.json` and expose it via `logs://last-simulation`.
- Deck layout and liquid handling summaries (`status://deck-layout`, `status://liquid-handling-config`) provide quick context without parsing the full TOML.
- `files://csvs` lists templates and generated CSVs available for new workflows.

## Testing

Run the full suite (unit + integration) with:

```bash
uv run pytest
```

Highlights:
- Unit tests cover individual tools (protocol, configuration, labware, deployment) and resources.
- Workflow tests ensure multi-step orchestration behaves correctly.
- `tests/test_mcp_integration.py` launches the server through uv, connects via `mcp-use`, and executes agent prompts end-to-end using Mistral.

## Repository Structure

- `src/ot2_cherrypick_mcp/` – FastMCP server, tools, resources, prompts, and core helpers
- `tests/` – unit, workflow, and mcp-use integration tests
- `CSVs/`, `settings.toml`, `labware_dict.toml` – configuration inputs consumed by the server/tools
- `utils/` – supporting scripts and the mcp-use config template (`mcp_use_config.json`)

## Workflow Summary

1. Inspect current configuration via status/resources.
2. Adjust settings or apply presets through `update_settings` / `apply_liquid_preset`.
3. Generate or review CSV transfer maps (`generate_csv_template`, `files://csvs`).
4. Run `full_workflow` with desired options (simulation/deployment). The tool automatically chains validation, generation, simulation, and protocol deployment.
5. If simulation fails, consult `logs://last-simulation` and invoke `troubleshoot_simulation_error` for corrective steps.

With these pieces in place, the OT-2 cherry-pick pipeline is fully accessible through MCP clients, enabling automated experiment setup, validation, and deployment from natural-language prompts.
