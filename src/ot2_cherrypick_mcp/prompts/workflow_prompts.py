"""
Core workflow prompts for MCP server.

Provides comprehensive guidance for setup, regeneration, deployment, validation,
and troubleshooting workflows.
"""

from __future__ import annotations

from fastmcp import FastMCP

__all__ = ["register_workflow_prompts"]


def register_workflow_prompts(mcp: FastMCP) -> None:
    """Register workflow prompts for guided interactions."""

    @mcp.prompt
    def setup_new_experiment() -> str:
        """
        Guide user through complete experimental setup from scratch.

        User intent: "Set up a new experiment" or "Start a new cherry-pick protocol from scratch"
        """

        return """
## Goal
Set up a complete cherry-pick experiment from project initialization through validated protocol

## This Workflow Covers
- Project directory initialization
- Deck layout configuration
- CSV transfer map creation
- Protocol generation
- Simulation validation

## Prerequisites
- Know your source and destination labware types
- Know approximate number of transfers
- Have transfer details (which wells → which wells)

## Workflow

### Step 1: Initialize Project
- **Tool:** `initialize_project()`
- **Action:** Create project directory structure with template files
- **Result:** Creates:
  - settings.toml (protocol configuration)
  - labware_dict.toml (labware catalog)
  - CherryPick_OT2.py (protocol template)
  - CSVs/ directory (for transfer maps)

**If project already exists:**
- Skip this step
- Proceed to Step 2 with existing files

### Step 2: Inspect Current Configuration
- **Tool:** Read `config://settings`
- **Action:** Review default settings
- **Tool:** Read `status://deck-layout`
- **Action:** See current deck configuration (likely empty for new project)

### Step 3: Configure Deck Layout
**Use the `configure_deck_layout` prompt for detailed guidance**

**Quick setup:**
- Add source labware to deck (e.g., slot 4)
- Add destination labware to deck (e.g., slot 2)
- Add tip racks to deck (e.g., slot 5)

**Tool:** `update_settings(path="settings.working_plate", value=[...array of labware entries...])`

**Example:**
```python
update_settings(
    path="settings.working_plate",
    value=[
        {"type": "source", "labware_id": "tube_rack_96_1500ul", "position_rack": "4"},
        {"type": "destination", "labware_id": "384_ppv_55ul", "position_rack": "2"},
        {"type": "tip", "labware_id": "opentrons_96_tiprack_300ul", "connection": "Pipette_1", "position_rack": "5"}
    ]
)
```

### Step 4: Configure Basic Settings

**Pipette Mode:**
- **Tool:** `update_settings(path="settings.general.mode", value="single_X1")`
- **Options:** "single_X1" (single-tip), "multi" (8-channel full), "multi_X1" (8-channel single-tip)
- **Default:** "single_X1" is safest for most applications

**Tip Reuse Strategy:**
- **Tool:** `update_settings(path="settings.general.tip_reuse", value="per_source")`
- **Options:** "never" (new tip every transfer), "per_source" (new tip per source plate), "always" (one tip entire protocol)
- **Recommendation:** "per_source" balances cleanliness and efficiency

**Head Speed (optional):**
- **Default:** 400 mm/min works for most applications
- **Only adjust if:** Working with volatile solvents (reduce to 250-300) or need faster throughput (increase to 500)

### Step 5: Create CSV Transfer Map
**Use the `create_csv_transfer_map` prompt for detailed guidance**

**Quick approach:**
- **Tool:** `generate_csv_template(source_labware="SOURCE_ID_SLOT", dest_labware="DEST_ID_SLOT", num_transfers=N)`
- **Example:** `generate_csv_template(source_labware="tube_rack_96_1500ul_4", dest_labware="384_ppv_55ul_2", num_transfers=24)`
- **Result:** Template CSV created in CSVs/ directory

**Edit the CSV:**
- Fill in Source Well, Dest Well, Volume columns
- Add height columns (Source Height, Dest Height)
- Save as .csv file

**Verify CSV exists:**
- **Tool:** Read `files://csvs`
- **Expected:** See your CSV filename listed

### Step 6: Validate Configuration
- **Tool:** `validate_configuration()`
- **Action:** Pre-flight checks before protocol generation
- **Check for:**
  - Labware ID mismatches
  - Slot conflicts
  - CSV format errors
  - Volume out of range

**If errors found:**
- Fix issues based on validation messages
- Re-run validation until clean

### Step 7: Generate Protocol
- **Tool:** `generate_protocol(csv_path="CSVs/your_file.csv")`
- **Action:** Compile TOML + CSV into executable protocol
- **Result:** CherryPick_OT2.py updated with embedded configuration

### Step 8: Simulate Protocol
- **Tool:** `simulate_protocol()`
- **Action:** Test protocol with Opentrons simulator
- **Check:** Read `logs://last-simulation` for results

**If simulation succeeds:**
- Protocol is ready for deployment
- Proceed to Step 9

**If simulation fails:**
- Use `troubleshoot_simulation_error` prompt for systematic debugging
- Fix issues and re-simulate

### Step 9: Deploy (Optional)
**If satisfied with simulation:**
- **Tool:** `deploy_to_opentrons(copy_to_clipboard=True)`
- **Action:** Copy protocol to clipboard for manual placement
- **Or:** `deploy_to_opentrons(target_path="/path/to/opentrons/protocols/")`

**For robot execution:**
- Open Opentrons App
- Import protocol (paste from clipboard or select file)
- Run "Labware Position Check" for calibration offsets
- Execute protocol

## Common Decision Points

### "I don't know which labware to use"
- **Check:** `config://labware` to see available labware catalog
- **If needed:** Use `add_custom_labware` prompt to add new labware

### "I want to use multi-channel pipette"
- **Use:** `switch_to_multi_channel` prompt instead of setting mode manually
- **Important:** Multi-channel only works with 96/384-well plates

### "My labware has calibration offsets"
- **Add offsets** when adding labware to catalog (labware_dict.toml)
- Or perform "Labware Position Check" in Opentrons App during robot setup

## Success Criteria
- ✓ Project initialized with all template files
- ✓ Deck layout configured (`status://deck-layout` shows labware)
- ✓ CSV transfer map created and valid
- ✓ `validate_configuration()` passes
- ✓ Protocol generates without errors
- ✓ Simulation succeeds (`logs://last-simulation` shows success)

## Next Steps
After successful setup:
- Run protocol on OT-2 with test samples (water/dye)
- Observe liquid handling performance
- Adjust parameters if needed (use `optimize_transfer_parameters` prompt)
- Run with real samples when validated

## Troubleshooting Quick Reference
- **Labware not found** → Check `config://labware`, verify api_id
- **Slot conflict** → Ensure unique position_rack values in deck layout
- **CSV format error** → Review required columns, check height column rules
- **Volume warning** → Verify transfer volumes within pipette range
- **Multi mode incompatible** → Switch to 96/384-well plates or use multi_X1 mode
"""

    @mcp.prompt
    def regenerate_protocol() -> str:
        """
        Quick workflow to regenerate protocol after CSV or settings changes.

        User intent: "I edited my CSV, regenerate the protocol" or "Quick regenerate"
        """

        return """
## Goal
Regenerate protocol after editing CSV or settings (quick workflow for experienced users)

## When to Use This Prompt
- You already have a working protocol
- You made changes to CSV transfer map
- You adjusted settings (tip strategy, head speed, etc.)
- You just need to regenerate and re-test

## Prerequisites
- Project already initialized
- CSV file exists and has been edited
- Settings.toml configured

## Workflow

### Step 1: Verify Changes
**If you edited CSV:**
- **Tool:** Read `files://csvs`
- **Action:** Confirm CSV file exists

**If you edited settings:**
- **Tool:** Read `config://settings`
- **Action:** Verify changes took effect

### Step 2: Optional Pre-Validation
**Recommended for significant changes:**
- **Tool:** `validate_configuration()`
- **Action:** Catch errors before generation
- **Benefit:** Faster feedback than waiting for simulation

**Skip if:**
- Only minor CSV edits (well positions, volumes)
- Confident in changes

### Step 3: Generate Protocol
- **Tool:** `generate_protocol(csv_path="CSVs/your_file.csv")`
- **Action:** Rebuild protocol with new configuration
- **Result:** CherryPick_OT2.py updated

### Step 4: Simulate
- **Tool:** `simulate_protocol()`
- **Action:** Validate new protocol works
- **Check:** Read `logs://last-simulation`

**If simulation succeeds:**
- Protocol ready for deployment
- Proceed to Step 5 or deploy

**If simulation fails:**
- **Tool:** Use `troubleshoot_simulation_error` prompt
- **Action:** Systematic debugging
- **Fix and return to Step 3**

### Step 5: Deploy (If Satisfied)
- **Tool:** `deploy_to_opentrons(copy_to_clipboard=True)`
- **Action:** Copy to clipboard or save to Opentrons App directory

## Quick Checklist

Before regenerating, ask yourself:
- ✓ Did I save CSV changes?
- ✓ Are labware references in CSV correct (match deck layout)?
- ✓ Did settings changes require updating CSV (e.g., switching to multi mode)?

## Common Scenarios

### Scenario: Added More Transfers to CSV
**Workflow:**
1. Edit CSV: Add rows with new transfers
2. Check tip rack capacity (`status://deck-layout` - ensure enough tips)
3. Regenerate: `generate_protocol(csv_path="CSVs/updated.csv")`
4. Simulate: `simulate_protocol()`

### Scenario: Changed Tip Reuse Strategy
**Workflow:**
1. Update setting: `update_settings(path="settings.general.tip_reuse", value="never")`
2. Regenerate: `generate_protocol(csv_path="CSVs/existing.csv")`
3. Simulate: Check tip consumption in logs

### Scenario: Adjusted Transfer Heights in CSV
**Workflow:**
1. Edit CSV: Update Source Height or Dest Height columns
2. Regenerate: `generate_protocol(csv_path="CSVs/adjusted.csv")`
3. Simulate: Verify no errors
4. Test on robot: Observe actual liquid handling

### Scenario: Switched to Multi-Channel Mode
**Workflow:**
1. **First use** `switch_to_multi_channel` prompt for guided setup
2. Verify CSV interpretation (each row = 8 transfers now)
3. Regenerate: `generate_protocol(csv_path="CSVs/existing.csv")`
4. Simulate: Expect 8× more transfers than CSV rows

## Success Criteria
- ✓ Protocol regenerates without errors
- ✓ Simulation succeeds
- ✓ Changes reflected in generated protocol

## If Errors Occur
- **Use:** `troubleshoot_simulation_error` prompt for systematic debugging
- **Common causes:**
  - CSV labware references don't match deck layout
  - Forgot to update CSV after changing pipette mode
  - Insufficient tips on deck for new strategy
"""

    @mcp.prompt
    def deploy_to_robot() -> str:
        """
        Final deployment workflow after successful simulation.

        User intent: "Deploy protocol to robot" or "Copy protocol to Opentrons App"
        """

        return """
## Goal
Deploy validated protocol to OT-2 robot for execution

## Prerequisites
- Protocol successfully simulated
- No errors in `logs://last-simulation`
- Protocol reviewed and approved for deployment

## Pre-Deployment Checklist

### Safety Check
- ✓ Protocol simulated successfully
- ✓ Transfer volumes within pipette range
- ✓ Deck layout matches physical robot setup
- ✓ Labware calibration offsets verified (if using custom offsets)
- ✓ Tip consumption calculated (sufficient tips on deck)

### Physical Setup Verification
**Ensure robot has:**
- ✓ All labware types from deck layout
- ✓ Sufficient tip racks
- ✓ Correct pipette(s) mounted (single vs multi-channel)
- ✓ Fresh tips loaded
- ✓ Samples/reagents ready

## Deployment Workflow

### Step 1: Final Validation
- **Tool:** Read `logs://last-simulation`
- **Action:** Review simulation output one last time
- **Look for:**
  - No errors or warnings
  - Expected number of transfers
  - Correct tip usage pattern

### Step 2: Optional Final Regeneration
**If any doubts about protocol state:**
- **Tool:** `generate_protocol(csv_path="CSVs/your_file.csv")`
- **Action:** Ensure protocol is latest version
- **Tool:** `simulate_protocol()`
- **Action:** Re-validate

### Step 3: Deploy Protocol
**Option A: Copy to Clipboard**
- **Tool:** `deploy_to_opentrons(copy_to_clipboard=True)`
- **Action:** Protocol text copied to clipboard
- **Next:** Paste into Opentrons App manually

**Option B: Copy to Opentrons Directory**
- **Tool:** `deploy_to_opentrons(target_path="/path/to/opentrons/protocols/")`
- **Action:** Protocol file copied to Opentrons App directory
- **Result:** Appears in app automatically

**Option C: Manual File Copy**
- Locate: CherryPick_OT2.py in project directory
- Copy to: Opentrons App protocols folder
- Typical path: `C:/Users/USERNAME/AppData/Roaming/Opentrons/protocols/`

### Step 4: Import in Opentrons App
1. Open Opentrons App
2. Navigate to Protocol Library
3. If used clipboard: Click "Import" → Paste protocol text
4. If used file copy: Protocol should appear automatically
5. Select protocol

### Step 5: Perform Labware Position Check
**CRITICAL for accurate pipetting:**
1. Click "Labware Position Check" in Opentrons App
2. For each labware on deck:
   - Jog pipette to correct position (well center, proper height)
   - Note offset values if different from defaults
3. Save calibration

**When to skip:**
- Using standard Opentrons labware with no custom offsets
- Previously calibrated same labware/robot combination (Opentrons v6.0.0+)

**When required:**
- First time using custom labware
- Custom calibration offsets in labware_dict.toml
- Different robot than previous runs

### Step 6: Dry Run (Recommended)
**Before running with samples:**
1. Load labware with water or colored dye
2. Run protocol
3. Observe:
   - Tips reach liquid correctly
   - Dispense in center of wells
   - No edge hits or crashes
   - Consistent volumes
4. Adjust if needed:
   - Update calibration offsets
   - Adjust heights in CSV
   - Tune flow rates

### Step 7: Production Run
**When dry run successful:**
1. Load actual samples/reagents
2. Verify labware positions match dry run
3. Run protocol
4. Monitor first few transfers
5. Pause if issues observed

## Post-Deployment

### If Protocol Runs Successfully
- Document:
  - Final CSV used
  - Calibration offsets
  - Any manual adjustments
  - Date and operator
- Archive protocol file for reproducibility

### If Protocol Fails During Run
**Common issues:**
- **Tip crashes:** Calibration offset incorrect → Re-run labware position check
- **Inconsistent volumes:** Heights too high/low → Adjust CSV heights
- **Dripping during movement:** Head speed too fast → Reduce to 250-300 mm/min
- **Splashing:** Dispense too high or fast → Lower dest height or flow rate

**Recovery:**
1. Stop protocol
2. Note error details
3. Use `troubleshoot_simulation_error` or `optimize_transfer_parameters` prompts
4. Fix issues
5. Regenerate and re-simulate
6. Re-deploy

## Deployment Options Comparison

| Method | Pros | Cons |
|--------|------|------|
| Clipboard | Quick, no file system access needed | Must paste manually each time |
| Direct copy | Automatic appearance in app | Requires correct path configuration |
| Manual copy | Full control, works offline | More steps, error-prone |

## Success Criteria
- ✓ Protocol appears in Opentrons App
- ✓ Labware position check completed (if required)
- ✓ Dry run successful (if performed)
- ✓ Production run executes without errors

## Next Steps
After successful deployment:
- Run protocol on actual samples
- Monitor and document performance
- Optimize if needed (use `optimize_transfer_parameters` prompt)
- Archive protocol and configuration files
"""

    @mcp.prompt
    def validate_before_run() -> str:
        """
        Pre-flight validation workflow before protocol generation.

        User intent: "Validate my configuration" or "Check for errors before generating"
        """

        return """
## Goal
Perform comprehensive validation checks before protocol generation or simulation

## When to Use This Prompt
- Before generating protocol for the first time
- After making significant configuration changes
- When troubleshooting errors
- As best practice before deployment

## What Gets Validated
- Deck layout (slot conflicts, missing labware)
- CSV format (required columns, data types)
- Labware references (CSV matches settings.toml)
- Volume ranges (within pipette capacity)
- Mode compatibility (multi-channel labware check)

## Workflow

### Step 1: Run Validation
- **Tool:** `validate_configuration()`
- **Action:** Execute all validation checks
- **Result:** Detailed error/warning report

### Step 2: Review Validation Results

**Validation Categories:**

**✓ Deck Layout Checks**
- No duplicate position_rack values (slot conflicts)
- All labware_ids exist in labware catalog
- Tip racks have connection field
- No labware in slot 12 (reserved for trash)

**✓ CSV Format Checks**
- Required columns present
- No both Height and Top columns (for source or dest)
- Labware references valid (match deck layout)
- Well names valid for labware type
- Volumes are numeric

**✓ Compatibility Checks**
- Multi-channel mode only with 96/384-well plates
- Pipettes exist in catalog
- Transfer volumes within pipette range

**✓ Reference Integrity**
- CSV labware references → working_plate entries
- working_plate labware_ids → labware catalog
- Tip rack connections → pipette definitions

### Step 3: Address Errors (If Any)

**Error Priority:**
1. **Critical (Must Fix):** Prevent protocol generation
   - Slot conflicts
   - Missing required columns in CSV
   - Invalid labware references
   - Both Height and Top columns present

2. **Warnings (Should Review):** May cause runtime issues
   - Volume out of recommended range
   - Unusual height values
   - Inconsistent heights for same labware

**For each error, validation provides:**
- Error description
- Location (file, line, field)
- Recommended fix

### Step 4: Fix Issues One by One

**Common Fixes:**

**"Slot conflict: position_rack '4' used by multiple labware"**
- **Fix:** Use `configure_deck_layout` prompt to assign unique slots
- **Tool:** `update_settings(path="settings.working_plate", ...)`

**"Labware not found: 'tube_rack_96_1500ul' not in catalog"**
- **Fix:** Use `add_custom_labware` prompt to add to catalog
- **Or:** Correct labware_id spelling

**"CSV references 'tube_rack_96_1500ul_4' but no labware in slot 4"**
- **Fix:** Add labware to slot 4 via `configure_deck_layout`
- **Or:** Change CSV labware reference to existing slot

**"Both Source Height and Source Top columns present"**
- **Fix:** Delete one set of columns from CSV
- **Keep:** Either all Height columns OR all Top columns (not both)

**"Transfer volume 350µL exceeds pipette range 300µL"**
- **Fix:** Either:
  - Reduce transfer volumes in CSV to ≤300µL
  - Change to larger pipette (P1000 instead of P300)

**"Multi mode incompatible with tube_rack labware"**
- **Fix:** Either:
  - Switch to single_X1 or multi_X1 mode
  - Change to 96/384-well plates

### Step 5: Re-Validate After Fixes
- **Tool:** `validate_configuration()`
- **Action:** Verify fixes worked
- **Repeat:** Until all errors cleared

### Step 6: Proceed with Confidence
**Once validation passes:**
- Generate protocol: `generate_protocol(csv_path="...")`
- Or continue with current workflow

## Validation Best Practices

### When to Validate
- ✓ Before first protocol generation (new project)
- ✓ After editing CSV (especially structural changes)
- ✓ After changing pipette mode
- ✓ After adding/removing deck labware
- ✓ Before deploying to robot (final check)

### What Validation Cannot Catch
- Physical calibration errors (labware offsets)
- Liquid property issues (viscosity, volatility)
- Sample tube/well actual contents
- Robot mechanical problems

**These require:** Physical testing on robot

## Validation Output Example

```
Validation Results:

ERRORS (Must Fix):
  ❌ settings.toml: Slot conflict - position_rack '4' used by 2 labware
  ❌ CSVs/transfers.csv: Row 5 - labware reference 'plate_99' not in deck layout
  ❌ CSVs/transfers.csv: Both Source Height and Source Top columns present

WARNINGS (Review):
  ⚠️  CSVs/transfers.csv: Row 12 - Volume 295µL near pipette max (300µL)
  ⚠️  CSVs/transfers.csv: Source Height varies (2mm vs 5mm) for same labware

Summary: 3 errors, 2 warnings
```

## Success Criteria
- ✓ Validation runs without errors
- ✓ All warnings reviewed and acceptable
- ✓ Configuration ready for protocol generation

## Next Steps
After successful validation:
- Proceed with `regenerate_protocol` or `setup_new_experiment`
- Generate and simulate protocol
- Deploy when ready
"""

    @mcp.prompt
    def troubleshoot_simulation_error() -> str:
        """
        Systematic troubleshooting guide for failed simulations.

        User intent: "My simulation failed, help me fix it" or "Debug protocol errors"
        """

        return """
## Goal
Systematically diagnose and fix protocol simulation errors

## When to Use This Prompt
- Simulation failed with errors
- Protocol generates but simulation crashes
- Unexpected behavior in simulation
- Need systematic debugging approach

## Workflow

### Step 1: Read Simulation Logs
- **Tool:** Read `logs://last-simulation`
- **Action:** Identify error message(s)
- **Look for:**
  - Specific error text
  - Line numbers or transfer numbers
  - Labware or pipette mentions

### Step 2: Identify Error Pattern

**Common Error Patterns:**

**A. "Labware not found" / "Unknown labware"**
- **Cause:** api_id in labware_dict.toml doesn't match Opentrons library
- **Fix:**
  1. Read `config://labware`
  2. Find labware entry with issue
  3. Verify api_id at https://labware.opentrons.com/
  4. Correct api_id in labware_dict.toml
  5. Regenerate protocol

**B. "Slot conflict" / "Labware already at position"**
- **Cause:** Multiple labware assigned to same deck slot
- **Fix:**
  1. Read `status://deck-layout`
  2. Identify duplicate position_rack values
  3. Use `configure_deck_layout` to reassign slots
  4. Ensure each labware has unique slot (1-11)
  5. Regenerate protocol

**C. "Volume out of range" / "Volume exceeds pipette capacity"**
- **Cause:** Transfer volume > pipette maximum volume
- **Fix:**
  1. Read `config://labware` → check pipette volume_range
  2. Review CSV transfer volumes
  3. Either:
     - Reduce volumes in CSV to fit pipette
     - Change to larger pipette (add to labware_dict.toml)
  4. Regenerate protocol

**D. "No tip available" / "Not enough tips"**
- **Cause:** Insufficient tip racks for chosen tip_reuse strategy
- **Fix:**
  1. Calculate tips needed:
     - tip_reuse="never": (CSV rows) × (tips per transfer based on mode)
     - tip_reuse="per_source": (# of unique source labware)
     - tip_reuse="always": 1 tip total
  2. Add more tip racks via `configure_deck_layout`
  3. Or change tip strategy: `update_settings(path="settings.general.tip_reuse", value="per_source")`
  4. Regenerate protocol

**E. "Multi-channel incompatible" / "Invalid labware for multi mode"**
- **Cause:** Multi mode used with non-96/384-well plates
- **Fix:**
  1. Either switch to multi_X1 mode: Use `switch_to_single_channel` prompt
  2. Or change labware to 96/384-well plates: Use `configure_deck_layout`
  3. Regenerate protocol

**F. "Well does not exist" / "Invalid well name"**
- **Cause:** CSV references well that doesn't exist in labware
- **Fix:**
  1. Check labware well count in `config://labware`
  2. Review CSV well names (A1-H12 for 96-well, A1-P24 for 384-well)
  3. Correct well names in CSV
  4. Regenerate protocol

**G. "Module not found" / "Pipette not attached"**
- **Cause:** Referenced pipette doesn't exist in labware_dict.toml
- **Fix:**
  1. Read `config://labware`
  2. Verify pipette definition exists
  3. Check `channels` field matches mode (1 for single, 8 for multi)
  4. Add pipette if missing via `add_labware_definition`
  5. Regenerate protocol

### Step 3: Apply Appropriate Fix

Based on error pattern identified in Step 2:
- Use relevant prompt for guidance (configure_deck_layout, switch_to_multi_channel, etc.)
- Make targeted fixes
- Don't change multiple things at once (harder to diagnose)

### Step 4: Re-Validate Configuration
- **Tool:** `validate_configuration()`
- **Action:** Catch any remaining issues before regenerating
- **Expected:** No errors (all previously found issues fixed)

### Step 5: Regenerate Protocol
- **Tool:** `generate_protocol(csv_path="CSVs/your_file.csv")`
- **Action:** Rebuild protocol with fixes applied
- **Result:** Updated CherryPick_OT2.py

### Step 6: Re-Simulate
- **Tool:** `simulate_protocol()`
- **Action:** Test if fixes resolved the error
- **Check:** Read `logs://last-simulation`

**If simulation now succeeds:**
- Error fixed!
- Proceed to deployment

**If simulation still fails:**
- **Different error:** Start troubleshooting workflow again (Step 1)
- **Same error:** Review fix carefully, may have been incomplete

### Step 7: Document Fix (Recommended)
Record what was wrong and how you fixed it:
- Original error message
- Root cause
- Fix applied
- Helps prevent recurrence

## Advanced Troubleshooting

### Intermittent Errors
**Symptom:** Error occurs sometimes, not always
- **Likely cause:** Race conditions or edge cases in CSV
- **Fix:** Review CSV for inconsistencies, unusual values

### Cryptic Error Messages
**Symptom:** Error message unclear or not matching common patterns
- **Strategy:**
  1. Run `validate_configuration()` - often catches root cause
  2. Review recent changes to config/CSV
  3. Try reverting to last known working state
  4. Change one thing at a time to isolate issue

### Multiple Simultaneous Errors
**Symptom:** Logs show many different errors
- **Strategy:**
  1. Fix errors in order of appearance
  2. Start with configuration errors (deck, labware)
  3. Then CSV errors
  4. Then pipette/volume errors
  5. Re-simulate after each fix

## Error Priority Guide

**Fix in this order for fastest resolution:**
1. Deck layout errors (slots, labware catalog)
2. CSV format errors (columns, references)
3. Compatibility errors (multi mode, volumes)
4. Tip management errors (racks, strategy)
5. Height/parameter errors (values)

## Prevention Best Practices

### Before Generating Protocol
- ✓ Always run `validate_configuration()` first
- ✓ Review `status://deck-layout` visually
- ✓ Verify CSV labware references match deck

### Before Deploying to Robot
- ✓ Successful simulation required
- ✓ Review logs for warnings (not just errors)
- ✓ Dry run with water recommended

## Success Criteria
- ✓ Simulation succeeds with no errors
- ✓ `logs://last-simulation` shows expected behavior
- ✓ Transfer count matches expectations
- ✓ Tip usage as expected

## Next Steps
After successful troubleshooting:
- If satisfied: Use `deploy_to_robot` prompt
- If optimizing: Use `optimize_transfer_parameters` prompt
- Document the fix for future reference
"""
