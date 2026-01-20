---
phase: 02-data-safety
plan: 01
subsystem: ui
tags: [react, mantine, typescript, modal, state-management]

# Dependency graph
requires:
  - phase: 01-core-selection
    provides: CSV file dropdown selector in CsvEditor
provides:
  - Dirty state detection comparing editorContent with originalContent
  - UnsavedChangesModal component with Discard/Cancel actions
  - File switch protection flow preventing data loss
affects: [02-02-auto-save-drafts, csv-editing, data-safety]

# Tech tracking
tech-stack:
  added: []
  patterns: [dirty-state-tracking, confirmation-modal-pattern]

key-files:
  created:
    - src/gui/frontend/src/components/wizard/csv/UnsavedChangesModal.tsx
  modified:
    - src/gui/frontend/src/components/wizard/csv/CsvEditor.tsx

key-decisions:
  - "Dirty state derived from editorContent !== originalContent comparison"
  - "Modal only appears when isDirty AND file selection differs from current"
  - "Cancel preserves current state, Discard proceeds with switch"
  - "originalContent reset when new file loads or selection cleared"

patterns-established:
  - "Confirmation modal pattern: opened state + onConfirm/onCancel handlers"
  - "Pending state pattern: store intended action until user confirms"
  - "Passive dirty detection: compare state without blocking normal editing"

# Metrics
duration: 7min
completed: 2026-01-20
---

# Phase 02 Plan 01: Unsaved Changes Detection and Warning Dialog Summary

**Dirty state tracking with confirmation modal prevents accidental data loss when switching CSV files**

## Performance

- **Duration:** 7 min
- **Started:** 2026-01-20T17:10:44Z
- **Completed:** 2026-01-20T17:17:39Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Added dirty state detection by comparing editor content with original loaded content
- Created UnsavedChangesModal component following LabwareModal pattern
- Integrated modal into file selection flow with Discard/Cancel actions
- Prevented accidental data loss when switching files with unsaved edits

## Task Commits

Each task was committed atomically:

1. **Task 1: Add dirty state tracking to CsvEditor** - `27aeaa6` (feat)
2. **Task 2: Create UnsavedChangesModal and integrate with CsvEditor** - `760af68` (feat)

## Files Created/Modified
- `src/gui/frontend/src/components/wizard/csv/UnsavedChangesModal.tsx` - Warning modal with Discard/Cancel buttons and alert icon
- `src/gui/frontend/src/components/wizard/csv/CsvEditor.tsx` - Added originalContent state, isDirty derivation, pendingFile flow, modal handlers and rendering

## Decisions Made

**1. Dirty state calculation**
- Derived as `selectedFile && editorContent !== originalContent`
- Only consider dirty when file IS selected (blank/new files aren't "dirty")
- Passive comparison without blocking normal text editing

**2. Modal trigger condition**
- Only show modal when `isDirty && newValue !== selectedFile`
- Allows switching when no edits exist or switching to same file (no-op)

**3. State management**
- `originalContent` stores server-loaded content as comparison baseline
- `pendingFile` stores intended selection while waiting for user decision
- Reset `originalContent` when clearing selection or loading new file

**4. Button labels**
- "Discard" (red button) for destructive action
- "Cancel" (default button) for safe action
- Per SAFE-02 requirement for clear action communication

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - TypeScript compiled successfully, all state transitions work as expected.

## Next Phase Readiness

- Unsaved changes protection complete
- Ready for auto-save drafts (02-02) which will build on dirty state detection
- Modal pattern established and can be reused for other confirmation dialogs

---
*Phase: 02-data-safety*
*Completed: 2026-01-20*
