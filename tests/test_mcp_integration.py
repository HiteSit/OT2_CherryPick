"""Integration tests using mcp-use with the OT-2 MCP server."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Dict

from langchain_mistralai import ChatMistralAI
from mcp_use import MCPAgent, MCPClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CSV_STRING = """Source Labware,Source Well,Volume (ul),Dest Labware,Dest Well,Source Height,Dest Top\n\
tube_rack_96_1500ul_4,A1,100,384_ppv_55ul_2,B1,2,-5\n\
tube_rack_96_1500ul_4,A2,50,384_ppv_55ul_2,B2,2,-5\n\
tube_rack_96_1500ul_4,A3,75,384_ppv_55ul_2,B3,2,-5\n\
tube_rack_96_1500ul_4,A4,25,384_ppv_55ul_2,B4,2,-5"""

TMP_UPLOAD_TARGET = str(PROJECT_ROOT / "tests" / "tmp" / "tmp_uploaded.csv")


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
    llm = ChatMistralAI(model="mistral-medium-2508")
    agent = MCPAgent(llm=llm, client=client, max_steps=20)
    return await agent.run(query)


def test_agent_lists_tools() -> None:
    result = asyncio.run(_run_agent("List available tools on the OT-2 cherry-pick server."))
    assert isinstance(result, str)
    assert result


def test_agent_runs_workflow_from_string() -> None:
    query = (
        f"Save the following CSV content as {TMP_UPLOAD_TARGET} using upload_csv_content,"
        " then run full_workflow on that file with simulation disabled and report the outcome.\n\nCSV_CONTENT:\n"
        f"{CSV_STRING}"
    )

    result = asyncio.run(_run_agent(query))
    assert isinstance(result, str)
    assert Path(TMP_UPLOAD_TARGET).exists()
    assert "no errors" in result.lower()


def test_agent_updates_settings(tmp_path: Path, capsys) -> None:
    settings_copy = tmp_path / "settings.toml"
    settings_copy.write_text((PROJECT_ROOT / "settings.toml").read_text(encoding="utf-8"), encoding="utf-8")

    query = (
        "Call update_settings with path 'settings.general.tip_reuse', value 'never', "
        f"and settings_path '{settings_copy}'. Afterwards, confirm the change."
    )

    client = MCPClient(config=_build_config())
    llm = ChatMistralAI(model="ministral-8b-2410")
    agent = MCPAgent(llm=llm, client=client, max_steps=8)
    result = asyncio.run(agent.run(query))

    print(f"Temporary settings path: {settings_copy}")
    captured = capsys.readouterr()
    assert str(settings_copy) in captured.out

    updated = settings_copy.read_text(encoding="utf-8")
    assert "tip_reuse = \"never\"" in updated
