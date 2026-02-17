#!/usr/bin/env python3
"""E2E scenario runner for MCP server agentic tests.

Loads JSON scenario files, executes them against the MCP server using mcp-use
with a Mistral LLM, and validates results against expected outcomes.

Usage:
    # Run all scenarios
    uv run python utils/e2e_scenarios/runner.py

    # Run a specific suite
    uv run python utils/e2e_scenarios/runner.py --suite basic_workflows

    # Run by tags
    uv run python utils/e2e_scenarios/runner.py --tags fluidity,preset

    # Run a single scenario by ID
    uv run python utils/e2e_scenarios/runner.py --id 01_001

    # Skip scenarios requiring simulation
    uv run python utils/e2e_scenarios/runner.py --skip-simulation

    # Use a different model
    uv run python utils/e2e_scenarios/runner.py --model mistral-large-latest

    # Verbose output (show full agent responses)
    uv run python utils/e2e_scenarios/runner.py --verbose
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import shutil
import stat
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from langchain_mistralai import ChatMistralAI
from mcp_use import MCPAgent, MCPClient

# Resolve paths relative to this file
_THIS_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _THIS_DIR.parents[1]
_SCENARIOS_DIR = _THIS_DIR / "scenarios"

# Add tests directory to path so we can import helpers
sys.path.insert(0, str(_PROJECT_ROOT / "tests"))

from validator import CheckResult, ValidationReport, Validator  # noqa: E402


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class Scenario:
    """A single test scenario loaded from JSON."""

    id: str
    name: str
    description: str
    tags: list[str]
    difficulty: str
    expected_tools: list[str]
    max_steps: int
    requires_simulation: bool
    requires_workspace: bool
    prompt: str | None
    multi_turn: list[str] | None
    validations: dict[str, Any]
    suite_name: str

    @classmethod
    def from_dict(cls, data: dict[str, Any], suite_name: str) -> Scenario:
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            tags=data.get("tags", []),
            difficulty=data.get("difficulty", "medium"),
            expected_tools=data.get("expected_tools", []),
            max_steps=data.get("max_steps", 20),
            requires_simulation=data.get("requires_simulation", False),
            requires_workspace=data.get("requires_workspace", True),
            prompt=data.get("prompt"),
            multi_turn=data.get("multi_turn"),
            validations=data.get("validations", {}),
            suite_name=suite_name,
        )


@dataclass
class ScenarioResult:
    """Result of running a single scenario."""

    scenario: Scenario
    report: ValidationReport
    duration_seconds: float = 0.0
    skipped: bool = False
    skip_reason: str = ""


@dataclass
class RunReport:
    """Aggregated results from running multiple scenarios."""

    results: list[ScenarioResult] = field(default_factory=list)
    total_duration: float = 0.0

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if not r.skipped and r.report.passed)

    @property
    def failed(self) -> int:
        return sum(1 for r in self.results if not r.skipped and not r.report.passed)

    @property
    def skipped(self) -> int:
        return sum(1 for r in self.results if r.skipped)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _remove_readonly(func: Any, path: str, _excinfo: Any) -> None:
    """Handle Windows readonly files during shutil.rmtree."""
    os.chmod(path, stat.S_IWRITE)
    func(path)


def _build_mcp_config(
    project_root: Path,
    project_dir: Path,
    labware_path: str,
) -> dict[str, Any]:
    """Build the MCP client configuration dictionary."""

    env: dict[str, str] = {"LABWARE_PATH": labware_path}
    env["OT2_PROJECT_DIR"] = str(project_dir)

    return {
        "mcpServers": {
            "ot2-cherrypick": {
                "command": "uv",
                "args": [
                    "--directory",
                    str(project_root),
                    "run",
                    "ot2-mcp-server",
                ],
                "env": env,
            }
        }
    }


def _create_workspace(project_root: Path) -> Path:
    """Create an isolated temp workspace with standard project files."""

    workspace = Path(tempfile.mkdtemp(prefix="e2e_scenario_"))
    # Copy template files from repo root
    for filename in ("settings.toml", "labware_dict.toml", "CherryPick_OT2.py"):
        src = project_root / filename
        if src.exists():
            shutil.copy2(src, workspace / filename)

    csv_src = project_root / "CSVs"
    if csv_src.exists():
        shutil.copytree(csv_src, workspace / "CSVs")
    else:
        (workspace / "CSVs").mkdir()

    (workspace / "logs").mkdir(exist_ok=True)
    return workspace


# ---------------------------------------------------------------------------
# Scenario loading
# ---------------------------------------------------------------------------

def load_scenarios(
    scenarios_dir: Path = _SCENARIOS_DIR,
    *,
    suite_filter: str | None = None,
    tag_filter: list[str] | None = None,
    id_filter: str | None = None,
) -> list[Scenario]:
    """Load scenarios from JSON files with optional filtering."""

    scenarios: list[Scenario] = []

    for json_file in sorted(scenarios_dir.glob("*.json")):
        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            print(f"  WARNING: Skipping {json_file.name}: {exc}")
            continue

        suite_name = data.get("suite_name", json_file.stem)

        if suite_filter and suite_filter.lower() not in suite_name.lower():
            continue

        for scenario_data in data.get("scenarios", []):
            scenario = Scenario.from_dict(scenario_data, suite_name)

            if id_filter and scenario.id != id_filter:
                continue

            if tag_filter and not any(t in scenario.tags for t in tag_filter):
                continue

            scenarios.append(scenario)

    return scenarios


# ---------------------------------------------------------------------------
# Scenario execution
# ---------------------------------------------------------------------------

async def _run_agent(
    config: dict[str, Any],
    model: str,
    prompts: list[str],
    max_steps: int,
) -> str:
    """Run the MCP agent with the given prompts and return the final response."""

    client = MCPClient(config=config)
    llm = ChatMistralAI(model=model)
    agent = MCPAgent(llm=llm, client=client, max_steps=max_steps)

    last_response = ""
    try:
        for prompt in prompts:
            last_response = await agent.run(prompt)
    finally:
        try:
            await client.close_all_sessions()
        except Exception:
            pass

    return last_response


def run_scenario(
    scenario: Scenario,
    project_root: Path,
    labware_path: str,
    model: str,
    *,
    skip_simulation: bool = False,
    verbose: bool = False,
) -> ScenarioResult:
    """Execute a single scenario and validate results."""

    # Check skip conditions
    if scenario.requires_simulation and skip_simulation:
        report = ValidationReport(
            scenario_id=scenario.id,
            scenario_name=scenario.name,
        )
        return ScenarioResult(
            scenario=scenario,
            report=report,
            skipped=True,
            skip_reason="Simulation required but --skip-simulation set",
        )

    # Build prompt list
    if scenario.multi_turn:
        prompts = scenario.multi_turn
    elif scenario.prompt:
        prompts = [scenario.prompt]
    else:
        report = ValidationReport(
            scenario_id=scenario.id,
            scenario_name=scenario.name,
            error="No prompt or multi_turn defined",
        )
        return ScenarioResult(scenario=scenario, report=report)

    # Create isolated workspace
    workspace = _create_workspace(project_root)

    try:
        config = _build_mcp_config(project_root, workspace, labware_path)

        if verbose:
            print(f"  Workspace: {workspace}")
            for i, p in enumerate(prompts):
                print(f"  Prompt[{i}]: {p[:100]}{'...' if len(p) > 100 else ''}")

        start = time.time()
        try:
            response = asyncio.run(
                _run_agent(config, model, prompts, scenario.max_steps)
            )
        except Exception as exc:
            duration = time.time() - start
            report = ValidationReport(
                scenario_id=scenario.id,
                scenario_name=scenario.name,
                error=f"Agent execution failed: {exc}",
            )
            return ScenarioResult(
                scenario=scenario, report=report, duration_seconds=duration
            )
        duration = time.time() - start

        if verbose:
            print(f"  Response ({len(response)} chars): {response[:200]}...")

        # Validate
        validator = Validator(workspace)
        checks = validator.run_all(scenario.validations, response)

        report = ValidationReport(
            scenario_id=scenario.id,
            scenario_name=scenario.name,
            checks=checks,
            agent_response=response,
        )

        return ScenarioResult(
            scenario=scenario, report=report, duration_seconds=duration
        )
    finally:
        # Clean up workspace
        try:
            shutil.rmtree(workspace, onexc=_remove_readonly)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def _status_icon(result: ScenarioResult) -> str:
    if result.skipped:
        return "SKIP"
    if result.report.passed:
        return "PASS"
    return "FAIL"


def print_report(run_report: RunReport, *, verbose: bool = False) -> None:
    """Print a formatted report to the console."""

    print("\n" + "=" * 80)
    print("E2E SCENARIO RESULTS")
    print("=" * 80)

    # Group by suite
    suites: dict[str, list[ScenarioResult]] = {}
    for result in run_report.results:
        suite = result.scenario.suite_name
        suites.setdefault(suite, []).append(result)

    for suite_name, results in suites.items():
        print(f"\n--- {suite_name} ---")
        for result in results:
            status = _status_icon(result)
            duration = f"{result.duration_seconds:.1f}s" if result.duration_seconds > 0 else "-"
            tags = ", ".join(result.scenario.tags) if result.scenario.tags else ""
            print(
                f"  [{status}] {result.scenario.id}: {result.scenario.name} "
                f"({duration}) [{tags}]"
            )

            if result.skipped:
                print(f"         Skip: {result.skip_reason}")
            elif result.report.error:
                print(f"         Error: {result.report.error}")
            elif not result.report.passed or verbose:
                for check in result.report.checks:
                    marker = "OK" if check.passed else "FAIL"
                    hard_soft = "hard" if check.hard else "soft"
                    print(f"         [{marker}] ({hard_soft}) {check.name}: {check.message}")

    # Summary
    print("\n" + "=" * 80)
    print(
        f"SUMMARY: {run_report.passed} passed, {run_report.failed} failed, "
        f"{run_report.skipped} skipped (total: {run_report.total})"
    )
    print(f"Total time: {run_report.total_duration:.1f}s")
    print("=" * 80)


def save_report_json(run_report: RunReport, output_path: Path) -> None:
    """Save the run report as a JSON file for later analysis."""

    data = {
        "summary": {
            "total": run_report.total,
            "passed": run_report.passed,
            "failed": run_report.failed,
            "skipped": run_report.skipped,
            "total_duration_seconds": run_report.total_duration,
        },
        "results": [],
    }

    for result in run_report.results:
        entry: dict[str, Any] = {
            "scenario_id": result.scenario.id,
            "scenario_name": result.scenario.name,
            "suite": result.scenario.suite_name,
            "tags": result.scenario.tags,
            "difficulty": result.scenario.difficulty,
            "duration_seconds": result.duration_seconds,
            "skipped": result.skipped,
        }
        if result.skipped:
            entry["skip_reason"] = result.skip_reason
        elif result.report.error:
            entry["error"] = result.report.error
            entry["passed"] = False
        else:
            entry["passed"] = result.report.passed
            entry["checks"] = [
                {
                    "name": c.name,
                    "passed": c.passed,
                    "message": c.message,
                    "hard": c.hard,
                }
                for c in result.report.checks
            ]
            # Truncate response for JSON output
            entry["response_preview"] = result.report.agent_response[:500]

        data["results"].append(entry)

    output_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"\nJSON report saved to: {output_path}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="E2E scenario runner for OT-2 MCP server agentic tests",
    )
    parser.add_argument(
        "--suite",
        type=str,
        default=None,
        help="Run only scenarios from this suite (substring match on suite_name)",
    )
    parser.add_argument(
        "--tags",
        type=str,
        default=None,
        help="Comma-separated tags to filter scenarios (any match)",
    )
    parser.add_argument(
        "--id",
        type=str,
        default=None,
        help="Run a single scenario by ID",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="mistral-medium-2508",
        help="Mistral model to use (default: mistral-medium-2508)",
    )
    parser.add_argument(
        "--skip-simulation",
        action="store_true",
        help="Skip scenarios that require opentrons_simulate",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show full agent responses and all check details",
    )
    parser.add_argument(
        "--labware-path",
        type=str,
        default="/mnt/c/Users/ricca/AppData/Roaming/Opentrons/labware",
        help="Path to Opentrons custom labware directory",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to save JSON report (optional)",
    )
    parser.add_argument(
        "--scenarios-dir",
        type=str,
        default=str(_SCENARIOS_DIR),
        help="Directory containing JSON scenario files",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    tag_filter = args.tags.split(",") if args.tags else None

    print("Loading scenarios...")
    scenarios = load_scenarios(
        Path(args.scenarios_dir),
        suite_filter=args.suite,
        tag_filter=tag_filter,
        id_filter=args.id,
    )

    if not scenarios:
        print("No scenarios matched the given filters.")
        sys.exit(1)

    print(f"Found {len(scenarios)} scenario(s) to run.")

    run_report = RunReport()
    total_start = time.time()

    for i, scenario in enumerate(scenarios, 1):
        print(f"\n[{i}/{len(scenarios)}] Running: {scenario.id} - {scenario.name}")

        result = run_scenario(
            scenario,
            project_root=_PROJECT_ROOT,
            labware_path=args.labware_path,
            model=args.model,
            skip_simulation=args.skip_simulation,
            verbose=args.verbose,
        )
        run_report.results.append(result)

        status = _status_icon(result)
        print(f"  -> {status} ({result.duration_seconds:.1f}s)")

    run_report.total_duration = time.time() - total_start

    print_report(run_report, verbose=args.verbose)

    if args.output:
        save_report_json(run_report, Path(args.output))

    # Exit with non-zero if any hard failures
    if run_report.failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
