import asyncio
import sys
from pathlib import Path
from langchain_mistralai import ChatMistralAI
from mcp_use import MCPAgent, MCPClient

# Add tests directory to path to import helpers
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tests"))
from helpers import ProjectSetup

async def main():
    # Get repository root (parent of utils directory)
    project_root = Path(__file__).resolve().parents[1]

    # Create a properly initialized project directory (not just empty)
    project_setup = ProjectSetup(project_root=project_root)
    project_dir = project_root / "utils" / "test_project"

    # Use the same setup as tests - copies template files
    if project_dir.exists():
        import shutil
        shutil.rmtree(project_dir)  # Clean up old version

    project_dir.mkdir()
    import shutil
    # shutil.copy2(project_root / "settings.toml", project_dir / "settings.toml")
    # shutil.copy2(project_root / "labware_dict.toml", project_dir / "labware_dict.toml")
    # shutil.copy2(project_root / "CherryPick_OT2.py", project_dir / "CherryPick_OT2.py")
    # shutil.copytree(project_root / "CSVs", project_dir / "CSVs")
    # (project_dir / "logs").mkdir()

    client = MCPClient(config={
        "mcpServers": {
            "ot2-cherrypick": {
                "command": "pixi",
                "args": [
                    "run",
                    "--manifest-path",
                    str(project_root / "pyproject.toml"),
                    "python",
                    "-m",
                    "ot2_cherrypick_mcp.server",
                ],
                "env": {
                    "LABWARE_PATH": str(project_root),
                    "OT2_PROJECT_DIR": str(project_dir),
                }
            }
        }
    })

    # Create LLM - use same model as tests to avoid duplicate tool call ID errors
    llm = ChatMistralAI(model="mistral-medium-2508")

    # Create agent with tools - use same max_steps as tests
    agent = MCPAgent(llm=llm, client=client, max_steps=20)

    # Run the query - project is already initialized with template files
    # Be specific about which CSV file to use
    result = await agent.run(
        "List all tools"
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
