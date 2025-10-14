"""Integration tests using mcp-use with the OT-2 MCP server."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import helper_cherry_pick
import pytest

from .helpers import AgentRunner, Assertions, ProjectSetup
from .test_data import (
    CSV_BASIC,
    CSV_TEMPLATE_SCENARIOS,
    LABWARE_SCENARIOS,
    LIQUID_PRESET_SCENARIOS,
    UPDATE_SETTINGS_SCENARIOS,
    VALIDATION_ERROR_SCENARIOS,
)


def _print_project_snapshot(context: str, project_dir: Path) -> None:
    """Emit project directory details for manual inspection."""

    print(
        f"[{context}] project_dir={project_dir} "
        f"settings={project_dir / 'settings.toml'} "
        f"protocol={project_dir / 'CherryPick_OT2.py'} "
        f"csv_dir={project_dir / 'CSVs'}",
        flush=True,
    )


def test_agent_lists_tools(agent_runner: AgentRunner) -> None:
    """Test that agent can list available tools."""

    result = agent_runner.run("What tools are available for the OT-2 cherry-pick protocol?")
    Assertions.assert_no_errors(result)
    assert result


def test_agent_runs_workflow_from_string(project_dir: Path, agent_runner: AgentRunner) -> None:
    """Test that agent can upload CSV and run workflow."""

    csv_dir = project_dir / "CSVs"
    tmp_target = csv_dir / "tmp_uploaded.csv"
    tmp_target.unlink(missing_ok=True)

    query = (
        "I have some transfer data in CSV format that I'd like you to save to "
        "'CSVs/tmp_uploaded.csv'. After saving it, please generate and validate the protocol "
        "(but skip the simulation step). Here's the CSV data:\n\n"
        f"{CSV_BASIC}\n\n"
        "Let me know if everything worked correctly."
    )

    result = agent_runner.run(query)
    Assertions.assert_no_errors(result)
    Assertions.assert_file_exists(tmp_target)

    _print_project_snapshot("workflow_from_string", project_dir)


def test_agent_full_pipeline_updates_protocol(
    project_dir: Path, agent_runner: AgentRunner
) -> None:
    """Ensure agents can update settings, run full workflow, and embed JSON in protocol."""

    csv_relative = "CSVs/pipeline_full.csv"
    csv_path = project_dir / csv_relative
    csv_path.unlink(missing_ok=True)

    upload_query = (
        "Please save the following CSV data to 'CSVs/pipeline_full.csv' so it can be used for "
        "a protocol run:\n\n"
        f"{CSV_BASIC}\n\n"
        "Confirm when it has been saved."
    )
    upload_result = agent_runner.run(upload_query)
    Assertions.assert_no_errors(upload_result)
    Assertions.assert_file_exists(csv_path)

    update_query = (
        "Use the update_settings tool to set the path 'settings.general.mode' to the value 'single_X1'."
    )
    update_result = agent_runner.run(update_query)
    Assertions.assert_no_errors(update_result)
    updated_settings = (project_dir / "settings.toml").read_text(encoding="utf-8")
    assert 'mode = "single_X1"' in updated_settings

    workflow_query = (
        "Run full_workflow on 'CSVs/pipeline_full.csv' with simulate set to false and deployment "
        "disabled. Let me know when the workflow is complete."
    )
    workflow_result = agent_runner.run(workflow_query)
    Assertions.assert_no_errors(workflow_result)

    protocol_path = project_dir / "CherryPick_OT2.py"
    expected_json = helper_cherry_pick.create_json_config(
        str(project_dir / "labware_dict.toml"),
        str(project_dir / "settings.toml"),
        str(csv_path),
        verbose=False,
    )
    Assertions.assert_file_contains(protocol_path, expected_json)

    _print_project_snapshot("full_pipeline", project_dir)


@pytest.mark.parametrize("path,value,expected,prompt", UPDATE_SETTINGS_SCENARIOS)
def test_agent_updates_settings(
    tmp_path: Path,
    project_setup: ProjectSetup,
    agent_factory: Callable[..., AgentRunner],
    path: str,
    value: str,
    expected: str,
    prompt: str,
) -> None:
    """Test that agent can update settings via natural language."""

    project_dir: Path = project_setup.create_standard_project(tmp_path)
    runner: AgentRunner = agent_factory(project_dir, max_steps=8)

    query = f"{prompt} in the settings file"
    result = runner.run(query)
    Assertions.assert_no_errors(result)

    settings_file = project_dir / "settings.toml"
    updated = settings_file.read_text(encoding="utf-8")
    assert expected in updated

    _print_project_snapshot("updates_settings", project_dir)


@pytest.mark.parametrize("scenario_name,params", CSV_TEMPLATE_SCENARIOS)
def test_agent_generate_csv_template(
    project_dir: Path,
    agent_runner: AgentRunner,
    scenario_name: str,
    params: dict[str, object],
) -> None:
    """Agent can generate CSV templates with requested characteristics."""

    filename = f"CSVs/generated_{scenario_name}.csv"
    base_prompt = (
        f"Use the generate_csv_template tool to create '{filename}' "
        f"with {params['transfers']} transfers from {params['source_labware']} to {params['dest_labware']} "
        f"and a default volume of {params.get('default_volume', 0)}."
    )
    if "source_height" in params:
        base_prompt += f" Set the source height to {params['source_height']}."

    result = agent_runner.run(base_prompt)
    Assertions.assert_no_errors(result)

    csv_path = project_dir / filename
    Assertions.assert_file_exists(csv_path)
    content = csv_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(content) == params["transfers"] + 1  # header + rows


@pytest.mark.parametrize("scenario_name,labware_def", LABWARE_SCENARIOS)
def test_agent_add_labware_definition(
    tmp_path: Path,
    project_setup: ProjectSetup,
    agent_factory: Callable[..., AgentRunner],
    scenario_name: str,
    labware_def: dict[str, object],
) -> None:
    """Agent can register custom labware definitions in labware_dict.toml."""

    project_dir = project_setup.create_standard_project(tmp_path)
    runner = agent_factory(project_dir)

    prompt = (
        "Use the add_labware_definition tool with the following parameters:\n"
        f"labware_id: {labware_def['labware_id']}\n"
        f"category: {labware_def['category']}\n"
        f"well_count: {labware_def['well_count']}\n"
        f"well_volume: {labware_def['well_volume']}\n"
    )
    if "offset_x" in labware_def:
        prompt += (
            f"offset_x: {labware_def['offset_x']}\n"
            f"offset_y: {labware_def['offset_y']}\n"
            f"offset_z: {labware_def['offset_z']}\n"
        )

    result = runner.run(prompt)
    Assertions.assert_no_errors(result)
    Assertions.assert_file_contains(
        project_dir / "labware_dict.toml",
        str(labware_def["labware_id"]),
    )


def test_agent_validate_configuration_success(
    project_with_csv: Path, agent_factory: Callable[..., AgentRunner]
) -> None:
    """Agent validates a correct configuration without errors."""

    runner = agent_factory(project_with_csv)
    query = (
        "Use the validate_configuration tool to validate the configuration for 'CSVs/test.csv'."
    )
    result = runner.run(query)
    Assertions.assert_no_errors(result)
    assert any(keyword in result.lower() for keyword in ("ok", "valid", "success"))


@pytest.mark.parametrize("scenario_name,bad_config,expected_error", VALIDATION_ERROR_SCENARIOS)
def test_agent_validate_configuration_errors(
    tmp_path: Path,
    project_setup: ProjectSetup,
    agent_factory: Callable[..., AgentRunner],
    scenario_name: str,
    bad_config: dict[str, object],
    expected_error: str,
) -> None:
    """Agent surfaces validation errors for incorrect configurations."""

    project_dir = project_setup.create_standard_project(tmp_path)
    runner = agent_factory(project_dir)

    csv_path = bad_config.get("csv_path")
    if csv_path:
        target = project_dir / csv_path
        if target.exists():
            target.unlink()

    query = "Use the validate_configuration tool to validate the configuration."
    result = runner.run(query)
    lower = result.lower()
    assert "not found" in lower
    assert "csv" in lower



def test_agent_initialize_project(
    empty_project_dir: Path, agent_factory: Callable[..., AgentRunner]
) -> None:
    """Agent can initialize a new project structure from scratch."""

    runner = agent_factory(empty_project_dir)
    query = "Use the initialize_project tool to set up a new OT2 project."
    result = runner.run(query)

    Assertions.assert_no_errors(result)
    Assertions.assert_file_exists(empty_project_dir / "settings.toml")
    Assertions.assert_file_exists(empty_project_dir / "labware_dict.toml")
    Assertions.assert_file_exists(empty_project_dir / "CherryPick_OT2.py")
    assert (empty_project_dir / "CSVs").exists()
    assert (empty_project_dir / "logs").exists()

    _print_project_snapshot("initialize_project", empty_project_dir)



@pytest.mark.parametrize("preset_name,expected_changes", LIQUID_PRESET_SCENARIOS)
def test_agent_apply_liquid_preset(
    project_dir: Path,
    agent_runner: AgentRunner,
    preset_name: str,
    expected_changes: dict,
) -> None:
    """Agent applies liquid handling presets and modifies settings.toml accordingly."""

    query = f"Use the apply_liquid_preset tool to apply the '{preset_name}' preset."
    result = agent_runner.run(query)

    Assertions.assert_no_errors(result)
    for path, value in expected_changes.items():
        full_path = f"settings.liquid_handling.{path}"
        Assertions.assert_toml_value(project_dir / "settings.toml", full_path, value)

    _print_project_snapshot("apply_liquid_preset", project_dir)



def test_agent_deploy_to_opentrons(
    project_with_protocol: Path, tmp_path: Path, agent_factory: Callable[..., AgentRunner]
) -> None:
    """Agent deploys protocol to specified target directory."""

    runner = agent_factory(project_with_protocol)
    target_dir = tmp_path / "deployment_target"
    target_dir.mkdir()

    query = f"Use the deploy tool to copy the protocol to '{target_dir}'."
    result = runner.run(query)

    Assertions.assert_no_errors(result)
    deployed_files = list(target_dir.glob("*.py"))
    assert len(deployed_files) == 1
    assert "CherryPick_OT2" in deployed_files[0].name

    _print_project_snapshot("deploy_to_opentrons", project_with_protocol)
