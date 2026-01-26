# Phase 4: Log Capture Baseline - Context

**Gathered:** 2026-01-26
**Status:** Ready for planning

<domain>
## Phase Boundary

Capture `opentrons_simulate` output as reusable fixtures and ensure simulation warnings/errors fail tests with clear context. No parsing or validation logic yet.

</domain>

<decisions>
## Implementation Decisions

### Simulation command usage
- Use `simulate_protocol.sh` as the canonical runner for fixture capture
- Always run the helper step to regenerate `CherryPick_OT2.py` before simulation
- Never use `--send-to-opentrons` during fixture runs (simulation only)
- Capture stdout/stderr even when simulation fails

### Labware path handling
- Source the Windows labware path from `simulate_protocol.sh` machine configuration
- Validate that required labware JSON definitions exist in the labware directory

### Fixture matrix
- Capture a broad fixture set from existing CSVs, but skip dual-mode CSVs
- Add extra fixtures for mode-boundary cases, labware variety, liquid-handling extremes, and intentional failure cases
- Settings.toml should vary across fixtures to cover differing labware positions

### Log capture rules
- Store fixture metadata alongside logs (CSV name, settings variant, simulator version, labware path, etc.)

### OpenCode's Discretion
- Fail-fast vs skip behavior when labware path is missing
- Whether to store resolved WSL path in fixture metadata
- Log format (raw vs normalized), stdout/stderr separation, and normalization rules
- Additional custom fixture scenarios beyond the listed categories

</decisions>

<specifics>
## Specific Ideas

- Before planning, review `opentrons_simulate -h` and run `simulate_protocol.sh` across multiple settings/CSV combinations to observe real stdout/stderr patterns.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 04-log-capture-baseline*
*Context gathered: 2026-01-26*
