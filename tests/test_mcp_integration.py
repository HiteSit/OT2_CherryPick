"""Integration tests using mcp-use with the OT-2 MCP server."""

from __future__ import annotations

import asyncio
import shutil
from pathlib import Path
from typing import Any, Dict

import pytest

from langchain_mistralai import ChatMistralAI
from mcp_use import MCPAgent, MCPClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CSV_STRING = """Source Labware,Source Well,Volume (ul),Dest Labware,Dest Well,Source Height,Dest Top\n\
tube_rack_96_1500ul_4,A1,100,384_ppv_55ul_2,B1,2,-5\n\
tube_rack_96_1500ul_4,A2,50,384_ppv_55ul_2,B2,2,-5\n\
tube_rack_96_1500ul_4,A3,75,384_ppv_55ul_2,B3,2,-5\n\
tube_rack_96_1500ul_4,A4,25,384_ppv_55ul_2,B4,2,-5"""
SETTINGS_TEMPLATE = (PROJECT_ROOT / "settings.toml").read_text(encoding="utf-8")
SETTINGS_SCENARIOS = [
    (
        "settings.general.tip_reuse",
        "never",
        'tip_reuse = "never"',
        "Change the tip reuse strategy to never",
    ),
    (
        "settings.general.mode",
        "single_X1",
        'mode = "single_X1"',
        "Set the pipette mode to single_X1",
    ),
    (
        "settings.general.head_speed.speed",
        "250",
        "speed = 250",
        "Reduce the head movement speed to 250 mm/min",
    ),
    (
        "settings.liquid_handling.delays.post_aspirate",
        "2.5",
        "post_aspirate = 2.5",
        "Set the post-aspirate delay to 2.5 seconds",
    ),
    (
        "settings.liquid_handling.push_out.enabled",
        "false",
        "enabled = false",
        "Disable the push-out feature",
    ),
]


def _setup_project_dir(tmp_path: Path) -> Path:
    """Set up a temporary project directory with required files."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()

    # Copy template files
    shutil.copy2(PROJECT_ROOT / "settings.toml", project_dir / "settings.toml")
    shutil.copy2(PROJECT_ROOT / "labware_dict.toml", project_dir / "labware_dict.toml")

    # Copy CSVs directory
    shutil.copytree(PROJECT_ROOT / "CSVs", project_dir / "CSVs")

    # Create logs directory
    (project_dir / "logs").mkdir()

    return project_dir


def _build_config(project_dir: Path) -> Dict[str, Any]:
    """Build MCP configuration with project directory."""
    return {
        "mcpServers": {
            "ot2-cherrypick": {
                "command": "pixi",
                "args": [
                    "run",
                    "--manifest-path",
                    str(PROJECT_ROOT / "pyproject.toml"),
                    "python",
                    "-m",
                    "ot2_cherrypick_mcp.server",
                ],
                "env": {
                    "LABWARE_PATH": str(PROJECT_ROOT),
                    "OT2_PROJECT_DIR": str(project_dir),
                },
            }
        }
    }


async def _run_agent(query: str, project_dir: Path) -> str:
    """Run agent with project directory configuration."""
    client = MCPClient(config=_build_config(project_dir))
    llm = ChatMistralAI(model="mistral-medium-2508")
    agent = MCPAgent(llm=llm, client=client, max_steps=20)
    return await agent.run(query)


def test_agent_lists_tools(tmp_path: Path) -> None:
    """Test that agent can list available tools."""
    project_dir = _setup_project_dir(tmp_path)
    result = asyncio.run(
        _run_agent("What tools are available for the OT-2 cherry-pick protocol?", project_dir)
    )
    assert isinstance(result, str)
    assert result


def test_agent_runs_workflow_from_string(tmp_path: Path) -> None:
    """Test that agent can upload CSV and run workflow."""
    project_dir = _setup_project_dir(tmp_path)

    # Use project CSVs directory for the uploaded file
    csv_dir = project_dir / "CSVs"
    tmp_target = csv_dir / "tmp_uploaded.csv"
    tmp_target.unlink(missing_ok=True)

    query = (
        f"I have some transfer data in CSV format that I'd like you to save to 'CSVs/tmp_uploaded.csv'. "
        f"After saving it, please generate and validate the protocol (but skip the simulation step). "
        f"Here's the CSV data:\n\n{CSV_STRING}\n\n"
        f"Let me know if everything worked correctly."
    )

    result = asyncio.run(_run_agent(query, project_dir))
    assert isinstance(result, str)
    assert tmp_target.exists()
    lower = result.lower()
    if "invalid_request_message_order" not in lower:
        assert "error" not in lower


@pytest.mark.parametrize("path,value,expected,prompt", SETTINGS_SCENARIOS)
def test_agent_updates_settings(
    tmp_path: Path, capsys, path: str, value: str, expected: str, prompt: str
) -> None:
    """Test that agent can update settings via natural language."""
    project_dir = _setup_project_dir(tmp_path)
    settings_file = project_dir / "settings.toml"

    query = f"{prompt} in the settings file"

    client = MCPClient(config=_build_config(project_dir))
    llm = ChatMistralAI(model="mistral-medium-2508")
    agent = MCPAgent(llm=llm, client=client, max_steps=8)
    _ = asyncio.run(agent.run(query))

    print(f"Project settings: {settings_file}")
    captured = capsys.readouterr()

    updated = settings_file.read_text(encoding="utf-8")
    assert expected in updated
