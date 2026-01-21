---
phase: 03-polish
plan: 01
subsystem: ui
tags: [react, mantine, csv, empty-state, ux]

# Dependency graph
requires:
  - phase: 02-data-safety
    provides: CSV dropdown with file selection and unsaved changes protection
provides:
  - Empty state detection when CSV directory has no files
  - Disabled dropdown with "No CSV files found" placeholder
  - Emphasized Upload CSV button (filled variant) when empty
  - Graceful UX degradation maintaining full editor functionality
affects: [03-polish]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Conditional UI variants based on data availability"
    - "isEmpty derivation pattern for empty state detection"

key-files:
  created: []
  modified:
    - src/gui/frontend/src/components/wizard/csv/CsvEditor.tsx

key-decisions:
  - "Use isEmpty derivation from csvListQuery.data.files.length === 0"
  - "Disable dropdown when isEmpty or isLoading to prevent interaction"
  - "Use filled variant for FileInput to visually emphasize upload action"
  - "Conditional placeholder: 'No CSV files found' vs 'Choose a file or type to search'"

patterns-established:
  - "Empty state pattern: derive isEmpty from query data, use for conditional rendering"
  - "Visual emphasis pattern: use filled variant for primary action when alternatives unavailable"

# Metrics
duration: 5min
completed: 2026-01-21
---

# Phase 03 Plan 01: Empty State Handling Summary

**CSV dropdown gracefully handles empty directory with disabled state and emphasized upload button**

## Performance

- **Duration:** 5 min
- **Started:** 2026-01-21T10:27:11Z
- **Completed:** 2026-01-21T10:32:37Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments
- User sees clear "No CSV files found" message when directory is empty
- Dropdown is disabled (non-interactive) when no files exist
- Upload CSV button is visually emphasized with filled variant when empty
- Editor remains fully functional for manual CSV creation regardless of empty state
- No regressions to existing Phase 1 and Phase 2 functionality

## Task Commits

Each task was committed atomically:

1. **Task 1: Add empty state detection and disabled dropdown** - `b164259` (feat)
2. **Task 2: Emphasize Upload CSV button when dropdown is empty** - `ab001e1` (feat)

## Files Created/Modified
- `src/gui/frontend/src/components/wizard/csv/CsvEditor.tsx` - Added isEmpty derivation, conditional disabled prop, conditional placeholder, conditional FileInput variant

## Decisions Made

**1. isEmpty derivation pattern**
- Derive from `csvListQuery.data !== undefined && csvListQuery.data.files.length === 0`
- Checks both that data is loaded (not undefined) AND that files array is empty
- Prevents false positives during initial loading state

**2. Conditional placeholder text**
- "No CSV files found" when empty (clear communication of state)
- "Choose a file or type to search" when files exist (normal interaction)
- User immediately understands why dropdown is disabled

**3. Filled variant for visual emphasis**
- FileInput uses `variant={isEmpty ? "filled" : "default"}`
- Filled variant provides solid background, draws attention to upload action
- Only emphasized when dropdown is empty (no files to select)

**4. Disabled state behavior**
- Dropdown disabled when `csvListQuery.isLoading || isEmpty`
- Prevents interaction attempts when no files available
- Maintains consistent UI layout (dropdown still renders, not hidden)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - implementation was straightforward with existing infrastructure.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Ready for 03-02 (auto-select first file when only one exists):
- Empty state handling complete
- Conditional rendering patterns established
- csvOptions and isEmpty derivations ready for single-file detection
- No blockers or concerns

---
*Phase: 03-polish*
*Completed: 2026-01-21*
