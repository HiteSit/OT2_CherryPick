# Conventions & Guidelines

Python:
- Python 3.12, 4-space indentation
- Naming: `snake_case` for functions/files/CSV columns; `PascalCase` for classes
- Module-level docstrings describe deck layout/consumables/safety notes
- Helper functions should be pure and explicit about configuration inputs

Workflow/Philosophy:
- Config-as-data: TOML + CSV compiled into JSON embedded in `CherryPick_OT2.py`
- Do NOT edit embedded JSON manually; regenerate via helper
- Prefer MCP tools/resources for configuration and workflow operations

Testing & Validation:
- Always simulate after changes to protocol-related logic
- Capture simulation logs for troubleshooting
