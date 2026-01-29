# Phase 09: Diagnostics + Policy Verification - Research

**Researched:** 2026-01-28
**Domain:** Simulation log diagnostics, CSV transfer coverage, policy verification tests
**Confidence:** HIGH

## Summary

This phase is about tightening diagnostics and policy verification in the simulation-log test pipeline. The repo already has structured parsing (versioned adapter -> normalized events), transfer matching with semantic reports, CSV row coverage metrics, and policy checks for tip reuse, mix, and air gap. The plan should wire these into the test suite so failures produce actionable summaries and coverage metrics that show which CSV rows are validated.

The established approach uses captured simulation fixtures as the baseline (Phase 4 decision) and validates against parsed events. Transfer matching currently fails on extra events unless `allow_extra_events=True` (Phase 6 decision). Diagnostics should consistently report missing/mismatched/extra transfers plus per-row coverage. Policy checks should compare CSV intent (Tip Action, Mix Volume, Air Gap) to observed normalized events and surface errors/warnings.

**Primary recommendation:** Use the existing `tests/unit/simulation_logs` pipeline (parse -> normalize -> match -> diagnostics -> policies) and ensure tests assert `format_transfer_report` and row coverage outputs on failure.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pytest | >=8.4.2,<9 | Test runner and assertions | Already in `pyproject.toml` and used across diagnostics/policy tests |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| tomllib | Python 3.12 stdlib | Parse settings profiles for normalization | Use for settings in fixture parsing and normalization |
| csv | Python stdlib | Parse CSV rows into transfer expectations | Use for CSV intent extraction (`parse_csv_rows`) |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| pytest | unittest | Loses existing fixtures/param patterns already used in repo |

**Installation:**
```bash
uv run python -m pip install -e .
```

## Architecture Patterns

### Recommended Project Structure
```
tests/
├── unit/simulation_logs/     # parse/normalize/match/diagnostics/policies
├── unit/transfer_mapping/    # assertions for coverage + semantic reports
├── integration/simulation_logs/fixtures/  # captured stdout/stderr fixtures
└── support/                  # fixture loaders, path helpers, settings profiles
```

### Pattern 1: Parse -> Normalize -> Match
**What:** Parse simulator stdout/stderr with a versioned adapter, normalize using settings (labware slot map, pipette mapping), then match against expected transfers.
**When to use:** Any diagnostics or policy verification that compares CSV intent to simulator output.
**Example:**
```python
# Source: tests/unit/simulation_logs/parse.py
result = parse_fixture("basic-single_x1")
expected = build_expected_transfers(csv_path, settings)
match = match_transfers(expected, result.events, allow_extra_events=False)
```

### Pattern 2: Semantic Failure Report + Row Coverage
**What:** Use `MatchResult.report()` for expected vs observed summaries and `compute_row_coverage` for per-CSV-row coverage metrics.
**When to use:** Test assertions so failures print actionable diagnostics (DIAG-02, DIAG-03).
**Example:**
```python
# Source: tests/unit/transfer_mapping/test_transfer_mapping.py
match = match_transfers(expectations, result.events)
coverage = compute_row_coverage(expectations, match)
assert match.success, format_transfer_report(match, expectations)
assert coverage.covered_rows == coverage.total_rows, format_row_coverage(coverage)
```

### Pattern 3: Policy Checks from CSV Intent
**What:** Extract CSV intent per row (Tip Action, Mix Volume, Air Gap) and verify against normalized events.
**When to use:** Enforce POL-01 behavior with explicit policy errors/warnings.
**Example:**
```python
# Source: tests/unit/simulation_logs/policies.py
result = evaluate_policies(expected_transfers, match, events, csv_path, settings)
assert not result.errors, result.summary()
```

### Anti-Patterns to Avoid
- **Bypass normalized events:** Comparing raw stdout lines to expectations is brittle; always normalize via `normalize_events`.
- **Silent failures:** Do not assert plain booleans; include `format_transfer_report` or `result.summary()` to preserve semantic diagnostics.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Transfer matching | Custom matching in tests | `match_transfers` | Handles ordering, distribution groups, and split transfers |
| CSV row coverage | Ad-hoc counters | `compute_row_coverage` / `format_row_coverage` | Uses `row_index` mapping and combines missing/mismatched rows |
| Policy checks | Custom tip/mix/air-gap logic | `evaluate_policies` | Encodes CSV intent parsing and standardized errors/warnings |
| Log parsing | Regex per test | `tests/unit/simulation_logs/adapters/v8_7_0.py` + `parse_fixture` | Centralized parsing with simulator version metadata |

**Key insight:** Diagnostics quality depends on shared utilities; duplicating logic increases drift and hides coverage gaps.

## Common Pitfalls

### Pitfall 1: Coverage counts ignore HOME rows
**What goes wrong:** Coverage percent looks inflated if HOME rows are included in totals.
**Why it happens:** HOME rows are intentionally skipped in expectations; counting them breaks row metrics.
**How to avoid:** Use `compute_row_coverage` which only counts rows with `row_index`.
**Warning signs:** Coverage percent doesn’t drop when HOME rows are missing.

### Pitfall 2: Extra events accidentally pass
**What goes wrong:** Extra aspirate/dispense events are ignored.
**Why it happens:** Passing `allow_extra_events=True` globally or skipping `match.extra`.
**How to avoid:** Default `allow_extra_events=False` unless explicitly overridden (Phase 6 decision).
**Warning signs:** `MatchResult.extra` non-empty but test still passes.

### Pitfall 3: Policy checks skipped due to missing intent
**What goes wrong:** Tip reuse/mix/air gap checks are skipped because CSV lacks intent columns or values.
**Why it happens:** `evaluate_policies` warns and exits for missing intent.
**How to avoid:** Ensure fixture CSVs include `Tip Action`, `Mix Volume`, or `Air Gap` when policy coverage is required.
**Warning signs:** Policy summary shows warnings but tests assert only on errors.

## Code Examples

Verified patterns from project sources:

### Semantic Transfer Report
```python
# Source: tests/unit/simulation_logs/matching.py
match = match_transfers(expected_transfers, events, allow_extra_events=False)
if not match.success:
    print(match.report())
```

### Row Coverage Summary
```python
# Source: tests/unit/simulation_logs/diagnostics.py
coverage = compute_row_coverage(expected_transfers, match)
summary = format_row_coverage(coverage)
```

### Policy Evaluation
```python
# Source: tests/unit/simulation_logs/policies.py
result = evaluate_policies(expected_transfers, match, events, csv_path, settings)
assert not result.errors, result.summary()
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Ad-hoc stdout assertions | Versioned fixture parsing + normalized events | Unknown | Stable, repeatable diagnostics tied to fixtures |

**Deprecated/outdated:**
- Raw line-by-line matching of simulator output: replaced by adapter + normalized events.

## Open Questions

1. **Should policy checks use `settings.general.tip_reuse` when `Tip Action` is missing?**
   - What we know: `evaluate_policies` currently only uses CSV intent and warns if intent missing.
   - What's unclear: Whether settings-level defaults should enforce policy when CSV omits intent.
   - Recommendation: Decide policy source of truth; if settings should apply, extend `_evaluate_tip_reuse` accordingly and update fixtures.

2. **Coverage metrics for distribution rows vs per-destination wells**
   - What we know: Coverage is per CSV row (`row_index`), not per destination well.
   - What's unclear: Whether DIAG-03 expects per-row or per-destination coverage for distribution transfers.
   - Recommendation: Confirm requirement; if per-destination is required, add a second metric based on `ExpectedTransfer` count.

## Sources

### Primary (HIGH confidence)
- `tests/unit/simulation_logs/matching.py` - semantic transfer matching and `allow_extra_events` behavior
- `tests/unit/simulation_logs/diagnostics.py` - row coverage metrics and formatted reports
- `tests/unit/simulation_logs/policies.py` - tip/mix/air gap policy evaluation
- `tests/unit/transfer_mapping/test_transfer_mapping.py` - assertions for diagnostics and coverage
- `tests/integration/simulation_logs/fixtures/manifest.json` - fixture baseline coverage

### Secondary (MEDIUM confidence)
- None

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Versions and usage confirmed in `pyproject.toml` and tests
- Architecture: HIGH - Derived directly from existing test modules and fixtures
- Pitfalls: MEDIUM - Inferred from behavior and tests, not explicitly documented

**Research date:** 2026-01-28
**Valid until:** 2026-02-27
