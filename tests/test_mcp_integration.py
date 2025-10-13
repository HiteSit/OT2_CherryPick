"""Integration tests using mcp-use with the OT-2 MCP server."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Dict

from langchain_mistralai import ChatMistralAI
from mcp_use import MCPAgent, MCPClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]


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
    llm = ChatMistralAI(model="mistral-large-latest")
    agent = MCPAgent(llm=llm, client=client, max_steps=20)
    return await agent.run(query)


def test_agent_lists_tools() -> None:
    result = asyncio.run(_run_agent("List available tools on the OT-2 cherry-pick server."))
    assert isinstance(result, str)
    assert result


def test_agent_runs_workflow(tmp_path: Path) -> None:
    csv_copy = tmp_path / "example_basic.csv"
    csv_copy.write_text(
        (PROJECT_ROOT / "CSVs" / "example_basic.csv").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    query = (
        "Use the full_workflow tool on the CSV located at"
        f" {csv_copy}. Report whether validation succeeded."
    )

    result = asyncio.run(_run_agent(query))
    assert isinstance(result, str)
    assert result
