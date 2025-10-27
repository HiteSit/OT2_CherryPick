"""
CSV and labware management prompts for MCP server.

Provides workflow guidance for creating CSV transfer maps, adding custom labware,
and configuring deck layouts.
"""

from fastmcp import FastMCP

__all__ = ["register_csv_labware_prompts"]


def register_csv_labware_prompts(mcp: FastMCP) -> None:
    """Register CSV and labware management prompts with the FastMCP app."""

    @mcp.prompt
    def create_csv_transfer_map(
        num_transfers: int = 24, source_labware_type: str = "tubes", dest_labware_type: str = "plate"
    ) -> str:
        """
        Guide user through creating a CSV transfer map file.

        Args:
            num_transfers: Approximate number of liquid transfers to perform
            source_labware_type: Type of source labware ("tubes", "plate", "reservoir")
            dest_labware_type: Type of destination labware ("tubes", "plate")

        User intent: "Create a new CSV file" or "Help me define my liquid transfers"
        """

        height_recommendations = {
            "tubes": {
                "source": "2-5mm from bottom (Source Height = 2 to 5)",
                "dest": "5mm from bottom (Dest Height = 5)",
            },
            "plate": {
                "source": "1-2mm from bottom (Source Height = 1 to 2)",
                "dest": "1mm from bottom (Dest Height = 1)",
            },
            "reservoir": {
                "source": "2mm from bottom (Source Height = 2)",
                "dest": "N/A (reservoirs typically not destinations)",
            },
        }

        source_height_rec = height_recommendations.get(source_labware_type, {}).get("source", "2mm from bottom")
        dest_height_rec = height_recommendations.get(dest_labware_type, {}).get("dest", "1mm from bottom")

        return f"""
## Goal
Create a CSV transfer map defining {num_transfers} liquid transfers from {source_labware_type} to {dest_labware_type}

## Understanding CSV Structure

The CSV file defines which liquid transfers the robot performs. Each row = one transfer operation.

**Required Columns:**
1. `Source Labware` - Labware ID + slot number (e.g., "tube_rack_96_1500ul_4")
2. `Source Well` - Well position (e.g., "A1", "H12")
3. `Volume (ul)` - Transfer volume in microliters (e.g., "50", "100.5")
4. `Dest Labware` - Destination labware ID + slot (e.g., "384_ppv_55ul_2")
5. `Dest Well` - Destination position (e.g., "B1", "P24")

**Height Columns (Choose ONE per source/dest):**
- For SOURCE: Use EITHER `Source Height` OR `Source Top` (never both)
  - `Source Height` = Distance from well bottom in mm
  - `Source Top` = Distance from well top in mm (negative goes down)
- For DESTINATION: Use EITHER `Dest Height` OR `Dest Top` (never both)

**Optional Advanced Columns:**
- `Mix Volume` - Volume to mix after dispense (µL)
- `Mix Height` - Mixing height from bottom (mm)
- `Flow Aspirate` - Aspiration speed multiplier (default 1.0)
- `Flow Dispense` - Dispense speed multiplier (default 1.0)
- `Air Gap` - Air gap volume to prevent dripping (µL)
- `Tip Action` - Override tip management ("new", "keep", "drop")

## Prerequisites
- Deck layout configured (labware positions assigned)
- Know labware IDs from `status://deck-layout` or `config://labware`

## Workflow

### Step 1: Discover Available Labware
- **Tool:** Read `status://deck-layout`
- **Action:** Identify labware IDs and their assigned slots
- **Example output:**
  ```
  Deck Layout:
  - Slot 4: tube_rack_96_1500ul [source]
  - Slot 2: 384_ppv_55ul [destination]
  - Slot 5: opentrons_96_tiprack_300ul [tip]
  ```

**Note the pattern:** Labware ID + underscore + slot number = Labware reference
- Source in slot 4 → `tube_rack_96_1500ul_4`
- Destination in slot 2 → `384_ppv_55ul_2`

### Step 2: Generate CSV Template
- **Tool:** `generate_csv_template(source_labware="SOURCE_ID_SLOT", dest_labware="DEST_ID_SLOT", num_transfers={num_transfers})`
- **Action:** Create skeleton CSV with proper columns
- **Result:** CSV file created in CSVs/ directory

**Example:**
```
generate_csv_template(
    source_labware="tube_rack_96_1500ul_4",
    dest_labware="384_ppv_55ul_2",
    num_transfers={num_transfers}
)
```

### Step 3: Understand Height Recommendations

For {source_labware_type} → {dest_labware_type}:

**Source Heights:**
- Recommended: {source_height_rec}
- Rationale: Aspirate above well bottom to avoid debris, but deep enough for consistent volume

**Destination Heights:**
- Recommended: {dest_height_rec}
- Rationale: Dispense near bottom for consistent deposition, avoiding splashing

**CRITICAL: Height Column Rules**
- Use EITHER "Source Height" OR "Source Top" - NEVER BOTH
- Use EITHER "Dest Height" OR "Dest Top" - NEVER BOTH
- Mixing both types causes validation errors

**When to use each:**
- `Height` (from bottom): Best for most applications, consistent across labware
- `Top` (from top): Useful when liquid level varies or volume is unknown

### Step 4: Fill in Transfer Details

Edit the generated CSV file with your specific transfers:

**Example CSV content:**
```csv
Source Labware,Source Well,Volume (ul),Dest Labware,Dest Well,Source Height,Dest Height
tube_rack_96_1500ul_4,A1,50,384_ppv_55ul_2,A1,3,1
tube_rack_96_1500ul_4,A2,50,384_ppv_55ul_2,A2,3,1
tube_rack_96_1500ul_4,A3,50,384_ppv_55ul_2,A3,3,1
```

**Tips for editing:**
- Use spreadsheet software (Excel, Google Sheets) for easier editing
- Keep column order consistent
- Use consistent height values for same labware type
- Save as `.csv` format (not `.xlsx`)

### Step 5: Validate CSV Format
- **Tool:** `validate_configuration()`
- **Action:** Check for common CSV errors before generation
- **Common errors caught:**
  - Both Height and Top columns present
  - Missing required columns
  - Invalid labware references
  - Volumes out of pipette range

### Step 6: Upload/Save CSV
**If CSV created externally:**
- **Tool:** `upload_csv_content(csv_path="CSVs/my_transfers.csv", content="[CSV text]")`
- **Action:** Save CSV content to project directory

**If using generated template:**
- Template already saved, just edit it directly

### Step 7: Verify via Resource Query
- **Tool:** Read `files://csvs`
- **Action:** Confirm your CSV file appears in the list
- **Expected:** See your CSV filename

## Common Issues & Solutions

### "Both Source Height and Source Top provided"
- **Cause:** CSV has both height column types
- **Fix:** Delete one set of columns (either Height or Top, but not both)

### "Labware instance not found"
- **Cause:** CSV references labware ID + slot that isn't in settings.toml
- **Fix:** Either:
  - Correct the labware reference in CSV to match `status://deck-layout`
  - Add missing labware to deck via `configure_deck_layout` prompt

### "Volume out of pipette range"
- **Cause:** Transfer volume exceeds pipette capacity
- **Fix:** Check `config://labware` for pipette volume_range, adjust CSV volumes

### CSV not appearing in `files://csvs`
- **Cause:** File not saved in correct directory or wrong format
- **Fix:** Ensure file saved in `CSVs/` directory with `.csv` extension

## CSV Best Practices

1. **Consistent Heights:** Use same height values for all transfers from same labware type
2. **Logical Well Order:** Organize transfers in column or row order for efficiency
3. **Volume Precision:** Match transfer volumes to pipette resolution (e.g., P300: 0.1µL precision)
4. **Test with Subset:** Start with 5-10 transfers, validate, then expand to full set

## Example: Complete CSV for {source_labware_type} → {dest_labware_type}

```csv
Source Labware,Source Well,Volume (ul),Dest Labware,Dest Well,Source Height,Dest Height
SOURCE_ID_4,A1,50,DEST_ID_2,A1,{source_height_rec.split()[0]},{dest_height_rec.split()[0]}
SOURCE_ID_4,A2,50,DEST_ID_2,A2,{source_height_rec.split()[0]},{dest_height_rec.split()[0]}
SOURCE_ID_4,A3,50,DEST_ID_2,A3,{source_height_rec.split()[0]},{dest_height_rec.split()[0]}
```
(Replace SOURCE_ID_4 and DEST_ID_2 with actual labware references from your deck layout)

## Success Criteria
- ✓ CSV file visible in `files://csvs`
- ✓ `validate_configuration()` passes with no CSV format errors
- ✓ All labware references match `status://deck-layout`
- ✓ Transfer count matches your experimental design

## Next Steps
- Use `regenerate_protocol` prompt to generate protocol from CSV
- Or if setting up from scratch: Use `setup_new_experiment` prompt
"""

    @mcp.prompt
    def add_custom_labware(labware_id: str = "custom_labware", api_id: str = "") -> str:
        """
        Guide user through adding custom labware to the catalog.

        Args:
            labware_id: Custom identifier for the labware (e.g., "my_custom_plate")
            api_id: Opentrons API labware ID (e.g., "corning_96_wellplate_360ul_flat")

        User intent: "Add new labware" or "I have custom labware not in the catalog"
        """

        return f"""
## Goal
Add custom labware "{labware_id}" to the labware catalog

## Understanding Labware Definitions

Each labware in the catalog needs:
1. **labware_id** - Your custom name (used in deck layout and CSV)
2. **api_id** - Opentrons library ID (from Opentrons labware library or custom definition)
3. **category** - Type: "plate", "tuberack", "reservoir", "tiprack"
4. **well_count** - Number of wells
5. **well_volume** - Maximum volume per well (µL)
6. **Calibration offsets** - X/Y/Z adjustments for physical positioning

## Prerequisites
- Know the Opentrons API ID for your labware
  - Find at: https://labware.opentrons.com/
  - Or use custom labware JSON file
- Have calibration offset values (if available)

## Workflow

### Step 1: Check If Labware Already Exists
- **Tool:** Read `config://labware`
- **Action:** Search for labware_id "{labware_id}" in the catalog
- **Decision:**
  - IF found: STOP and inform user "Labware already exists. Use different labware_id or modify existing entry"
  - ELSE: Proceed to Step 2

### Step 2: Gather Labware Specifications

You need the following information:

**Required Fields:**
- `labware_id`: "{labware_id}" (your custom name)
- `api_id`: "{api_id if api_id else '[Find from Opentrons library]'}"
- `category`: Choose from: "plate", "tuberack", "reservoir", "tiprack"
- `well_count`: Number of wells (e.g., 96, 384, 24)
- `well_volume`: Maximum volume per well in µL (e.g., 200, 1500)

**Optional Calibration Offsets:**
- `offset_x`: X-axis adjustment in mm (negative = left, positive = right)
- `offset_y`: Y-axis adjustment in mm (negative = front, positive = back)
- `offset_z`: Z-axis adjustment in mm (negative = down, positive = up)

**Offset Guidelines:**
- Default to 0 if unknown (can calibrate later on robot)
- Typical range: -2.0 to +2.0 mm
- Measure via Opentrons App "Labware Position Check"

### Step 3: Find Opentrons API ID

**Option A: Standard Opentrons Labware**
1. Visit https://labware.opentrons.com/
2. Search for your labware by manufacturer and model
3. Copy the API name (e.g., "corning_96_wellplate_360ul_flat")

**Option B: Custom Labware Definition**
1. Create custom labware JSON using Opentrons Labware Creator: https://labware.opentrons.com/create/
2. Place JSON file in $LABWARE_PATH directory
3. Use the "loadName" field from JSON as api_id

### Step 4: Add Labware to Catalog
- **Tool:** `add_labware_definition(
    labware_id="{labware_id}",
    api_id="YOUR_API_ID",
    category="plate|tuberack|reservoir|tiprack",
    well_count=96,
    well_volume=200,
    offset_x=0.0,
    offset_y=0.0,
    offset_z=0.0
)`
- **Action:** Append labware entry to labware_dict.toml
- **Result:** New `[[labware]]` entry in catalog

**Example:**
```
add_labware_definition(
    labware_id="{labware_id}",
    api_id="corning_96_wellplate_360ul_flat",
    category="plate",
    well_count=96,
    well_volume=360,
    offset_x=-0.5,
    offset_y=0.8,
    offset_z=-0.3
)
```

### Step 5: Verify Addition
- **Tool:** Read `config://labware`
- **Action:** Confirm new labware entry appears in catalog
- **Expected:** See `[[labware]]` section with labware_id="{labware_id}"

### Step 6: Add to Deck Layout (If Immediate Use)
**If you want to use this labware now:**
- Use `configure_deck_layout` prompt to add labware to a deck slot
- This updates settings.toml working_plate array

## Calibration Offset Details

Offsets fine-tune pipette positioning relative to labware:

**X-axis (Left/Right):**
- Negative value → Pipette moves LEFT
- Positive value → Pipette moves RIGHT
- Example: offset_x=-0.5 means "move 0.5mm left of default position"

**Y-axis (Front/Back):**
- Negative value → Pipette moves toward FRONT
- Positive value → Pipette moves toward BACK
- Example: offset_y=0.8 means "move 0.8mm toward back"

**Z-axis (Up/Down):**
- Negative value → Pipette moves DOWN
- Positive value → Pipette moves UP
- Example: offset_z=-0.3 means "move 0.3mm lower"

**When to Adjust:**
- Pipette tips hit well edges → Adjust X/Y
- Pipette too deep/shallow → Adjust Z
- Inconsistent aspiration → Check Z offset

**How to Measure:**
1. Run "Labware Position Check" in Opentrons App
2. Manually jog pipette to correct position
3. Note the offset values displayed
4. Add those values to labware_dict.toml

## Common Issues & Solutions

### "Labware not found" during protocol run
- **Cause:** api_id doesn't match Opentrons library
- **Fix:** Verify api_id at https://labware.opentrons.com/ or check custom labware JSON

### "Invalid category"
- **Cause:** Category not one of: "plate", "tuberack", "reservoir", "tiprack"
- **Fix:** Use exact category names (lowercase)

### Pipette crashes into labware during run
- **Cause:** Incorrect calibration offsets
- **Fix:**
  - Run "Labware Position Check" in Opentrons App
  - Update offset values based on measurements
  - Regenerate protocol

### Calibration offsets not applied
- **Cause:** Protocol generated before offsets were added
- **Fix:** Regenerate protocol with `generate_protocol()` to embed new offsets

## Success Criteria
- ✓ Labware appears in `config://labware` catalog
- ✓ All required fields present (labware_id, api_id, category, well_count, well_volume)
- ✓ Can be referenced in `configure_deck_layout` prompt
- ✓ Protocol simulates successfully when using this labware

## Next Steps
- Use `configure_deck_layout` prompt to add labware to a deck slot
- Create CSV referencing this labware
- Generate and simulate protocol
- Perform physical calibration on OT-2 before first run
"""

    @mcp.prompt
    def configure_deck_layout(operation: str = "add") -> str:
        """
        Guide user through arranging labware on the OT-2 deck.

        Args:
            operation: Either "add" (add labware to deck), "remove" (remove labware), or "view" (just view current layout)

        User intent: "Configure deck positions" or "Arrange my labware on the deck"
        """

        operation_instructions = {
            "add": """
### Operation: Add Labware to Deck

You'll add a labware item to a specific deck slot.

**Steps:**
1. Choose labware from catalog (`config://labware`)
2. Choose available deck slot (1-11, NOT 12 - reserved for trash)
3. Specify labware type (source, destination, or tip)
4. Update settings.toml working_plate array
""",
            "remove": """
### Operation: Remove Labware from Deck

You'll remove a labware item from its current deck slot.

**Steps:**
1. View current layout (`status://deck-layout`)
2. Identify labware to remove by slot number
3. Update settings.toml to remove working_plate entry
""",
            "view": """
### Operation: View Current Deck Layout

You'll inspect the current deck configuration.

**Steps:**
1. Read `status://deck-layout` for visual summary
2. Read `config://settings` for full working_plate details
3. Verify no slot conflicts or missing labware
""",
        }

        return f"""
## Goal
{operation_instructions[operation].strip().split('\\n')[0].replace('### Operation: ', '')}

## Understanding OT-2 Deck Layout

The OT-2 deck has 12 positions arranged as:

```
┌─────┬─────┬─────┬─────┐
│ 10  │ 11  │ Trash (12) │
├─────┼─────┼─────┤      │
│  7  │  8  │  9  │      │
├─────┼─────┼─────┼──────┘
│  4  │  5  │  6  │
├─────┼─────┼─────┤
│  1  │  2  │  3  │
└─────┴─────┴─────┘
```

**Slot 12 is RESERVED for trash** - do not use for labware

**Best Practices:**
- Source labware → Left side (slots 1, 4, 7, 10)
- Destination → Center/Right (slots 2, 5, 8, 11)
- Tips → Right side (slots 3, 6, 9)
- Heavy items → Lower slots (1-3) for stability
- Frequently accessed → Front slots (1-3) for easy access

## Prerequisites
- Labware defined in `config://labware` catalog
- No conflicting slot assignments

{operation_instructions[operation]}

## Workflow

### Step 1: View Current Deck Layout
- **Tool:** Read `status://deck-layout`
- **Action:** See what's currently on the deck
- **Example output:**
  ```
  Deck Layout:
  - Slot 4: tube_rack_96_1500ul [source]
  - Slot 2: 384_ppv_55ul [destination]
  - Slot 5: opentrons_96_tiprack_300ul [tip]
  ```

### Step 2: Identify Available Slots
**Occupied slots:** (from status://deck-layout)
**Available slots:** [Calculate: 1-11 minus occupied]
**Reserved:** Slot 12 (trash)

""" + ("""
### Step 3: Choose Labware to Add
- **Tool:** Read `config://labware`
- **Action:** Select labware from catalog by labware_id
- **Required info:**
  - labware_id (e.g., "384_ppv_55ul")
  - type: "source", "destination", or "tip"
  - position_rack: Available slot number (1-11)

**For tip racks only:**
- `connection`: Which pipette uses these tips (e.g., "Pipette_1", "Pipette_8")

### Step 4: Add Labware to Deck
- **Tool:** `update_settings(
    path="settings.working_plate",
    value=[...existing entries..., new entry]
)`
- **Action:** Append new working_plate entry

**Example for adding destination plate to slot 2:**
```python
update_settings(
    path="settings.working_plate",
    value=[
        # ...existing entries...
        {
            "type": "destination",
            "labware_id": "384_ppv_55ul",
            "position_rack": "2"
        }
    ]
)
```

**Example for adding tip rack to slot 5:**
```python
update_settings(
    path="settings.working_plate",
    value=[
        # ...existing entries...
        {
            "type": "tip",
            "labware_id": "opentrons_96_tiprack_300ul",
            "connection": "Pipette_8",  # For 8-channel pipette
            "position_rack": "5"
        }
    ]
)
```

### Step 5: Verify No Slot Conflicts
- **Tool:** Read `status://deck-layout` again
- **Action:** Confirm new labware appears
- **Check:** All position_rack values are unique (no duplicates)

""" if operation == "add" else """
### Step 3: Identify Labware to Remove
From `status://deck-layout`, note:
- Slot number of labware to remove
- Labware ID

### Step 4: Remove from working_plate Array
- **Tool:** `update_settings(path="settings.working_plate", value=[...remaining entries...])`
- **Action:** Remove the entry with matching position_rack
- **Important:** Preserve all other entries

### Step 5: Verify Removal
- **Tool:** Read `status://deck-layout`
- **Action:** Confirm labware no longer appears
- **Expected:** Slot now available for reuse

""" if operation == "remove" else """
### Step 2: Review Detailed Configuration
- **Tool:** Read `config://settings`
- **Action:** Examine full working_plate array
- **Look for:**
  - Duplicate position_rack values (slot conflicts)
  - Missing type or labware_id fields
  - Tip racks without connection field
  - Labware_ids not in labware catalog

### Step 3: Validate Configuration
- **Tool:** `validate_configuration()`
- **Action:** Check for deck layout errors
- **Common issues detected:**
  - Slot conflicts
  - Labware not found in catalog
  - Missing required fields

""" if operation == "view" else "") + """
## Common Issues & Solutions

### "Slot conflict: position_rack already in use"
- **Cause:** Two labware assigned to same slot
- **Fix:** Choose different slot or remove conflicting entry

### "Labware not found in catalog"
- **Cause:** labware_id in working_plate doesn't exist in labware_dict.toml
- **Fix:** Either:
  - Correct labware_id to match catalog
  - Add labware via `add_custom_labware` prompt

### "Tip rack missing connection field"
- **Cause:** Tip rack entry doesn't specify which pipette uses it
- **Fix:** Add `"connection": "Pipette_1"` or `"Pipette_8"` to entry

### "Position_rack is 12"
- **Cause:** Trying to use slot 12 (reserved for trash)
- **Fix:** Choose slot 1-11 instead

### Working_plate array syntax error
- **Cause:** Malformed TOML when editing manually
- **Fix:** Use `update_settings` tool instead of manual editing

## Deck Layout Examples

### Basic Setup (Single-Channel)
```
Slot 4: tube_rack_96_1500ul [source]
Slot 2: 96_wellplate_200ul [destination]
Slot 5: opentrons_96_tiprack_300ul [tip, Pipette_1]
```

### Multi-Source Setup
```
Slot 1: source_plate_A [source]
Slot 4: source_plate_B [source]
Slot 7: source_plate_C [source]
Slot 2: destination_plate [destination]
Slot 3: tiprack_1 [tip, Pipette_1]
Slot 6: tiprack_2 [tip, Pipette_1]
```

### Multi-Channel Setup
```
Slot 4: 96_wellplate_source [source]
Slot 2: 384_wellplate_dest [destination]
Slot 5: tiprack_multichannel [tip, Pipette_8]
```

## Success Criteria
- ✓ All labware visible in `status://deck-layout`
- ✓ No duplicate position_rack values
- ✓ All labware_ids exist in catalog
- ✓ Tip racks have connection field
- ✓ `validate_configuration()` passes

## Next Steps
After configuring deck:
- Create CSV transfer map via `create_csv_transfer_map` prompt
- Generate protocol via `setup_new_experiment` or `regenerate_protocol`
- Simulate to verify deck configuration
"""
