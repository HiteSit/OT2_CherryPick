# Codebase Concerns

**Analysis Date:** 2026-01-20

## Tech Debt

**Monolithic Protocol File (1546 lines):**
- Issue: `CherryPick_OT2.py` contains all protocol logic in a single file - validation, labware loading, pipette configuration, transfer execution, distribution mode, and module management
- Files: `CherryPick_OT2.py`
- Impact: Difficult to test individual components, high cognitive load for modifications, harder to maintain
- Fix approach: Extract logical sections into separate modules (e.g., `protocol_validation.py`, `transfer_executor.py`, `distribution_handler.py`). However, note that Opentrons protocols must be self-contained at runtime - modularization benefits development only.

**Duplicated HOME Row Detection Logic:**
- Issue: `is_home_control_row()` function is implemented twice with nearly identical logic
- Files: `CherryPick_OT2.py:111-142`, `src/ot2_cherrypick_mcp/core/validation.py:31-51`
- Impact: Bug fixes must be applied in two places, risk of behavior divergence
- Fix approach: Extract to a shared utility module importable by both protocol runtime and validation tools

**Legacy toml Import Fallback:**
- Issue: Protocol generator has fragile toml/tomllib import logic
- Files: `src/ot2_cherrypick_mcp/core/protocol_generator.py:16-19`
- Impact: Potential runtime errors if import order changes, Python 3.11+ already has tomllib built-in
- Fix approach: Since project targets Python 3.12, remove the fallback and use only tomllib

**Hardcoded Windows Paths in Shell Script:**
- Issue: Machine-specific paths hardcoded with manual `MACHINE_CONFIG` switch
- Files: `simulate_protocol.sh:15-22`
- Impact: New users must edit script to use their paths, error-prone setup
- Fix approach: Use environment variables or a `.env` file for machine-specific configuration

**Exception Handling with Generic Exception:**
- Issue: Several locations catch broad `Exception` and re-raise with string formatting
- Files: `src/ot2_cherrypick_mcp/core/protocol_generator.py:45-46,70-71`, `CherryPick_OT2.py:917-918,924-925`
- Impact: Original exception context may be lost, harder to debug
- Fix approach: Use `raise ... from e` pattern consistently, or use specific exception types

## Known Bugs

**Opentrons Simulator Accepts Physically Impossible Operations:**
- Symptoms: Simulation passes for multi-channel operations that would fail on real hardware
- Files: `CherryPick_OT2.py` (affects all multi-mode operations)
- Trigger: Using invalid well targets (e.g., C1, D1 on 384-well plate) with 8-channel pipette
- Workaround: Added `validate_distribution_wells_for_multi_mode()` validation at lines 702-751, but only covers distribution mode. Cherry-pick multi-mode may still pass invalid configs through simulator.

**HeaterShaker Module Empty labware_id:**
- Symptoms: 16 unit test failures related to heaterShaker module configuration
- Files: `settings.toml` (module entry with `labware_id = ""`)
- Trigger: Running unit tests with default settings.toml
- Workaround: None documented - tests fail

## Security Considerations

**Subprocess Execution with User-Provided Paths:**
- Risk: Path injection when constructing shell commands
- Files: `src/gui/backend/state.py:328-351`, `src/ot2_cherrypick_mcp/core/simulation.py:97-100`
- Current mitigation: Paths are resolved and validated before use
- Recommendations: Add explicit path sanitization, avoid shell=True in subprocess calls

**No Input Validation on CSV Content:**
- Risk: Malformed CSV content could cause unexpected behavior
- Files: `src/ot2_cherrypick_mcp/tools/csv_tools.py:93-133`
- Current mitigation: Basic column checks in validation module
- Recommendations: Add length limits, sanitize well names against injection patterns

**Clipboard Command Execution:**
- Risk: Hardcoded clipboard command path could be hijacked
- Files: `src/ot2_cherrypick_mcp/core/deployment.py:13`
- Current mitigation: Uses absolute path `/mnt/c/Windows/System32/clip.exe`
- Recommendations: Validate executable existence before execution (already done at line 79)

## Performance Bottlenecks

**Full File Read for JSON Embedding:**
- Problem: Protocol file read entirely into memory, regex replacement on full content
- Files: `src/ot2_cherrypick_mcp/core/protocol_generator.py:147-166`
- Cause: `re.sub()` with `re.DOTALL` on entire 70KB+ file
- Improvement path: Use line-by-line processing to find and replace only the `get_values()` function

**Simulation Subprocess Timeout:**
- Problem: Default 120-second timeout may be too short for complex protocols
- Files: `src/ot2_cherrypick_mcp/core/simulation.py:40,54`
- Cause: Large protocols with many transfers take longer to simulate
- Improvement path: Make timeout configurable per-protocol based on transfer count

## Fragile Areas

**JSON Embedding in Protocol File:**
- Files: `src/ot2_cherrypick_mcp/core/protocol_generator.py:155-176`
- Why fragile: Regex pattern `r'(_all_values = json\.loads\(\"\"\").*?(\"\"\")\)'` depends on exact formatting
- Safe modification: Always test with protocols containing special characters in labware names
- Test coverage: Only basic happy-path tests exist

**Nozzle Reconfiguration During Dual-Pipette Mode:**
- Files: `CherryPick_OT2.py:1293-1305`
- Why fragile: Mid-protocol nozzle layout changes require tips to be dropped first, strict API requirements
- Safe modification: Ensure `pipette.has_tip` check always precedes `configure_nozzle_layout()`
- Test coverage: No direct unit tests for mode switching logic

**TOML Path Patching:**
- Files: `src/gui/backend/state.py:473-501`
- Why fragile: Complex path explosion logic with bracket notation support (e.g., `settings.working_plate[0].type`)
- Safe modification: Add comprehensive tests for edge cases (nested arrays, special keys)
- Test coverage: Limited - mostly happy-path

**Tip Rack Mode Assignment:**
- Files: `CherryPick_OT2.py:1146-1167`
- Why fragile: Legacy configs without `mode` field trigger warning and auto-assignment
- Safe modification: Always test with both new configs (with mode) and legacy configs (without)
- Test coverage: E2E tests exist but no unit isolation

## Scaling Limits

**CSV Transfer Count:**
- Current capacity: Protocol tested up to ~100 transfers
- Limit: Large CSVs with 1000+ transfers may hit memory limits or timeout
- Scaling path: Implement chunked processing or streaming CSV parsing

**Embedded JSON Size:**
- Current capacity: JSON config up to ~100KB works reliably
- Limit: Very large labware dictionaries or long CSVs may exceed reasonable embedding limits
- Scaling path: Consider external config file loading at protocol runtime (breaks self-contained design)

## Dependencies at Risk

**mcp-use Library for Testing:**
- Risk: Integration tests depend on third-party MCP client library
- Impact: Test suite breaks if mcp-use API changes
- Migration plan: Mock MCP interactions for unit tests, use mcp-use only for true integration tests
- Files: `tests/conftest.py:11-12`, `tests/test_mcp_integration.py`

**Mistral LLM for Integration Tests:**
- Risk: Tests use `mistral-small-2506` model which may be deprecated
- Impact: Integration tests fail if model unavailable
- Migration plan: Make model configurable via environment variable
- Files: `tests/conftest.py:84`

**tomlkit for Format-Preserving Edits:**
- Risk: tomlkit has complex API for preserving comments/formatting
- Impact: TOML edits may unexpectedly change formatting
- Migration plan: Document expected behavior, add regression tests for format preservation
- Files: `src/ot2_cherrypick_mcp/utils/toml.py`, `src/gui/backend/state.py`

## Missing Critical Features

**No Protocol Versioning:**
- Problem: No way to track which configuration version generated a protocol
- Blocks: Reproducibility of experiments, rollback to previous configs

**No Dry Run Mode for Deployment:**
- Problem: `deploy_protocol()` immediately copies file, no preview
- Blocks: Safe deployment verification before overwriting production protocols

**No Volume Tracking/Depletion Warnings:**
- Problem: No tracking of source well volumes across transfers
- Blocks: Early detection of insufficient source volume before protocol fails mid-run

## Test Coverage Gaps

**Protocol Runtime Functions:**
- What's not tested: `perform_liquid_contact()`, `perform_post_aspirate_actions()`, `perform_dispense_with_options()`
- Files: `CherryPick_OT2.py:253-360`
- Risk: Liquid handling bugs only caught at real hardware runtime
- Priority: Medium - these depend on Opentrons API mocking which is complex

**Multi-Channel Cherry-Pick Validation:**
- What's not tested: Cherry-pick mode with multi-channel doesn't validate well targets like distribution mode does
- Files: `CherryPick_OT2.py:1394-1426`
- Risk: Invalid multi-channel targets pass simulation but fail on hardware
- Priority: High - same bug class as distribution mode

**GUI State Synchronization:**
- What's not tested: Race conditions in concurrent GUI state updates
- Files: `src/gui/backend/state.py`
- Risk: Corrupted config state from rapid user interactions
- Priority: Low - single-user desktop app

**Error Recovery Paths:**
- What's not tested: Many `# pragma: no cover` comments on exception handlers
- Files: Multiple in `src/ot2_cherrypick_mcp/` (28 instances found)
- Risk: Error handling code never executed in tests, may have bugs
- Priority: Medium - defensive code but still should be exercised

---

*Concerns audit: 2026-01-20*
