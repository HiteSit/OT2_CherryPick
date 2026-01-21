# Phase 3: Polish - Context

**Gathered:** 2026-01-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Handle the empty state gracefully when no CSV files exist in the directory. The dropdown should communicate this clearly while keeping the rest of the editor fully functional for manual CSV creation.

**Scope change:** Auto-selection on startup (START-01) has been removed from this phase — user prefers manual selection behavior.

</domain>

<decisions>
## Implementation Decisions

### Empty State Presentation
- Dropdown is **disabled** when no CSV files exist
- Placeholder text shows "No CSV files found"
- No additional hint text needed — users know where files go
- Upload CSV button gets **visual emphasis** (primary color/variant) when dropdown is empty
- **Critical:** Rest of editor (filename input, Add Row, Remove Row, spreadsheet, tabs) remains fully functional — users can still manually create CSVs from scratch

### Loading States
- Current loading behavior is sufficient — no changes needed
- "Loading CSV files..." text message during directory scan is fine
- "Loading file content..." during file load is fine
- No need for spinners, skeletons, or disabled states

### Claude's Discretion
- Exact styling of disabled dropdown
- How to detect "emphasize upload" state (empty file list)
- Whether emphasis is via `variant="filled"` or color change

</decisions>

<specifics>
## Specific Ideas

- Empty state affects ONLY the Select dropdown — everything else stays functional
- User explicitly wants to preserve ability to create CSVs manually without selecting from dropdown

</specifics>

<deferred>
## Deferred Ideas

- Auto-selection on startup — explicitly removed from scope (user prefers current manual behavior)

</deferred>

---

*Phase: 03-polish*
*Context gathered: 2026-01-21*
