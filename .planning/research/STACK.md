# Stack Research: File Selector Dropdown

**Project:** OT2 CherryPick GUI - File Selector Feature
**Researched:** 2026-01-20
**Scope:** Mantine components and patterns for file selection dropdown in React 19 + Mantine 8.3+

## Executive Summary

For a file selector dropdown that loads CSV content on selection, the **Mantine `Select` component** is the correct choice. The codebase already uses this pattern in `CsvManager.tsx` (line 186-194), and it remains the standard Mantine v8 approach. No additional libraries are needed beyond the existing stack.

## Recommended Components

### Primary: Mantine `Select` (from `@mantine/core`)

**Why Select over alternatives:**

| Component | Purpose | Why NOT for this use case |
|-----------|---------|---------------------------|
| **Select** | Fixed option selection from predefined list | **Correct choice** - file list is server-provided, no custom values |
| Autocomplete | Text input with suggestions | Wrong - allows arbitrary text, users shouldn't type filenames |
| Combobox | Low-level building blocks for custom dropdowns | Overkill - Select provides everything needed with less code |

**Key Select props for this feature:**

```typescript
<Select
  label="CSV File"
  placeholder="Select a CSV file"
  searchable              // Filter long file lists by typing
  clearable               // Allow deselection (optional)
  data={csvOptions}       // Array of { value: string, label: string }
  value={selectedFile}    // Controlled value
  onChange={(value, option) => {
    setSelectedFile(value)
    // option contains { value, label } - useful if label differs from value
  }}
  nothingFoundMessage="No CSV files found"
  disabled={isLoading}
  rightSection={isLoading ? <Loader size="xs" /> : undefined}
/>
```

**Confidence: HIGH** - Verified against Mantine v8 documentation at mantine.dev/core/select/

### Supporting Components (Already in Stack)

| Component | Use Case | Import |
|-----------|----------|--------|
| `Loader` | Show loading state in dropdown | `@mantine/core` |
| `Group` | Layout file selector with action buttons | `@mantine/core` |
| `Paper` | Container styling | `@mantine/core` |
| `ActionIcon` | Refresh/reload button next to dropdown | `@mantine/core` |

## Additional Libraries

**None required.** The existing stack covers everything:

| Need | Already Have | Status |
|------|--------------|--------|
| Dropdown component | `@mantine/core` Select | Already installed (v8.3.7) |
| Async data fetching | `@tanstack/react-query` | Already installed (v5.90.8) |
| CSV parsing | `papaparse` | Already installed (v5.4.1) |
| Icons | `@tabler/icons-react` | Already installed (v3.35.0) |
| Notifications | `@mantine/notifications` | Already installed (v8.3.7) |

## Integration Notes

### Pattern 1: Direct with react-query (Recommended)

The existing `useCsvListQuery()` and `useCsvContentQuery()` hooks provide everything needed:

```typescript
// Existing hooks in src/api/hooks.ts
const csvListQuery = useCsvListQuery()        // Fetches file list
const csvContentQuery = useCsvContentQuery(activeName)  // Fetches content when name changes

// Transform for Select data prop
const csvOptions = useMemo(
  () => (csvListQuery.data?.files ?? []).map((name) => ({ value: name, label: name })),
  [csvListQuery.data],
)
```

**Why this works well:**
- react-query handles caching, refetching, loading states
- `enabled: Boolean(name)` in `useCsvContentQuery` prevents unnecessary fetches
- Query invalidation on file changes already implemented

**Confidence: HIGH** - Verified against existing `CsvManager.tsx` implementation

### Pattern 2: Lazy-load on dropdown open (Alternative)

For very large file lists, Mantine supports loading data only when dropdown opens via Combobox:

```typescript
const combobox = useCombobox({
  onDropdownOpen: () => {
    if (data.length === 0 && !loading) {
      setLoading(true)
      fetchData().then((response) => {
        setData(response)
        setLoading(false)
      })
    }
  },
})
```

**When to use:** Only if file list is large (100+ files) and you want to avoid fetching until user interaction.

**Recommendation:** Use Pattern 1 (direct with react-query) for this project. File lists are typically small, and the UX benefit of immediate availability outweighs the minor cost of an early fetch.

**Confidence: HIGH** - Code verified from Mantine GitHub at mantinedev/mantine

### onChange Signature (v8.3+)

Mantine v8.3+ `Select` provides both value and full option object:

```typescript
onChange={(value: string | null, option: ComboboxItem) => {
  // value = "example_basic.csv" (or null if cleared)
  // option = { value: "example_basic.csv", label: "example_basic.csv" }
  setSelectedFile(value)
}}
```

**Confidence: HIGH** - Verified in Mantine v8.3.0 changelog

### Styling Considerations

Mantine Select supports the Styles API with selectors:
- `wrapper`, `input`, `dropdown`, `options`, `option`, `label`, `error`

For consistent styling with existing components, use the same `Paper` container pattern seen in `CsvManager.tsx`:

```typescript
<Paper withBorder radius="md" p="md">
  <Select ... />
</Paper>
```

## Anti-Patterns to Avoid

### 1. Using Combobox when Select suffices

**Problem:** Combobox requires significantly more code for the same functionality.

**Evidence:** The async example from Mantine docs requires ~50 lines. Select achieves the same in ~10 lines when data is already fetched.

### 2. Implementing custom loading state management

**Problem:** Duplicating what react-query already provides.

**Correct approach:**
```typescript
const csvListQuery = useCsvListQuery()
// csvListQuery.isLoading, csvListQuery.data, csvListQuery.isError already available
```

### 3. Using allowDeselect with required fields

**Problem:** If a file selection is required, `allowDeselect={true}` (default) creates confusing UX.

**Solution:** Set `allowDeselect={false}` when selection is mandatory.

## Version Compatibility Matrix

| Package | Current Version | Required Version | Status |
|---------|-----------------|------------------|--------|
| `@mantine/core` | 8.3.7 | >=8.0.0 | OK |
| `@mantine/hooks` | 8.3.7 | >=8.0.0 | OK |
| `react` | 19.2.0 | >=18.0.0 | OK |
| `@tanstack/react-query` | 5.90.8 | >=5.0.0 | OK |

**Confidence: HIGH** - Verified against package.json

## Confidence Assessment

| Topic | Confidence | Rationale |
|-------|------------|-----------|
| Select as correct component | HIGH | Official Mantine docs + existing codebase usage |
| react-query integration pattern | HIGH | Already implemented in `CsvManager.tsx` |
| No additional libraries needed | HIGH | Verified existing dependencies cover all needs |
| onChange signature (v8.3+) | HIGH | Verified in Mantine v8.3.0 changelog |
| Styles API selectors | MEDIUM | General Mantine pattern, not specifically tested |

## Sources

**Official Documentation:**
- [Mantine Select Component](https://mantine.dev/core/select/) - Core Select reference
- [Mantine Combobox Component](https://mantine.dev/core/combobox/) - Low-level alternative
- [Mantine v8.3.0 Changelog](https://mantine.dev/changelog/8-3-0/) - onChange option parameter

**GitHub:**
- [Mantine Async Select Example](https://github.com/mantinedev/mantine/blob/master/apps/mantine.dev/src/combobox-examples/examples/SelectAsync/SelectAsync.tsx) - Lazy-load pattern
- [Mantine Discussion #345](https://github.com/orgs/mantinedev/discussions/345) - Async data patterns
- [Mantine Discussion #4726](https://github.com/orgs/mantinedev/discussions/4726) - onChange full option object

**Existing Codebase:**
- `/mnt/d/Amadteus_Main/OpenTron/OT2_CherryPick/src/gui/frontend/src/components/CsvManager.tsx` - Reference implementation (lines 186-194)
- `/mnt/d/Amadteus_Main/OpenTron/OT2_CherryPick/src/gui/frontend/src/api/hooks.ts` - react-query integration pattern
