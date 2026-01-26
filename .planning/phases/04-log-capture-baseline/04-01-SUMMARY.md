---
phase: 04-log-capture-baseline
plan: 01
subsystem: testing
tags: [pytest, opentrons_simulate, fixtures, simulation]

# Dependency graph
requires:
  - phase: 03-polish
    provides: GUI baseline and pytest harness
provides:
  - Simulation fixture manifest for capture coverage
  - Capture helper with settings swap and metadata capture
  - Pytest coverage for log fixtures and warning surfacing
affects: [structured event parsing, transfer mapping validation, diagnostics]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Manifest-driven simulation fixture capture via simulate_protocol.sh"
    - "Settings profile swap for per-fixture simulation runs"

key-files:
  created:
    - tests/fixtures/simulation/manifest.json
    - tests/fixtures/csvs/invalid_labware.csv
    - tests/e2e/configs/liquid_extreme/settings.toml
    - tests/fixtures/simulation/capture.py
    - tests/fixtures/simulation/__init__.py
    - tests/e2e/test_simulation_log_fixtures.py
  modified: []

key-decisions:
  - "None - followed plan as specified"

patterns-established:
  - "Simulation fixtures stored with stdout.txt, stderr.txt, metadata.json per fixture"

# Metrics
duration: 7 min
completed: 2026-01-26
---

# Phase 4 Plan 01: Log Capture Baseline Summary

**Manifest-driven log capture fixtures with metadata, settings profile swapping, and pytest checks that fail on simulator warnings/errors.**

## Performance

- **Duration:** 7 min
- **Started:** 2026-01-26T08:29:43Z
- **Completed:** 2026-01-26T08:36:55Z
- **Tasks:** 3
- **Files modified:** 6

## Accomplishments
- Defined a fixture matrix covering mode boundaries, labware variety, liquid handling extremes, and failure cases.
- Implemented a capture helper that resolves labware paths, swaps settings profiles, and stores stdout/stderr plus metadata.
- Added pytest coverage that reuses fixtures or refreshes them, and fails on warnings/errors with log excerpts.

## Task Commits

Each task was committed atomically:

1. **Task 1: Define fixture matrix and coverage assets** - `13018e3` (test)
2. **Task 2: Implement simulation fixture capture helper** - `5f5b56a` (feat)
3. **Task 3: Add pytest coverage for fixture capture and error surfacing** - `993d1cc` (test)

**Plan metadata:** Pending

_Note: TDD tasks may have multiple commits (test → feat → refactor)_

## Files Created/Modified
- `tests/fixtures/simulation/manifest.json` - Fixture matrix defining CSV/settings coverage and failure cases.
- `tests/fixtures/csvs/invalid_labware.csv` - Intentional failure CSV with unknown labware IDs.
- `tests/e2e/configs/liquid_extreme/settings.toml` - Extreme liquid handling profile for stress coverage.
- `tests/fixtures/simulation/capture.py` - Helper to run simulate_protocol.sh, swap settings, and write logs/metadata.
- `tests/fixtures/simulation/__init__.py` - Export capture helpers for tests.
- `tests/e2e/test_simulation_log_fixtures.py` - Pytest coverage for fixture capture reuse/refresh and warning detection.

## Decisions Made
None - followed plan as specified.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Simulation fixture capture test not executed here because `opentrons_simulate` requires a valid labware directory; run on a machine with labware JSONs to refresh fixtures.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
Baseline fixtures and capture harness are ready; run the fixture capture test on a machine with valid labware JSONs to populate stdout/stderr baselines before starting structured parsing work.

---
*Phase: 04-log-capture-baseline*
*Completed: 2026-01-26*
