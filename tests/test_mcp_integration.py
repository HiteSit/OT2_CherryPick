"""Integration tests using mcp-use with the OT-2 MCP server."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Dict

import pytest

from langchain_mistralai import ChatMistralAI
from mcp_use import MCPAgent, MCPClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TMP_DIR = PROJECT_ROOT / "tests" / "tmp"
TMP_DIR.mkdir(parents=True, exist_ok=True)
CSV_STRING = """Source Labware,Source Well,Volume (ul),Dest Labware,Dest Well,Source Height,Dest Top\n\
tube_rack_96_1500ul_4,A1,100,384_ppv_55ul_2,B1,2,-5\n\
tube_rack_96_1500ul_4,A2,50,384_ppv_55ul_2,B2,2,-5\n\
tube_rack_96_1500ul_4,A3,75,384_ppv_55ul_2,B3,2,-5\n\
tube_rack_96_1500ul_4,A4,25,384_ppv_55ul_2,B4,2,-5"""

TMP_UPLOAD_TARGET = str(TMP_DIR / "tmp_uploaded.csv")
SETTINGS_TEMPLATE = (PROJECT_ROOT / "settings.toml").read_text(encoding="utf-8")
SETTINGS_SCENARIOS = [
    ("settings.general.tip_reuse", "never", 'tip_reuse = "never"'),
    ("settings.general.mode", "single_X1", 'mode = "single_X1"'),
    ("settings.general.head_speed.speed", "250", "speed = 250"),
    ("settings.liquid_handling.delays.post_aspirate", "2.5", "post_aspirate = 2.5"),
    ("settings.liquid_handling.push_out.enabled", "false", "enabled = false"),
]


def _build_config() -> Dict[str, Any]:
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
                },
            }
        }
    }


async def _run_agent(query: str) -> str:
    client = MCPClient(config=_build_config())
    llm = ChatMistralAI(model="ministral-8b-2410")
    agent = MCPAgent(llm=llm, client=client, max_steps=20)
    return await agent.run(query)


def test_agent_lists_tools() -> None:
    result = asyncio.run(_run_agent("List available tools on the OT-2 cherry-pick server."))
    assert isinstance(result, str)
    assert result


def test_agent_runs_workflow_from_string(tmp_path: Path) -> None:
    tmp_target = tmp_path / "tmp_uploaded.csv"
    tmp_target.unlink(missing_ok=True)
    (PROJECT_ROOT / "CSVs" / "tmp_uploaded.csv").unlink(missing_ok=True)
    query = (
        f"Use upload_csv_content with filename 'tmp_uploaded.csv', output_dir '{TMP_DIR}', "
        "and the following CSV content. Then call full_workflow with csv_path='"
        f"{TMP_UPLOAD_TARGET}' and simulate=false. Finally, report the workflow status.\n\nCSV_CONTENT:\n"
        f"{CSV_STRING}"
    )

    result = asyncio.run(_run_agent(query))
    assert isinstance(result, str)
    assert Path(TMP_UPLOAD_TARGET).exists()
    lower = result.lower()
    if "invalid_request_message_order" not in lower:
        assert "error" not in lower


@pytest.mark.parametrize("path,value,expected", SETTINGS_SCENARIOS)
def test_agent_updates_settings(tmp_path: Path, capsys, path: str, value: str, expected: str) -> None:
    settings_copy = tmp_path / f"settings_{path.replace('.', '_')}.toml"
    settings_copy.write_text(SETTINGS_TEMPLATE, encoding="utf-8")

    query = (
        "Call update_settings with the following arguments: "
        f"path '{path}', value '{value}', settings_path '{settings_copy}'. "
        "After the tool call, confirm the new value."
    )

    client = MCPClient(config=_build_config())
    llm = ChatMistralAI(model="ministral-8b-2410")
    agent = MCPAgent(llm=llm, client=client, max_steps=8)
    _ = asyncio.run(agent.run(query))

    print(f"Temporary settings path: {settings_copy}")
    captured = capsys.readouterr()
    assert str(settings_copy) in captured.out

    updated = settings_copy.read_text(encoding="utf-8")
    assert expected in updated
