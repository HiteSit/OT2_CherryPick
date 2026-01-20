# Architecture Research: File Selector Integration

**Domain:** React/FastAPI GUI for OT-2 Protocol Generator
**Researched:** 2026-01-20
**Overall Confidence:** HIGH (based on existing codebase patterns)

## Executive Summary

The file selector feature integrates a CSV file dropdown into the Transfer Map wizard step. The existing architecture already provides all necessary building blocks: `useCsvListQuery()` for fetching file lists, `useCsvContentQuery()` for loading content, WizardContext for state management, and the CsvEditor component structure. The key architectural decision is where to place state ownership and how to handle the dirty state warning for unsaved changes.

## Data Flow

### Current Architecture (As-Is)

```
Backend                          Frontend
-------                          --------
FileStateStore                   WizardContext
  |                                |
  +-- csv_dir (gui_state/CSVs/)    +-- state.csv { filename, content }
  |                                |
  v                                v
/csvs endpoint                   CsvEditor
  |                                |
  +-- GET /csvs -> list files      +-- useState(editorContent)
  +-- GET /csvs/{name} -> content  +-- useState(filename)
  +-- POST /csvs -> save           +-- react-spreadsheet
  +-- DELETE /csvs/{name}          +-- Textarea
```

### Proposed Architecture (To-Be)

```
Backend (no changes needed)      Frontend
---------------------------      --------
FileStateStore                   WizardContext
  |                                |
  +-- list_csv_files()             +-- state.csv { filename, content }
  |                                +-- (NEW) isDirty tracking via derived state
  v                                |
@tanstack/react-query              v
  |                              CsvEditor (enhanced)
  +-- useCsvListQuery()            |
  +-- useCsvContentQuery()         +-- FileSelector dropdown (NEW)
  |                                +-- useState(editorContent)
  |                                +-- isDirty = editorContent !== state.csv.content
  v                                |
CsvEditor                          +-- UnsavedChangesWarning modal (NEW)
  |                                |
  +-- Select dropdown              +-- Spreadsheet + Text views
  +-- Load file on selection
  +-- Track dirty state locally
```

### Data Flow Sequence

1. **Page Load:**
   ```
   CsvEditor mounts
     -> useCsvListQuery() fetches /csvs -> returns ["file1.csv", "file2.csv"]
     -> Select dropdown populated with options
     -> If state.csv.filename exists, pre-select it
   ```

2. **File Selection:**
   ```
   User selects "file1.csv" from dropdown
     -> Check isDirty (editorContent !== lastSavedContent)
     -> If dirty: show UnsavedChangesWarning modal
       -> User confirms discard OR cancels
     -> If not dirty OR confirmed:
       -> useCsvContentQuery("file1.csv") fetches /csvs/file1.csv
       -> setCSV(filename, content) updates WizardContext
       -> setEditorContent(content) updates local state
   ```

3. **Content Editing:**
   ```
   User edits spreadsheet or text view
     -> handleSheetChange() / handleTextChange()
     -> setEditorContent(newContent)
     -> setCSV(filename, newContent) updates WizardContext
     -> isDirty = editorContent !== lastSavedContent (derived)
   ```

4. **Save Operation:**
   ```
   User clicks "Save to workspace"
     -> uploadCsv.mutate({ name: filename, content: editorContent })
     -> On success: lastSavedContent = editorContent
     -> isDirty becomes false
   ```

## State Management

### Recommendation: Local State with WizardContext Sync

The existing pattern in CsvEditor is correct. Keep state ownership local with sync to WizardContext:

| State Variable | Location | Purpose |
|---------------|----------|---------|
| `filename` | useState | Currently editing filename |
| `editorContent` | useState | Current content (may be dirty) |
| `state.csv` | WizardContext | Last known good state for wizard validation |
| `isDirty` | Derived | `editorContent !== savedContent` |
| `savedContent` | useRef | Track last successfully saved content |

### Dirty State Detection

**Option A (Recommended): Compare against last saved content**

```typescript
const savedContentRef = useRef(state.csv.content)
const isDirty = editorContent !== savedContentRef.current

// Update ref on successful save
const handleSave = () => {
  uploadCsv.mutate({ ... }, {
    onSuccess: () => {
      savedContentRef.current = editorContent
    }
  })
}
```

**Option B: Track explicitly with boolean**

```typescript
const [isDirty, setIsDirty] = useState(false)

const handleTextChange = (value: string) => {
  setEditorContent(value)
  setIsDirty(true)
}

const handleSave = () => {
  // ... on success:
  setIsDirty(false)
}
```

**Recommendation:** Use Option A. Derived state is simpler and avoids synchronization bugs where `isDirty` could become inconsistent with actual content state.

### Why Not Lift State to WizardContext?

WizardContext already stores `state.csv` but adding `isDirty` there would:
1. Require all wizard steps to re-render on every keystroke
2. Complicate the context interface unnecessarily
3. Violate single responsibility (WizardContext manages step validation, not editor state)

Keep dirty state local to CsvEditor where it matters.

## Component Structure

### Current Component Hierarchy

```
TransferMapStep
  |
  +-- Paper > CsvEditor
  |     |
  |     +-- TextInput (filename)
  |     +-- FileInput (upload)
  |     +-- Tabs
  |         +-- Spreadsheet
  |         +-- Textarea
  |
  +-- Paper > ValidationPanel
  |
  +-- Paper > TransferPreview
```

### Proposed Component Hierarchy

```
TransferMapStep
  |
  +-- Paper > CsvEditor (enhanced)
  |     |
  |     +-- Group
  |     |   +-- FileSelector (NEW) - Select dropdown for existing files
  |     |   +-- TextInput (filename) - For new files / rename
  |     |   +-- FileInput (upload) - Upload from disk
  |     |
  |     +-- UnsavedChangesWarning (NEW) - Modal for dirty state warning
  |     |
  |     +-- Group (row actions)
  |     +-- Group (save button)
  |     +-- Tabs
  |         +-- Spreadsheet
  |         +-- Textarea
  |
  +-- Paper > ValidationPanel
  +-- Paper > TransferPreview
```

### FileSelector Component Design

```typescript
interface FileSelectorProps {
  selectedFile: string
  onSelect: (filename: string) => void
  isDirty: boolean
}

function FileSelector({ selectedFile, onSelect, isDirty }: FileSelectorProps) {
  const { data, isLoading } = useCsvListQuery()
  const [pendingSelection, setPendingSelection] = useState<string | null>(null)
  const [showWarning, setShowWarning] = useState(false)

  const handleChange = (value: string | null) => {
    if (!value) return
    if (isDirty) {
      setPendingSelection(value)
      setShowWarning(true)
    } else {
      onSelect(value)
    }
  }

  const confirmDiscard = () => {
    if (pendingSelection) {
      onSelect(pendingSelection)
    }
    setShowWarning(false)
    setPendingSelection(null)
  }

  return (
    <>
      <Select
        label="Load existing CSV"
        placeholder="Select file..."
        data={data?.files.map(f => ({ value: f, label: f })) ?? []}
        value={selectedFile}
        onChange={handleChange}
        loading={isLoading}
        searchable
        clearable={false}
      />
      <UnsavedChangesModal
        opened={showWarning}
        onConfirm={confirmDiscard}
        onCancel={() => setShowWarning(false)}
      />
    </>
  )
}
```

### UnsavedChangesWarning Component Design

```typescript
interface UnsavedChangesModalProps {
  opened: boolean
  onConfirm: () => void
  onCancel: () => void
}

function UnsavedChangesModal({ opened, onConfirm, onCancel }: UnsavedChangesModalProps) {
  return (
    <Modal opened={opened} onClose={onCancel} title="Unsaved Changes">
      <Text>You have unsaved changes. Loading a different file will discard them.</Text>
      <Group mt="md" justify="flex-end">
        <Button variant="default" onClick={onCancel}>Cancel</Button>
        <Button color="red" onClick={onConfirm}>Discard Changes</Button>
      </Group>
    </Modal>
  )
}
```

## Integration Points

### Backend (No Changes Required)

The existing `/csvs` endpoints provide everything needed:

| Endpoint | Method | Purpose | Already Exists |
|----------|--------|---------|----------------|
| `/csvs` | GET | List all CSV files | YES |
| `/csvs/{name}` | GET | Get file content | YES |
| `/csvs` | POST | Save/create file | YES |
| `/csvs/{name}` | DELETE | Delete file | YES |

### Frontend API Layer (No Changes Required)

Existing hooks in `api/hooks.ts`:

| Hook | Purpose | Already Exists |
|------|---------|----------------|
| `useCsvListQuery()` | Fetch file list | YES |
| `useCsvContentQuery(name)` | Fetch file content | YES |
| `useUploadCsv()` | Save file | YES |
| `useDeleteCsv()` | Delete file | YES |

### Existing Pattern Reference: CsvManager Component

The `CsvManager.tsx` component already implements the exact pattern needed:
- Uses `useCsvListQuery()` for dropdown
- Uses `useCsvContentQuery(activeName)` for content loading
- Tracks `gridDirty` state for unsaved changes
- Syncs state via `useEffect` when content loads

**Key insight:** CsvManager is a standalone CSV editor (not in wizard). The CsvEditor in the wizard can adopt the same file selection pattern with minor modifications for WizardContext integration.

## Build Order

### Phase 1: Core File Selection (Minimal Viable)

1. **Add FileSelector dropdown to CsvEditor**
   - Add `Select` component above filename input
   - Wire up `useCsvListQuery()` for options
   - On selection: load content via `useCsvContentQuery()`
   - Update both local state and WizardContext

2. **Track dirty state**
   - Add `savedContentRef` to track last saved content
   - Derive `isDirty` from comparison

**Dependencies:** None - uses existing backend and hooks

### Phase 2: Unsaved Changes Warning

3. **Create UnsavedChangesModal component**
   - Simple Mantine Modal with confirm/cancel buttons
   - Text explaining data will be lost

4. **Integrate modal into file selection flow**
   - Check `isDirty` before selection
   - Show modal if dirty
   - Only proceed on confirm

**Dependencies:** Phase 1 complete

### Phase 3: Polish and Edge Cases

5. **Handle edge cases**
   - Empty file list state
   - Loading states
   - Network errors on file load
   - Newly uploaded file auto-selection

6. **Visual dirty indicator**
   - Add asterisk to filename when dirty
   - Or badge/icon indicator

**Dependencies:** Phase 2 complete

### Phase Ordering Rationale

1. **Phase 1 first:** Provides immediate value (file selection) with no UX degradation. Users can still work without the warning system.

2. **Phase 2 second:** Adds data safety once selection works. Critical for preventing accidental data loss.

3. **Phase 3 last:** Polish items that improve UX but aren't blocking functionality.

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Dirty state false positives | Low | Medium | Use content comparison, not flag |
| React-query cache stale after save | Low | Low | Invalidate queries on mutation success |
| Modal focus trap issues | Low | Low | Use Mantine Modal (handles focus) |
| Large file performance | Low | Medium | Content is text, not binary; React-query caches |

## Sources

- Existing codebase analysis (HIGH confidence)
  - `/src/gui/frontend/src/components/CsvManager.tsx` - Reference implementation
  - `/src/gui/frontend/src/components/wizard/csv/CsvEditor.tsx` - Target component
  - `/src/gui/frontend/src/api/hooks.ts` - Existing query hooks
  - `/src/gui/backend/routes/csvs.py` - Backend endpoints
- Mantine UI documentation for Modal, Select components (assumed current via training)

## Confidence Assessment

| Area | Level | Reason |
|------|-------|--------|
| Data flow | HIGH | Verified against existing codebase |
| State management approach | HIGH | Mirrors existing CsvManager pattern |
| Component structure | HIGH | Direct codebase analysis |
| Build order | HIGH | Dependency analysis from code |
| Backend changes | HIGH | None required - endpoints exist |

## Open Questions

None - the existing architecture provides all necessary building blocks. This is a pure frontend enhancement with no backend changes needed.
