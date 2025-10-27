import asyncio
import sys
import os
import stat
from pathlib import Path
from langchain_mistralai import ChatMistralAI
from mcp_use import MCPAgent, MCPClient

# Add tests directory to path to import helpers
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tests"))

# Add env variables
os.environ["MISTRAL_API_KEY"] = "Yzo2ydbnnu2IqsqsLVecRvRyRGOpr2z6"

PROMPTS = [
    {
        "name": "General_Prompt",
        "prompt": """Execute this complete workflow step by step, ONE AT A TIME:

            1. Initialize the project to create all necessary template files
            2. Update the tip reuse setting to 'never' in settings.toml
            3. Add a pre-aspirate handling delay of 2.5 seconds
            4. Generate a protocol from CSVs/example_basic.csv
            5. Simulate the generated protocol to validate it works correctly

            IMPORTANT: Complete each step fully before moving to the next.
            Report each step's outcome clearly.""",
        "requires_workspace": True,
    },
    {
        "name": "General_Prompt_TempFolder",
        "prompt": """Execute this complete workflow step by step, ONE AT A TIME:

        1. Initialize the project to create all necessary template files. Notice that you need to work on a tmp file.
        2. Update the tip reuse setting to 'never' in settings.toml
        3. Add a pre-aspirate handling delay of 2.5 seconds
        4. Generate a protocol from CSVs/example_basic.csv
        5. Simulate the generated protocol to validate it works correctly
        6. Package everything into zip

        IMPORTANT: Complete each step fully before moving to the next.
        Report each step's outcome clearly.""",
        "requires_workspace": False,
    },
]

def remove_readonly(func, path, excinfo):
    """
    Error handler for shutil.rmtree to handle Windows readonly files.
    Works on both Windows and Linux - on Linux it has no effect.
    """
    os.chmod(path, stat.S_IWRITE)
    func(path)

async def main():
    # Get repository root (parent of utils directory)
    project_root = Path(__file__).resolve().parents[1]

    labware_path = "/mnt/c/Users/ricca/AppData/Roaming/Opentrons/labware"

    # Ensure process-level OT2_PROJECT_DIR does not leak into prompts that expect fallback
    os.environ.pop("OT2_PROJECT_DIR", None)

    # Create LLM once - reuse for both prompts
    llm = ChatMistralAI(model="mistral-medium-2508")

    for spec in PROMPTS:
        name = spec["name"]
        prompt = spec["prompt"]
        requires_workspace = spec["requires_workspace"]

        project_dir = project_root / "utils" / f"{name.lower()}_workspace"
        if requires_workspace:
            if project_dir.exists():
                import shutil
                shutil.rmtree(project_dir, onexc=remove_readonly)
            project_dir.mkdir(parents=True, exist_ok=True)
        else:
            if project_dir.exists():
                import shutil
                shutil.rmtree(project_dir, onexc=remove_readonly)

        env = {"LABWARE_PATH": labware_path}
        if requires_workspace:
            env["OT2_PROJECT_DIR"] = str(project_dir)

        client = MCPClient(
            config={
                "mcpServers": {
                    "ot2-cherrypick": {
                        "command": "uv",
                        "args": [
                            "--directory",
                            str(project_root),
                            "run",
                            "ot2-mcp-server",
                        ],
                        "env": env,
                    }
                }
            }
        )

        agent = MCPAgent(llm=llm, client=client, max_steps=20)

        print("\n" + "=" * 80)
        print(f"RUNNING: {name}")
        print("=" * 80)

        try:
            result = await agent.run(prompt)
        finally:
            await client.close_all_sessions()

        print("\n" + "-" * 80)
        print("RESULT:")
        print("-" * 80)
        print(result)
        print("\n" + "-" * 80)

        if requires_workspace:
            print(f"Workspace on disk: {project_dir}")
        else:
            print("Workspace managed by server (auto-created)")

if __name__ == "__main__":
    asyncio.run(main())
