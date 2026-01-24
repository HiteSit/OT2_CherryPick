# OT2 CherryPick GUI Enhancement

## What This Is

Web GUI enhancement for the OT-2 CherryPick protocol generator. Provides a dropdown-based CSV file selector in the Configuration tab with immediate content loading, unsaved changes protection, and graceful empty state handling. Built with React 19 + Mantine UI on existing FastAPI backend.

## Core Value

Users can select CSV files from a dropdown and immediately see the content loaded in the editor views — no manual path typing, no guessing filenames, with protection against accidental data loss.

## Current Milestone: v2.0 Simulation Log Validation

**Goal:** Refactor tests to validate CSV-driven transfers by parsing simulation output and asserting correct pipetting behavior.

**Target features:**
- Test suite refactor: restructure directories/fixtures to support log validation
- Structured parsing of simulation output for test assertions
- Verification of transfer mapping, labware configuration, and tip actions against CSV inputs
- Coverage of liquid handling parameters (heights, flow rates, air gaps) based on settings/CSV

## Requirements

### Validated

**v1.0 (Shipped 2026-01-21):**
- ✓ CSV file dropdown selector in Configuration tab — v1.0
- ✓ Backend endpoint to list CSVs from gui_state/CSVs directory — v1.0
- ✓ Immediate load on selection (SpreadSheet + Text views) — v1.0
- ✓ Manual refresh button to re-scan directory — v1.0
- ✓ Unsaved changes warning dialog before switching files — v1.0
- ✓ Disabled dropdown with "No CSV files found" when empty — v1.0

**Existing (Pre-v1.0):**
- ✓ Protocol generation from TOML + CSV
- ✓ Web GUI with Configuration tab
- ✓ SpreadSheet View for CSV editing
- ✓ Text View for raw CSV content
- ✓ Workflow execution (generate → simulate → deploy)
- ✓ gui_state workspace isolation

### Active

- [ ] Refactor test suite structure (directories, fixtures, harness) for simulation log validation
- [ ] Parse simulation output into structured data for tests
- [ ] Test transfer mapping, labware setup, and tip actions against CSV inputs
- [ ] Validate liquid handling parameters (heights, flow rates, air gaps) from settings/CSV

### Out of Scope

- Auto-refresh / polling for new files — manual refresh is sufficient
- File metadata in dropdown (size, date) — filename only for simplicity
- File upload through dropdown — existing mechanisms handle this
- Multi-file selection — one file at a time

## Context

**Current State (v1.0):**
- 170 lines TypeScript/React added across 2 files
- CsvEditor.tsx: File selector with search, dirty detection, empty state handling
- UnsavedChangesModal.tsx: Confirmation dialog for unsaved changes
- Tech stack: React 19.2, Mantine 8.3+, FastAPI, TanStack Query
- All v1.0 requirements validated through integration testing

**Technical Environment:**
- React 19.2 with Mantine 8.3+ component library
- FastAPI backend with FileStateStore managing gui_state/
- CSV directory: `gui_state/CSVs/` (dev) or volume mount (Docker)
- Existing components: SpreadSheet view uses react-spreadsheet, Text view for raw content
- PapaParse for CSV parsing

## Constraints

- **UI Framework**: Must use Mantine components for consistency with existing UI
- **State Location**: CSV files live in gui_state/CSVs, not repo root
- **Backend Pattern**: Follow existing FastAPI route patterns in src/gui/backend/

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Custom rightSection Group for X and refresh buttons | Avoids Mantine clearable conflict | ✓ Good — clean UI, both buttons functional |
| Refresh always clears selection | Prevent stale content display | ✓ Good — per CONTEXT.md requirement |
| Case-insensitive substring search | Better UX for file discovery | ✓ Good — Mantine Select default works well |
| Alphabetical file sorting | Predictable, scannable dropdown list | ✓ Good — users can find files easily |
| Dirty state from editorContent !== originalContent | Passive dirty detection without blocking editing | ✓ Good — simple and reliable |
| Modal only when isDirty AND file differs | Allows switching when no edits or same file | ✓ Good — prevents unnecessary warnings |
| Confirmation modal with pending state | Store intended action until user confirms | ✓ Good — clean state management pattern |
| isEmpty from csvListQuery.data.files.length === 0 | Defensive check (data !== undefined first) | ✓ Good — prevents false positives during loading |
| Filled variant for FileInput when empty | Visual emphasis on upload when dropdown disabled | ✓ Good — clear call-to-action |
| Disabled dropdown when isEmpty or isLoading | Prevent interaction with empty or loading state | ✓ Good — clear feedback, no confusion |

---
*Last updated: 2026-01-24 after v2.0 milestone start*
