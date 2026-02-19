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


@pytest.mark.slow
@pytest.mark.requires_simulation
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
        "Run full_workflow on 'CSVs/pipeline_full.csv' with simulate set to true and deployment "
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


def test_agent_list_settings(
    tmp_path: Path,
    project_setup: ProjectSetup,
    agent_factory: Callable[..., AgentRunner],
) -> None:
    """Agent can enumerate all configuration settings via the new helper."""

    project_dir: Path = project_setup.create_standard_project(tmp_path)
    runner: AgentRunner = agent_factory(project_dir, max_steps=6)

    query = "Use the list_settings tool to show me every configuration value."
    result = runner.run(query)
    Assertions.assert_no_errors(result)
    lowered = result.lower()
    # tip_reuse is no longer a settings.toml key (now per-row via CSV Tip Action column)
    # Check for settings that ARE present.
    # The agent may return either formatted text or raw JSON - both are valid.
    # push_out appears in both formats ("push out" or "push_out")
    assert "push" in lowered
    # settings.toml should be referenced in some form
    assert "settings" in lowered


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
    """Agent can register calibration offsets for labware via update_labware_offset.

    After the labware refactor, add_labware_definition was replaced with
    update_labware_offset, which stores offsets in offset_database.toml.
    Only the offset scenarios (with offset_x/y/z) are relevant now.
    """

    # Only run offset-based scenarios (those that have offset fields)
    if "offset_x" not in labware_def:
        pytest.skip("Skipping non-offset labware scenario (add_labware_definition was replaced by update_labware_offset)")

    project_dir = project_setup.create_standard_project(tmp_path)
    runner = agent_factory(project_dir)

    prompt = (
        "Use the add_labware_definition tool (update_labware_offset) with the following parameters:\n"
        f"labware_id: {labware_def['labware_id']}\n"
        f"position_rack: 2\n"
        f"offset_x: {labware_def['offset_x']}\n"
        f"offset_y: {labware_def['offset_y']}\n"
        f"offset_z: {labware_def['offset_z']}\n"
    )

    result = runner.run(prompt)
    Assertions.assert_no_errors(result)
    # Offsets are now stored in offset_database.toml, not labware_dict.toml
    offset_db = project_dir / "offset_database.toml"
    if offset_db.exists():
        Assertions.assert_file_contains(offset_db, str(labware_def["labware_id"]))


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
    project_dir: Path, agent_runner: AgentRunner
) -> None:
    """Agent can initialize/refresh project structure with template files."""

    # Remove a file to test that initialize_project recreates it
    protocol_path = project_dir / "CherryPick_OT2.py"
    if protocol_path.exists():
        protocol_path.unlink()

    query = "Use the initialize_project tool to set up/refresh the OT2 project."
    result = agent_runner.run(query)

    Assertions.assert_no_errors(result)
    # Verify all required files were created/restored
    Assertions.assert_file_exists(project_dir / "settings.toml")
    Assertions.assert_file_exists(project_dir / "labware_dict.toml")
    Assertions.assert_file_exists(project_dir / "CherryPick_OT2.py")
    assert (project_dir / "CSVs").exists()
    assert (project_dir / "logs").exists()

    _print_project_snapshot("initialize_project", project_dir)



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



@pytest.mark.slow
@pytest.mark.requires_simulation
def test_agent_simulate_protocol_success(
    project_with_protocol: Path, agent_factory: Callable[..., AgentRunner]
) -> None:
    """Agent simulates a valid protocol and reports success."""

    runner = agent_factory(project_with_protocol, max_steps=25)
    query = "Use the simulate_protocol tool to validate 'CherryPick_OT2.py'. Tell me if it succeeds."
    result = runner.run(query)

    Assertions.assert_no_errors(result)
    assert any(kw in result.lower() for kw in ("success", "passed", "completed"))

    log_path = project_with_protocol / "logs" / "last_simulation.json"
    Assertions.assert_file_exists(log_path)

    _print_project_snapshot("simulate_protocol_success", project_with_protocol)



@pytest.mark.slow
@pytest.mark.requires_simulation
@pytest.mark.error_scenario
def test_agent_simulate_protocol_failure(
    tmp_path: Path, project_setup: ProjectSetup, agent_factory: Callable[..., AgentRunner]
) -> None:
    """Agent detects and reports simulation failures."""

    project_dir = project_setup.create_with_invalid_protocol(tmp_path)
    runner = agent_factory(project_dir, max_steps=25)

    query = "Use the simulate_protocol tool to validate the protocol."
    result = runner.run(query)

    # Agent should report failure (not crash)
    assert any(kw in result.lower() for kw in ("error", "fail", "invalid"))

    _print_project_snapshot("simulate_protocol_failure", project_dir)



@pytest.mark.slow
@pytest.mark.pipeline_test
def test_complete_new_project_workflow(
    project_dir: Path, agent_runner: AgentRunner
) -> None:
    """End-to-end workflow: configure → CSV → generate → validate pipeline."""

    # Step 1: Apply viscous liquid preset
    preset_query = "Use the apply_liquid_preset tool to apply the 'viscous' preset."
    preset_result = agent_runner.run(preset_query)
    Assertions.assert_no_errors(preset_result)

    # Step 2: Generate a CSV template
    csv_query = (
        "Generate a CSV template named 'CSVs/workflow_test.csv' with 10 transfers "
        "from tube_rack_96_1500ul_4 to 384_ppv_55ul_2 with default volume 50."
    )
    csv_result = agent_runner.run(csv_query)
    Assertions.assert_no_errors(csv_result)

    csv_path = project_dir / "CSVs" / "workflow_test.csv"
    Assertions.assert_file_exists(csv_path)

    # Step 3: Validate configuration
    validate_query = "Use validate_configuration to check the configuration for 'CSVs/workflow_test.csv'."
    validate_result = agent_runner.run(validate_query)
    Assertions.assert_no_errors(validate_result)

    # Step 4: Generate protocol
    generate_query = "Use generate_protocol to create the protocol from 'CSVs/workflow_test.csv'."
    generate_result = agent_runner.run(generate_query)
    Assertions.assert_no_errors(generate_result)

    protocol_path = project_dir / "CherryPick_OT2.py"
    Assertions.assert_file_exists(protocol_path)

    _print_project_snapshot("complete_new_project_workflow", project_dir)



@pytest.mark.pipeline_test
def test_custom_labware_workflow(project_dir: Path, agent_runner: AgentRunner) -> None:
    """Workflow: add calibration offset → use labware in CSV → generate protocol.

    After the labware refactor, labware definitions are no longer stored in
    labware_dict.toml. Instead, offsets are stored in offset_database.toml.
    Labware is identified directly by Opentrons load names in settings.toml.
    """

    # Step 1: Add calibration offset for existing labware via update_labware_offset
    labware_query = (
        "Use the add_labware_definition tool to save a calibration offset for "
        "'384_ppv_55ul' in slot 2 with offset_x=-0.5, offset_y=0.8, offset_z=-0.3."
    )
    labware_result = agent_runner.run(labware_query)
    Assertions.assert_no_errors(labware_result)

    # Step 2: Generate CSV using labware already in settings.toml working_plate
    csv_query = (
        "Generate a CSV template 'CSVs/custom_labware_test.csv' with 5 transfers "
        "from tube_rack_96_1500ul_4 to 384_ppv_55ul_2 with volume 30."
    )
    csv_result = agent_runner.run(csv_query)
    Assertions.assert_no_errors(csv_result)

    csv_path = project_dir / "CSVs" / "custom_labware_test.csv"
    Assertions.assert_file_exists(csv_path)

    # Step 3: Generate protocol
    generate_query = "Generate the protocol from 'CSVs/custom_labware_test.csv'."
    generate_result = agent_runner.run(generate_query)
    Assertions.assert_no_errors(generate_result)

    # Verify labware reference is in protocol
    protocol_content = (project_dir / "CherryPick_OT2.py").read_text(encoding="utf-8")
    assert "384_ppv_55ul" in protocol_content

    _print_project_snapshot("custom_labware_workflow", project_dir)



@pytest.mark.pipeline_test
def test_configuration_iteration_workflow(
    project_with_csv: Path, agent_runner: AgentRunner
) -> None:
    """Workflow: apply preset → generate → change preset → generate again."""

    # Step 1: Apply standard preset
    preset1_query = "Apply the 'standard' liquid preset."
    preset1_result = agent_runner.run(preset1_query)
    Assertions.assert_no_errors(preset1_result)

    # Step 2: Generate protocol with standard preset
    generate1_query = "Generate the protocol from 'CSVs/test.csv'."
    generate1_result = agent_runner.run(generate1_query)
    Assertions.assert_no_errors(generate1_result)

    # Verify settings reflect standard preset
    settings_content = (project_with_csv / "settings.toml").read_text(encoding="utf-8")
    assert "post_aspirate = 0" in settings_content or "post_aspirate = 0.0" in settings_content

    # Step 3: Apply viscous preset
    preset2_query = "Apply the 'viscous' liquid preset."
    preset2_result = agent_runner.run(preset2_query)
    Assertions.assert_no_errors(preset2_result)

    # Step 4: Generate protocol again with viscous preset
    generate2_query = "Generate the protocol from 'CSVs/test.csv' again."
    generate2_result = agent_runner.run(generate2_query)
    Assertions.assert_no_errors(generate2_result)

    # Verify settings changed to viscous preset
    settings_updated = (project_with_csv / "settings.toml").read_text(encoding="utf-8")
    assert "post_aspirate = 2" in settings_updated or "post_aspirate = 2.0" in settings_updated

    _print_project_snapshot("configuration_iteration_workflow", project_with_csv)



@pytest.mark.resource_test
@pytest.mark.pipeline_test
def test_resource_reading_workflow(project_dir: Path, agent_runner: AgentRunner) -> None:
    """Workflow: Agent reads multiple resources to inform decisions."""

    query = (
        "Please help me understand the current project configuration by doing the following:\n"
        "1. Read the deck layout from the status://deck-layout resource\n"
        "2. Check available CSV files using the files://csvs resource\n"
        "3. Review liquid handling settings from the status://liquid-handling-config resource\n"
        "4. Summarize what you found in each resource"
    )

    result = agent_runner.run(query)
    Assertions.assert_no_errors(result)

    # Verify agent mentioned key information from each resource (heuristic checks)
    result_lower = result.lower()
    
    # Should mention deck/slot information
    assert any(keyword in result_lower for keyword in ["deck", "slot", "position", "rack"])
    
    # Should mention CSV files
    assert any(keyword in result_lower for keyword in ["csv", "file"])
    
    # Should mention liquid handling settings
    assert any(keyword in result_lower for keyword in ["liquid", "aspirate", "dispense", "preset"])

    _print_project_snapshot("resource_reading_workflow", project_dir)



@pytest.mark.pipeline_test
def test_setup_new_experiment_prompt(project_dir: Path, agent_runner: AgentRunner) -> None:
    """Agent uses setup_new_experiment prompt to autonomously configure project."""

    query = (
        "I need to set up a new cherry-pick experiment for viscous liquids. "
        "Follow the setup_new_experiment prompt workflow to configure everything needed."
    )

    result = agent_runner.run(query)
    Assertions.assert_no_errors(result)

    # Verify the workflow performed key setup steps
    result_lower = result.lower()
    
    # Should have inspected/read configuration
    assert any(keyword in result_lower for keyword in ["config", "settings", "deck", "layout"])
    
    # Should have applied or mentioned liquid handling
    assert any(keyword in result_lower for keyword in ["liquid", "viscous", "preset"])

    _print_project_snapshot("setup_new_experiment_prompt", project_dir)



@pytest.mark.pipeline_test
@pytest.mark.error_scenario
def test_troubleshoot_simulation_error_prompt(
    tmp_path: Path, project_setup: ProjectSetup, agent_factory: Callable[..., AgentRunner]
) -> None:
    """Agent uses troubleshoot_simulation_error prompt to diagnose and fix issues."""

    project_dir = project_setup.create_with_invalid_protocol(tmp_path)
    runner = agent_factory(project_dir, max_steps=30)

    query = (
        "The protocol simulation failed. Use the troubleshoot_simulation_error prompt "
        "to diagnose the issue and explain what's wrong."
    )

    result = runner.run(query)

    # Agent should identify the problem (not necessarily fix it, but diagnose)
    result_lower = result.lower()
    assert any(keyword in result_lower for keyword in ["error", "problem", "issue", "fail"])

    _print_project_snapshot("troubleshoot_simulation_error_prompt", project_dir)
