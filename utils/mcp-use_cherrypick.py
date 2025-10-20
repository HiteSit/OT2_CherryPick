import asyncio
import sys
from pathlib import Path
from langchain_mistralai import ChatMistralAI
from mcp_use import MCPAgent, MCPClient

# Add tests directory to path to import helpers
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tests"))

DICT_DATABASE = {
    "General_Prompt": """Execute this complete workflow step by step, ONE AT A TIME:

        1. Initialize the project to create all necessary template files
        2. Update the tip reuse setting to 'never' in settings.toml
        3. Add a pre-aspirate handling delay of 2.5 seconds
        4. Check what CSV files are available in the CSVs directory
        5. Generate a protocol from example_basic.csv
        6. Simulate the generated protocol to validate it works correctly

        IMPORTANT: Complete each step fully before moving to the next.
        Report each step's outcome clearly."""
}

async def main():
    # Get repository root (parent of utils directory)
    project_root = Path(__file__).resolve().parents[1]

    # Create a properly initialized project directory (not just empty)
    project_dir = project_root / "utils" / "test_project"

    # Use the same setup as tests - copies template files
    if project_dir.exists():
        import shutil
        shutil.rmtree(project_dir)  # Clean up old version

    project_dir.mkdir()
    # Files no longer need to be copied manually - initialize_project will create them

    client = MCPClient(config={
        "mcpServers": {
            "ot2-cherrypick": {
                "command": "uv",
                "args": [
                    "--directory", str(project_root),
                    "run",
                    "ot2-mcp-server",
                ],
                "env": {
                    "LABWARE_PATH": "/mnt/c/Users/ricca/AppData/Roaming/Opentrons/labware",
                    "OT2_PROJECT_DIR": str(project_dir),
                },
            }
        }
    })

    # Create LLM - use same model as tests to avoid duplicate tool call ID errors
    llm = ChatMistralAI(model="mistral-medium-2508")

    # Create agent with tools - use same max_steps as tests
    agent = MCPAgent(llm=llm, client=client, max_steps=20)

    # Run comprehensive workflow: initialize → configure → generate → validate
    # NOTE: "ONE AT A TIME" forces sequential execution to avoid Mistral parallel tool call errors
    result = await agent.run(DICT_DATABASE["General_Prompt"])

    print("\n" + "="*80)
    print("RESULT:")
    print("="*80)
    print(result)
    print("\n" + "="*80)
    print(f"Project directory: {project_dir}")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(main())
