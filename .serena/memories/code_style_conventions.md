# Code Style & Conventions

## Python Standards
- **Python 3.12** with four-space indentation
- **Module-level docstrings**: Summarize deck layout, consumables, safety notes
- **Naming**: `snake_case` for functions/files/CSV columns; `PascalCase` for classes only
- **Helper functions**: Keep pure and side-effect free; pass configuration explicitly
- **Operator feedback**: Emit concise `print()` statements for progress tracking

## File Naming
- CSV columns: lowercase with spaces (e.g., `Source Labware`, `Volume (ul)`)
- Python files: snake_case
- TOML keys: snake_case

## Version Control
- **Conventional Commits**: `feat:`, `fix:`, `chore:` with <60 char subjects
- **Never create commits** as an AI agent - only repository owner commits
- Keep sensitive data out of repo

## MCP Server Conventions
- Tools return structured responses with success/error status
- TomlHandler preserves formatting and comments
- Backup files created before TOML modifications (`.toml.backup`)

## Testing
- Unit tests in `tests/` directory
- MCP integration tests use mcp-use with Mistral LLM
- Always simulate after changes
