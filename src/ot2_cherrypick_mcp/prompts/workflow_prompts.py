"""Workflow-oriented prompt templates."""

from __future__ import annotations

from fastmcp import FastMCP

__all__ = ["register_workflow_prompts"]


def register_workflow_prompts(mcp: FastMCP) -> None:
    """Register workflow prompts for guided interactions."""

    @mcp.prompt
    def setup_new_experiment() -> str:  # pragma: no cover - prompt text tested separately
        """Guide an agent through configuring a new cherry-pick experiment."""

        return (
            "Goal: configure a new cherry-pick run.\n\n"
            "1. Inspect current configuration via config://settings and status://deck-layout.\n"
            "2. Apply liquid handling presets with the apply_liquid_preset tool if appropriate.\n"
            "3. Use update_settings to adjust parameters such as tip reuse or head speed.\n"
            "4. Generate a CSV template with generate_csv_template or review existing files via files://csvs.\n"
            "5. Validate, generate, and simulate using the full_workflow tool, enabling deployment if needed."
        )

    @mcp.prompt
    def troubleshoot_simulation_error() -> str:  # pragma: no cover - prompt text tested separately
        """Guide troubleshooting of failed simulations."""

        return (
            "When a simulation fails:\n"
            "- Read logs://last-simulation to understand the failure.\n"
            "- Re-check deck layout via status://deck-layout and ensure labware IDs match labware_dict.toml.\n"
            "- Validate inputs with validate_configuration; address any errors.\n"
            "- Re-run full_workflow after fixing issues, and report concrete changes made."
        )
