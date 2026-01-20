# Research Summary: CSV File Selector

**Project:** OT2 CherryPick GUI - File Selector Feature
**Domain:** React/FastAPI GUI Enhancement
**Researched:** 2026-01-20
**Confidence:** HIGH

## Stack Decision

Use **Mantine `Select`** component with the existing `@tanstack/react-query` hooks. No new libraries required. The codebase already contains the exact pattern needed: `useCsvListQuery()` provides file list, `useCsvContentQuery(name)` fetches content on selection. The `Select` component with `searchable` prop handles type-ahead filtering for long file lists. Reference implementation exists in `CsvManager.tsx` (lines 186-194).

## Key UX Patterns

**Table Stakes (required):**
- Keyboard navigation (arrow keys, Enter, Escape)
- Clear visual states (default, hover, selected, disabled)
- Loading indicator during file list refresh
- Empty state message when no CSVs exist ("No CSV files found")
- Unsaved changes warning before switching files (prevent data loss)

**Differentiators (recommended):**
- Type-ahead filtering (essential if >10 files accumulate)
- File metadata tooltip (date modified helps identify correct file)
- Persist last selection across sessions (localStorage)
- Truncate long filenames with hover to show full name

**Anti-Features (avoid):**
- Auto-load on page refresh (loses unsaved work)
- Confirmation dialog for every selection (only when dirty)
- Alphabetical-only sort (hide recent files)

## Architecture Approach

**Data Flow:** Single source of truth pattern. `activeName` state controls everything; `editorContent` derives from react-query based on `activeName`. The existing `CsvEditor` component gains a `FileSelector` sub-component above the filename input. Backend requires no changes - all endpoints exist (`GET /csvs`, `GET /csvs/{name}`, `POST /csvs`).

**Build Order:**
1. **Phase 1 - Core Selection:** Add Select dropdown, wire to existing hooks, update local + WizardContext state
2. **Phase 2 - Data Safety:** Add dirty detection via content comparison, create UnsavedChangesModal
3. **Phase 3 - Polish:** Empty state UI, loading skeleton, auto-select first file (with flag to prevent re-trigger)

**Key Components:**
- `FileSelector` - Select dropdown with react-query integration
- `UnsavedChangesModal` - Mantine Modal with Discard/Cancel buttons
- Enhanced `CsvEditor` - Orchestrates dirty state and file switching

## Critical Pitfalls

1. **Race condition on rapid file switching** - Use react-query `queryKey` changes (not manual `useEffect` fetch) to auto-cancel stale requests. The existing `useCsvContentQuery` pattern is correct.

2. **Stale closure in dirty detection** - Use `useRef` to track current dirty state, not captured closure value. Update ref on every render, read in handlers.

3. **Delete-while-viewing ghost state** - Clear `activeName` and `editorContent` in delete mutation's `onSuccess` BEFORE cache invalidation. Otherwise editor shows deleted file's content.

4. **Mantine Select value/data mismatch** - Validate that `activeName` exists in file list after data loads. Use `null` (not `undefined`) for no selection. Add `useEffect` guard to clear orphaned selections.

5. **Confirmation dialog fatigue** - Compare normalized content (`trim()`) against server content, not "any edit happened" flag. Only show dialog when truly dirty.

## Implementation Confidence

| Area | Level | Rationale |
|------|-------|-----------|
| Stack | HIGH | No new deps, existing pattern in CsvManager.tsx |
| Features | HIGH | Well-documented UX patterns, W3C/NN/g sources |
| Architecture | HIGH | Direct codebase analysis, no backend changes |
| Pitfalls | HIGH | Verified patterns, react-query docs, existing code |

**Overall: HIGH** - This is a well-scoped frontend enhancement using established patterns already present in the codebase. All building blocks exist.

## Gaps to Address

- **Auto-select behavior decision:** Research supports either first-file auto-select OR placeholder. Recommend persisting last selection in localStorage for best UX. Decision needed during requirements.
- **React 19 batching edge cases:** Theoretical concern based on React 19 changes. Monitor during implementation but low risk with single-state-update pattern.

## Ready for Requirements

**Yes.** No blockers identified. All research converges on clear implementation path using existing infrastructure.

---
*Research completed: 2026-01-20*
*Ready for roadmap: yes*
