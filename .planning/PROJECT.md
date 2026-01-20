# OT2 CherryPick GUI Enhancement

## What This Is

Improving the web GUI for the OT-2 CherryPick protocol generator to provide a better user experience when selecting and loading CSV transfer files. The GUI already exists (React 19 + Mantine, FastAPI backend) — this enhances the Configuration tab with a proper file selector instead of manual text entry.

## Core Value

Users can select CSV files from a dropdown and immediately see the content loaded in the editor views — no manual path typing, no guessing filenames.

## Requirements

### Validated

- ✓ Protocol generation from TOML + CSV — existing
- ✓ Web GUI with Configuration tab — existing
- ✓ SpreadSheet View for CSV editing — existing
- ✓ Text View for raw CSV content — existing
- ✓ Workflow execution (generate → simulate → deploy) — existing
- ✓ gui_state workspace isolation — existing

### Active

- [ ] CSV file dropdown selector in Configuration tab
- [ ] Backend endpoint to list CSVs from gui_state/CSVs directory
- [ ] Immediate load on selection (SpreadSheet + Text views)
- [ ] Manual refresh button to re-scan directory
- [ ] Unsaved changes warning dialog before switching files
- [ ] Disabled dropdown with "No CSV files found" when empty
- [ ] Default selection: first file alphabetically, auto-loaded on startup

### Out of Scope

- Auto-refresh / polling for new files — manual refresh is sufficient
- File metadata in dropdown (size, date) — filename only for simplicity
- File upload through dropdown — existing mechanisms handle this
- Multi-file selection — one file at a time

## Context

**Technical environment:**
- React 19.2 with Mantine 8.3+ component library
- FastAPI backend with FileStateStore managing gui_state/
- CSV directory: `gui_state/CSVs/` (dev) or volume mount (Docker)
- Existing components: SpreadSheet view uses react-spreadsheet, Text view for raw content
- PapaParse for CSV parsing

**Current state:**
- Configuration tab has text input field for CSV filename
- Users must type filename manually or know what files exist
- No discovery of available CSV files

## Constraints

- **UI Framework**: Must use Mantine components for consistency with existing UI
- **State Location**: CSV files live in gui_state/CSVs, not repo root
- **Backend Pattern**: Follow existing FastAPI route patterns in src/gui/backend/

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Dropdown over file browser | Simpler UX, scoped to known directory | — Pending |
| Immediate load on select | Reduces clicks, feels responsive | — Pending |
| Warn on unsaved changes | Prevent accidental data loss | — Pending |
| Manual refresh only | Simpler than polling, user controls when | — Pending |

---
*Last updated: 2026-01-20 after initialization*
