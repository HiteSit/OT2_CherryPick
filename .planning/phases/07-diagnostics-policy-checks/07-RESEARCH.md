# Phase 7: Diagnostics + Policy Checks - Research

**Researched:** 2026-01-27
**Domain:** OT-2 simulation log diagnostics, coverage, and liquid-handling policy checks
**Confidence:** MEDIUM

## Summary

This phase should be implemented by parsing `opentrons_simulate` stdout/stderr into typed events, normalizing them with settings-derived labware/pipette context, and comparing them against CSV-derived expectations. The repo already has a tested parsing/normalization/matching stack in `tests/simulation_logs/` that should be promoted or mirrored for production diagnostics instead of new parsers.

Diagnostics and policy checks should be evidence-driven: only assert policies that can be verified from simulator output. Missing or ambiguous evidence should produce warnings (per phase decision), not test failures. Coverage should be computed in terms of CSV rows by mapping expected transfers back to row-group IDs (the current expectation builder already tags distribution rows with `group_id`).

**Primary recommendation:** Reuse the existing simulation-log adapter → normalize → match pipeline, then layer policy checks and CSV-row coverage on top with explicit evidence gating.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | 3.12 | Runtime for diagnostics + tests | Project standard (`pyproject.toml`) |
| pytest | >=8.4.2,<9 | Test runner for policy failures | Project test harness |
| opentrons_simulate | 8.7.0 (fixtures) | Canonical simulator output | Current fixtures target this output format |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| csv (stdlib) | stdlib | CSV parsing for expectations | Use for row-level coverage and intent parsing |
| re (stdlib) | stdlib | Log line parsing | Use for adapter regexes per simulator version |
| dataclasses (stdlib) | stdlib | Typed event models | Use for normalized events and diagnostics records |
| tomllib (stdlib) | stdlib | Settings parsing for normalization | Use for slot/labware/pipette context |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Regex log adapters | Structured JSON logs | Not available from `opentrons_simulate` in this repo; would require different simulator output source |

**Installation:**
```bash
uv run pytest
```

## Architecture Patterns

### Recommended Project Structure
```
src/ot2_cherrypick_mcp/
├── diagnostics/        # New: log parsing, normalization, policy checks
├── core/               # Existing: simulation log capture
└── utils/              # Shared errors and helpers
tests/
└── simulation_logs/    # Existing: adapters + models + normalization + matching
```

### Pattern 1: Versioned Log Adapter → Normalized Events
**What:** Parse simulator output with a version-specific adapter, then normalize events with settings-derived labware and pipette context.
**When to use:** Always, because raw simulator output is unstructured and may change by version.
**Example:**
```python
# Source: tests/simulation_logs/parse.py
adapter = select_adapter(metadata)
stdout_result = adapter(stdout_text, source="stdout")
stderr_result = adapter(stderr_text, source="stderr")
raw_events = [*stdout_result.events, *stderr_result.events]
normalized = normalize_events(raw_events, settings)
```

### Pattern 2: CSV Expectations → Match Against Events
**What:** Build expected transfers from CSV + settings, then match to normalized aspirate/dispense events in sequence order.
**When to use:** For coverage and diagnostics (missing/mismatched/extra transfers).
**Example:**
```python
# Source: tests/simulation_logs/matching.py
match = match_transfers(expected_transfers, normalized_events)
if not match.success:
    raise AssertionError(match.report())
```

### Pattern 3: Evidence-Gated Policy Checks
**What:** Only enforce policies where the simulator output provides explicit evidence; otherwise warn and skip.
**When to use:** Tip reuse, mix, and air-gap checks.
**Example:**
```python
# Source: tests/simulation_logs/adapters/v8_7_0.py
if MIX_RE.match(line):
    events.append(MixEvent(...))
```

### Anti-Patterns to Avoid
- **Assuming evidence exists:** If a policy cannot be proven from stdout/stderr (e.g., air gap rate), emit a warning and skip.
- **Parsing without version adapters:** Simulator output changes; always route through `select_adapter`.
- **Ignoring settings context:** Slot-to-labware/pipette mapping is required to interpret events accurately.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Simulator log parsing | Ad-hoc string scanning | Versioned adapters in `tests/simulation_logs/adapters` | Regexes are centralized and tested per simulator version |
| Event normalization | Inline mapping logic | `normalize_events` in `tests/simulation_logs/normalize.py` | Ensures consistent labware/pipette inference |
| Transfer matching | Custom diff logic | `match_transfers` in `tests/simulation_logs/matching.py` | Handles order, distribution groups, split transfers |
| CSV expectation expansion | One-off CSV parsing | `build_expected_transfers` in `tests/simulation_logs/expectations.py` | Already handles air gap + distribution expansion |

**Key insight:** The repo already contains a working diagnostics pipeline in tests; reuse it to avoid drift between tests and runtime diagnostics.

## Common Pitfalls

### Pitfall 1: Simulator version drift
**What goes wrong:** Parsers fail to recognize new or reformatted simulator output lines.
**Why it happens:** The adapter is hardcoded for `opentrons_simulate 8.7.0` patterns.
**How to avoid:** Gate by `simulator_version` metadata and add new adapters when output changes.
**Warning signs:** Parse warnings spike; events lists are empty.

### Pitfall 2: Ambiguous tip lifecycle
**What goes wrong:** Tip reuse validation fails because drop/return events cannot be attributed to a specific pipette.
**Why it happens:** Tip drops rely on inferred `pipette_id` from the last pickup; missing pickups break inference.
**How to avoid:** Require a pickup before any aspirate/dispense; warn when `pipette_id` can’t be inferred.
**Warning signs:** Normalization raises “Unable to infer pipette for tip drop event”.

### Pitfall 3: Over-asserting air gap/mix policies
**What goes wrong:** Tests fail on policies that are not explicitly logged by the simulator.
**Why it happens:** `opentrons_simulate` logs aspirate/dispense/mix actions, but not every sub-action (e.g., air-gap rate).
**How to avoid:** Only check air gap presence/volume if it can be inferred from volume deltas; otherwise warn/skip.
**Warning signs:** Consistent “policy violation” where logs contain no relevant evidence.

### Pitfall 4: Coverage miscount for distribution rows
**What goes wrong:** Coverage is under- or over-counted by counting expanded transfers instead of CSV rows.
**Why it happens:** Distribution rows expand to multiple expected transfers.
**How to avoid:** Use `group_id` (e.g., `distribution-<row>`) to aggregate event coverage by source row.
**Warning signs:** Coverage > 100% or fluctuates with distribution count.

## Code Examples

Verified patterns from official sources (repo fixtures/tests):

### Parse + Normalize Simulation Logs
```python
# Source: tests/simulation_logs/parse.py
stdout_result = adapter(stdout_text, source="stdout")
stderr_result = adapter(stderr_text, source="stderr")
raw_events = [*stdout_result.events, *stderr_result.events]
normalized = normalize_events(raw_events, settings)
```

### Build Expected Transfers with Air Gap + Distribution Expansion
```python
# Source: tests/simulation_logs/expectations.py
air_gap_ul = _parse_float(row.get("Air Gap")) or 0.0
dispense_volume = volume + air_gap_ul
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Ad-hoc log parsing | Versioned adapters + normalization | repo tests (current) | Stable diagnostics tied to simulator output |
| Transfer checks only | Transfer + distribution group matching | repo tests (current) | Enables row-level coverage + policy checks |

**Deprecated/outdated:**
- Unversioned log parsing: brittle against simulator output changes.

## Open Questions

1. **Does `opentrons_simulate` output include explicit air-gap events?**
   - What we know: Current adapter patterns capture pick-up, drop, aspirate, dispense, mix lines only.
   - What's unclear: Whether newer simulator versions emit air-gap or blowout lines we should parse.
   - Recommendation: Check a fresh simulator log from the target environment and update adapters if needed.

2. **What simulator version will be used in CI/production?**
   - What we know: Fixtures target `opentrons_simulate 8.7.0`.
   - What's unclear: Whether CI and users run the same version.
   - Recommendation: Record simulator version in logs and add adapter coverage for any new version.

## Sources

### Primary (HIGH confidence)
- `tests/simulation_logs/parse.py` - adapter selection and normalization pipeline
- `tests/simulation_logs/expectations.py` - CSV expectations + air gap handling
- `tests/simulation_logs/matching.py` - transfer matching + diagnostics
- `tests/simulation_logs/adapters/v8_7_0.py` - regex patterns for simulator output
- `src/ot2_cherrypick_mcp/core/simulation.py` - log capture and storage

### Secondary (MEDIUM confidence)
- https://docs.opentrons.com/v2/cli.html - general protocol execution/simulation context (no log format specifics)

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: MEDIUM - versions inferred from repo and fixtures, simulator output not officially documented here
- Architecture: HIGH - based on existing repo pipeline in tests
- Pitfalls: MEDIUM - derived from known adapter limitations and normalization behavior

**Research date:** 2026-01-27
**Valid until:** 2026-02-26
