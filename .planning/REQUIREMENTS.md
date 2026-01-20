# Requirements: CSV File Selector

**Defined:** 2026-01-20
**Core Value:** Users can select CSV files from a dropdown and immediately see content loaded

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Core Selection

- [ ] **SEL-01**: Dropdown showing CSV files from gui_state/CSVs directory
- [ ] **SEL-02**: Selecting a file immediately loads content into SpreadSheet and Text views
- [ ] **SEL-03**: Manual refresh button to re-scan directory for new files
- [ ] **SEL-04**: Type-ahead filtering (searchable dropdown) for finding files

### Data Safety

- [ ] **SAFE-01**: Unsaved changes warning dialog before switching files when content is dirty
- [ ] **SAFE-02**: Dialog has clear Discard/Cancel button labels

### Empty State

- [ ] **EMPTY-01**: Disabled dropdown with "No CSV files found" message when directory is empty

### Startup Behavior

- [ ] **START-01**: First file (alphabetically) auto-selected and loaded on page load

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Polish

- **POLISH-01**: Visual dirty indicator (asterisk or dot on filename)
- **POLISH-02**: Loading skeleton during file list fetch
- **POLISH-03**: Guidance message in empty state ("Add a CSV file to get started")
- **POLISH-04**: File metadata tooltip showing modified date
- **POLISH-05**: Persist last selection across sessions (localStorage)

## Out of Scope

| Feature | Reason |
|---------|--------|
| File upload through dropdown | Existing upload mechanism handles this separately |
| Multi-file selection | One file at a time is sufficient for workflow |
| Auto-refresh / polling | Manual refresh is simpler and sufficient |
| Drag-and-drop reordering | Alphabetical sort is sufficient |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| SEL-01 | Phase 1 | Pending |
| SEL-02 | Phase 1 | Pending |
| SEL-03 | Phase 1 | Pending |
| SEL-04 | Phase 1 | Pending |
| SAFE-01 | Phase 2 | Pending |
| SAFE-02 | Phase 2 | Pending |
| EMPTY-01 | Phase 3 | Pending |
| START-01 | Phase 3 | Pending |

**Coverage:**
- v1 requirements: 8 total
- Mapped to phases: 8
- Unmapped: 0

---
*Requirements defined: 2026-01-20*
*Last updated: 2026-01-20 after roadmap creation*
