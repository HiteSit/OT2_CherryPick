"""Response formatting utilities for MCP tools.

Converts tool response dictionaries into different formats:
- JSON: Raw dictionary (default, for programmatic use)
- Markdown: Human-readable formatted text
- Concise: Minimal single-line summary

Follows MCP best practices:
- Character limit of 25,000 to prevent context exhaustion
- Truncation with clear indicators
- Consistent formatting patterns across tool types
"""

from enum import Enum
from typing import Any, Dict, List, Literal


class ResponseFormat(str, Enum):
    """Output format options for tool responses."""

    JSON = "json"
    MARKDOWN = "markdown"
    CONCISE = "concise"


# Character limit recommendation from MCP best practices
CHARACTER_LIMIT = 25000


def truncate_text(text: str, limit: int = CHARACTER_LIMIT) -> str:
    """Truncate text to character limit with indicator.

    Args:
        text: Text to truncate
        limit: Maximum character count

    Returns:
        Truncated text with indicator if limit exceeded
    """
    if len(text) <= limit:
        return text
    truncated_chars = len(text) - limit
    return text[:limit] + f"\n\n... [truncated {truncated_chars:,} characters]"


class ResponseFormatter:
    """Format tool responses into different output formats."""

    @staticmethod
    def format(
        response: Dict[str, Any],
        tool_type: str,
        format_type: ResponseFormat = ResponseFormat.JSON,
    ) -> str | Dict[str, Any]:
        """Main dispatcher for formatting responses.

        Args:
            response: Tool response dictionary
            tool_type: Type of tool (e.g., "protocol_generation", "simulation")
            format_type: Desired output format

        Returns:
            Formatted response (dict for JSON, str for Markdown/Concise)
        """
        if format_type == ResponseFormat.JSON:
            return response

        # Route to appropriate formatter based on tool type
        formatters = {
            "protocol_generation": ResponseFormatter.format_protocol_generation,
            "simulation": ResponseFormatter.format_simulation,
            "validation": ResponseFormatter.format_validation,
            "workflow": ResponseFormatter.format_workflow,
            "config_update": ResponseFormatter.format_config_update,
            "config_list": ResponseFormatter.format_config_list,
            "deployment": ResponseFormatter.format_deployment,
            "csv": ResponseFormatter.format_csv,
            "labware": ResponseFormatter.format_labware,
        }

        formatter = formatters.get(tool_type)
        if not formatter:
            # Fallback for unknown types
            return ResponseFormatter._format_generic(response, format_type)

        return formatter(response, format_type)

    @staticmethod
    def format_protocol_generation(
        response: Dict[str, Any], format_type: ResponseFormat
    ) -> str:
        """Format protocol generation tool response.

        Expected keys: protocol_file, json_size, message
        """
        if format_type == ResponseFormat.CONCISE:
            json_size = response.get("json_size", 0)
            return f"✓ Generated ({json_size:,} chars)"

        # Markdown
        protocol_file = response.get("protocol_file", "unknown")
        json_size = response.get("json_size", 0)
        message = response.get("message", "")

        md = f"""# Protocol Generation

✓ **Success**

- **File:** `{protocol_file}`
- **JSON Size:** {json_size:,} characters

{message}

**Next step:** Run simulation to validate protocol
"""
        return truncate_text(md.strip())

    @staticmethod
    def format_simulation(
        response: Dict[str, Any], format_type: ResponseFormat
    ) -> str:
        """Format simulation tool response.

        Expected keys: command, stdout, stderr, returncode, log_file
        """
        returncode = response.get("returncode", -1)
        stdout = response.get("stdout", "")
        stderr = response.get("stderr", "")
        log_file = response.get("log_file")

        if format_type == ResponseFormat.CONCISE:
            if returncode == 0:
                return "✓ Simulation passed"
            return "✗ Simulation failed"

        # Markdown
        status = "✓ **PASSED**" if returncode == 0 else "✗ **FAILED**"

        md_parts = [
            "# Simulation Results",
            "",
            f"## Status",
            f"{status} (exit code: {returncode})",
            "",
        ]

        # Add stdout if present
        if stdout:
            stdout_preview = stdout[:500] if len(stdout) > 500 else stdout
            md_parts.extend([
                "## Output Preview",
                "```",
                stdout_preview,
                "```",
                "",
            ])

            if len(stdout) > 500:
                md_parts.append("<details>")
                md_parts.append("<summary>Full Output (click to expand)</summary>")
                md_parts.append("")
                md_parts.append("```")
                md_parts.append(stdout)
                md_parts.append("```")
                md_parts.append("</details>")
                md_parts.append("")

        # Add stderr if present
        if stderr:
            md_parts.extend([
                "## Errors",
                "```",
                stderr,
                "```",
                "",
            ])

        # Add log file reference
        if log_file:
            md_parts.extend([
                "## Log File",
                f"`{log_file}`",
            ])

        md = "\n".join(md_parts)
        return truncate_text(md.strip())

    @staticmethod
    def format_validation(
        response: Dict[str, Any], format_type: ResponseFormat
    ) -> str:
        """Format validation tool response.

        Expected keys: status, errors, warnings
        """
        status = response.get("status", "error")
        errors = response.get("errors", [])
        warnings = response.get("warnings", [])

        if format_type == ResponseFormat.CONCISE:
            error_count = len(errors)
            warning_count = len(warnings)

            if status == "ok":
                if warning_count > 0:
                    return f"✓ Valid ({warning_count} warning{'s' if warning_count != 1 else ''})"
                return "✓ Valid"
            return f"✗ Invalid ({error_count} error{'s' if error_count != 1 else ''})"

        # Markdown
        status_emoji = "✓" if status == "ok" else "✗"
        status_text = "OK - Ready to generate protocol" if status == "ok" else "INVALID"

        md_parts = [
            "# Configuration Validation",
            "",
            "## Status",
            f"{status_emoji} **{status_text}**",
            "",
            "## Summary",
            f"- **Errors:** {len(errors)}",
            f"- **Warnings:** {len(warnings)}",
            "",
        ]

        if errors:
            md_parts.append("## Errors")
            for error in errors:
                md_parts.append(f"- {error}")
            md_parts.append("")

        if warnings:
            md_parts.append("## Warnings")
            for warning in warnings:
                md_parts.append(f"- {warning}")
            md_parts.append("")

        md = "\n".join(md_parts)
        return truncate_text(md.strip())

    @staticmethod
    def format_workflow(
        response: Dict[str, Any], format_type: ResponseFormat
    ) -> str:
        """Format workflow tool response.

        Expected keys: validation, generation, simulation, deployment, status
        """
        status = response.get("status", "error")
        validation = response.get("validation", {})
        generation = response.get("generation", {})
        simulation = response.get("simulation")
        deployment = response.get("deployment")

        if format_type == ResponseFormat.CONCISE:
            stages_completed = sum([
                bool(validation),
                bool(generation),
                bool(simulation),
                bool(deployment)
            ])

            if status == "ok":
                return f"✓ Complete ({stages_completed}/4 stages)"

            # Determine which stage failed
            if not validation or validation.get("status") == "error":
                return "✗ Failed at validation"
            if not generation:
                return "✗ Failed at generation"
            if simulation is not None and simulation.get("returncode") != 0:
                return "✗ Failed at simulation"
            return "✗ Failed at deployment"

        # Markdown
        overall_status = "✓ COMPLETE" if status == "ok" else "✗ FAILED"

        md_parts = [
            "# Full Workflow Execution",
            "",
            f"## Pipeline Status: {overall_status}",
            "",
        ]

        # Validation stage
        if validation:
            val_status = validation.get("status", "error")
            val_emoji = "✓" if val_status == "ok" else "✗"
            val_errors = len(validation.get("errors", []))
            val_warnings = len(validation.get("warnings", []))
            md_parts.append(f"### 1. Validation {val_emoji}")
            md_parts.append(f"{val_emoji} {val_status.upper()} ({val_errors} errors, {val_warnings} warnings)")
            md_parts.append("")

        # Generation stage
        if generation:
            gen_emoji = "✓"
            json_size = generation.get("json_size", 0)
            md_parts.append(f"### 2. Generation {gen_emoji}")
            md_parts.append(f"{gen_emoji} PASSED ({json_size:,} chars)")
            md_parts.append("")

        # Simulation stage
        if simulation:
            sim_returncode = simulation.get("returncode", -1)
            sim_emoji = "✓" if sim_returncode == 0 else "✗"
            md_parts.append(f"### 3. Simulation {sim_emoji}")
            md_parts.append(f"{sim_emoji} {'PASSED' if sim_returncode == 0 else 'FAILED'} (exit code {sim_returncode})")
            md_parts.append("")

        # Deployment stage
        if deployment:
            deploy_emoji = "✓"
            copies_count = len(deployment.get("copies", []))
            clipboard = deployment.get("clipboard", {})
            clipboard_success = clipboard.get("success", False) if clipboard else False
            md_parts.append(f"### 4. Deployment {deploy_emoji}")
            md_parts.append(f"{deploy_emoji} PASSED ({copies_count} file{'s' if copies_count != 1 else ''}, {'clipboard' if clipboard_success else 'no clipboard'})")
            md_parts.append("")

        md = "\n".join(md_parts)
        return truncate_text(md.strip())

    @staticmethod
    def format_config_update(
        response: Dict[str, Any], format_type: ResponseFormat
    ) -> str:
        """Format configuration update tool response.

        Expected keys: settings_file, path, old_value, new_value, backup_file
        """
        if format_type == ResponseFormat.CONCISE:
            old_value = response.get("old_value", "")
            new_value = response.get("new_value", "")
            return f"✓ Updated: {old_value} → {new_value}"

        # Markdown
        settings_file = response.get("settings_file", "unknown")
        path = response.get("path", "")
        old_value = response.get("old_value", "")
        new_value = response.get("new_value", "")
        backup_file = response.get("backup_file", "")

        md = f"""# Settings Updated

✓ **Success**

- **Path:** `{path}`
- **Old Value:** `{old_value}`
- **New Value:** `{new_value}`

**Backup:** `{backup_file}`
"""
        return truncate_text(md.strip())

    @staticmethod
    def format_config_list(
        response: Dict[str, Any], format_type: ResponseFormat
    ) -> str:
        """Format configuration list tool response.

        Expected keys: settings_file, entries, data, total_entries, message
        """
        total_entries = response.get("total_entries", 0)

        if format_type == ResponseFormat.CONCISE:
            return f"✓ Settings loaded ({total_entries} entries)"

        # Markdown
        settings_file = response.get("settings_file", "unknown")
        entries = response.get("entries", [])

        md_parts = [
            "# Settings Configuration",
            "",
            f"**File:** `{settings_file}`",
            f"**Total Entries:** {total_entries}",
            "",
            "## Settings",
        ]

        # Group entries by top-level section
        sections: Dict[str, List[tuple]] = {}
        for entry in entries:
            path = entry.get("path", "")
            value = entry.get("value", "")

            # Extract top-level section (e.g., "settings.general" -> "general")
            parts = path.split(".")
            if len(parts) >= 2:
                section = parts[1]
                rest = ".".join(parts[2:])
            else:
                section = "other"
                rest = path

            if section not in sections:
                sections[section] = []
            sections[section].append((rest, value))

        # Format by section
        for section, items in sorted(sections.items()):
            md_parts.append(f"### {section}")
            for path, value in items:
                # Format value representation
                if isinstance(value, str):
                    value_str = f'`"{value}"`'
                elif isinstance(value, bool):
                    value_str = f"`{str(value).lower()}`"
                elif isinstance(value, (int, float)):
                    value_str = f"`{value}`"
                else:
                    value_str = f"`{value}`"

                md_parts.append(f"- **{path}:** {value_str}")
            md_parts.append("")

        md = "\n".join(md_parts)
        return truncate_text(md.strip())

    @staticmethod
    def format_deployment(
        response: Dict[str, Any], format_type: ResponseFormat
    ) -> str:
        """Format deployment tool response.

        Expected keys: protocol_file, copies, clipboard
        """
        if format_type == ResponseFormat.CONCISE:
            copies = response.get("copies", [])
            clipboard = response.get("clipboard", {})
            clipboard_success = clipboard.get("success", False) if clipboard else False

            parts = []
            if copies:
                parts.append(f"{len(copies)} file{'s' if len(copies) != 1 else ''}")
            if clipboard_success:
                parts.append("clipboard")

            return f"✓ Deployed ({', '.join(parts)})"

        # Markdown
        protocol_file = response.get("protocol_file", "unknown")
        copies = response.get("copies", [])
        clipboard = response.get("clipboard", {})

        md_parts = [
            "# Deployment",
            "",
            "✓ **Success**",
            "",
            f"**Source:** `{protocol_file}`",
            "",
        ]

        if copies:
            md_parts.append("## Copied To")
            for dest in copies:
                md_parts.append(f"- `{dest}`")
            md_parts.append("")

        if clipboard:
            clipboard_success = clipboard.get("success", False)
            clipboard_msg = clipboard.get("message", "")
            clipboard_emoji = "✓" if clipboard_success else "✗"
            md_parts.append("## Clipboard")
            md_parts.append(f"{clipboard_emoji} {clipboard_msg}")

        md = "\n".join(md_parts)
        return truncate_text(md.strip())

    @staticmethod
    def format_csv(
        response: Dict[str, Any], format_type: ResponseFormat
    ) -> str:
        """Format CSV tool response.

        Expected keys: csv_file, transfers, source_labware, dest_labware
        """
        if format_type == ResponseFormat.CONCISE:
            transfers = response.get("transfers", 0)
            return f"✓ Template created ({transfers} transfers)"

        # Markdown
        csv_file = response.get("csv_file", "unknown")
        transfers = response.get("transfers", 0)
        source_labware = response.get("source_labware", "")
        dest_labware = response.get("dest_labware", "")

        md = f"""# CSV Template

✓ **Created**

- **File:** `{csv_file}`
- **Transfers:** {transfers}
- **Source:** {source_labware}
- **Destination:** {dest_labware}

**Next step:** Edit CSV to define specific transfers
"""
        return truncate_text(md.strip())

    @staticmethod
    def format_labware(
        response: Dict[str, Any], format_type: ResponseFormat
    ) -> str:
        """Format labware tool response.

        Expected keys: labware_file, labware_id, category, well_count, well_volume, offsets, backup_file
        """
        if format_type == ResponseFormat.CONCISE:
            well_count = response.get("well_count", 0)
            well_volume = response.get("well_volume", 0)
            return f"✓ Added ({well_count}-well, {well_volume}µL)"

        # Markdown
        labware_file = response.get("labware_file", "unknown")
        labware_id = response.get("labware_id", "")
        category = response.get("category", "")
        well_count = response.get("well_count", 0)
        well_volume = response.get("well_volume", 0)
        offsets = response.get("offsets", {})

        md = f"""# Labware Definition

✓ **Added**

- **ID:** `{labware_id}`
- **Category:** {category}
- **Wells:** {well_count}
- **Volume:** {well_volume} µL
- **Offsets:** X={offsets.get('x', 0)}, Y={offsets.get('y', 0)}, Z={offsets.get('z', 0)}

**File:** `{labware_file}`
"""
        return truncate_text(md.strip())

    @staticmethod
    def _format_generic(
        response: Dict[str, Any], format_type: ResponseFormat
    ) -> str:
        """Fallback formatter for unknown tool types.

        Args:
            response: Tool response dictionary
            format_type: Desired output format

        Returns:
            Formatted string representation
        """
        if format_type == ResponseFormat.CONCISE:
            # Try to extract a status or message
            if "status" in response:
                status = response["status"]
                emoji = "✓" if status == "ok" else "✗"
                return f"{emoji} {status}"
            if "message" in response:
                return response["message"][:100]  # First 100 chars
            return "✓ Complete"

        # Markdown fallback - simple key-value list
        md_parts = ["# Tool Response", ""]
        for key, value in response.items():
            if isinstance(value, str) and len(value) > 100:
                # Truncate long strings
                md_parts.append(f"**{key}:** `{value[:100]}...`")
            else:
                md_parts.append(f"**{key}:** `{value}`")

        md = "\n".join(md_parts)
        return truncate_text(md.strip())
