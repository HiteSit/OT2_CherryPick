# Phase 11: Backfill Phase 7 Verification - Research

**Researched:** 2026-01-29
**Domain:** Phase verification reporting for diagnostics/policy checks (DIAG-02/03, POL-01)
**Confidence:** HIGH

## Summary

This phase is strictly about producing a missing verification report for Phase 7 diagnostics and policy checks. The evidence already exists in the current unit test layout (post-Phase 8 refactor) and in the verification report format used for other phases. The plan should point to the specific unit tests and helpers that demonstrate DIAG-02, DIAG-03, and POL-01, and mirror the existing verification report schema (Observable Truths, Required Artifacts, Key Links, Requirements Coverage).

Verification should cite the unit transfer mapping tests for semantic failure reporting and row coverage (DIAG-02/DIAG-03), and the unit transfer policy tests for tip reuse, mix, and air gap intent checks (POL-01). The matching logic defaults to failing on extra transfer events unless `allow_extra_events` is true, which is a Phase 6 decision that should be reflected in the verification narrative.

**Primary recommendation:** Use the existing verification report template from other phases and anchor evidence to `tests/unit/transfer_mapping/*` plus `tests/unit/simulation_logs/*` modules that implement diagnostics, coverage, and policy checks.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | >=3.12,<3.13 | Verification tooling + test execution | Project runtime (`pyproject.toml`) |
| pytest | >=8.4.2,<9 | Assert verification evidence in tests | Project test harness (`pyproject.toml`) |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| uv | managed | Run tests in repo venv | Use `uv run pytest` for verification runs |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Unit test evidence | Manual log inspection | Manual verification is slower and less repeatable |

**Installation:**
```bash
uv run pytest tests/unit/transfer_mapping/test_transfer_mapping.py tests/unit/transfer_mapping/test_transfer_policies.py
```

## Architecture Patterns

### Recommended Project Structure
```
.planning/phases/11-backfill-phase-7-verification/
└── 11-RESEARCH.md          # This research file
tests/unit/transfer_mapping/
├── test_transfer_mapping.py    # Diagnostics + coverage evidence
└── test_transfer_policies.py   # Policy checks evidence
tests/unit/simulation_logs/
├── diagnostics.py              # Coverage + report formatting
├── matching.py                 # MatchResult + report semantics
└── policies.py                 # Tip reuse/mix/air gap policy checks
```

### Pattern 1: Verification Report Mirrors Existing Templates
**What:** Use the same verification sections as other phases (Observable Truths, Required Artifacts, Key Links, Requirements Coverage, Gaps Summary).
**When to use:** Always; this backfill should be format-consistent with Phase 08–10 verification reports.
**Example:**
```markdown
// Source: .planning/phases/09-diagnostics-policy-verification/09-diagnostics-policy-verification-VERIFICATION.md
### Observable Truths
| # | Truth | Status | Evidence |
```

### Pattern 2: Diagnostics Evidence From Transfer Mapping Tests
**What:** Prove DIAG-02/DIAG-03 using `test_transfer_mapping.py` with `format_transfer_report` and `format_row_coverage`.
**When to use:** For semantic expected-vs-observed transfer failure summaries and row coverage metrics.
**Example:**
```python
// Source: tests/unit/transfer_mapping/test_transfer_mapping.py
report = format_transfer_report(match, mutated)
assert "Missing:" in report
assert "Mismatched:" in report
assert "Extra:" in report
assert "Coverage:" in report
```

### Pattern 3: Policy Evidence From Policy Tests
**What:** Prove POL-01 using `test_transfer_policies.py` and `evaluate_policies`.
**When to use:** Tip reuse, mix, and air gap intent validation against CSV/settings intent.
**Example:**
```python
// Source: tests/unit/transfer_mapping/test_transfer_policies.py
result = evaluate_policies(expected, match, parsed.events, csv_path, settings)
assert not result.errors, result.summary()
```

### Anti-Patterns to Avoid
- **Referencing pre-refactor paths:** Phase 8 moved modules to `tests/unit/*`; don’t cite legacy `tests/simulation_logs/*` paths.
- **Omitting evidence gating:** Policy checks warn/skip when evidence is missing; verification should not imply hard failures for warnings.
- **Ignoring extra-event default:** `match_transfers` fails on extra events unless `allow_extra_events=True`.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Verification report format | New custom structure | Existing `*-VERIFICATION.md` schema | Consistency across phases |
| Diagnostics evidence | Manual log parsing | Unit tests + `format_transfer_report` | Already asserts semantic sections |
| Coverage metrics | Custom counting | `compute_row_coverage` | Uses row_index + missing/mismatched transfers |
| Policy evaluation | Ad-hoc checks | `evaluate_policies` + tests | Evidence-gated and row-aware |

**Key insight:** Phase 7 functionality is already proven by unit tests; verification should document and cite those tests rather than re-deriving logic.

## Common Pitfalls

### Pitfall 1: Using outdated file paths
**What goes wrong:** Verification points to `tests/simulation_logs/*` which no longer exists after Phase 8.
**Why it happens:** Phase 7 plans referenced pre-refactor paths.
**How to avoid:** Cite `tests/unit/simulation_logs/*` and `tests/unit/transfer_mapping/*` in the verification report.
**Warning signs:** Evidence links 404 or mismatch with current repo tree.

### Pitfall 2: Missing row coverage evidence
**What goes wrong:** DIAG-03 is claimed without pointing to row coverage reporting.
**Why it happens:** The diagnostic report combines match report and coverage; both must be cited.
**How to avoid:** Use `format_transfer_report`/`format_row_coverage` evidence from `test_transfer_mapping.py`.
**Warning signs:** No explicit mention of `Coverage:` or `compute_row_coverage` in evidence.

### Pitfall 3: Overstating policy enforcement
**What goes wrong:** Report implies hard failures for policy checks even when evidence is missing.
**Why it happens:** `evaluate_policies` produces warnings for missing evidence and skips enforcement.
**How to avoid:** In verification, note warning-only behavior for missing evidence.
**Warning signs:** No mention of warnings or evidence gating in POL-01 proof.

## Code Examples

Verified patterns from repo tests:

### Semantic Failure Report + Coverage
```python
// Source: tests/unit/transfer_mapping/test_transfer_mapping.py
report = format_transfer_report(match, mutated)
assert "Missing:" in report
assert "Mismatched:" in report
assert "Extra:" in report
assert "Coverage:" in report
```

### Policy Evaluation Entry Point
```python
// Source: tests/unit/simulation_logs/policies.py
def evaluate_policies(expected_transfers, match_result, events, csv_path, settings) -> PolicyResult:
    intents = _load_row_intents(csv_path)
    _evaluate_tip_reuse(intents, events, errors, warnings)
    _evaluate_mix(intents, events, errors, warnings)
    _evaluate_air_gap(intents, match_result, expected_transfers, errors, warnings)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `tests/simulation_logs/*` modules | `tests/unit/simulation_logs/*` modules | Phase 8 refactor | Verification must cite new paths |

**Deprecated/outdated:**
- Legacy `tests/simulation_logs/*` references in Phase 7 plans; use `tests/unit/*` paths now.

## Open Questions

1. **Should the Phase 7 verification report explicitly map old paths to new paths?**
   - What we know: Phase 7 plans cite `tests/simulation_logs/*`; Phase 8 moved them to `tests/unit/simulation_logs/*`.
   - What's unclear: Whether the verification report must show the mapping or just cite current paths.
   - Recommendation: Use current paths and add a brief note in the report that Phase 8 refactor moved the modules.

## Sources

### Primary (HIGH confidence)
- `tests/unit/transfer_mapping/test_transfer_mapping.py` - semantic transfer report + coverage assertions
- `tests/unit/transfer_mapping/test_transfer_policies.py` - tip reuse/mix/air gap policy evidence
- `tests/unit/simulation_logs/diagnostics.py` - row coverage computation + report formatting
- `tests/unit/simulation_logs/matching.py` - MatchResult report structure + extra-event default
- `tests/unit/simulation_logs/policies.py` - policy evaluation + evidence gating
- `.planning/phases/09-diagnostics-policy-verification/09-diagnostics-policy-verification-VERIFICATION.md` - verification report format reference
- `pyproject.toml` - Python/pytest versions

### Secondary (MEDIUM confidence)
- None

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - versions explicitly in `pyproject.toml`
- Architecture: HIGH - verification report format established in prior phases
- Pitfalls: MEDIUM - inferred from refactor and evidence-gated policy behavior

**Research date:** 2026-01-29
**Valid until:** 2026-02-28
