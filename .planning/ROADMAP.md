# Roadmap: CSV File Selector

## Overview

This feature adds a dropdown-based CSV file selector to the OT2 CherryPick GUI Configuration tab. Users will be able to discover and select CSV files from a searchable dropdown, with immediate content loading into the editor views. The implementation leverages existing react-query hooks and Mantine components already present in the codebase.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

- [x] **Phase 1: Core Selection** - Dropdown with file list, immediate load, refresh button
- [x] **Phase 2: Data Safety** - Unsaved changes detection and warning dialog
- [x] **Phase 3: Polish** - Empty state handling

## Phase Details

### Phase 1: Core Selection
**Goal**: Users can select CSV files from a searchable dropdown and see content immediately loaded
**Depends on**: Nothing (first phase)
**Requirements**: SEL-01, SEL-02, SEL-03, SEL-04
**Success Criteria** (what must be TRUE):
  1. User sees a dropdown in Configuration tab showing all CSV files from gui_state/CSVs
  2. User can type in dropdown to filter the file list (type-ahead search)
  3. Selecting a file immediately loads content into SpreadSheet and Text views
  4. User can click refresh button to re-scan directory and update file list
**Plans**: 1 plan

Plans:
- [x] 01-01-PLAN.md — File selector with search, clear, refresh, and immediate content loading

### Phase 2: Data Safety
**Goal**: Users are protected from accidentally losing unsaved changes when switching files
**Depends on**: Phase 1
**Requirements**: SAFE-01, SAFE-02
**Success Criteria** (what must be TRUE):
  1. User sees warning dialog when selecting different file with unsaved changes
  2. Dialog presents clear "Discard" and "Cancel" button labels
  3. Clicking "Cancel" keeps current file and unsaved changes intact
  4. Clicking "Discard" switches to new file and loads its content
**Plans**: 1 plan

Plans:
- [x] 02-01-PLAN.md — Dirty state detection and UnsavedChangesModal with Discard/Cancel actions

### Phase 3: Polish
**Goal**: Empty state handled gracefully with appropriate user feedback
**Depends on**: Phase 1
**Requirements**: EMPTY-01
**Success Criteria** (what must be TRUE):
  1. User sees disabled dropdown with "No CSV files found" message when directory is empty
  2. Upload CSV button is visually emphasized when dropdown is empty
  3. Rest of editor remains fully functional for manual CSV creation
**Plans**: 1 plan

Plans:
- [x] 03-01-PLAN.md — Empty state detection with disabled dropdown and emphasized upload button

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Core Selection | 1/1 | ✓ Complete | 2026-01-20 |
| 2. Data Safety | 1/1 | ✓ Complete | 2026-01-20 |
| 3. Polish | 1/1 | ✓ Complete | 2026-01-21 |

---
*Roadmap created: 2026-01-20*
*Last updated: 2026-01-21 - Phase 3 complete*
