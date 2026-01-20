# Pitfalls Research: File Selector

**Feature:** CSV File Selector with Async Loading
**Tech Stack:** React 19, Mantine 8.3+, TanStack Query (react-query), FastAPI
**Researched:** 2026-01-20
**Confidence:** HIGH (based on existing codebase analysis + verified patterns)

---

## Critical Pitfalls

### 1. Race Condition: Out-of-Order File Loads

**What goes wrong:** User selects File A, then quickly switches to File B. If File A's response arrives after File B's response, the editor displays File A's content while the dropdown shows File B selected.

**Why it happens:** Async requests complete in unpredictable order. Without cancellation, the slower request's callback overwrites the faster one's state.

**Warning signs:**
- Content flickers between files after rapid selection changes
- Editor content doesn't match selected dropdown value
- User reports "wrong file loaded"

**Prevention strategy:**
```typescript
// TanStack Query handles this automatically when queryKey changes
// The key insight: useCsvContentQuery(activeName) with enabled: Boolean(activeName)
// creates a new query per filename, and TanStack Query cancels stale fetches

// DO NOT do this (manual useEffect pattern):
useEffect(() => {
  fetchFile(activeName).then(setContent) // RACE CONDITION!
}, [activeName])

// DO this (already in codebase - hooks.ts):
export const useCsvContentQuery = (name?: string) =>
  useQuery({
    queryKey: ['csvs', name],  // Key changes = new query
    queryFn: () => fetchCsvContent(name!),
    enabled: Boolean(name),
  })
```

**Implementation step:** File selection handler - verify `activeName` state update triggers query key change, not manual fetch.

**Sources:**
- [Fixing Race Conditions in React with useEffect](https://maxrozen.com/race-conditions-fetching-data-react-with-useeffect)
- [Race Conditions in useEffect - Modern Patterns 2025](https://medium.com/@sureshdotariya/race-conditions-in-useeffect-with-async-modern-patterns-for-reactjs-2025-9efe12d727b0)

---

### 2. Stale Closure in Unsaved Changes Detection

**What goes wrong:** The "unsaved changes" check always returns `false` (or always `true`) because the isDirty flag was captured at render time, not at check time.

**Why it happens:** Event handlers and callbacks capture variables from their closure scope. If `isDirty` is captured when `false`, it stays `false` even after user edits.

**Warning signs:**
- No warning appears when switching files with unsaved edits
- Warning appears even for unmodified files
- `console.log(isDirty)` in handler shows stale value

**Prevention strategy:**
```typescript
// BAD: Stale closure captures initial isDirty value
const handleFileSwitch = () => {
  if (isDirty) {  // This isDirty is from when handleFileSwitch was created
    showWarning()
  }
}

// GOOD: Use ref to always get current value
const isDirtyRef = useRef(isDirty)
isDirtyRef.current = isDirty  // Update on every render

const handleFileSwitch = useCallback(() => {
  if (isDirtyRef.current) {  // Always reads current value
    showWarning()
  }
}, [])  // Empty deps - function identity stable

// ALSO GOOD: Use functional state check
const handleFileSwitch = useCallback((newFile: string) => {
  // Check state at call time, not definition time
  setActiveName(prev => {
    if (hasUnsavedChanges(editorContent, serverContent)) {
      openConfirmModal(newFile)
      return prev  // Don't switch yet
    }
    return newFile
  })
}, [editorContent, serverContent])
```

**Implementation step:** Unsaved changes detection hook - use refs for current dirty state.

**Sources:**
- [Be Aware of Stale Closures when Using React Hooks](https://dmitripavlutin.com/react-hooks-stale-closures/)
- [React useEffectEvent: Goodbye to stale closure headaches](https://blog.logrocket.com/react-useeffectevent/)

---

### 3. Delete-While-Viewing: Stale File Reference

**What goes wrong:** User deletes the currently-selected file. The dropdown updates (file removed from list), but the editor still shows the deleted file's content. Saving then recreates the deleted file.

**Why it happens:** Delete mutation invalidates the file list query, but nothing resets the `activeName` state or clears the editor content when the active file is the one deleted.

**Warning signs:**
- Editor still shows content after deletion confirmation
- Save button is enabled for a "ghost" file
- react-admin issue #5541: "getOne called on deleted object"

**Prevention strategy:**
```typescript
const deleteMutation = useDeleteCsv()

const handleDelete = () => {
  if (!activeName) return

  const fileToDelete = activeName

  deleteMutation.mutate(fileToDelete, {
    onSuccess: () => {
      // CRITICAL: Clear state BEFORE cache invalidation triggers re-render
      setActiveName('')
      setEditorContent('')
      setSheetData(ensureHeaderRow([]))
      setGridDirty(false)

      notifications.show({
        color: 'teal',
        title: 'Deleted',
        message: `${fileToDelete} removed.`
      })
    },
    onError: (error) => {
      // File may have been deleted by another user/process
      if (isNotFoundError(error)) {
        setActiveName('')
        setEditorContent('')
      }
      notifications.show({
        color: 'red',
        title: 'Delete failed',
        message: error.message
      })
    },
  })
}
```

**Implementation step:** Delete handler - reset all editor state in onSuccess callback, before or during cache invalidation.

**Sources:**
- [React-Admin Delete Redirect Race Condition](https://github.com/marmelab/react-admin/issues/5541)

---

## State Synchronization Pitfalls

### 4. Dual-Source-of-Truth Between Dropdown and Editor

**What goes wrong:** Dropdown selection state (`activeName`) and editor content state (`editorContent`) drift apart. User thinks they're editing File A but changes are saved to File B.

**Why it happens:** Selection change triggers async content load. If editor content is set independently of selection (e.g., via direct text input before load completes), states become misaligned.

**Warning signs:**
- File saved to wrong filename
- Filename input shows different value than dropdown
- "Save" button saves to unexpected file

**Prevention strategy:**
```typescript
// SINGLE source of truth: activeName controls everything
// Derived state: editorContent comes from query based on activeName

// Current codebase pattern (CsvManager.tsx) is CORRECT:
const [activeName, setActiveName] = useState('')
const csvContentQuery = useCsvContentQuery(activeName)  // Derived from activeName

useEffect(() => {
  if (csvContentQuery.data !== undefined) {
    setEditorContent(csvContentQuery.data)  // Sync derived state
    setGridDirty(false)
  } else if (!activeName) {
    setEditorContent('')
    setGridDirty(false)
  }
}, [csvContentQuery.data, activeName])

// DANGER ZONE: The TextInput for "Active filename" allows direct editing
// This creates second source of truth - user can type "newfile.csv" while
// dropdown shows "existing.csv"

// MITIGATION: Use dropdown as authoritative, TextInput as display-only
// OR: Add validation that newName !== existing list names before save
```

**Implementation step:** Evaluate whether filename input should be editable independently or only via dropdown selection.

---

### 5. React 19 Automatic Batching Surprises

**What goes wrong:** Multiple state updates that should be atomic are batched differently in React 19, causing intermediate renders with inconsistent state.

**Why it happens:** React 19 batches all state updates (even in async callbacks), but the timing of when batched renders complete can surprise developers expecting immediate updates.

**Warning signs:**
- Dropdown shows correct selection, but content load fires for previous selection
- State updates seem "delayed" by one interaction
- `console.log` in render shows unexpected intermediate states

**Prevention strategy:**
```typescript
// Group related state updates to ensure atomicity
const handleFileSelect = useCallback((newFile: string | null) => {
  if (!newFile) {
    // Clear all related state together
    setActiveName('')
    setEditorContent('')
    setGridDirty(false)
    return
  }

  // Only set activeName - content will sync via useEffect
  setActiveName(newFile)
  // DO NOT set editorContent here - let the query handle it
}, [])
```

**Implementation step:** File selection handler - set only `activeName`, let query sync trigger content update.

---

### 6. Mantine Select Controlled Component Value/Data Mismatch

**What goes wrong:** Selected value shows as blank or shows raw value instead of label, even though selection worked.

**Why it happens:** Mantine Select requires the `value` prop to match an item in the `data` array. If data loads async and value is set before data contains that item, display breaks.

**Warning signs:**
- Dropdown shows blank after selection
- Selected item shows value instead of label
- "nothingFoundMessage" displays when there should be options

**Prevention strategy:**
```typescript
// Ensure value exists in data before setting
const csvOptions = useMemo(
  () => (csvListQuery.data?.files ?? []).map((name) => ({
    value: name,
    label: name
  })),
  [csvListQuery.data],
)

// Guard against orphaned selection
useEffect(() => {
  if (activeName && csvListQuery.data?.files &&
      !csvListQuery.data.files.includes(activeName)) {
    // Selected file no longer exists - clear selection
    setActiveName('')
  }
}, [activeName, csvListQuery.data?.files])

// Mantine-specific: data must include all values
<Select
  data={csvOptions}
  value={activeName || null}  // null, not undefined, for "no selection"
  onChange={(value) => value && setActiveName(value)}
/>
```

**Implementation step:** Selection change handler + useEffect guard - validate activeName exists in file list.

**Sources:**
- [Mantine Select Controlled Component Issues](https://github.com/orgs/mantinedev/discussions/345)

---

## Edge Cases

### 7. Empty Directory State Without Guidance

**What goes wrong:** User sees blank dropdown with no indication of what to do. They don't realize they need to upload a file first.

**Why it happens:** No files exist in CSVs/ directory, dropdown shows empty list without actionable guidance.

**Warning signs:**
- Users ask "how do I create a file?"
- High bounce rate on file selector screen
- Support tickets about "nothing appears"

**Prevention strategy:**
```tsx
// Provide clear empty state with action
{csvListQuery.isLoading ? (
  <Group gap="xs">
    <Loader size="sm" />
    <Text c="dimmed">Loading CSV files...</Text>
  </Group>
) : csvOptions.length === 0 ? (
  <Paper withBorder p="md" bg="gray.0">
    <Stack align="center" gap="sm">
      <IconFileOff size={32} color="gray" />
      <Text ta="center" c="dimmed">
        No CSV files in workspace yet.
      </Text>
      <Text ta="center" size="sm" c="dimmed">
        Upload a CSV file below or drag and drop to get started.
      </Text>
    </Stack>
  </Paper>
) : (
  <Select
    label="Select a CSV file"
    data={csvOptions}
    value={activeName}
    onChange={(value) => value && setActiveName(value)}
  />
)}
```

**Implementation step:** Render logic - add empty state component between loading and populated states.

**Sources:**
- [Empty State UX - The Most Overlooked Aspect](https://www.toptal.com/designers/ux/empty-state-ux-design)
- [Dropbox Empty Folder Redesign Example](https://www.eleken.co/blog-posts/empty-state-ux)

---

### 8. Auto-Select First File: Double-Trigger and Loading Flicker

**What goes wrong:** On mount, component auto-selects first file. This triggers a content load, but the initial render already showed loading state. User sees: loading -> empty -> loading -> content (flicker).

**Why it happens:** Auto-selection happens in useEffect after initial render. Each state change triggers re-render.

**Warning signs:**
- Brief flash of "no file selected" on app load
- Content loading indicator appears twice
- First file sometimes doesn't auto-load

**Prevention strategy:**
```typescript
// Auto-select ONLY on initial load, with proper timing
const [hasAutoSelected, setHasAutoSelected] = useState(false)

useEffect(() => {
  // Only auto-select once, only when we have data
  if (!hasAutoSelected &&
      csvListQuery.isSuccess &&
      csvListQuery.data.files.length > 0 &&
      !activeName) {
    setActiveName(csvListQuery.data.files[0])
    setHasAutoSelected(true)
  }
}, [csvListQuery.isSuccess, csvListQuery.data?.files, activeName, hasAutoSelected])

// Alternative: Initialize with first file at query level
const csvListQuery = useCsvListQuery()
const initialFile = csvListQuery.data?.files?.[0] ?? null

// Delay rendering selector until we know if there are files
if (csvListQuery.isLoading) {
  return <Skeleton height={36} />
}
```

**Implementation step:** Initial load logic - use flag to prevent repeated auto-selection, consider SSR-style initial state.

---

### 9. File Renamed/Moved Externally

**What goes wrong:** User renames CSV file in file explorer. The app still references old filename. Content query fails, but activeName persists.

**Why it happens:** File selector assumes files are only modified through the app. External changes aren't detected.

**Warning signs:**
- "File not found" errors for seemingly-selected file
- Save creates new file instead of updating
- File list shows outdated names until manual refresh

**Prevention strategy:**
```typescript
// Handle 404 gracefully in content query
const csvContentQuery = useQuery({
  queryKey: ['csvs', activeName],
  queryFn: async () => {
    const response = await fetchCsvContent(activeName!)
    return response
  },
  enabled: Boolean(activeName),
  retry: (failureCount, error) => {
    // Don't retry 404s - file is gone
    if (error instanceof Response && error.status === 404) return false
    return failureCount < 2
  },
})

// React to query errors
useEffect(() => {
  if (csvContentQuery.error) {
    const is404 = csvContentQuery.error?.message?.includes('not found')
    if (is404) {
      notifications.show({
        color: 'orange',
        title: 'File not found',
        message: `${activeName} may have been moved or deleted.`,
      })
      setActiveName('')
      // Refresh file list
      queryClient.invalidateQueries({ queryKey: ['csvs'] })
    }
  }
}, [csvContentQuery.error, activeName])
```

**Implementation step:** Content query error handling - detect 404, clear selection, refresh list.

---

## UX Antipatterns

### 10. Confirmation Dialog Fatigue

**What goes wrong:** User gets "Unsaved changes - discard?" dialog every time they switch files, even for trivial edits. They start clicking "Discard" reflexively and lose important work.

**Why it happens:** Dirty detection is too sensitive (any keystroke = dirty) or dialog appears too eagerly.

**Warning signs:**
- Users complain about "too many popups"
- Users lose work despite dialogs (reflexive dismissal)
- Dirty flag true even when content matches server

**Prevention strategy:**
```typescript
// Compare actual content, not just "any edit happened"
const isDirty = useMemo(() => {
  if (!serverContent) return false  // New file, not dirty

  // Normalize whitespace for comparison
  const normalizedEditor = editorContent.trim()
  const normalizedServer = serverContent.trim()

  return normalizedEditor !== normalizedServer
}, [editorContent, serverContent])

// Only show dialog if truly dirty
const handleFileSwitch = (newFile: string) => {
  if (isDirty) {
    openConfirmModal({
      title: 'Unsaved changes',
      children: (
        <Text>
          You have unsaved changes to <strong>{activeName}</strong>.
          <br />
          Save before switching?
        </Text>
      ),
      labels: { confirm: 'Save & Switch', cancel: 'Discard' },
      onConfirm: () => {
        handleSave()
        setActiveName(newFile)
      },
      onCancel: () => setActiveName(newFile),
    })
  } else {
    setActiveName(newFile)
  }
}
```

**Implementation step:** Dirty detection - compare normalized content, not change events.

**Sources:**
- [Form Data Loss Prevention in React](https://angular-evan.medium.com/form-data-loss-prevention-in-react-f7c3bbbe45e1)
- [Cloudscape Unsaved Changes Pattern](https://cloudscape.design/patterns/general/unsaved-changes/)

---

### 11. No Loading State During File Switch

**What goes wrong:** User clicks different file in dropdown. Nothing visibly changes for 500ms while content loads. User clicks again, thinking first click didn't register.

**Why it happens:** Loading state isn't shown during the brief window between selection change and content arrival.

**Warning signs:**
- Double-clicks cause race conditions (Pitfall #1)
- Users report "laggy" file switching
- Dropdown doesn't feel responsive

**Prevention strategy:**
```typescript
// Show loading state in editor during content fetch
const isLoadingContent = csvContentQuery.isFetching && Boolean(activeName)

return (
  <Stack>
    <Select
      disabled={isLoadingContent}  // Prevent rapid switching
      {...otherProps}
    />

    {isLoadingContent ? (
      <Paper withBorder p="xl" ta="center">
        <Loader size="sm" />
        <Text c="dimmed" mt="sm">Loading {activeName}...</Text>
      </Paper>
    ) : (
      <Textarea value={editorContent} {...editorProps} />
    )}
  </Stack>
)
```

**Implementation step:** Editor panel - show skeleton/loader when `csvContentQuery.isFetching`.

---

### 12. Optimistic Updates Without Rollback

**What goes wrong:** User saves file, UI shows "saved!" but API call fails silently. User navigates away, losing their work.

**Why it happens:** Optimistic update assumed success, but no rollback mechanism restored original state on error.

**Warning signs:**
- "Save" appears successful but data reverts on refresh
- No error notification despite failed API call
- Users report "changes didn't stick"

**Prevention strategy:**
```typescript
const uploadMutation = useMutation({
  mutationFn: (payload: CsvUploadPayload) => uploadCsv(payload),

  onMutate: async ({ name, content }) => {
    // Cancel in-flight queries
    await queryClient.cancelQueries({ queryKey: ['csvs', name] })

    // Snapshot previous value
    const previousContent = queryClient.getQueryData(['csvs', name])

    // Optimistically update
    queryClient.setQueryData(['csvs', name], content)

    return { previousContent, name }
  },

  onError: (error, variables, context) => {
    // Rollback on failure
    if (context?.previousContent !== undefined) {
      queryClient.setQueryData(
        ['csvs', context.name],
        context.previousContent
      )
    }

    notifications.show({
      color: 'red',
      title: 'Save failed',
      message: error.message || 'Could not save file. Please try again.',
    })
  },

  onSuccess: () => {
    notifications.show({
      color: 'teal',
      title: 'Saved',
      message: 'File saved successfully.',
    })
  },

  onSettled: (_, __, variables) => {
    // Always refetch to ensure consistency
    queryClient.invalidateQueries({ queryKey: ['csvs'] })
    queryClient.invalidateQueries({ queryKey: ['csvs', variables.name] })
  },
})
```

**Implementation step:** Upload mutation - add `onMutate` snapshot and `onError` rollback.

**Sources:**
- [TanStack Query Optimistic Updates](https://tanstack.com/query/v4/docs/framework/react/guides/optimistic-updates)
- [Concurrent Optimistic Updates Race Conditions](https://tkdodo.eu/blog/concurrent-optimistic-updates-in-react-query)

---

## Summary: Implementation Checklist

| Phase | Pitfall to Watch | Prevention |
|-------|------------------|------------|
| File Selection Handler | #1 Race Conditions | Use TanStack Query queryKey, not manual fetch |
| | #5 React 19 Batching | Set only activeName, let query sync content |
| | #6 Value/Data Mismatch | Validate value exists in data array |
| Unsaved Changes Hook | #2 Stale Closures | Use refs for current dirty state |
| | #10 Confirmation Fatigue | Compare normalized content, not change flags |
| Delete Handler | #3 Delete-While-Viewing | Clear all state in onSuccess, before invalidation |
| Empty State UI | #7 No Guidance | Show actionable empty state with upload CTA |
| Auto-Select Logic | #8 Double-Trigger | Use flag to prevent repeated auto-selection |
| Content Query | #9 External Changes | Handle 404, clear selection, refresh list |
| Loading States | #11 No Feedback | Disable dropdown during fetch, show skeleton |
| Save Mutation | #12 Silent Failures | Snapshot + rollback in mutation callbacks |
| Editor State | #4 Dual Source of Truth | Single activeName drives all derived state |

---

## Confidence Assessment

| Pitfall | Confidence | Basis |
|---------|------------|-------|
| Race Conditions | HIGH | Verified with TanStack Query docs + existing codebase pattern |
| Stale Closures | HIGH | Well-documented React antipattern with clear solutions |
| Delete-While-Viewing | HIGH | Identified in react-admin issue, clear reproduction |
| Dual Source of Truth | HIGH | Observed in existing CsvManager.tsx code |
| React 19 Batching | MEDIUM | Theoretical based on React 19 changes, not directly verified |
| Mantine Value/Data | HIGH | Documented in Mantine GitHub discussions |
| Empty State UX | HIGH | Standard UX pattern with many examples |
| Auto-Select Flicker | MEDIUM | Common pattern issue, timing-dependent |
| External Changes | MEDIUM | Edge case, depends on usage pattern |
| Confirmation Fatigue | HIGH | Well-documented UX antipattern |
| Loading Feedback | HIGH | Standard UX requirement |
| Optimistic Rollback | HIGH | TanStack Query documented pattern |
