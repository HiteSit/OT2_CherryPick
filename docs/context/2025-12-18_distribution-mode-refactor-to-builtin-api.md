# Distribution Mode Refactoring: Manual Implementation → Built-in `distribute()` API

> **Date**: 2025-12-18
> **Type**: refactor
> **Tags**: #distribution #opentrons-api #multi-channel #liquid-handling #breaking-change

## Summary

The distribution mode implementation in `CherryPick_OT2.py` was refactored from a manual aspirate/dispense loop to use Opentrons' built-in `pipette.distribute()` API. This change was motivated by a bug in the manual implementation and the realization that the built-in API handles trip planning, carryover, and multi-destination dispensing automatically.

A key discovery during this refactoring was that **per-destination mixing is NOT supported** by the `distribute()` API—it ignores the `mix_after` parameter. This was deemed acceptable because distribution mode is primarily used for dilution workflows where destination mixing is not needed.

Additionally, the mixing configuration was enhanced with an `enabled` boolean field for cleaner validation logic, following the pattern established by other settings sections (`pre_aspirate_contact.enabled`, `post_aspirate_wick.enabled`, etc.).

## Why the Old Implementation Was Problematic

### 1. Manual Trip Planning Complexity

The old implementation included a `plan_distribution_trips()` function that manually calculated how to split large distributions across multiple aspirate cycles. This duplicated logic that the Opentrons API already provides via the `carryover=True` parameter.

```python
# OLD: Deleted function - manual trip planning
def plan_distribution_trips(dest_volumes, max_capacity, min_volume, air_gap_volume):
    """
    Plan distribution trips to fit within pipette capacity
    ... ~50 lines of complex logic ...
    """
```

### 2. Manual Aspirate/Dispense Loop

The old implementation manually looped through destinations, handling each dispense individually:

```python
# OLD: Manual implementation pattern (conceptual)
for trip in trips:
    pipette.aspirate(total_volume, source)
    for dest_well, volume in trip.destinations:
        pipette.dispense(volume, dest_well)
        if air_gap:
            pipette.air_gap(air_gap_volume)
    pipette.blow_out()
```

This was error-prone and didn't leverage the API's built-in optimizations for:
- Air gap handling between destinations
- Disposal volume management
- Automatic blow-out positioning

### 3. Bug in Manual Implementation

The specific bug that triggered this refactoring was not fully diagnosed, but the manual implementation had edge cases around:
- Volume tracking across multi-trip distributions
- Air gap accumulation
- Tip state management between trips

## The New Implementation

### Core Change: Single API Call

The `perform_distribution()` function now uses a single `pipette.distribute()` call:

```python
# NEW: Built-in API (CherryPick_OT2.py lines 766-777)
pipette.distribute(
    volume=dest_volumes,          # List of volumes [50, 50, 50, 50]
    source=source_location,       # Source well with height offset
    dest=dest_well_objs,          # List of destination Well objects
    air_gap=air_gap_volume,       # Air gap between destinations
    disposal_volume=0,            # No disposal (user decision - keep simple)
    mix_before=mix_tuple,         # Optional source mixing
    blow_out=True,                # Blow out after distribution
    blowout_location='source well',
    new_tip='never',              # Manual tip management via Tip Action column
    carryover=True                # Enable multi-trip if volumes exceed capacity
)
```

### Function Signature Changes

The `perform_distribution()` function signature was simplified:

```python
# OLD signature (more parameters for manual control)
def perform_distribution(transfer, pipette, loaded_labware, pipette_config,
                        liquid_contact_config, wick_config, delay_config,
                        push_out_config, mixing_config, mixing_location,  # <-- removed
                        mixing_repetitions, source_remixing, mixed_source_wells,
                        general_settings, protocol, mode, row_index):

# NEW signature (removed push_out_config and mixing_location - handled differently)
def perform_distribution(transfer, pipette, loaded_labware, pipette_config,
                        liquid_contact_config, wick_config, delay_config,
                        mixing_config, mixing_repetitions,  # mixing_location now from config
                        source_remixing, mixed_source_wells, general_settings,
                        protocol, mode, row_index):
```

### Mixing Configuration Enhancement

Added `enabled` boolean to `[settings.liquid_handling.mixing]`:

```toml
# OLD format
[settings.liquid_handling.mixing]
location = "none"           # Used "none" to disable
repetitions = 3
source_remixing = "once"

# NEW format
[settings.liquid_handling.mixing]
enabled = false             # Explicit enable/disable boolean
location = "destination"    # Now always a valid location
repetitions = 3
source_remixing = "once"
```

This matches the pattern of other sections and enables cleaner validation:

```python
# NEW: Clean boolean check (CherryPick_OT2.py lines 722-730)
mixing_enabled = mixing_config.get('enabled', False)

should_mix_source = (
    mixing_enabled and
    mix_volume > 0 and
    mixing_location == 'source' and
    (source_remixing == 'always' or source_well_key not in mixed_source_wells)
)
```

### Deleted Code

The `plan_distribution_trips()` function was completely removed:

```python
# Line 637-638 in CherryPick_OT2.py
# plan_distribution_trips() function has been REMOVED
# The built-in pipette.distribute() API handles trip planning automatically via carryover=True parameter
```

## Critical I/O Change: 8-Channel Well Format

### The Problem

When testing with `multi` mode (full 8-channel), the `distribute()` API threw:

```
RuntimeError [line 766]: Invalid target for multichannel transfer:
[C1 of 384_ppv_55ul on slot 2, C2 of 384_ppv_55ul on slot 2, ...]
```

### Root Cause

For 8-channel pipettes on 384-well plates, the Opentrons API only accepts **primary wells** as targets:
- **A-row wells** (A1, A2, A3...) → access odd rows: A, C, E, G, I, K, M, O
- **B-row wells** (B1, B2, B3...) → access even rows: B, D, F, H, J, L, N, P

Wells like C1, D1, E1 are NOT valid primary targets because they're intermediate rows that the 8-channel pipette accesses implicitly when targeting A1 or B1.

### CSV Format Change (Breaking Change)

**OLD CSV format** (individual wells across rows - INVALID for 8-channel):
```csv
Source Labware,Source Well,Distribution Volume (ul),Dest Labware,Dest Well,...
tube_rack_96_1500ul_4,A1,50,384_ppv_55ul_2,B1|B2|B3|B4,...
tube_rack_96_1500ul_4,A2,100,384_ppv_55ul_2,C1|C2|C3|C4,...  # INVALID: C-row
tube_rack_96_1500ul_4,A3,60,384_ppv_55ul_2,D1|D2|D3|D4|D5,...  # INVALID: D-row
tube_rack_96_1500ul_4,A4,20,384_ppv_55ul_2,E1|E2|E3|E4,...  # INVALID: E-row
```

**NEW CSV format** (column representatives for 8-channel):
```csv
Source Labware,Source Well,Distribution Volume (ul),Dest Labware,Dest Well,...
tube_rack_96_1500ul_4,A1,50,384_ppv_55ul_2,A1|A2|A3|A4,...    # A-row: columns 1-4
tube_rack_96_1500ul_4,A2,100,384_ppv_55ul_2,A5|A6|A7|A8,...   # A-row: columns 5-8
tube_rack_96_1500ul_4,A3,60,384_ppv_55ul_2,B1|B2|B3|B4|B5,... # B-row: columns 1-5
tube_rack_96_1500ul_4,A4,20,384_ppv_55ul_2,B6|B7|B8|B9,...    # B-row: columns 6-9
```

### Semantic Difference by Mode

| Mode | Dest Well `A1\|A2\|A3\|A4` | Wells Filled |
|------|---------------------------|--------------|
| `single_X1` | 4 individual wells | 4 wells total |
| `multi_X1` | 4 individual wells (single-tip from 8ch) | 4 wells total |
| `multi` | 4 columns (8 wells each) | 32 wells total |

## Files Changed

### Core Protocol

- **`CherryPick_OT2.py`**
  - `perform_distribution()`: Refactored to use `distribute()` API (lines 640-787)
  - `plan_distribution_trips()`: **DELETED** (was ~50 lines)
  - Mixing validation: Now checks `mixing_enabled` boolean (lines 722-730, 825-826)
  - Warning for distribution + destination mixing: Added user notification (lines 840-842)

### Configuration

- **`settings.toml`**
  - Added `enabled = false` to `[settings.liquid_handling.mixing]`
  - Changed `location = "none"` → `location = "destination"`
  - Updated all 6 presets (standard, viscous, slippery, minimal, aggressive, cell_resuspension) to include `enabled = true`

### Test Configuration Files

Six E2E config files updated with new mixing format:

- `tests/e2e/configs/distribution/settings.toml`
- `tests/e2e/configs/single_X1/settings.toml`
- `tests/e2e/configs/multi/settings.toml`
- `tests/e2e/configs/multi_X1/settings.toml`
- `tests/e2e/configs/dual/settings.toml`
- `tests/e2e/configs/fill_analytics/settings.toml`

All changed from:
```toml
[settings.liquid_handling.mixing]
location = "none"
```

To:
```toml
[settings.liquid_handling.mixing]
enabled = false
location = "destination"
```

### Test CSVs

- **`CSVs/example_distribution.csv`**: Changed destinations from C/D/E-row to A/B-row wells
- **`CSVs/example_mixed_modes.csv`**: Changed `C1|C2|C3|C4` → `A6|A7|A8|A9`

## Test Results

After changes:
- **87 E2E tests pass** (all distribution, mixed modes, multi-channel tests)
- 16 unit test failures are **pre-existing issues** (unrelated to this refactoring)
  - Root cause: `settings.toml` has empty `labware_id = ""` in heaterShaker module entry

Specific test files that now pass:
- `tests/e2e/test_distribution.py` - 8 tests
- `tests/e2e/test_distribution_validation.py` - 19 tests
- `tests/e2e/test_real_world.py::TestProtocolCompleteness::test_protocol_completes[example_distribution.csv-multi]`

## Key Technical Decisions

### 1. No Disposal Volume

**Choice**: Set `disposal_volume=0` in the `distribute()` call.

**Why**: User explicitly chose simplicity over accuracy. Disposal volume aspirates extra liquid that gets blown out, which wastes reagent. For most distribution use cases (dilutions), this waste is unacceptable.

**Trade-off**: Slightly less accurate final dispenses due to residual liquid in tip.

### 2. Mix Before Only (No Mix After)

**Choice**: Accept that `distribute()` ignores `mix_after` parameter.

**Why**: Distribution mode is primarily for dilutions where destination mixing is scientifically inappropriate (you'd mix the dilution gradient). If per-destination mixing is needed, cherry-pick mode should be used instead.

**Documentation**: Warning added to protocol output (lines 840-842).

### 3. Manual Tip Management

**Choice**: Set `new_tip='never'` and manage tips via `Tip Action` CSV column.

**Why**: Preserves existing per-row tip control from CSV. The built-in `new_tip` options ('always', 'once', 'never') don't map cleanly to the CSV's row-by-row specification.

## API Reference

From Opentrons documentation (confirmed via web search):

```python
distribute(
    self,
    volume: Union[float, Sequence[float]],  # Single or list of volumes
    source: labware.Well,                    # Source well (accepts Location too)
    dest: List[labware.Well],                # Destination wells
    *args, **kwargs
) → InstrumentContext
```

Key parameters:
- `air_gap`: Volume of air gap between destinations
- `disposal_volume`: Extra volume to aspirate (blown out at end)
- `mix_before`: Tuple of (reps, volume) or (reps, volume, location)
- `blow_out`: Whether to blow out after dispensing
- `blowout_location`: 'source well', 'destination well', or 'trash'
- `carryover`: If True, enables multi-trip when volumes exceed capacity
- `new_tip`: 'always', 'once', or 'never'

**Important**: For multi-channel pipettes on 384-well plates, only A-row or B-row wells are valid targets.

## Multi-Channel Distribution Validation (Added 2025-12-18)

### The Hidden Problem: Simulator Lies

After the initial refactoring, we discovered a critical issue: **the Opentrons simulator silently accepts physically impossible operations**.

When running `example_distribution.csv` with `mode = "multi"`, the simulation showed:
```
Using legacy mode: multi
Picking up tip from A1 of Opentrons OT-2 96 Tip Rack 300 µL on slot 1
Dispensing 50.0 uL into A1 of 384_ppv_55ul on slot 2
Dispensing 50.0 uL into A2 of 384_ppv_55ul on slot 2
Dispensing 50.0 uL into A3 of 384_ppv_55ul on slot 2
...
Protocol complete: 4 transfers
=== Simulation successful!
```

**The lie**: In `multi` mode, "Picking up tip from A1" means **8 tips at once** (A1-H1). But the simulation showed individual well dispensing (A1, A2, A3, A4) - which is **physically impossible** with 8 tips loaded.

The real robot would either:
1. Crash with an error
2. Dispense to wrong wells (8 at a time instead of 1)
3. Behave unpredictably

### The Validation Fix

We added validation at **two layers** to catch this before it ever reaches the misleading simulator.

#### 1. Protocol Level (`CherryPick_OT2.py` lines 640-689)

New function `validate_distribution_wells_for_multi_mode()`:

```python
def validate_distribution_wells_for_multi_mode(dest_wells: list, mode: str, row_index: int):
    """
    Validate that destination wells are compatible with multi-channel pipette operation.

    In multi mode (8-channel with all nozzles active), each well name represents a COLUMN:
    - 96-well plate: A1 means column 1 (all 8 wells A1-H1)
    - 384-well plate: A1 means column 1 with A-interleaving (A1,C1,E1,G1,I1,K1,M1,O1)
                      B1 means column 1 with B-interleaving (B1,D1,F1,H1,J1,L1,N1,P1)

    For distribution to work correctly with multi-channel:
    - All destination wells MUST have the same row letter (same interleaving pattern)
    - Valid: A1|A2|A3|A4 (all A-row = distribute to columns 1,2,3,4)
    - Valid: B1|B2|B3 (all B-row = distribute to columns 1,2,3 with B-interleaving)
    - INVALID: A1|B2|A3 (mixing rows = physically impossible with 8-channel)
    """
    if mode != 'multi':
        return  # Only validate for full multi-channel mode

    # Extract row letters from all destination wells
    row_letters = set()
    for well in dest_wells:
        row_letter = ''.join(c for c in well.strip().upper() if c.isalpha())
        if row_letter:
            row_letters.add(row_letter)

    if len(row_letters) > 1:
        raise ValueError(
            f"Row {row_index + 2}: Distribution wells are incompatible with multi-channel mode. "
            f"Found mixed row letters: {sorted(row_letters)}. "
            f"In multi mode, ALL destination wells must have the SAME row letter."
        )
```

Called immediately after parsing destination wells in `perform_distribution()`:

```python
dest_well_names = dest_wells_str.split('|')
validate_distribution_wells_for_multi_mode(dest_well_names, mode, row_index)  # NEW
```

#### 2. GUI Level (`ValidationPanel.tsx` lines 165-184)

Added validation in the CSV validation panel:

```typescript
// Multi-channel distribution validation
const currentMode = state.settings?.settings?.general?.mode
if (hasPipe && currentMode === 'multi') {
  const wellNames = destWell.split('|').map((w: string) => w.trim().toUpperCase())
  const rowLetters = new Set(
    wellNames
      .filter((w: string) => w.length > 0)
      .map((w: string) => w.replace(/\d+/g, ''))  // Extract row letter(s)
  )

  if (rowLetters.size > 1) {
    newResults.push({
      type: 'error',
      message: `Distribution wells incompatible with multi-channel mode. Found mixed row letters. In multi mode, all wells must have the SAME row letter.`,
      row: i + 2
    })
  }
}
```

### The Surprise: example_distribution.csv Was Already Valid

Upon investigation, the existing `example_distribution.csv` **is actually valid** for multi mode:

| Row | Dest Well | Row Letters | Valid for Multi? |
|-----|-----------|-------------|------------------|
| 2 | A1\|A2\|A3\|A4 | A only | ✅ Yes |
| 3 | A5\|A6\|A7\|A8 | A only | ✅ Yes |
| 4 | B1\|B2\|B3\|B4\|B5 | B only | ✅ Yes |
| 5 | B6\|B7\|B8\|B9 | B only | ✅ Yes |

Each distribution line uses consistent row letters within itself. The A-row and B-row distributions are **separate operations**, each targeting their respective interleaving pattern.

An **invalid** CSV would be:
```csv
Dest Well
A1|B2|A3|B4   # INVALID: Mixed A and B rows in single distribution
```

### Test Results

Three scenarios tested:

1. **single_X1 + distribution CSV** → ✅ PASS (4 transfers, individual wells)
2. **multi + valid distribution CSV** → ✅ PASS (4 transfers, column operations)
3. **multi + invalid mixed-row CSV** → ✅ FAIL with clear error:
   ```
   ValueError [line 683]: Row 2: Distribution wells 'A1|B2|A3|B4' are incompatible
   with multi-channel mode. Found mixed row letters: ['A', 'B']. In multi mode,
   ALL destination wells must have the SAME row letter.
   ```

### Updated Test Configuration

Updated `tests/e2e/conftest.py` with clearer documentation:

```python
# Distribution CSVs - work with multi mode ONLY if each distribution uses consistent row letters
# (e.g., A1|A2|A3 or B1|B2|B3, NOT A1|B2|A3 which mixes interleaving patterns)
# Both CSVs use consistent row letters per distribution, so they're multi-compatible
"example_distribution.csv": ["multi", "single_X1", "multi_X1"],
"example_mixed_modes.csv": ["multi", "single_X1", "multi_X1"],
```

## Next Steps

- [x] ~~Consider adding validation in `validate_csv_labware_match()` to check for invalid multi-channel well targets~~ **DONE** (implemented as `validate_distribution_wells_for_multi_mode()` + GUI validation)
- [ ] Document the CSV format difference between single-channel and multi-channel distribution in CLAUDE.md
- [ ] Fix pre-existing unit test failures (empty `labware_id` in heaterShaker module)

---

*Consolidated from conversation on 2025-12-18*
*Updated 2025-12-18 with multi-channel distribution validation*
