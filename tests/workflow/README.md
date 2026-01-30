# Unified Protocol Workflow Tests (Phase 3)

Fast, comprehensive protocol validation with dual-mode execution.

## Quick Start

### Baseline Mode (Default, Fast - 11 seconds)

```bash
# All 35 workflow tests using captured fixtures
uv run pytest tests/workflow/ -v

# Single test (very fast)
uv run pytest tests/workflow/ -k "basic-single_x1" -v

# Quiet output
uv run pytest tests/workflow/ -q
```

### Live Mode (Comprehensive - 50 seconds)

```bash
# Run actual simulations for all tests
OT2_LIVE_SIMULATION=1 uv run pytest tests/workflow/ -v

# Single test with live simulation
OT2_LIVE_SIMULATION=1 uv run pytest tests/workflow/ -k "basic-single_x1" -v
```

### Refresh Baselines (Capture Mode)

```bash
# Update baseline fixtures from live simulation
OT2_REFRESH_BASELINES=1 uv run pytest tests/workflow/ -v --tb=short
```

## What Gets Tested

| Fixture | Transfers | Mode | Purpose |
|---------|-----------|------|---------|
| basic-single_x1 | 4 | Baseline | Single-channel cherry-pick |
| basic-multi_x1 | 4 | Baseline | 8-channel single-tip mode |
| multi-multi | 2 | Baseline | Full 8-channel mode |
| distribution-multi | 17 | Baseline | Distribution with multi-channel |
| fill-analytics | 48 | Baseline | Custom deck layout (analytics plate) |
| home-control-single_x1 | 6 | Baseline | HOME row feature validation |
| extreme-single_x1 | 4 | Baseline | Extreme liquid handling parameters |
| invalid-labware | - | Baseline | Expected failure case |
| **11 E2E-only fixtures** | various | Live | New or advanced features |
| **19 Total** | ~100+ | Mixed | Comprehensive coverage |

## Test Functions

### test_protocol_simulation (19 cases)

Validates protocol generation and simulation for all 19 manifest entries:
- ✓ Success cases: returncode == 0
- ✓ Failure cases (invalid-labware): returncode != 0
- ✓ Runs in baseline mode by default, live on demand

```bash
uv run pytest tests/workflow/test_protocol_workflow.py::test_protocol_simulation -v
```

### test_baseline_settings_profile_parity (8 cases)

Validates that baseline metadata matches manifest:
- Only runs for fixtures with `has_baseline=true`
- Ensures settings_profile consistency
- Detects baseline corruption

```bash
uv run pytest tests/workflow/test_protocol_workflow.py::test_baseline_settings_profile_parity -v
```

### test_baseline_returncode_consistency (8 cases)

Validates return codes match expectations:
- expect_failure=true → returncode != 0
- expect_failure=false → returncode == 0
- Prevents invalid baselines

```bash
uv run pytest tests/workflow/test_protocol_workflow.py::test_baseline_returncode_consistency -v
```

## Development Workflow

### Adding a New Fixture

1. Add entry to `tests/support/manifest.json`:
   ```json
   {
     "fixture_id": "my-test-single_x1",
     "csv_path": "CSVs/my_test.csv",
     "settings_profile": "single_X1",
     "expect_failure": false,
     "has_baseline": false,
     "description": "My new test case"
   }
   ```

2. Test in live mode first:
   ```bash
   OT2_LIVE_SIMULATION=1 uv run pytest tests/workflow/ -k "my-test-single_x1" -v
   ```

3. Once working, capture baseline:
   ```bash
   OT2_REFRESH_BASELINES=1 uv run pytest tests/workflow/ -k "my-test-single_x1" -v
   ```

4. Update manifest with `"has_baseline": true`

5. Verify in baseline mode:
   ```bash
   uv run pytest tests/workflow/ -k "my-test-single_x1" -v
   ```

### Debugging a Failed Test

1. Run with verbose output:
   ```bash
   OT2_LIVE_SIMULATION=1 uv run pytest tests/workflow/ -k "fixture-name" -vv
   ```

2. See full traceback:
   ```bash
   OT2_LIVE_SIMULATION=1 uv run pytest tests/workflow/ -k "fixture-name" --tb=long
   ```

3. Check baseline files:
   ```bash
   cat tests/integration/simulation_logs/fixtures/fixture-name/{stdout,stderr}.txt
   ```

4. Refresh baseline if needed:
   ```bash
   OT2_REFRESH_BASELINES=1 uv run pytest tests/workflow/ -k "fixture-name" -v
   ```

## Performance

| Mode | Tests | Time | Per-test |
|------|-------|------|----------|
| Baseline | 35 | 11s | 0.3s |
| Live | 35 | 50s | 1.4s |
| Refresh | 35 | 50s | 1.4s |

**Baseline mode is the recommended default** for:
- Developer iteration
- Pre-commit validation
- CI/CD quick checks
- Pull request validation

**Live mode is recommended for**:
- Pre-release comprehensive testing
- Baseline captures/refreshes
- Integration with new labware
- System-level validation

## CI/CD Integration

### Quick Validation (Baseline)
```yaml
test:fast:
  script:
    - uv run pytest tests/workflow/ -v
  duration: 30s
```

### Comprehensive Validation (Live)
```yaml
test:comprehensive:
  script:
    - OT2_LIVE_SIMULATION=1 uv run pytest tests/workflow/ -v
  duration: 90s
```

### Scheduled Baseline Refresh
```yaml
update:baselines:
  schedule: weekly
  script:
    - OT2_REFRESH_BASELINES=1 uv run pytest tests/workflow/ -v --tb=short
```

## Markers and Filtering

All workflow tests are marked with:
- `@pytest.mark.requires_simulation` - Requires opentrons_simulate
- `@pytest.mark.pipeline_test` - Suitable for CI/CD

Run tests by marker:
```bash
# Only pipeline tests
uv run pytest tests/workflow/ -m "pipeline_test" -v

# Exclude slow tests (none in workflow, shown for reference)
uv run pytest tests/workflow/ -m "not slow" -v
```

## Pytest Marks

Available marks for organization:
- `requires_simulation` - Tests needing opentrons_simulate
- `pipeline_test` - CI/CD suitable tests
- `baseline_test` - Baseline validation tests
- `slow` - Long-running tests
- `workflow` - Unified workflow tests (all workflow tests have this)

## Environment Variables

| Variable | Default | Effect |
|----------|---------|--------|
| OT2_LIVE_SIMULATION | unset | Force live simulation mode |
| OT2_REFRESH_BASELINES | unset | Capture new baselines |
| LABWARE_PATH_WIN_OVERRIDE | unset | Override Windows labware path |

## Troubleshooting

### Tests hanging or taking too long
- Check LABWARE_PATH is correctly configured
- Run with shorter timeout: `pytest --timeout=60`
- Check for network issues if simulating remotely

### "Labware not found" errors
- Ensure LABWARE_PATH points to Opentrons labware definitions
- Verify custom labware files exist: `ls $LABWARE_PATH/*.json`
- Check simulate_protocol.sh for LABWARE_PATH_WIN configuration

### Baseline tests failing
- Regenerate baselines: `OT2_REFRESH_BASELINES=1 uv run pytest ...`
- Check manifest.json has `"has_baseline": true` for updated fixtures
- Verify baseline files exist in `tests/integration/simulation_logs/fixtures/`

### "duplicate parametrization" error
- Ensure only one `@pytest.mark.parametrize` decorator per test
- Don't mix pytest_generate_tests hook with parametrize decorators
- Check for fixture name conflicts

## Architecture

```
tests/workflow/
├── __init__.py              # Package marker
├── conftest.py              # Shared test utilities
├── test_protocol_workflow.py # Main test module (35 tests)
└── README.md                # This file

Unified manifest:
tests/support/manifest.json  # Single source of truth (19 fixtures)

Baseline storage:
tests/integration/simulation_logs/fixtures/
├── basic-single_x1/
│   ├── stdout.txt
│   ├── stderr.txt
│   └── metadata.json
├── ... (8 more fixtures)
```

## References

- Full Phase 3 documentation: `.planning/phases/13-phase-3-unified-workflows/PHASE-3-COMPLETE.md`
- Manifest format: `tests/support/manifest.json`
- Test implementation: `tests/workflow/test_protocol_workflow.py`
- Fixture utilities: `tests/support/fixtures.py`
- Workspace utilities: `tests/support/workspace.py`

## See Also

- E2E Tests: `tests/e2e/` - Raw protocol generation + simulation
- Integration Tests: `tests/integration/simulation_logs/` - Log parsing validation
- Unit Tests: `tests/unit/` - Component-level validation
- Root Tests: `tests/test_*.py` - MCP tool unit tests
