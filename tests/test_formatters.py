"""Tests for response formatters."""

import pytest

from src.ot2_cherrypick_mcp.utils.formatters import (
    ResponseFormat,
    ResponseFormatter,
    truncate_text,
)


class TestTruncateText:
    """Test text truncation utility."""

    def test_no_truncation_when_under_limit(self):
        """Short text is not truncated."""
        text = "Short text"
        result = truncate_text(text, limit=100)
        assert result == text
        assert "[truncated" not in result

    def test_truncation_when_over_limit(self):
        """Long text is truncated with indicator."""
        text = "a" * 1000
        result = truncate_text(text, limit=100)
        assert len(result) < len(text)
        assert result.startswith("a" * 100)
        assert "[truncated 900 characters]" in result


class TestProtocolGenerationFormatting:
    """Test protocol generation response formatting."""

    def test_json_format_returns_dict(self):
        """JSON format returns original dict."""
        response = {
            "protocol_file": "/tmp/CherryPick_OT2.py",
            "json_size": 12345,
            "message": "Protocol generated successfully",
        }

        result = ResponseFormatter.format(
            response, "protocol_generation", ResponseFormat.JSON
        )

        assert result == response
        assert isinstance(result, dict)

    def test_markdown_format_returns_string(self):
        """Markdown format returns formatted string."""
        response = {
            "protocol_file": "/tmp/CherryPick_OT2.py",
            "json_size": 12345,
            "message": "Protocol generated successfully",
        }

        result = ResponseFormatter.format(
            response, "protocol_generation", ResponseFormat.MARKDOWN
        )

        assert isinstance(result, str)
        assert "# Protocol Generation" in result
        assert "✓ **Success**" in result
        assert "/tmp/CherryPick_OT2.py" in result
        assert "12,345" in result

    def test_concise_format_single_line(self):
        """Concise format returns single-line summary."""
        response = {
            "protocol_file": "/tmp/CherryPick_OT2.py",
            "json_size": 12345,
            "message": "Protocol generated successfully",
        }

        result = ResponseFormatter.format(
            response, "protocol_generation", ResponseFormat.CONCISE
        )

        assert isinstance(result, str)
        assert result == "✓ Generated (12,345 chars)"
        assert "\n" not in result


class TestSimulationFormatting:
    """Test simulation response formatting."""

    def test_simulation_pass_concise(self):
        """Concise format shows pass status."""
        response = {
            "command": ["opentrons_simulate", "protocol.py"],
            "stdout": "Simulation output here...",
            "stderr": "",
            "returncode": 0,
            "log_file": "/tmp/sim.log",
        }

        result = ResponseFormatter.format(
            response, "simulation", ResponseFormat.CONCISE
        )

        assert result == "✓ Simulation passed"

    def test_simulation_fail_concise(self):
        """Concise format shows fail status."""
        response = {
            "command": ["opentrons_simulate", "protocol.py"],
            "stdout": "",
            "stderr": "Error: labware not found",
            "returncode": 1,
            "log_file": "/tmp/sim.log",
        }

        result = ResponseFormatter.format(
            response, "simulation", ResponseFormat.CONCISE
        )

        assert result == "✗ Simulation failed"

    def test_simulation_markdown_with_collapsible(self):
        """Markdown format includes collapsible output."""
        response = {
            "command": ["opentrons_simulate", "protocol.py"],
            "stdout": "a" * 1000,  # Long output
            "stderr": "",
            "returncode": 0,
            "log_file": "/tmp/sim.log",
        }

        result = ResponseFormatter.format(
            response, "simulation", ResponseFormat.MARKDOWN
        )

        assert "# Simulation Results" in result
        assert "✓ **PASSED**" in result
        assert "<details>" in result
        assert "Full Output (click to expand)" in result


class TestValidationFormatting:
    """Test validation response formatting."""

    def test_validation_ok_concise(self):
        """Concise format for successful validation."""
        response = {
            "status": "ok",
            "errors": [],
            "warnings": ["Row 5: unusual well format"],
        }

        result = ResponseFormatter.format(
            response, "validation", ResponseFormat.CONCISE
        )

        assert result == "✓ Valid (1 warning)"

    def test_validation_error_concise(self):
        """Concise format for failed validation."""
        response = {
            "status": "error",
            "errors": ["Missing column: Volume", "Slot conflict: position 4"],
            "warnings": [],
        }

        result = ResponseFormatter.format(
            response, "validation", ResponseFormat.CONCISE
        )

        assert result == "✗ Invalid (2 errors)"

    def test_validation_markdown_with_lists(self):
        """Markdown format includes error/warning lists."""
        response = {
            "status": "error",
            "errors": ["Missing column: Volume"],
            "warnings": ["Row 5: unusual well format"],
        }

        result = ResponseFormatter.format(
            response, "validation", ResponseFormat.MARKDOWN
        )

        assert "# Configuration Validation" in result
        assert "✗ **INVALID**" in result
        assert "## Errors" in result
        assert "- Missing column: Volume" in result
        assert "## Warnings" in result
        assert "- Row 5: unusual well format" in result


class TestWorkflowFormatting:
    """Test workflow response formatting."""

    def test_workflow_complete_concise(self):
        """Concise format for completed workflow."""
        response = {
            "status": "ok",
            "validation": {"status": "ok", "errors": [], "warnings": []},
            "generation": {"protocol_file": "/tmp/protocol.py", "json_size": 12345},
            "simulation": {"returncode": 0, "stdout": "", "stderr": ""},
            "deployment": {"copies": ["/target/protocol.py"], "clipboard": {"success": True}},
        }

        result = ResponseFormatter.format(
            response, "workflow", ResponseFormat.CONCISE
        )

        assert result == "✓ Complete (4/4 stages)"

    def test_workflow_failed_at_validation_concise(self):
        """Concise format for workflow failed at validation."""
        response = {
            "status": "error",
            "validation": {"status": "error", "errors": ["Error"], "warnings": []},
            "generation": None,
            "simulation": None,
            "deployment": None,
        }

        result = ResponseFormatter.format(
            response, "workflow", ResponseFormat.CONCISE
        )

        assert result == "✗ Failed at validation"

    def test_workflow_markdown_pipeline_view(self):
        """Markdown format shows pipeline stages."""
        response = {
            "status": "ok",
            "validation": {"status": "ok", "errors": [], "warnings": []},
            "generation": {"protocol_file": "/tmp/protocol.py", "json_size": 12345},
            "simulation": {"returncode": 0, "stdout": "", "stderr": "", "log_file": None},
            "deployment": None,
        }

        result = ResponseFormatter.format(
            response, "workflow", ResponseFormat.MARKDOWN
        )

        assert "# Full Workflow Execution" in result
        assert "✓ COMPLETE" in result
        assert "### 1. Validation ✓" in result
        assert "### 2. Generation ✓" in result
        assert "### 3. Simulation ✓" in result


class TestGenericFallback:
    """Test fallback formatter for unknown types."""

    def test_unknown_type_concise(self):
        """Unknown type gets generic concise format."""
        response = {"status": "ok", "message": "Something happened"}

        result = ResponseFormatter.format(
            response, "unknown_tool", ResponseFormat.CONCISE
        )

        assert isinstance(result, str)
        assert "✓" in result

    def test_unknown_type_markdown(self):
        """Unknown type gets generic markdown format."""
        response = {"field1": "value1", "field2": 42}

        result = ResponseFormatter.format(
            response, "unknown_tool", ResponseFormat.MARKDOWN
        )

        assert "# Tool Response" in result
        assert "field1" in result
        assert "field2" in result
