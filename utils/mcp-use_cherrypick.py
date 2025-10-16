import asyncio
import sys
from pathlib import Path
from langchain_mistralai import ChatMistralAI
from mcp_use import MCPAgent, MCPClient

# Add tests directory to path to import helpers
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tests"))

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
                    "LABWARE_PATH": str(project_root),
                    "OT2_PROJECT_DIR": str(project_dir),
                },
            }
        }
    })

    # Create LLM - use same model as tests to avoid duplicate tool call ID errors
    llm = ChatMistralAI(model="mistral-medium-2508")

    # Create agent with tools - use same max_steps as tests
    agent = MCPAgent(llm=llm, client=client, max_steps=20)

    # Run the query - first initialize the project, then configure settings, then generate protocol
    result = await agent.run(
        "List all Tools"
    )

    print("\n" + "="*80)
    print("RESULT:")
    print("="*80)
    print(result)
    print("\n" + "="*80)
    print(f"Project directory: {project_dir}")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(main())
