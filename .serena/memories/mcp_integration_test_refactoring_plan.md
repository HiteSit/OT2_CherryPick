# MCP Integration Test Refactoring and Expansion Plan

## Context and Current State

### Existing Test Landscape
The project has **two types of tests**:

1. **Unit tests** (53+ tests across 13 files): Test individual Python functions directly
   - `test_config_tools.py`, `test_csv_tools.py`, `test_deployment_tools.py`, etc.
   - These test internal logic WITHOUT the MCP layer
   - These are GOOD and should remain unchanged

2. **Agent-driven end-to-end tests** (9 test cases in 1 file): Test MCP tools via AI agent
   - `test_mcp_integration.py` - Uses mcp-use + Mistral LLM to invoke tools
   - Tests the full stack: agent → MCP protocol → tool execution → result
   - Currently has only 9 test cases covering ~3 of 9 tool categories

**This refactoring focuses EXCLUSIVELY on expanding test_mcp_integration.py** - the agent-driven end-to-end tests.

### Current test_mcp_integration.py Coverage

**What EXISTS (9 test cases):**
- `test_agent_lists_tools` - Basic connectivity check
- `test_agent_runs_workflow_from_string` - CSV upload + generate_protocol
- `test_agent_full_pipeline_updates_protocol` - Multi-step workflow (simulate=false, deploy=false)
- `test_agent_updates_settings[...]` - 5 parametrized scenarios testing update_settings tool

**Critical GAPS:**
- ❌ initialize_project tool (never tested by agent)
- ❌ apply_liquid_preset tool (never tested by agent)
- ❌ generate_csv_template tool (never tested by agent)
- ❌ add_labware_definition tool (never tested by agent)
- ❌ validate_configuration tool (never tested by agent)
- ❌ simulate_protocol tool (explicitly DISABLED in all tests!)
- ❌ deploy_to_opentrons tool (never tested by agent)
- ❌ No resource reading by agents (config://, status://, files://, logs://)
- ❌ No prompt-driven workflows (setup_new_experiment, troubleshoot_simulation_error)
- ❌ No error scenario testing (validation failures, simulation errors)

---

## Refactoring Philosophy

### Two-Tier Architecture

**Tier 1: Tool Enumeration Tests** (Horizontal Coverage)
- Each of 9 MCP tools gets parametrized test function(s)
- Each tool tested with multiple realistic scenarios
- Focus: "Does this tool work correctly when invoked by an agent?"
- Pattern: Single tool call → verify outcome

**Tier 2: Pipeline Integration Tests** (Vertical Coverage)
- Multi-step workflows chaining 3-7 tools together
- Tests inter-tool dependencies and state propagation
- Focus: "Do these tools work together in realistic user workflows?"
- Pattern: Manual chain of tool calls → verify end state

### Key Principles
1. **All tests use mcp-use + Mistral LLM** - No direct function calls
2. **Fixtures reduce duplication** - Shared setup via pytest fixtures
3. **Parametrization for scenarios** - One test function, many cases
4. **Helper classes for clarity** - ProjectSetup, AgentRunner, Assertions, TestData
5. **Incremental testing** - Test after each implementation phase
6. **Pytest markers for filtering** - Run subsets selectively

---

## Implementation Plan: 10 Phases

### Phase 0: Baseline Exploration and Test Current State ✓

**Goal:** Understand current codebase, establish baseline

**Actions:**
1. List all test files and count test functions
2. Identify which tests are unit vs agent-driven
3. Run current agent tests to establish baseline

**Commands:**
```bash
# List test files
ls -la tests/

# Count test functions per file
find tests -name "test_*.py" -exec sh -c 'echo "=== {} ==="; grep -c "^def test_" {} || echo 0' \;

# Run current integration tests to establish baseline
pixi run pytest tests/test_mcp_integration.py -v

# Check current coverage
pixi run pytest tests/test_mcp_integration.py -v --cov=src/ot2_cherrypick_mcp --cov-report=term-missing
```

**Expected Result:** 
- 9 test cases pass (4 base + 5 parametrized)
- Understand test execution time (~2-5 min per test with LLM calls)

**Status:** ✓ Completed

---

### Phase 1: Foundation Fixtures Extraction

**Goal:** Extract and reorganize fixtures from existing test_mcp_integration.py

**Actions:**

1. **Create `tests/conftest.py`** with shared fixtures
2. **Extract existing helpers** from test_mcp_integration.py:
   - `_setup_project_dir()` → fixture `project_dir(tmp_path)`
   - `_build_config()` → fixture `mcp_config(project_dir)`
   - `_run_agent()` → fixture `agent_runner(mcp_config)`

3. **Add new Level 0 fixtures:**
   ```python
   @pytest.fixture
   def project_dir(tmp_path: Path) -> Path:
       """Create basic project structure with required files."""
       
   @pytest.fixture
   def mcp_config(project_dir: Path) -> Dict[str, Any]:
       """Build MCP client configuration."""
       
   @pytest.fixture
   def mcp_client(mcp_config: Dict[str, Any]) -> MCPClient:
       """Initialize MCP client."""
       
   @pytest.fixture
   def llm() -> ChatMistralAI:
       """Create LLM instance (potentially cached)."""
       
   @pytest.fixture
   def agent(mcp_client: MCPClient, llm: ChatMistralAI) -> MCPAgent:
       """Create configured agent."""
       
   @pytest.fixture
   def agent_runner(agent: MCPAgent) -> AgentRunner:
       """Helper for running agent queries."""
   ```

4. **Add Level 1 specialized fixtures:**
   ```python
   @pytest.fixture
   def empty_project_dir(tmp_path: Path) -> Path:
       """Empty directory for initialize_project tests."""
       
   @pytest.fixture
   def project_with_csv(project_dir: Path) -> Path:
       """Project + example CSV file."""
       
   @pytest.fixture
   def project_with_protocol(project_dir: Path) -> Path:
       """Project + generated protocol file."""
   ```

**Test After Implementation:**
```bash
# Verify fixtures work
pixi run pytest tests/test_mcp_integration.py::test_agent_lists_tools -v

# Should still pass with refactored fixtures
```

**Files Modified:**
- Create: `tests/conftest.py`
- Modify: `tests/test_mcp_integration.py` (use new fixtures)

**Expected Result:** Same 9 tests pass, code is cleaner

---

### Phase 2: Helper Classes Implementation

**Goal:** Create reusable helper classes for test clarity

**Actions:**

1. **Add to `tests/conftest.py`** or separate `tests/helpers.py`:

   ```python
   class ProjectSetup:
       """Helper for creating project directories with different configurations."""
       
       @staticmethod
       def create_minimal(tmp_path: Path) -> Path:
           """Only settings.toml, labware_dict.toml, empty CSVs/, logs/"""
           
       @staticmethod
       def create_with_csv(tmp_path: Path, csv_content: str, filename: str = "test.csv") -> Path:
           """Project + specific CSV file"""
           
       @staticmethod
       def create_with_custom_labware(tmp_path: Path, labware_def: dict) -> Path:
           """Project + custom labware in labware_dict.toml"""
           
       @staticmethod
       def create_with_protocol(tmp_path: Path) -> Path:
           """Project + generated CherryPick_OT2.py"""
           
       @staticmethod
       def create_with_simulation_logs(tmp_path: Path, success: bool = True) -> Path:
           """Project + simulation log file"""
   
   
   class AgentRunner:
       """Helper for executing agent queries and chains."""
       
       def __init__(self, agent: MCPAgent):
           self.agent = agent
           
       async def run_query(self, query: str, max_steps: int = 20) -> str:
           """Execute single query."""
           
       async def run_query_chain(self, queries: List[str]) -> List[str]:
           """Execute multiple queries sequentially."""
           
       async def run_with_resource_check(self, query: str, expected_resource: str) -> tuple[str, bool]:
           """Run query and check if agent read specific resource."""
   
   
   class Assertions:
       """Reusable assertion helpers."""
       
       @staticmethod
       def assert_no_errors(result: str):
           """Check agent result has no error messages."""
           
       @staticmethod
       def assert_file_exists(path: Path, message: str = ""):
           """Check file exists with helpful message."""
           
       @staticmethod
       def assert_file_contains(path: Path, content: str):
           """Check file contains specific text."""
           
       @staticmethod
       def assert_toml_value(path: Path, dotted_path: str, expected: Any):
           """Parse TOML and check specific value."""
           
       @staticmethod
       def assert_json_embedded(protocol_path: Path, json_str: str):
           """Check JSON is embedded in protocol's get_values()."""
           
       @staticmethod
       def assert_simulation_success(log_path: Path):
           """Parse simulation log and verify success."""
           
       @staticmethod
       def assert_resource_was_read(agent_output: str, resource_uri: str) -> bool:
           """Heuristic check if agent likely read a resource."""
   ```

2. **Update existing tests** to use helper classes

**Test After Implementation:**
```bash
# Run all existing tests with new helpers
pixi run pytest tests/test_mcp_integration.py -v

# Should still pass, now using helper classes
```

**Files Modified:**
- Create: `tests/helpers.py` (or add to conftest.py)
- Modify: `tests/test_mcp_integration.py` (use helper classes)

**Expected Result:** Same 9 tests pass, much cleaner code

---

### Phase 3: Test Data Extraction to test_data.py

**Goal:** Centralize test data for reusability

**Actions:**

1. **Create `tests/test_data.py`:**

   ```python
   """Centralized test data for agent-driven integration tests."""
   
   # CSV test data
   CSV_BASIC = """Source Labware,Source Well,Volume (ul),Dest Labware,Dest Well,Source Height,Dest Top
   tube_rack_96_1500ul_4,A1,100,384_ppv_55ul_2,B1,2,-5
   tube_rack_96_1500ul_4,A2,50,384_ppv_55ul_2,B2,2,-5"""
   
   CSV_WITH_MIXING = """..."""
   
   CSV_WITH_AIR_GAP = """..."""
   
   # Liquid preset scenarios
   LIQUID_PRESET_SCENARIOS = [
       ("standard", {"post_aspirate": 0, "push_out.volume_ul": 5}),
       ("viscous", {"post_aspirate": 2.5, "push_out.volume_ul": 8}),
       ("slippery", {"head_speed.speed": 250}),
       ("minimal", {"pre_aspirate_contact.enabled": False}),
       ("aggressive", {"pre_aspirate_contact.enabled": True}),
   ]
   
   # Update settings scenarios (expand existing)
   UPDATE_SETTINGS_SCENARIOS = [
       # Existing 5 scenarios
       ("settings.general.tip_reuse", "never", 'tip_reuse = "never"', "..."),
       # ... existing ones ...
       
       # NEW scenarios
       ("settings.liquid_handling.pre_aspirate_contact.enabled", "true", "enabled = true", "..."),
       ("settings.liquid_handling.post_aspirate_wick.radius", "2", "radius = 2", "..."),
   ]
   
   # CSV template generation scenarios
   CSV_TEMPLATE_SCENARIOS = [
       ("basic", {"transfers": 10, "source": "tube_rack_96_1500ul_4", "dest": "384_ppv_55ul_2"}),
       ("large", {"transfers": 96, "source": "tube_rack_96_1500ul_4", "dest": "384_ppv_55ul_2"}),
       ("with_source_height", {...}),
   ]
   
   # Labware definition scenarios
   LABWARE_SCENARIOS = [
       ("basic_plate", {"labware_id": "test_96_plate", "category": "plate", "well_count": 96, "well_volume": 200}),
       ("with_offsets", {"labware_id": "test_384_plate", "category": "plate", "well_count": 384, "well_volume": 50, 
                         "offset_x": -0.5, "offset_y": 0.8, "offset_z": -0.3}),
   ]
   
   # Validation error scenarios (for error testing)
   VALIDATION_ERROR_SCENARIOS = [
       ("missing_csv", {"csv_path": "nonexistent.csv"}, "CSV transfer map not found"),
       ("invalid_labware", {"csv_content": "..."}, "not defined in labware_dict.toml"),
       ("slot_conflict", {"working_plate": [...]}, "duplicate slot"),
   ]
   ```

2. **Import in test_mcp_integration.py:**
   ```python
   from .test_data import (
       CSV_BASIC, LIQUID_PRESET_SCENARIOS, UPDATE_SETTINGS_SCENARIOS,
       CSV_TEMPLATE_SCENARIOS, LABWARE_SCENARIOS, VALIDATION_ERROR_SCENARIOS
   )
   ```

**Test After Implementation:**
```bash
# Verify import works and tests still pass
pixi run pytest tests/test_mcp_integration.py -v
```

**Files Modified:**
- Create: `tests/test_data.py`
- Modify: `tests/test_mcp_integration.py` (import and use test_data)

**Expected Result:** Same 9 tests pass, data is centralized

---

### Phase 4: Refactor Existing Tool Tests

**Goal:** Improve existing tests before adding new ones

**Actions:**

1. **Refactor `test_agent_updates_settings`:**
   - Use `UPDATE_SETTINGS_SCENARIOS` from test_data.py
   - Use `Assertions.assert_toml_value()` helper
   - Use `AgentRunner` helper

2. **Refactor `test_agent_full_pipeline_updates_protocol`:**
   - Break into smaller verification steps
   - Add explicit assertions for each step
   - Use helper classes

3. **Refactor `test_agent_runs_workflow_from_string`:**
   - Use `CSV_BASIC` from test_data.py
   - Use helper assertions

**Test After Implementation:**
```bash
# Run refactored tests
pixi run pytest tests/test_mcp_integration.py::test_agent_updates_settings -v
pixi run pytest tests/test_mcp_integration.py::test_agent_full_pipeline_updates_protocol -v
pixi run pytest tests/test_mcp_integration.py::test_agent_runs_workflow_from_string -v

# All should still pass
```

**Files Modified:**
- Modify: `tests/test_mcp_integration.py` (refactor 3 existing test functions)

**Expected Result:** Same 9 tests pass, code is cleaner and uses helpers

---

### Phase 5: Add Missing Tool Tests (Part 1: No Simulation)

**Goal:** Add agent tests for 6 missing tools that don't require simulation

**Actions:**

Add these new test functions to `tests/test_mcp_integration.py`:

1. **Test initialize_project:**
   ```python
   def test_agent_initialize_project(empty_project_dir: Path, agent_runner: AgentRunner):
       """Agent can initialize a new project structure."""
       query = "Initialize a new OT2 project using the initialize_project tool"
       result = await agent_runner.run_query(query)
       
       Assertions.assert_no_errors(result)
       Assertions.assert_file_exists(empty_project_dir / "settings.toml")
       Assertions.assert_file_exists(empty_project_dir / "labware_dict.toml")
       Assertions.assert_file_exists(empty_project_dir / "CherryPick_OT2.py")
       assert (empty_project_dir / "CSVs").exists()
       assert (empty_project_dir / "logs").exists()
   ```

2. **Test apply_liquid_preset:**
   ```python
   @pytest.mark.parametrize("preset_name,expected_changes", LIQUID_PRESET_SCENARIOS)
   def test_agent_apply_liquid_preset(
       project_dir: Path, agent_runner: AgentRunner, 
       preset_name: str, expected_changes: dict
   ):
       """Agent can apply liquid handling presets."""
       query = f"Use apply_liquid_preset to set the preset to '{preset_name}'"
       result = await agent_runner.run_query(query)
       
       Assertions.assert_no_errors(result)
       for path, value in expected_changes.items():
           Assertions.assert_toml_value(project_dir / "settings.toml", f"settings.liquid_handling.{path}", value)
   ```

3. **Test generate_csv_template:**
   ```python
   @pytest.mark.parametrize("scenario_name,params", CSV_TEMPLATE_SCENARIOS)
   def test_agent_generate_csv_template(
       project_dir: Path, agent_runner: AgentRunner,
       scenario_name: str, params: dict
   ):
       """Agent can generate CSV templates with various parameters."""
       query = f"Use generate_csv_template to create 'test_{scenario_name}.csv' with {params['transfers']} transfers..."
       result = await agent_runner.run_query(query)
       
       Assertions.assert_no_errors(result)
       csv_path = project_dir / "CSVs" / f"test_{scenario_name}.csv"
       Assertions.assert_file_exists(csv_path)
       # Verify CSV structure
       content = csv_path.read_text()
       assert "Source Labware" in content
       assert len(content.splitlines()) == params['transfers'] + 1  # +1 for header
   ```

4. **Test add_labware_definition:**
   ```python
   @pytest.mark.parametrize("scenario_name,labware_def", LABWARE_SCENARIOS)
   def test_agent_add_labware_definition(
       project_dir: Path, agent_runner: AgentRunner,
       scenario_name: str, labware_def: dict
   ):
       """Agent can add custom labware definitions."""
       query = f"Use add_labware_definition to add labware with ID '{labware_def['labware_id']}'..."
       result = await agent_runner.run_query(query)
       
       Assertions.assert_no_errors(result)
       # Verify labware added to labware_dict.toml
       labware_content = (project_dir / "labware_dict.toml").read_text()
       assert labware_def['labware_id'] in labware_content
   ```

5. **Test validate_configuration (success case):**
   ```python
   def test_agent_validate_configuration_success(project_with_csv: Path, agent_runner: AgentRunner):
       """Agent can validate a correct configuration."""
       query = "Use validate_configuration to check the configuration for 'CSVs/test.csv'"
       result = await agent_runner.run_query(query)
       
       Assertions.assert_no_errors(result)
       assert "valid" in result.lower() or "success" in result.lower()
   ```

6. **Test validate_configuration (error cases):**
   ```python
   @pytest.mark.parametrize("scenario_name,bad_config,expected_error", VALIDATION_ERROR_SCENARIOS)
   def test_agent_validate_configuration_errors(
       tmp_path: Path, agent_runner: AgentRunner,
       scenario_name: str, bad_config: dict, expected_error: str
   ):
       """Agent detects validation errors in bad configurations."""
       # Setup project with intentional error
       project_dir = ProjectSetup.create_with_error(tmp_path, bad_config)
       
       query = "Use validate_configuration to check the configuration"
       result = await agent_runner.run_query(query)
       
       # Should report error (not crash)
       assert "error" in result.lower() or "invalid" in result.lower()
       assert expected_error.lower() in result.lower()
   ```

7. **Test deploy_to_opentrons:**
   ```python
   def test_agent_deploy_to_opentrons(project_with_protocol: Path, tmp_path: Path, agent_runner: AgentRunner):
       """Agent can deploy protocol to target directory."""
       target_dir = tmp_path / "deployment_target"
       target_dir.mkdir()
       
       query = f"Use deploy_to_opentrons to copy the protocol to '{target_dir}'"
       result = await agent_runner.run_query(query)
       
       Assertions.assert_no_errors(result)
       deployed_files = list(target_dir.glob("*.py"))
       assert len(deployed_files) == 1
       assert "CherryPick_OT2.py" in deployed_files[0].name
   ```

**Test After Implementation:**
```bash
# Test each new tool test individually as you add it
pixi run pytest tests/test_mcp_integration.py::test_agent_initialize_project -v
pixi run pytest tests/test_mcp_integration.py::test_agent_apply_liquid_preset -v
pixi run pytest tests/test_mcp_integration.py::test_agent_generate_csv_template -v
pixi run pytest tests/test_mcp_integration.py::test_agent_add_labware_definition -v
pixi run pytest tests/test_mcp_integration.py::test_agent_validate_configuration_success -v
pixi run pytest tests/test_mcp_integration.py::test_agent_validate_configuration_errors -v
pixi run pytest tests/test_mcp_integration.py::test_agent_deploy_to_opentrons -v

# Then run all new tests together
pixi run pytest tests/test_mcp_integration.py -k "initialize_project or apply_liquid_preset or generate_csv_template or add_labware or validate_configuration or deploy_to_opentrons" -v
```

**Files Modified:**
- Modify: `tests/test_mcp_integration.py` (add 7 new test functions)
- Modify: `tests/test_data.py` (add any new scenarios)

**Expected Result:** 
- 7 new test functions added
- With parametrization: ~15-20 additional test cases
- Total test cases: ~24-29

---

### Phase 6: Add Missing Tool Tests (Part 2: With Simulation)

**Goal:** Add tests for simulate_protocol tool (CURRENTLY DISABLED - CRITICAL!)

**Actions:**

1. **Test simulate_protocol (success case):**
   ```python
   @pytest.mark.slow
   @pytest.mark.requires_simulation
   def test_agent_simulate_protocol_success(project_with_protocol: Path, agent_runner: AgentRunner):
       """Agent can simulate a valid protocol and verify success."""
       query = "Use simulate_protocol to validate 'CherryPick_OT2.py' and tell me if it succeeds"
       result = await agent_runner.run_query(query)
       
       Assertions.assert_no_errors(result)
       assert "success" in result.lower() or "passed" in result.lower()
       
       # Verify simulation log created
       log_path = project_with_protocol / "logs" / "last_simulation.json"
       Assertions.assert_file_exists(log_path)
       Assertions.assert_simulation_success(log_path)
   ```

2. **Test simulate_protocol (failure case):**
   ```python
   @pytest.mark.slow
   @pytest.mark.requires_simulation
   @pytest.mark.error_scenario
   def test_agent_simulate_protocol_failure(tmp_path: Path, agent_runner: AgentRunner):
       """Agent detects simulation failures and reports errors."""
       # Create project with protocol that will fail simulation
       project_dir = ProjectSetup.create_with_invalid_protocol(tmp_path)
       
       query = "Use simulate_protocol to validate the protocol"
       result = await agent_runner.run_query(query)
       
       # Agent should report failure (not crash)
       assert "error" in result.lower() or "fail" in result.lower()
       
       # Log should exist with error details
       log_path = project_dir / "logs" / "last_simulation.json"
       Assertions.assert_file_exists(log_path)
   ```

3. **Update test_agent_full_pipeline_updates_protocol:**
   ```python
   def test_agent_full_pipeline_with_simulation(tmp_path: Path):
       """Complete workflow including simulation (ENABLED)."""
       # This is the REFACTORED version with simulate=True
       # Previously it was disabled with simulate=false
   ```

**Test After Implementation:**
```bash
# Test simulation tests individually
pixi run pytest tests/test_mcp_integration.py::test_agent_simulate_protocol_success -v
pixi run pytest tests/test_mcp_integration.py::test_agent_simulate_protocol_failure -v
pixi run pytest tests/test_mcp_integration.py::test_agent_full_pipeline_with_simulation -v

# Run all simulation tests
pixi run pytest tests/test_mcp_integration.py -m requires_simulation -v

# Run all tests EXCEPT slow simulation tests (for fast iteration)
pixi run pytest tests/test_mcp_integration.py -m "not slow" -v
```

**Files Modified:**
- Modify: `tests/test_mcp_integration.py` (add 3 simulation test functions)

**Expected Result:**
- 3 new simulation tests added
- Simulation is now ENABLED and tested
- Total test cases: ~27-32

---

### Phase 7: Pipeline Integration Tests

**Goal:** Add multi-step workflow tests that chain tools together

**Actions:**

Add these new pipeline test functions:

1. **Complete new project workflow:**
   ```python
   @pytest.mark.slow
   @pytest.mark.pipeline_test
   async def test_complete_new_project_workflow(empty_project_dir: Path, agent_runner: AgentRunner):
       """End-to-end: initialize → configure → generate → simulate → deploy."""
       
       queries = [
           "Initialize the project using initialize_project",
           "Apply the viscous liquid preset",
           "Generate a CSV template with 10 transfers from tube_rack_96_1500ul_4 to 384_ppv_55ul_2",
           "Generate the protocol from the CSV",
           "Validate the configuration",
           "Simulate the protocol",
           "Deploy the protocol to the deployment_target directory"
       ]
       
       results = await agent_runner.run_query_chain(queries)
       
       # Verify each step succeeded
       for i, result in enumerate(results):
           Assertions.assert_no_errors(result)
       
       # Verify final state
       Assertions.assert_file_exists(empty_project_dir / "CherryPick_OT2.py")
       Assertions.assert_simulation_success(empty_project_dir / "logs" / "last_simulation.json")
   ```

2. **Troubleshooting workflow:**
   ```python
   @pytest.mark.pipeline_test
   async def test_troubleshooting_workflow(tmp_path: Path, agent_runner: AgentRunner):
       """Workflow: detect error → fix → validate → succeed."""
       
       # Setup with intentional error
       project_dir = ProjectSetup.create_with_labware_mismatch(tmp_path)
       
       queries = [
           "Validate the configuration",  # Should fail
           "Read the validation errors and tell me what's wrong",
           "Fix the labware ID mismatch by updating the settings",
           "Validate the configuration again",  # Should pass
           "Generate and simulate the protocol"
       ]
       
       results = await agent_runner.run_query_chain(queries)
       
       # First validation should report error
       assert "error" in results[0].lower()
       # Last steps should succeed
       Assertions.assert_no_errors(results[-1])
   ```

3. **Custom labware workflow:**
   ```python
   @pytest.mark.pipeline_test
   async def test_custom_labware_workflow(project_dir: Path, agent_runner: AgentRunner):
       """Workflow: add labware → use in CSV → generate → simulate."""
       
       queries = [
           "Add a labware definition for 'custom_384_pcr' with 384 wells, 50µL volume, plate category",
           "Generate a CSV template using custom_384_pcr_2 as destination",
           "Generate the protocol from the CSV",
           "Simulate the protocol to verify custom labware works"
       ]
       
       results = await agent_runner.run_query_chain(queries)
       
       for result in results:
           Assertions.assert_no_errors(result)
       
       # Verify custom labware is in protocol
       protocol_content = (project_dir / "CherryPick_OT2.py").read_text()
       assert "custom_384_pcr" in protocol_content
   ```

4. **Configuration iteration workflow:**
   ```python
   @pytest.mark.pipeline_test
   async def test_configuration_iteration_workflow(project_with_csv: Path, agent_runner: AgentRunner):
       """Workflow: configure → simulate → adjust → simulate again."""
       
       queries = [
           "Apply the standard liquid preset",
           "Generate and simulate the protocol",
           "Read the simulation log",
           "Now apply the viscous preset",
           "Generate and simulate the protocol again"
       ]
       
       results = await agent_runner.run_query_chain(queries)
       
       for result in results:
           Assertions.assert_no_errors(result)
       
       # Verify settings changed
       settings_content = (project_with_csv / "settings.toml").read_text()
       assert "viscous" in settings_content or "2.5" in settings_content  # viscous preset value
   ```

5. **Resource reading workflow:**
   ```python
   @pytest.mark.resource_test
   @pytest.mark.pipeline_test
   async def test_resource_reading_workflow(project_dir: Path, agent_runner: AgentRunner):
       """Workflow: Agent reads resources to inform decisions."""
       
       query = (
           "Please do the following:\n"
           "1. Read the current deck layout from status://deck-layout\n"
           "2. Read available CSV files from files://csvs\n"
           "3. Read the liquid handling config from status://liquid-handling-config\n"
           "4. Tell me what you found in each resource"
       )
       
       result, resources_read = await agent_runner.run_with_resource_check(
           query, 
           expected_resources=["status://deck-layout", "files://csvs", "status://liquid-handling-config"]
       )
       
       Assertions.assert_no_errors(result)
       # Verify agent read the resources (heuristic check)
       assert any(r in result for r in ["deck", "layout", "slot"])
       assert any(r in result for r in ["csv", "files"])
       assert any(r in result for r in ["liquid", "aspirate", "dispense"])
   ```

**Test After Implementation:**
```bash
# Test each pipeline individually
pixi run pytest tests/test_mcp_integration.py::test_complete_new_project_workflow -v
pixi run pytest tests/test_mcp_integration.py::test_troubleshooting_workflow -v
pixi run pytest tests/test_mcp_integration.py::test_custom_labware_workflow -v
pixi run pytest tests/test_mcp_integration.py::test_configuration_iteration_workflow -v
pixi run pytest tests/test_mcp_integration.py::test_resource_reading_workflow -v

# Run all pipeline tests
pixi run pytest tests/test_mcp_integration.py -m pipeline_test -v
```

**Files Modified:**
- Modify: `tests/test_mcp_integration.py` (add 5 pipeline test functions)

**Expected Result:**
- 5 new pipeline tests added
- Total test cases: ~32-37

---

### Phase 8: Prompt-Driven Workflow Tests

**Goal:** Test the 2 registered prompts work correctly

**Actions:**

1. **Test setup_new_experiment prompt:**
   ```python
   @pytest.mark.pipeline_test
   async def test_setup_new_experiment_prompt(empty_project_dir: Path, agent: MCPAgent):
       """Agent uses setup_new_experiment prompt to autonomously configure."""
       
       # Invoke the prompt (how to do this with mcp-use?)
       query = (
           "Follow the setup_new_experiment prompt workflow to set up a new cherry-pick experiment "
           "for viscous liquids with 96-to-384 well transfers"
       )
       
       result = await agent.run(query)
       
       Assertions.assert_no_errors(result)
       # Verify project is fully configured
       Assertions.assert_file_exists(empty_project_dir / "settings.toml")
       Assertions.assert_file_exists(empty_project_dir / "CherryPick_OT2.py")
   ```

2. **Test troubleshoot_simulation_error prompt:**
   ```python
   @pytest.mark.pipeline_test
   @pytest.mark.error_scenario
   async def test_troubleshoot_simulation_error_prompt(tmp_path: Path, agent: MCPAgent):
       """Agent uses troubleshoot_simulation_error prompt to fix issues."""
       
       # Setup with simulation error
       project_dir = ProjectSetup.create_with_simulation_error(tmp_path)
       
       query = (
           "The protocol simulation failed. Use the troubleshoot_simulation_error prompt "
           "to diagnose and fix the issue"
       )
       
       result = await agent.run(query)
       
       # Agent should identify problem and propose/implement fix
       assert "error" in result.lower() or "problem" in result.lower()
       assert "fix" in result.lower() or "solution" in result.lower()
   ```

**Test After Implementation:**
```bash
# Test prompt-driven workflows
pixi run pytest tests/test_mcp_integration.py::test_setup_new_experiment_prompt -v
pixi run pytest tests/test_mcp_integration.py::test_troubleshoot_simulation_error_prompt -v
```

**Files Modified:**
- Modify: `tests/test_mcp_integration.py` (add 2 prompt test functions)

**Expected Result:**
- 2 new prompt tests added
- Total test cases: ~34-39

---

### Phase 9: Pytest Markers and Documentation

**Goal:** Add markers for selective test execution, document test structure

**Actions:**

1. **Add markers to tests:**
   ```python
   # In test_mcp_integration.py, add decorators:
   
   @pytest.mark.tool_test  # All tool enumeration tests
   @pytest.mark.pipeline_test  # All pipeline integration tests
   @pytest.mark.slow  # Tests taking >10 seconds
   @pytest.mark.requires_simulation  # Tests that run opentrons_simulate
   @pytest.mark.error_scenario  # Tests expecting failures
   @pytest.mark.resource_test  # Tests verifying resource reading
   ```

2. **Configure markers in `pyproject.toml` or `pytest.ini`:**
   ```toml
   [tool.pytest.ini_options]
   markers = [
       "tool_test: Tests for individual MCP tools",
       "pipeline_test: Multi-step workflow integration tests",
       "slow: Tests that take >10 seconds",
       "requires_simulation: Tests that run opentrons_simulate",
       "error_scenario: Tests that expect errors",
       "resource_test: Tests that verify resource reading"
   ]
   ```

3. **Create test documentation in `tests/README.md`:**
   ```markdown
   # MCP Integration Tests
   
   ## Overview
   Agent-driven end-to-end tests using mcp-use + Mistral LLM
   
   ## Test Categories
   - Tool Tests: Test individual MCP tools
   - Pipeline Tests: Multi-step workflows
   
   ## Running Tests
   
   # All integration tests
   pixi run pytest tests/test_mcp_integration.py -v
   
   # Only tool tests
   pixi run pytest tests/test_mcp_integration.py -m tool_test -v
   
   # Only pipeline tests
   pixi run pytest tests/test_mcp_integration.py -m pipeline_test -v
   
   # Fast tests only (no simulation)
   pixi run pytest tests/test_mcp_integration.py -m "not slow" -v
   
   # Simulation tests only
   pixi run pytest tests/test_mcp_integration.py -m requires_simulation -v
   ```

**Test After Implementation:**
```bash
# Verify markers work
pixi run pytest tests/test_mcp_integration.py -m tool_test -v
pixi run pytest tests/test_mcp_integration.py -m pipeline_test -v
pixi run pytest tests/test_mcp_integration.py -m "not slow" -v
pixi run pytest tests/test_mcp_integration.py -m requires_simulation -v

# List all markers
pixi run pytest --markers | grep "tool_test\|pipeline_test\|slow\|requires_simulation"
```

**Files Modified:**
- Modify: `tests/test_mcp_integration.py` (add marker decorators)
- Modify: `pyproject.toml` (configure markers)
- Create: `tests/README.md` (test documentation)

**Expected Result:**
- All tests properly marked
- Can run selective test subsets
- Documentation helps contributors

---

### Phase 10: Final Integration and Cleanup

**Goal:** Run full test suite, optimize, document

**Actions:**

1. **Run complete test suite:**
   ```bash
   # Run ALL integration tests
   pixi run pytest tests/test_mcp_integration.py -v
   
   # Generate coverage report
   pixi run pytest tests/test_mcp_integration.py --cov=src/ot2_cherrypick_mcp --cov-report=html
   
   # Check test execution time
   pixi run pytest tests/test_mcp_integration.py -v --durations=20
   ```

2. **Optimize slow tests if needed:**
   - Consider LLM caching strategies
   - Identify bottlenecks in test setup
   - Optimize fixture scope (session vs function)

3. **Update main test documentation:**
   - Update `CLAUDE.md` with test instructions
   - Document test philosophy and structure
   - Add CI/CD considerations

4. **Final cleanup:**
   - Remove any unused helper functions
   - Ensure consistent naming conventions
   - Add type hints where missing
   - Run linters: `pixi run ruff check tests/`

**Test After Implementation:**
```bash
# Full test suite final run
pixi run pytest tests/test_mcp_integration.py -v --tb=short

# Verify all markers work
pixi run pytest tests/test_mcp_integration.py -m tool_test --collect-only
pixi run pytest tests/test_mcp_integration.py -m pipeline_test --collect-only

# Check coverage
pixi run pytest tests/test_mcp_integration.py --cov=src/ot2_cherrypick_mcp --cov-report=term-missing
```

**Files Modified:**
- Update: `CLAUDE.md` (add testing section)
- Update: `tests/README.md` (finalize documentation)
- Cleanup: `tests/test_mcp_integration.py` (final polish)

**Expected Result:**
- ~50-60 total test cases (from initial 9)
- All 9 MCP tools tested via agent
- All 6 resources tested
- 2 prompts tested
- 5-7 pipeline workflows tested
- Test execution time: ~15-30 minutes (with LLM calls)
- Clear documentation for contributors

---

## Final Test Structure

### `tests/test_mcp_integration.py` Structure (After Refactoring)

```
# Imports and setup
from .conftest import *
from .helpers import ProjectSetup, AgentRunner, Assertions
from .test_data import *

# ----- TIER 1: TOOL ENUMERATION TESTS -----

# Tool 1: Project Management
def test_agent_initialize_project(...)

# Tool 2: Configuration
@pytest.mark.parametrize("preset_name,expected", LIQUID_PRESET_SCENARIOS)
def test_agent_apply_liquid_preset(...)

def test_agent_updates_settings(...)  # Existing, refactored

# Tool 3: CSV Management
@pytest.mark.parametrize("scenario,params", CSV_TEMPLATE_SCENARIOS)
def test_agent_generate_csv_template(...)

def test_agent_upload_csv_content(...)  # Existing

# Tool 4: Labware
@pytest.mark.parametrize("scenario,labware_def", LABWARE_SCENARIOS)
def test_agent_add_labware_definition(...)

# Tool 5: Validation
def test_agent_validate_configuration_success(...)

@pytest.mark.parametrize("scenario,bad_config,error", VALIDATION_ERROR_SCENARIOS)
def test_agent_validate_configuration_errors(...)

# Tool 6: Protocol Generation
def test_agent_generate_protocol(...)  # Existing

# Tool 7: Simulation
@pytest.mark.slow
@pytest.mark.requires_simulation
def test_agent_simulate_protocol_success(...)

@pytest.mark.slow
@pytest.mark.requires_simulation
@pytest.mark.error_scenario
def test_agent_simulate_protocol_failure(...)

# Tool 8: Deployment
def test_agent_deploy_to_opentrons(...)

# Tool 9: Full Workflow (existing, refactored)
def test_agent_full_workflow(...)

# ----- TIER 2: PIPELINE INTEGRATION TESTS -----

@pytest.mark.pipeline_test
def test_complete_new_project_workflow(...)

@pytest.mark.pipeline_test
def test_troubleshooting_workflow(...)

@pytest.mark.pipeline_test
def test_custom_labware_workflow(...)

@pytest.mark.pipeline_test
def test_configuration_iteration_workflow(...)

@pytest.mark.resource_test
@pytest.mark.pipeline_test
def test_resource_reading_workflow(...)

@pytest.mark.pipeline_test
def test_setup_new_experiment_prompt(...)

@pytest.mark.pipeline_test
@pytest.mark.error_scenario
def test_troubleshoot_simulation_error_prompt(...)

# ----- LEGACY TESTS -----
def test_agent_lists_tools(...)  # Keep for basic connectivity check
```

### Supporting Files

**`tests/conftest.py`:** Foundation fixtures (project_dir, mcp_config, agent, etc.)

**`tests/helpers.py`:** Helper classes (ProjectSetup, AgentRunner, Assertions)

**`tests/test_data.py`:** Centralized test data and scenarios

**`tests/README.md`:** Test documentation and usage guide

---

## Coverage Goals (After Completion)

### Tool Coverage
✅ **9/9 tools tested via agent** (~30-40 test cases)
- initialize_project: 1 test
- apply_liquid_preset: 5 parametrized tests
- update_settings: 7 parametrized tests
- generate_csv_template: 4 parametrized tests
- upload_csv_content: 1 test
- add_labware_definition: 3 parametrized tests
- validate_configuration: 4 tests (1 success + 3 error scenarios)
- generate_protocol: 1 test
- simulate_protocol: 2 tests (success + failure)
- deploy_to_opentrons: 1 test
- full_workflow: 1 test

### Resource Coverage
✅ **6/6 resources verified in workflows**
- config://settings (read in resource_reading_workflow)
- config://labware (read in resource_reading_workflow)
- status://deck-layout (read in resource_reading_workflow)
- status://liquid-handling-config (read in resource_reading_workflow)
- files://csvs (read in resource_reading_workflow)
- logs://last-simulation (read in troubleshooting workflows)

### Pipeline Coverage
✅ **7 realistic end-to-end workflows**
- Complete new project
- Troubleshooting
- Custom labware
- Configuration iteration
- Resource reading
- Setup prompt workflow
- Troubleshoot prompt workflow

### Total Test Metrics
- **Before:** 9 test cases (4 base + 5 parametrized)
- **After:** ~50-60 test cases (~35-40 tool tests + ~15-20 pipeline/resource tests)
- **Execution time:** ~15-30 minutes (LLM calls are slow)
- **Tool coverage:** 9/9 (100%)
- **Resource coverage:** 6/6 (100%)
- **Prompt coverage:** 2/2 (100%)

---

## Important Notes

### What NOT to Change
- **DO NOT modify unit test files** (test_config_tools.py, test_csv_tools.py, etc.)
- Those test internal Python functions directly and are valuable
- They complement the agent-driven tests

### Test Execution Considerations
- **LLM calls are slow:** Each test takes 30-120 seconds
- **Use markers for fast iteration:** `-m "not slow"` during development
- **Parallelization:** Consider pytest-xdist for parallel execution
- **API costs:** Be mindful of Mistral API usage in CI/CD

### Maintenance
- **Keep test_data.py updated** when adding new scenarios
- **Document new helpers** in docstrings
- **Update CLAUDE.md** when test structure changes significantly

---

## Success Criteria

✅ All 9 MCP tools have agent-driven tests
✅ All 6 resources are read by agents in tests
✅ Both prompts are tested in workflows
✅ Simulation is ENABLED (not disabled)
✅ Error scenarios are tested (validation, simulation failures)
✅ Pipeline workflows chain 3-7 tools together
✅ Helper classes reduce duplication
✅ Fixtures enable clean test setup
✅ Markers allow selective test execution
✅ Documentation guides contributors
✅ Test coverage significantly improved

**The refactoring transforms test_mcp_integration.py from basic smoke tests into comprehensive agent-driven validation of the entire MCP surface area.**