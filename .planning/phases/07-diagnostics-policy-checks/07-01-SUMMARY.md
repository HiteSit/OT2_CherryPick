---
phase: 07-diagnostics-policy-checks
plan: 01
subsystem: testing
tags: [python, pytest, diagnostics, coverage, simulation-logs]

# Dependency graph
requires:
  - phase: 06-transfer-mapping-validation
    provides: CSV-derived transfer expectations and baseline matching
provides:
  - Row-indexed ExpectedTransfer metadata for diagnostics
  - CSV row coverage reporting for fixture validation
affects: [07-diagnostics-policy-checks, 08-test-suite-refactor]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Row-indexed coverage computed from ExpectedTransfer metadata
    - Semantic transfer diagnostics tied to match metadata

key-files:
  created:
    - tests/simulation_logs/diagnostics.py
  modified:
    - tests/simulation_logs/expectations.py
    - tests/simulation_logs/matching.py
    - tests/simulation_logs/__init__.py
    - tests/test_transfer_mapping.py

key-decisions:
  - "None - followed plan as specified"

patterns-established:
  - "CSV row coverage computed from missing/mismatched ExpectedTransfer lists"
  - "Row-aware diagnostic labels in match reports"

# Metrics
duration: 1 min
completed: 2026-01-27
---

# Phase 7 Plan 1: Diagnostics + Policy Checks Summary

**Row-indexed transfer expectations with coverage diagnostics and richer match metadata for fixture validation**

## Performance

- **Duration:** 1 min
- **Started:** 2026-01-27T14:43:37Z
- **Completed:** 2026-01-27T14:44:21Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Added row indexing to ExpectedTransfer and surfaced missing/mismatched objects for diagnostics
- Introduced diagnostics helpers for CSV row coverage and semantic failure reporting
- Updated transfer mapping tests to enforce coverage and emit row-aware reports

## Task Commits

Per repo policy, no commits were created. Planned commit messages:

1. **Task 1: Add CSV row indexing and match metadata** - `feat(07-01): add row-indexed match metadata`
2. **Task 2: Add diagnostics helpers and coverage reporting** - `feat(07-01): add coverage diagnostics helpers`

## Files Created/Modified
- `tests/simulation_logs/diagnostics.py` - Coverage computation and formatted diagnostics report helpers
- `tests/simulation_logs/expectations.py` - Added row_index metadata to ExpectedTransfer from CSV rows
- `tests/simulation_logs/matching.py` - MatchResult exposes missing/mismatched ExpectedTransfer lists and row-aware labels
- `tests/simulation_logs/__init__.py` - Exported diagnostics helpers for test use
- `tests/test_transfer_mapping.py` - Added coverage assertions and row-aware diagnostics in failures

## Decisions Made
None - followed plan as specified.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
Ready for 07-02-PLAN.md.

---
*Phase: 07-diagnostics-policy-checks*
*Completed: 2026-01-27*
