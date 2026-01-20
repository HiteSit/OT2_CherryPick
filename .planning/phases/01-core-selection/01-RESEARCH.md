# Phase 1: Core Selection - Research

**Researched:** 2026-01-20
**Domain:** React/Mantine dropdown file selection with react-query data fetching
**Confidence:** HIGH

## Summary

This research investigates implementing a CSV file selector dropdown for the OT-2 CherryPick GUI. The codebase already has all necessary infrastructure: Mantine v8.3.7 Select component, react-query v5 hooks for CSV operations, and a WizardContext for state management.

The existing `CsvManager.tsx` component demonstrates the exact pattern needed: a searchable Select using `useCsvListQuery()` for the file list and `useCsvContentQuery(name)` for loading content. The new component will follow this pattern but be located in `CsvEditor.tsx` within the Transfer Map step, with additions for clearable selection and a refresh button.

**Primary recommendation:** Create a `CsvFileSelector` component using Mantine Select with `searchable`, `clearable`, and custom `rightSection` for refresh. Use existing `useCsvListQuery` with `.refetch()` for refresh functionality, and `useCsvContentQuery` for immediate content loading on selection.

## Standard Stack

The codebase already uses the complete stack needed for this feature:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| @mantine/core | 8.3.7 | UI components (Select) | Already used throughout codebase |
| @tanstack/react-query | 5.90.8 | Data fetching/caching | Already used for all API calls |
| @tabler/icons-react | 3.35.0 | Icons (IconRefresh, IconX) | Already used for all icons |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| papaparse | 5.4.1 | CSV parsing | Already used in CsvEditor for parsing |
| react-spreadsheet | 0.10.1 | Spreadsheet display | Already used in CsvEditor |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Mantine Select | Mantine Autocomplete | Select is better for discrete options; Autocomplete for free-form input |
| Custom dropdown | Mantine Combobox | Combobox offers more customization but overkill for file list |

**Installation:**
No new packages needed - all dependencies already installed.

## Architecture Patterns

### Recommended Project Structure
```
src/gui/frontend/src/
├── api/
│   ├── hooks.ts          # useCsvListQuery, useCsvContentQuery (EXISTING)
│   ├── client.ts         # fetchCsvList, fetchCsvContent (EXISTING)
│   └── types.ts          # CsvListResponse (EXISTING)
├── components/
│   └── wizard/
│       └── csv/
│           ├── CsvEditor.tsx       # ADD selector here (MODIFY)
│           └── CsvFileSelector.tsx # NEW: extracted selector component (OPTIONAL)
```

### Pattern 1: Existing CSV Selection Pattern (from CsvManager.tsx)
**What:** Mantine Select with react-query data, loads content on selection
**When to use:** This is the EXACT pattern to follow
**Example:**
```typescript
// Source: /src/gui/frontend/src/components/CsvManager.tsx lines 57-77
const csvListQuery = useCsvListQuery()
const [activeName, setActiveName] = useState('')
const csvContentQuery = useCsvContentQuery(activeName)

const csvOptions = useMemo(
  () => (csvListQuery.data?.files ?? []).map((name) => ({ value: name, label: name })),
  [csvListQuery.data],
)

// Effect syncs content to local state when query data changes
useEffect(() => {
  if (csvContentQuery.data !== undefined) {
    setEditorContent(csvContentQuery.data)
    setSheetData(parseCsvToSheet(csvContentQuery.data))
  }
}, [csvContentQuery.data, activeName])
```

### Pattern 2: Wizard Context Integration (from CsvEditor.tsx)
**What:** Sync local state with WizardContext for cross-step validation
**When to use:** When selected file must be available to other wizard steps
**Example:**
```typescript
// Source: /src/gui/frontend/src/components/wizard/csv/CsvEditor.tsx lines 11-26
const { state, setCSV } = useWizard()
const [editorContent, setEditorContent] = useState(state.csv.content)
const [filename, setFilename] = useState(state.csv.filename || 'wizard.csv')

useEffect(() => {
  if (state.csv.filename) {
    setFilename(state.csv.filename)
  }
  setEditorContent(state.csv.content)
}, [state.csv.filename, state.csv.content])
```

### Pattern 3: Manual Refetch Pattern (from SettingsEditor.tsx)
**What:** Use query.refetch() for explicit refresh button
**When to use:** When user needs manual control over data refresh
**Example:**
```typescript
// Source: /src/gui/frontend/src/components/SettingsEditor.tsx lines 392-400
<ActionIcon
  variant="default"
  onClick={() => rawQuery.refetch()}
  disabled={rawQuery.isFetching}
  aria-label="Reload settings"
>
  <IconRefresh size={18} />
</ActionIcon>
```

### Anti-Patterns to Avoid
- **Calling setCSV in onChange directly:** Always update local state first, then sync to context
- **Not handling loading states:** Always show feedback during fetch operations
- **Forgetting to clear content on deselection:** When X button clicked, clear both filename and content
- **Not memoizing csvOptions:** The data array should be memoized to prevent unnecessary re-renders

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| File list fetching | Custom fetch + state | `useCsvListQuery()` | Already handles caching, loading, error states |
| File content loading | Custom fetch + state | `useCsvContentQuery(name)` | Automatic caching, conditional fetch when name set |
| Search filtering | Custom filter logic | Mantine Select `searchable` | Built-in substring matching, keyboard navigation |
| Clear button | Custom X icon + handler | Mantine Select `clearable` | Handles accessibility, states automatically |
| Empty state message | Custom conditional render | Mantine Select `nothingFoundMessage` | Consistent UX with other Mantine components |

**Key insight:** The CsvManager.tsx already implements 90% of the needed functionality. The main additions are: clearable selection and a refresh button with clear-on-refresh behavior.

## Common Pitfalls

### Pitfall 1: clearable + rightSection Conflict
**What goes wrong:** Mantine Select's `clearable` prop renders its X button in the rightSection. If you set a custom `rightSection`, the clearable button disappears.
**Why it happens:** Mantine prioritizes explicit `rightSection` over built-in features
**How to avoid:** Compose both buttons in a single rightSection Group:
```typescript
rightSection={
  <Group gap={4} wrap="nowrap">
    {value && (
      <ActionIcon size="sm" variant="subtle" onClick={handleClear}>
        <IconX size={14} />
      </ActionIcon>
    )}
    <ActionIcon size="sm" variant="subtle" onClick={handleRefresh} loading={isRefetching}>
      <IconRefresh size={14} />
    </ActionIcon>
  </Group>
}
rightSectionPointerEvents="all"  // CRITICAL: allow clicks on right section
```
**Warning signs:** Clear button visible without rightSection but disappears when you add refresh icon

### Pitfall 2: Content Not Loading on Selection
**What goes wrong:** User selects file but SpreadSheet/Text views remain empty
**Why it happens:** `useCsvContentQuery(name)` only fetches when `enabled: Boolean(name)`. If name is empty string (falsy), query never runs.
**How to avoid:**
1. Ensure onChange sets a non-empty name: `onChange={(value) => setSelectedFile(value || '')}`
2. Check that `useCsvContentQuery` receives the selected filename, not empty string
3. Use effect to sync query data to local editor state
**Warning signs:** Network tab shows no request to `/csvs/{name}` endpoint after selection

### Pitfall 3: State Desync Between Selector and Editor
**What goes wrong:** Dropdown shows "example.csv" but editor shows content from different file
**Why it happens:** Local state updated without syncing to WizardContext, or context updated without updating local state
**How to avoid:**
1. Single source of truth: keep selected filename in one place (recommend local state synced to context)
2. Use effect to sync bidirectionally when context changes externally
3. Always update both filename AND content together
**Warning signs:** Validation errors reference files not shown in dropdown

### Pitfall 4: Refresh Doesn't Show New Files
**What goes wrong:** User adds file to gui_state/CSVs, clicks refresh, file doesn't appear
**Why it happens:** react-query may serve stale cache. `refetch()` only works if query key hasn't changed.
**How to avoid:**
```typescript
const queryClient = useQueryClient()
const handleRefresh = () => {
  // Invalidate to force fresh fetch
  queryClient.invalidateQueries({ queryKey: ['csvs'] })
  // Or use refetch with network-only
  csvListQuery.refetch()
  // ALWAYS clear selection per user requirement
  setSelectedFile('')
  setCSV('', '')
}
```
**Warning signs:** New files only appear after page refresh, not after clicking refresh button

## Code Examples

Verified patterns from the existing codebase:

### Complete Select with Searchable + Loading State
```typescript
// Source: /src/gui/frontend/src/components/CsvManager.tsx lines 180-195
{csvListQuery.isLoading ? (
  <Group gap="xs">
    <Loader size="sm" />
    <Text c="dimmed">Loading available CSV files...</Text>
  </Group>
) : (
  <Select
    label="Existing CSV files"
    placeholder="Select a CSV to edit"
    searchable
    data={csvOptions}
    value={activeName}
    onChange={(value) => value && setActiveName(value)}
    nothingFoundMessage="No CSV files in workspace."
  />
)}
```

### Effect to Sync Query Data to Local State
```typescript
// Source: /src/gui/frontend/src/components/CsvManager.tsx lines 67-77
useEffect(() => {
  if (csvContentQuery.data !== undefined) {
    setEditorContent(csvContentQuery.data)
    setSheetData(parseCsvToSheet(csvContentQuery.data))
    setGridDirty(false)
  } else if (!activeName) {
    setEditorContent('')
    setSheetData(ensureHeaderRow([]))
    setGridDirty(false)
  }
}, [csvContentQuery.data, activeName])
```

### Memoized Options Array
```typescript
// Source: /src/gui/frontend/src/components/CsvManager.tsx lines 79-82
const csvOptions = useMemo(
  () => (csvListQuery.data?.files ?? []).map((name) => ({ value: name, label: name })),
  [csvListQuery.data],
)
```

### ActionIcon with Tooltip for Refresh
```typescript
// Source: /src/gui/frontend/src/components/CsvManager.tsx lines 254-259
<Tooltip label="Rebuild CSV text from spreadsheet">
  <ActionIcon variant="default" onClick={syncTextFromGrid} aria-label="Sync text from grid">
    <IconRefresh size={16} />
  </ActionIcon>
</Tooltip>
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| FileInput only | Select + FileInput | Already implemented | Users can select existing or upload new |
| Page reload for refresh | react-query refetch | Already implemented | Instant refresh without losing state |

**Deprecated/outdated:**
- None identified - codebase uses current patterns

## Open Questions

Things that couldn't be fully resolved:

1. **Case sensitivity of search filter**
   - What we know: Mantine Select `searchable` uses case-insensitive substring matching by default
   - What's unclear: Whether this matches the "exact substring matching" requirement from CONTEXT.md
   - Recommendation: Use default case-insensitive search (better UX). If case-sensitive required, use `filter` prop

2. **File list sorting**
   - What we know: Backend returns files in directory order (arbitrary)
   - What's unclear: Whether users prefer alphabetical, by date, or unsorted
   - Recommendation: Sort alphabetically on frontend for predictability:
     ```typescript
     const csvOptions = useMemo(
       () => (csvListQuery.data?.files ?? [])
         .sort((a, b) => a.localeCompare(b))
         .map((name) => ({ value: name, label: name })),
       [csvListQuery.data],
     )
     ```

3. **Display format: filename vs path**
   - What we know: Backend returns just filenames (e.g., "example_basic.csv"), not full paths
   - What's unclear: If future phases need subdirectory support
   - Recommendation: Display just filename. Current API structure doesn't support subdirectories.

## Sources

### Primary (HIGH confidence)
- `/src/gui/frontend/src/components/CsvManager.tsx` - Existing CSV selection implementation
- `/src/gui/frontend/src/components/wizard/csv/CsvEditor.tsx` - Target file for modifications
- `/src/gui/frontend/src/api/hooks.ts` - React Query hooks for CSV operations
- `/src/gui/frontend/src/components/wizard/WizardContext.tsx` - State management for wizard
- `/src/gui/frontend/package.json` - Dependency versions (Mantine 8.3.7, react-query 5.90.8)

### Secondary (MEDIUM confidence)
- [Mantine Select Documentation](https://mantine.dev/core/select/) - Official docs for Select props
- [GitHub Issue #7110](https://github.com/mantinedev/mantine/issues/7110) - clearable + rightSection conflict

### Tertiary (LOW confidence)
- None - all findings verified against codebase

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries already in package.json and in use
- Architecture: HIGH - Patterns directly observed in existing components
- Pitfalls: HIGH - clearable/rightSection conflict confirmed via GitHub issues and official docs

**Research date:** 2026-01-20
**Valid until:** 2026-02-20 (30 days - stable patterns, no fast-moving dependencies)
