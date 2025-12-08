# MCP Implementation Learning Brief

## Context Budget: Use max 20% of available tokens (~40K)

## Task
Understand the MCP server implementation wrapping @CherryPick_OT2.py

## Required Reading (in order)
1. @docs/readme_fastmcp.md - FastMCP framework basics
2. @docs/readme_mcp_use.md - MCP-Use library
3. @docs/mcp_tools_guide.md - Tools concept (critical)
4. @utils/mcp-use_cherrypick.py - End-to-end integration test (shows complete workflow)

## Exploration Strategy
- **Use Serena symbolic tools only** (`get_symbols_overview`, `find_symbol`)
- Read documentation first, **then connect concepts to code**: spot-check 2-3 key implementations in @src/ot2_cherrypick_mcp
- Map: FastMCP decorators → tool implementations, MCP-Use patterns
- Focus on: server entry point, one tool example, how mcp-use test exercises the system
- **Do NOT read entire implementation files**

## Deliverable
Brief explanation covering:
- MCP server architecture (how it wraps protocol generation)
- How tools expose functionality
- How components (tools/resources/prompts) interact
