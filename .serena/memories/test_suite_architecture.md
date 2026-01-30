# Test Suite Architecture & Coverage Report (Phase 3: Unified Workflows)

## Executive Summary

The OT2_CherryPick test suite contains **65 Python test files** with **~400+ test cases** organized across 6 distinct testing layers. The suite validates MCP tools, protocol generation, unified workflows (Phase 3), E2E simulation, FastAPI backend, and simulation log parsing.

**Overall Status**: Phase 3 complete with unified workflow tests passing in baseline mode (fast, 0.3s per test) and live mode (comprehensive, 1-2s per test). All 35 workflow tests pass successfully.

---

## Directory Structure

```
tests/
├── conftest.py              # MCP integration fixtures (session-scoped)
├── helpers.py               # ProjectSetup, AgentRunner, Assertions classes
├── test_data.py             # Centralized test scenarios & CSV fixtures
├── test_*.py                # 19 root-level MCP tool tests
│
├── e2e/                     # End-to-end protocol simulation tests
│   ├── conftest.py          # E2EWorkspace, simulation helpers
│   ├── configs/             # Settings profiles (single_X1, multi_X1, multi, dual, etc.)
│   └── test_*.py            # 8 E2E test modules (92 tests)
│
├── fastapi/                 # FastAPI backend endpoint tests
│   ├── conftest.py          # TestClient with FileStateStore isolation
│   └── test_*.py            # 6 API test modules (52 tests)
│
├── integration/             # Integration tests with captured fixtures
│   └── simulation_logs/
│       ├── fixtures/        # 8 captured simulation outputs
│       │   ├── manifest.json
│       │   └── {fixture_id}/ (metadata.json, stdout.txt, stderr.txt)
│       └── test_simulation_log_fixtures.py
│
├── unit/                    # Unit tests for parsing/matching modules
│   ├── simulation_logs/     # Parser, normalizer, adapter modules + tests
│   │   ├── adapters/v8_7_0.py
│   │   ├── models.py, parse.py, normalize.py, matching.py
│   │   ├── expectations.py, policies.py, diagnostics.py
│   │   └── test_*.py        # 6 unit tests
│   └── transfer_mapping/    # Transfer expectation/policy tests
│       └── test_*.py        # 18 tests
│
├── workflow/                # [PHASE 3] Unified workflow tests
│   ├── conftest.py          # Workflow fixtures and shared utilities
│   └── test_protocol_workflow.py  # 35 unified baseline+live tests
│
└── support/                 # Shared test utilities
    ├── fixtures.py          # FixtureEntry, load_manifest, capture_fixture
    ├── paths.py             # LRU-cached path resolution
    ├── simulation.py        # Settings loading, expectation building
    ├── workspace.py         # E2EWorkspace, SimulationResult
    └── manifest.json        # Unified fixture manifest (19 entries)
```

---

## Test Categories & Coverage

### 0. Unified Workflow Tests (Phase 3) - 35 tests

**Purpose**: Consolidated protocol workflow validation with dual-mode execution (baseline/live)

**File**: `tests/workflow/test_protocol_workflow.py`

| Test Function | Count | Purpose |
|---------------|-------|---------|
| test_protocol_simulation | 19 | All manifest entries (success/failure validation) |
| test_baseline_settings_profile_parity | 8 | Baseline metadata consistency |
| test_baseline_returncode_consistency | 8 | Expected failure/success alignment |

**Modes**:
- **Baseline Mode (Default, Fast)**: Uses captured stdout/stderr/metadata from `tests/integration/simulation_logs/fixtures/`. ~0.3s per test, ~11s total for all 35.
- **Live Mode (OT2_LIVE_SIMULATION=1)**: Runs actual protocol generation + `opentrons_simulate`. ~1-2s per test, ~50s total for all 35.
- **Refresh Mode (OT2_REFRESH_BASELINES=1)**: Captures new baselines while running live simulations.

**Status**: ✓ All 35 tests pass in baseline mode

### 1. Root-Level MCP Tool Tests (~149 tests)

**Purpose**: Unit test all MCP tools exposed by the server

**Files**: `tests/test_*.py` (19 files)

| Module | Tests | Coverage |
|--------|-------|----------|
| test_config_tools.py | 7 | update_settings, liquid_presets |
| test_csv_tools.py | 5 | generate_csv_template, save_csv_content |
| test_csv_tools_distribution.py | 13 | Distribution CSV format |
| test_deployment_tools.py | 5 | deploy_protocol, clipboard |
| test_formatters.py | 16 | JSON/Markdown/Concise formatting |
| test_home_control.py | 17 | HOME row validation |
| test_labware_tools.py | 2 | add_labware_definition |
| test_mcp_integration.py | 20 | Full MCP agent workflows (Mistral LLM) |
| test_project_tools.py | 9 | initialize_project, export_archive |
| test_prompts.py | 1 | Prompt registration |
| test_resources.py | 7 | MCP resources |
| test_simulation_tools.py | 5 | simulate_protocol |
| test_toml_handler.py | 5 | TomlHandler utilities |
| test_tools.py | 2 | Protocol generation |
| test_validation.py | 4 | Configuration validation |
| test_validation_distribution.py | 20 | Distribution validation |
| test_workflow_tools.py | 3 | Full workflow orchestration |

**Status**: ✓ Unit tests pass. MCP integration tests may fail due to Mistral API rate limits.

### 2. E2E Protocol Simulation Tests (92 tests)

**Purpose**: Validate complete protocol generation → simulation workflow

**Files**: `tests/e2e/test_*.py` (8 files)

| Module | Tests | Scenarios |
|--------|-------|-----------|
| test_cherrypick_basic.py | 12 | Basic transfers, HOME control, volume splitting |
| test_cherrypick_advanced.py | 4 | Tip actions, heights, air gaps |
| test_distribution.py | 8 | 1:N distribution patterns (equal, geometric) |
| test_distribution_validation.py | 35 | Distribution CSV validation & error cases |
| test_dual_pipette.py | 11 | Runtime mode switching (single↔multi↔multi_X1) |
| test_gui_dual_mode_integration.py | 24 | GUI backend dual-mode compatibility |
| test_multi_channel.py | 4 | Full 8-channel column operations |
| test_real_world.py | 12 | 48-transfer protocols, custom layouts |

**Methodology**:
1. Creates isolated E2EWorkspace with config profile
2. Runs `helper_cherry_pick.py` (protocol generation)
3. Runs `opentrons_simulate` (validation)
4. Asserts simulation success + output patterns

**Pipette Modes Tested**: single_X1, multi_X1, multi, dual, fill_analytics

**Status**: ✓ All pass when `LABWARE_PATH` configured

### 3. FastAPI Backend Tests (52 tests)

**Purpose**: Validate GUI backend API endpoints

**Files**: `tests/fastapi/test_*.py` (6 files)

| Module | Tests | Endpoints |
|--------|-------|-----------|
| test_csvs.py | 2 | /csvs CRUD |
| test_gui_dual_mode_updates.py | 24 | /settings dual-mode |
| test_gui_workflow_dual_mode.py | 17 | /workflow generation |
| test_settings_labware.py | 5 | /settings, /labware |
| test_system.py | 1 | / health check |
| test_workflow.py | 6 | /workflow generation |

**Status**: 50/52 passing (96%)
- ✗ `test_reset_settings_restores_defaults` - KeyError: 'tip_reuse' (schema drift)
- ✗ `test_send_to_opentrons_requires_target_path` - target_path now optional

### 4. Unit Tests - Simulation Logs (57 tests)

**Purpose**: Validate simulation output parsing, expectation building, and transfer matching

**Modules** (in `tests/unit/simulation_logs/`):

| File | LOC | Purpose |
|------|-----|---------|
| models.py | 94 | Raw event dataclasses (TipPickup, Aspirate, Dispense, Mix) |
| normalize.py | 279 | Normalized events with labware_id enrichment |
| parse.py | 64 | Fixture parser with adapter selection |
| expectations.py | 207 | CSV → ExpectedTransfer builder |
| matching.py | 489 | Expected vs actual transfer comparison |
| policies.py | 333 | Tip reuse, air gap, mix policy validation |
| diagnostics.py | 71 | Coverage reports and diagnostics |
| adapters/v8_7_0.py | 120 | Regex parser for opentrons_simulate 8.7.0 |

**Test Coverage**:
- Adapter parsing (2 tests)
- Full fixture parsing (4 tests)
- Transfer expectations (5 tests)
- Transfer matching (7 tests)
- Policy validation (12 tests)
- Integration with fixtures (16 tests)

**Known Issue**: Module-level `FIXTURE_ROOT` state mutation in one test causes cascading failures in subsequent tests. Fix: Use function-scoped fixture instead of module variable.

### 5. Integration Tests - Fixture Validation (16 tests)

**Purpose**: Validate captured simulation fixtures against manifest expectations

**Fixtures** (in `tests/integration/simulation_logs/fixtures/`):

| Fixture ID | CSV | Mode | Transfers |
|------------|-----|------|-----------|
| basic-single_x1 | example_basic.csv | single_X1 | 4 |
| basic-multi_x1 | example_basic.csv | multi_X1 | 4 |
| multi-multi | example_multi_mode.csv | multi | 2 |
| distribution-multi | example_distribution.csv | multi | 17 |
| home-control-single_x1 | example_home_control.csv | single_X1 | 6 |
| fill-analytics | fill_analytics_plate.csv | fill_analytics | 48 |
| extreme-single_x1 | example_basic.csv | liquid_extreme | 4 |
| invalid-labware | invalid_labware.csv | single_X1 | (expect_failure) |

---

## Support Infrastructure

### Fixture Classes

**ProjectSetup** (`tests/helpers.py`):
- `create_standard_project()` - Full project with templates
- `create_empty_project()` - For initialize_project tests
- `create_with_csv()` - Pre-populated CSV
- `create_with_protocol()` - Includes protocol template

**AgentRunner** (`tests/helpers.py`):
- Wraps MCPAgent for synchronous execution
- `run(query)` → execute single query
- `run_chain(queries)` → execute sequence

**E2EWorkspace** (`tests/e2e/conftest.py`):
- Isolated workspace with settings profile
- Copies labware_dict.toml, CSVs, protocol template

### Path Utilities (`tests/support/paths.py`)

```python
repo_root()              # LRU-cached project root
tests_root()             # tests/ directory
simulation_fixtures_root()  # integration/simulation_logs/fixtures/
settings_profile_path(profile)  # e2e/configs/{profile}/settings.toml
```

### Test Data (`tests/test_data.py`)

Centralized test scenarios:
- `CSV_BASIC`, `CSV_WITH_MIXING`, `CSV_WITH_AIR_GAP`
- `CSV_DISTRIBUTION_*` variants
- `UPDATE_SETTINGS_SCENARIOS` for parametrization
- `LIQUID_PRESET_SCENARIOS`
- `DISTRIBUTION_VALIDATION_SCENARIOS`

---

## Testing Philosophy

### What Tests Validate ✓

1. **Protocol Structure** - Generated Python is valid, JSON embedded correctly
2. **Configuration Parsing** - TOML/CSV read correctly, values propagated
3. **Simulation Compatibility** - opentrons_simulate accepts protocols
4. **Feature Completeness** - All pipette modes, distribution patterns, tip actions
5. **Error Handling** - Invalid inputs caught with appropriate messages
6. **API Contract** - HTTP methods, status codes, response schemas
7. **Data Persistence** - Settings survive across requests

### What Tests Don't Validate ✗

1. **Physical Hardware** - Tests use simulator, not real robot
2. **Tip Positioning Accuracy** - No crash detection
3. **Volume Precision** - Distribution math not numerically verified
4. **Performance** - Execution time not measured
5. **Cross-Contamination** - Sample isolation not validated

---

## Known Issues & Fixes Needed

### ~~1. FastAPI Schema Drift (2 failing tests)~~ ✅ FIXED (2026-01-30)
- `test_reset_settings_restores_defaults` - Now checks `mode` field instead of removed `tip_reuse`
- `test_send_to_opentrons_requires_target_path` - Renamed and updated for optional target_path behavior

### ~~2. Module-Level State Mutation (simulation_logs)~~ ✅ FIXED (2026-01-30)
- Fixed in `test_simulation_log_parsing.py` with proper try/finally cleanup

### 3. Unregistered Pytest Marks
- **Marks**: `@pytest.mark.slow`, `requires_simulation`, `pipeline_test`
- **Fix**: Add to `[tool.pytest.ini_options]` in pyproject.toml

### 4. MCP Integration Test Flakiness
- **Cause**: Mistral API rate limits, capacity issues
- **Fix**: Add retry logic or mark as optional CI tests

---

## Test Commands

```bash
# Run all tests
uv run pytest tests/ -v

# Run specific category
uv run pytest tests/e2e/ -v
uv run pytest tests/fastapi/ -v
uv run pytest tests/unit/ -v

# Run with coverage
uv run pytest tests/ --cov=src --cov-report=html

# Skip slow/integration tests
uv run pytest tests/ -m "not slow" -v

# Refresh simulation fixtures
OT2_REFRESH_SIM_FIXTURES=1 uv run pytest tests/integration/ -v
```

---

## Summary Statistics

| Category | Files | Tests | Status |
|----------|-------|-------|--------|
| Unified Workflows (Phase 3) | 1 | 35 | ✓ All pass (baseline) |
| Root MCP Tools | 19 | ~149 | ✓ Pass (unit), ⚠ Flaky (integration) |
| E2E Simulation | 8 | 92 | ✓ Pass |
| FastAPI Backend | 6 | 52 | 50/52 Pass |
| Unit (sim_logs) | 11 | ~30 | ⚠ Fixture path issue |
| Integration | 1 | 16 | ✓ Pass |
| **Total** | **46** | **~400** | **~96% Pass** |

---

## Recommendations

1. **Fix the 2 FastAPI tests** - Update assertions for dual-mode schema
2. **Fix module state mutation** - Replace FIXTURE_ROOT with pytest fixture
3. **Register pytest marks** - Add to pyproject.toml
4. **Add pytest.ini** - Document test organization
5. **Consolidate duplicate fixtures** - Merge project_root definitions
6. **Consider splitting MCP integration tests** - Separate unit from LLM-dependent
