# Protocol Wizard Architecture

## Component Hierarchy

```
ProtocolWizard
└── WizardProvider (Context)
    └── WizardContent
        ├── Mantine Stepper
        │   ├── Step 0: Deck Setup ✅
        │   ├── Step 1: Configuration ✅
        │   ├── Step 2: Transfer Map ✅
        │   └── Step 3: Review & Execute ✅
        └── WizardNavigation (Back/Next buttons)
```

---

## Step 0: Deck Setup (Phase 2 - Complete) ✅

```
DeckSetupStep
├── DeckGrid
│   ├── EmptySlot (12 slots: 1-11 + trash)
│   └── LabwareCard (drag-and-drop)
└── LabwareModal
    └── Add labware form
```

**State Managed:**
- `state.deckLayout: WorkingPlateEntry[]`

**Actions:**
- Add labware to slot
- Remove labware from slot
- Drag-and-drop reordering

**Validation:**
- `canProceed(0)`: Requires ≥1 source, ≥1 destination, ≥1 tip rack

---

## Step 1: Configuration (Phase 3 - Complete) ✅

```
ConfigurationStep
├── Grid (7/12 + 5/12)
│   ├── BasicSettingsForm
│   │   ├── Pipette Mode Select
│   │   ├── Tip Reuse Select
│   │   ├── Head Speed Input
│   │   └── Starting Tip Well Input
│   ├── AdvancedSettingsAccordion
│   │   ├── Pre-Aspirate Contact
│   │   ├── Post-Aspirate Wick
│   │   ├── Delays & Push-Out
│   │   └── Mixing Settings
│   └── Help Panel (sticky)
└── Multi-mode Warning Alert
```

**State Managed:**
- `state.settings: SettingsDocument`
- Auto-saved via `usePatchSetting` hook

**Features:**
- Help tooltips on every field (from `HELP_TEXT` constant)
- Auto-save with notifications
- Context-aware warnings (multi mode + non-96/384 plates)

**Validation:**
- `canProceed(1)`: Requires `settings !== null`

---

## Step 2: Transfer Map (Phase 4 - Complete) ✅

```
TransferMapStep
├── Grid (6/12 + 3/12 + 3/12)
│   ├── CsvEditor
│   │   ├── File Upload Button
│   │   ├── Add Row/Column Buttons
│   │   └── Tabs
│   │       ├── Spreadsheet View (react-spreadsheet)
│   │       └── Text View (textarea)
│   ├── TransferPreview (sticky)
│   │   └── First 5 transfers display
│   └── ValidationPanel (sticky)
│       ├── Validate Button
│       └── Results
│           ├── Summary Badges
│           └── Error/Warning List
```

**State Managed:**
- `state.csv.filename: string`
- `state.csv.content: string`

**Features:**
- Dual editing modes (spreadsheet/text)
- Real-time transfer preview
- Comprehensive validation:
  - Required columns check
  - Labware reference validation (against deck)
  - Well format validation (A1-H12, A1-P24)
  - Volume validation (numeric, positive)
  - Height column conflict detection

**Validation:**
- `canProceed(2)`: Requires `filename !== ''` and `content !== ''`

---

## Step 3: Review & Execute (Phase 5 - Complete) ✅

```
ReviewExecuteStep
├── ConfigSummary
│   ├── Pipette Mode Badge
│   ├── Tip Strategy Badge
│   ├── Head Speed
│   ├── Deck Layout Summary
│   ├── CSV Info
│   └── Liquid Handling Badges
├── PreflightChecklist
│   └── Validation Items (8 checks)
├── Execution Options
│   ├── Run Simulation Switch
│   ├── Copy to Clipboard Switch
│   └── Send to Opentrons Switch
├── Run Workflow Button
└── ProgressDisplay
    └── Mantine Stepper
        ├── Generate Step
        ├── Simulate Step
        └── Deploy Step
```

**State Managed:**
- All wizard state (read-only summary)
- Workflow execution state (via `useWorkflowRunner`)

**Features:**
- Comprehensive pre-flight validation (8 checks)
- Configurable execution options
- Real-time progress tracking
- Detailed simulation output display
- Error handling and user feedback

**Workflow API Call:**
```typescript
{
  csv: state.csv.filename,
  run_simulation: boolean,
  copy_to_clipboard: boolean,
  send_to_opentrons: boolean,
  use_shell_runner: false
}
```

**Validation:**
- `canProceed(3)`: Always true (final step)
- Button disabled if pre-flight checks fail

---

## State Flow Diagram

```
┌─────────────────────────────────────────────────────┐
│              WizardContext (Global State)            │
├─────────────────────────────────────────────────────┤
│ • currentStep: number (0-3)                         │
│ • deckLayout: WorkingPlateEntry[]                   │
│ • settings: SettingsDocument | null                 │
│ • csv: { filename: string, content: string }        │
└─────────────────────────────────────────────────────┘
           │
           ├─── Step 0 (Deck Setup)
           │    └─ Updates: deckLayout
           │
           ├─── Step 1 (Configuration)
           │    └─ Updates: settings (auto-saved to backend)
           │
           ├─── Step 2 (Transfer Map)
           │    └─ Updates: csv.filename, csv.content
           │
           └─── Step 3 (Review & Execute)
                └─ Reads: all state (immutable)
                └─ Executes: workflow API call
```

---

## API Integration

### Hooks Used

| Hook | Usage | Steps |
|------|-------|-------|
| `useSettingsQuery()` | Fetch settings from backend | 1, 3 |
| `usePatchSetting()` | Auto-save setting changes | 1 |
| `useWorkflowRunner()` | Execute protocol workflow | 3 |
| `useWizard()` | Access wizard context | All |
| `useLabwareQuery()` | Fetch labware definitions | 0 |

### Backend Endpoints

| Endpoint | Method | Purpose | Used In |
|----------|--------|---------|---------|
| `/api/settings` | GET | Fetch settings | Step 1, 3 |
| `/api/settings/patch` | POST | Update single setting | Step 1 |
| `/api/settings/working-plate` | POST | Add deck labware | Step 0 |
| `/api/settings/working-plate/{idx}` | DELETE | Remove deck labware | Step 0 |
| `/api/workflow` | POST | Execute full workflow | Step 3 |
| `/api/labware` | GET | Fetch labware catalog | Step 0 |
| `/api/csvs` | GET | List CSV files | Step 2 |
| `/api/csvs/upload` | POST | Upload CSV content | Step 2 |

---

## Validation Rules

### Step Progression (canProceed)

```typescript
canProceed(step: number): boolean {
  switch (step) {
    case 0: // Deck → Config
      return hasSource && hasDestination && hasTip
    case 1: // Config → Transfer
      return settings !== null
    case 2: // Transfer → Review
      return csv.filename !== '' && csv.content !== ''
    case 3: // Review (final)
      return true
  }
}
```

### Pre-flight Checks (Step 3)

```typescript
[
  { condition: hasSource, severity: 'error' },
  { condition: hasDestination, severity: 'error' },
  { condition: hasTip, severity: 'error' },
  { condition: settings !== null, severity: 'error' },
  { condition: csv.content !== '', severity: 'error' },
  { condition: csv.filename !== '', severity: 'warning' },
  { condition: noDuplicateSlots, severity: 'error' },
  { condition: slotCount <= 11, severity: 'error' }
]
```

### CSV Validation (Step 2)

```typescript
[
  'Required columns present',
  'Labware references exist in deck',
  'Well names valid format',
  'Volumes numeric and positive',
  'No height column conflicts (Source Height/Top, Dest Height/Top)'
]
```

---

## User Flow

```
1. User opens wizard
   └─> Lands on Step 0 (Deck Setup)

2. User adds labware to deck
   ├─> Clicks empty slot
   ├─> Selects labware type, slot, connection
   ├─> Labware appears on deck grid
   └─> Minimum: 1 source + 1 dest + 1 tip rack

3. User clicks "Next"
   └─> Proceeds to Step 1 (Configuration)

4. User configures settings
   ├─> Selects pipette mode
   ├─> Chooses tip reuse strategy
   ├─> Adjusts liquid handling parameters
   └─> Settings auto-save to backend

5. User clicks "Next"
   └─> Proceeds to Step 2 (Transfer Map)

6. User defines transfers
   ├─> Uploads CSV file OR
   ├─> Manually enters transfers in spreadsheet/text
   ├─> Previews transfers
   ├─> Validates CSV
   └─> Fixes any errors

7. User clicks "Next"
   └─> Proceeds to Step 3 (Review & Execute)

8. User reviews configuration
   ├─> Checks summary
   ├─> Verifies pre-flight checklist
   ├─> Enables execution options (simulate, clipboard, deploy)
   └─> Clicks "Run Workflow"

9. Workflow executes
   ├─> Generate protocol (helper_cherry_pick.py)
   ├─> Simulate protocol (opentrons_simulate) [optional]
   ├─> Deploy protocol (copy to paths) [optional]
   └─> Display results

10. User sees results
    ├─> Success: Green checkmarks, protocol ready
    ├─> Failure: Error messages, simulation output
    └─> Can retry or go back to fix issues
```

---

## File Structure

```
src/components/wizard/
├── ProtocolWizard.tsx          # Root wizard component
├── WizardContext.tsx            # Global state management
├── WizardNavigation.tsx         # Back/Next buttons
│
├── steps/
│   ├── DeckSetupStep.tsx        # Step 0 ✅
│   ├── ConfigurationStep.tsx    # Step 1 ✅
│   ├── TransferMapStep.tsx      # Step 2 ✅
│   └── ReviewExecuteStep.tsx    # Step 3 ✅
│
├── deck/
│   ├── DeckGrid.tsx             # Visual deck layout
│   ├── EmptySlot.tsx            # Empty slot placeholder
│   ├── LabwareCard.tsx          # Labware display card
│   └── LabwareModal.tsx         # Add labware dialog
│
├── config/
│   ├── BasicSettingsForm.tsx    # Core settings ✅
│   └── AdvancedSettingsAccordion.tsx  # Liquid handling ✅
│
├── csv/
│   ├── CsvEditor.tsx            # Spreadsheet/text editor ✅
│   ├── TransferPreview.tsx      # Preview panel ✅
│   └── ValidationPanel.tsx      # Validation results ✅
│
└── review/
    ├── ConfigSummary.tsx        # Configuration overview ✅
    ├── PreflightChecklist.tsx   # Validation checks ✅
    └── ProgressDisplay.tsx      # Workflow execution ✅
```

**Total: 18 component files**

---

## Design Principles

1. **Progressive Disclosure:** Complex settings hidden in accordions
2. **Inline Help:** Tooltips on every field (no external docs needed)
3. **Auto-save:** No save buttons, changes persist immediately
4. **Validation First:** Block progression if requirements not met
5. **Immediate Feedback:** Real-time validation and preview
6. **Error Recovery:** Clear error messages with actionable steps
7. **Transparency:** Progress display shows each execution step
8. **Flexibility:** Optional execution features (simulation, clipboard, deploy)

---

## Future Enhancements

- [ ] CSV template generator with pre-filled headers
- [ ] Deck layout templates (96→384, tube→plate, etc.)
- [ ] Liquid handling presets (viscous, volatile, standard)
- [ ] Protocol export/import (save wizard state as JSON)
- [ ] Undo/redo for deck modifications
- [ ] Validation auto-fix suggestions
- [ ] Real-time collaboration (multiple users)

---

**Architecture Status: COMPLETE ✅**
**Implementation Status: COMPLETE ✅**
**Build Status: PASSING ✅**
