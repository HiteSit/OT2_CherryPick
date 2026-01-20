# Phase 1: Core Selection - Context

**Gathered:** 2026-01-20
**Status:** Ready for planning

<domain>
## Phase Boundary

A dropdown-based file selector that enables users to discover CSV files from `gui_state/CSVs/` directory, filter them by typing, select a file, and immediately see its content loaded into both SpreadSheet and Text views. Includes a refresh mechanism to re-scan the directory.

This phase delivers the fundamental file discovery and selection mechanism. Content editing, validation, and deployment are handled in separate phases.

</domain>

<decisions>
## Implementation Decisions

### Dropdown UI components
- Dropdown includes an **X button** to clear/remove current selection
- Dropdown includes a **refresh button** to re-scan the folder contents
- Both buttons integrated into the dropdown component

### Selection behavior
- Content loads **immediately on selection** (as soon as user picks a file)
- Selection is **clearable** - X button returns to empty state (no file selected)
- Currently selected file is **highlighted** when dropdown is opened
- When search yields no matches, show **"No matches" message** (not just blank)

### Refresh mechanics
- Clicking refresh **always clears selection** (user must re-select after refresh)
- Refresh re-scans `gui_state/CSVs/` directory for updated file list

### Search/filter behavior
- **Exact substring matching** (not fuzzy) - user must type actual characters from filename
- Typing filters the file list in real-time

### Claude's Discretion
- Exact placement of X and refresh buttons (inline, suffix icons, etc.)
- Loading states and progress indicators during refresh operation
- Case sensitivity of search filter
- File list sorting (alphabetical, by date, etc.)
- How files are displayed (full path vs just filename)
- Visual styling, spacing, and typography
- Error handling for directory read failures

</decisions>

<specifics>
## Specific Ideas

No specific product references or interaction patterns mentioned - open to standard Mantine Select component approaches.

</specifics>

<deferred>
## Deferred Ideas

None - discussion stayed within phase scope.

</deferred>

---

*Phase: 01-core-selection*
*Context gathered: 2026-01-20*
