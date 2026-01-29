# Phase 10: Fixture Downstream Coverage - Research

**Researched:** 2026-01-28
**Domain:** Simulation log fixtures coverage across parse/match/policy tests
**Confidence:** HIGH

## Summary

This phase closes integration coverage gaps by ensuring every captured simulation fixture (from `tests/integration/simulation_logs/fixtures/manifest.json`) is exercised by downstream parse/match/policy tests. The repository already provides the full pipeline: versioned log adapter parsing, normalization with settings profiles, transfer expectation building from CSVs, semantic match reports, row coverage metrics, and policy evaluations. The gap is fixture coverage, not missing primitives.

The standard approach should be manifest-driven: iterate all fixtures, map each to expected transfers and parsed events, and assert match/coverage/policy behavior according to `expect_failure`. This preserves the Phase 4 decision to use captured fixtures as the baseline and the Phase 6 decision to fail on extra events by default.

**Primary recommendation:** Add manifest-parametrized downstream tests that route each fixture through `parse_fixture_entry` + `build_expected_transfers_for_entry` + `match_transfers` + `evaluate_policies`, with explicit handling for `expect_failure` fixtures.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pytest | >=8.4.2,<9 | Test runner and fixtures | Already used throughout tests and pinned in `pyproject.toml` |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| tests.support.fixtures | repo | Manifest loader + fixture metadata | Use `load_manifest()` to drive fixture param lists |
| tests.support.simulation | repo | Fixture parsing + expectations helpers | Use `build_expected_transfers_for_entry()` and `parse_fixture_entry()` |
| tests.unit.simulation_logs.* | repo | Parse/normalize/match/diagnostics/policies | Use `match_transfers`, `format_transfer_report`, `evaluate_policies` |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Manifest-driven fixture lists | Hard-coded fixture IDs per test | Easy to add a test but easy to miss fixtures and drift from manifest |

**Installation:**
```bash
uv run python -m pip install -e .
```

## Architecture Patterns

### Recommended Project Structure
```
tests/
├── integration/simulation_logs/fixtures/   # Captured stdout/stderr + manifest
├── support/                                # load_manifest + fixture helpers
├── unit/simulation_logs/                   # parse/normalize/match/policy primitives
└── unit/transfer_mapping/                  # fixture-driven downstream assertions
```

### Pattern 1: Manifest-Driven Fixture Matrix
**What:** Load the fixture manifest and parametrize tests over its entries so coverage grows with the manifest.
**When to use:** Any test that should run on every captured fixture.
**Example:**
```python
# Source: tests.support.fixtures + tests.support.simulation
entries = load_manifest()
@pytest.mark.parametrize("entry", entries, ids=lambda e: e.fixture_id)
def test_fixture_downstream(entry):
    expected = build_expected_transfers_for_entry(entry)
    parsed = parse_fixture_entry(entry)
```

### Pattern 2: Parse -> Normalize -> Match -> Coverage
**What:** Use normalized events for semantic matching and assert coverage with diagnostics.
**When to use:** Any downstream transfer validation for fixtures.
**Example:**
```python
# Source: tests/unit/transfer_mapping/test_transfer_mapping.py
match = match_transfers(expectations, result.events)
coverage = compute_row_coverage(expectations, match)
assert match.success, format_transfer_report(match, expectations)
assert coverage.covered_rows == coverage.total_rows, format_row_coverage(coverage)
```

### Pattern 3: Policy Evaluation from CSV Intent
**What:** Evaluate tip reuse, mix, and air gap policies based on CSV intent columns.
**When to use:** Fixtures with policy intent in CSVs, or to assert warnings for missing intent.
**Example:**
```python
# Source: tests/unit/transfer_mapping/test_transfer_policies.py
result = evaluate_policies(expected, match, events, csv_path, settings)
assert not result.errors, result.summary()
```

### Pattern 4: Expected-Failure Fixture Handling
**What:** Treat `expect_failure` fixtures as negative tests: parsing should run, matching should fail, and diagnostics should explain why.
**When to use:** Fixtures like `invalid-labware` with non-zero simulator return codes.
**Example:**
```python
# Source: tests/integration/simulation_logs/test_simulation_log_fixtures.py
if entry.expect_failure:
    assert returncode != 0
```

### Anti-Patterns to Avoid
- **Hard-coded fixture subsets:** Leads to fixtures like `extreme-single_x1` and `invalid-labware` being untested downstream.
- **Bypassing diagnostics:** Asserting only booleans hides missing/mismatched/extra transfer details.
- **Allowing extra events by default:** Violates Phase 6; keep `allow_extra_events=False` unless explicitly needed.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Fixture selection | Manual lists per test | `load_manifest()` | Keeps tests aligned with captured fixtures |
| Fixture parsing | Manual stdout/stderr handling | `parse_fixture_entry()` | Centralized parsing + normalization by settings profile |
| Expectations | Hand-built expected transfers | `build_expected_transfers_for_entry()` | Handles distribution, air gaps, HOME rows |
| Diagnostics | Custom output formatting | `format_transfer_report()` / `format_row_coverage()` | Consistent semantic failure reporting |
| Policy checks | Custom tip/mix/air-gap logic | `evaluate_policies()` | Standardized policy errors and warnings |

**Key insight:** The repo already encodes fixture semantics; reusing helpers prevents drift and guarantees fixture coverage scales with the manifest.

## Common Pitfalls

### Pitfall 1: Fixtures added to manifest but not downstream tests
**What goes wrong:** New fixture folders are captured but never validated by parse/match/policy tests.
**Why it happens:** Tests use hard-coded fixture IDs instead of `load_manifest()`.
**How to avoid:** Parametrize downstream tests over manifest entries, then branch on `expect_failure`.
**Warning signs:** `manifest.json` contains fixture IDs that never appear in test files (e.g., `extreme-single_x1`).

### Pitfall 2: Expected-failure fixtures treated as success
**What goes wrong:** Downstream tests assert `match.success` on fixtures like `invalid-labware`.
**Why it happens:** Tests assume every fixture has valid events.
**How to avoid:** For `expect_failure`, assert parse warnings and a non-success match with missing transfers.
**Warning signs:** `invalid-labware` causes test failures or is excluded entirely.

### Pitfall 3: Policy checks silently skipped
**What goes wrong:** Policy tests show only warnings because CSVs lack intent columns.
**Why it happens:** `evaluate_policies` warns and exits when intent columns are missing.
**How to avoid:** Either ensure fixture CSVs include `Tip Action`, `Mix Volume`, or `Air Gap`, or explicitly assert warnings.
**Warning signs:** Policy tests pass with zero errors but output includes warnings about missing intent.

## Code Examples

Verified patterns from project sources:

### Fixture Context Builder
```python
# Source: tests/support/simulation.py
expected_transfers = build_expected_transfers_for_entry(entry)
parsed_result = parse_fixture_entry(entry)
csv_path = resolve_fixture_csv(entry)
settings = load_settings_profile(entry.settings_profile)
```

### Transfer Match + Coverage
```python
# Source: tests/unit/transfer_mapping/test_transfer_mapping.py
match = match_transfers(expectations, result.events)
coverage = compute_row_coverage(expectations, match)
assert match.success, format_transfer_report(match, expectations)
assert coverage.covered_rows == coverage.total_rows, format_row_coverage(coverage)
```

### Policy Evaluation
```python
# Source: tests/unit/transfer_mapping/test_transfer_policies.py
result = evaluate_policies(expected, match, events, csv_path, settings)
assert not result.errors, result.summary()
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Fixture IDs hard-coded per test | Manifest-driven parametrization across downstream tests | Phase 10 (planned) | Ensures every captured fixture is validated by parse/match/policy |

**Deprecated/outdated:**
- Fixture coverage inferred from integration capture alone: does not prove downstream parsing/matching/policy correctness.

## Open Questions

1. **How should `expect_failure` fixtures be validated downstream?**
   - What we know: `invalid-labware` has a non-zero simulator return code and stderr errors.
   - What's unclear: Whether downstream tests should only assert warnings/no events or also assert a specific failure signature in match diagnostics.
   - Recommendation: Decide a minimal failure contract (e.g., parse warnings present + match fails with missing transfers) and codify it.

2. **Should all fixtures be required to exercise policy checks?**
   - What we know: `evaluate_policies` warns when CSV intent is missing.
   - What's unclear: Whether warnings are acceptable or fixtures should be augmented to include policy intent columns.
   - Recommendation: Define a policy coverage target (e.g., at least one fixture per policy vs every fixture).

## Sources

### Primary (HIGH confidence)
- `tests/integration/simulation_logs/fixtures/manifest.json` - fixture inventory and `expect_failure` flags
- `tests/support/fixtures.py` - fixture manifest loader and capture helpers
- `tests/support/simulation.py` - fixture parsing/expectation helpers
- `tests/unit/simulation_logs/parse.py` - fixture parsing + normalization pipeline
- `tests/unit/simulation_logs/matching.py` - transfer matching (extra events default off)
- `tests/unit/simulation_logs/diagnostics.py` - row coverage + transfer report formatting
- `tests/unit/simulation_logs/policies.py` - tip/mix/air gap policy evaluation
- `tests/unit/transfer_mapping/test_transfer_mapping.py` - downstream match/coverage assertions
- `tests/unit/transfer_mapping/test_transfer_policies.py` - downstream policy assertions

### Secondary (MEDIUM confidence)
- None

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Versions and utilities confirmed in `pyproject.toml` and test modules
- Architecture: HIGH - Patterns derived from existing tests and fixture helpers
- Pitfalls: MEDIUM - Inferred from current coverage gaps and fixture metadata

**Research date:** 2026-01-28
**Valid until:** 2026-02-27
