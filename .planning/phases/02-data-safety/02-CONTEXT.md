# Phase 2: Data Safety - Context

**Gathered:** 2026-01-20
**Status:** Ready for planning

<domain>
## Phase Boundary

Protect users from accidentally losing unsaved CSV edits when switching files, clearing selection, or navigating away. The existing workflow has a "Save to Workspace" button - this phase adds warnings when users attempt actions that would lose unsaved changes.

**Existing workflow:**
1. User selects file from dropdown → content loads
2. User edits content in editor
3. User clicks "Save to Workspace" to persist changes
4. **Problem:** Selecting another file OR clicking X OR navigating away discards edits silently

**Solution scope:** Detect unsaved changes and show warning dialog before allowing destructive actions.

</domain>

<decisions>
## Implementation Decisions

### Warning Triggers

When to show the unsaved changes warning:
- **Dropdown selection change** - Selecting a different CSV file
- **X button (clear)** - Clicking the clear selection button
- **Refresh button** - Clicking the directory re-scan button (which clears selection)
- **Tab navigation** - Switching to Configuration or Workflow tabs
- **NO browser-level warning** - Don't use `beforeunload` for browser close/navigation

### Dialog Design

Dialog structure and content:
- **Three buttons:** Save + Discard + Cancel
- **Primary action:** Save button (visually emphasized/primary styling)
- **Message tone:** Direct/technical (e.g., "Unsaved changes detected. Save before proceeding?")
- **Keyboard shortcuts:**
  - Enter key → Save
  - Escape key → Cancel

### Save Action Behavior

When user clicks "Save" in the dialog:
- **Save AND proceed** - Automatically complete the action that triggered warning (switch files, clear, navigate, etc.)
- **Silent success** - No success notification after save, just proceed smoothly
- **Error handling** - If save fails, show error message but keep dialog open so user can retry or choose Discard/Cancel

### Discard Action Behavior

When user clicks "Discard" in the dialog:
- **Immediate discard** - No confirmation dialog, immediately abandon changes and proceed with action

### Dirty State Detection

How to determine content is "unsaved":
- Editor content differs from originally loaded content
- AND user hasn't clicked "Save to Workspace" button since editing
- Simple comparison approach (Claude's discretion on exact implementation)

### Claude's Discretion

Areas where Claude can decide implementation details:
- Exact dialog component choice (Mantine Modal, custom component, etc.)
- Specific wording of dialog message (as long as tone is direct/technical)
- Visual styling of buttons (as long as Save is clearly primary)
- Dirty state comparison algorithm (string equality, content hash, etc.)
- Loading/saving state handling in dialog

</decisions>

<specifics>
## Specific Ideas

- The "Save" action in the dialog should behave **exactly like** the "Save to Workspace" button - same API call, same behavior
- Keep it simple - this is protective UX, not a complex save system
- Focus on preventing accidental data loss, not building sophisticated change tracking

</specifics>

<deferred>
## Deferred Ideas

None - discussion stayed within phase scope

</deferred>

---

*Phase: 02-data-safety*
*Context gathered: 2026-01-20*
