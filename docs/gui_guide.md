# GUI Guide

The OT2 CherryPick web interface provides a 4-step wizard for configuring, validating, and executing liquid handling protocols.

**Access:** Launch with Docker (`docker compose up -d`) and open [http://localhost](http://localhost).

## Step 1: Deck Setup

<!-- Screenshot: The Deck Setup tab showing protocol name field, mode selector dropdown, custom labware path input, and the interactive DeckGrid with slots 1-11 plus Trash -->
![Deck Setup](imgs/deck_setup.png)

Configure the physical layout of your OT-2 deck.

**Controls:**
- **Protocol name** -- Identifier embedded in the generated protocol
- **Mode selector** -- Choose pipette mode: `single_X1`, `multi_X1`, `multi`, or `dual`
- **DeckGrid** -- Visual representation of the 11-slot OT-2 deck plus trash

**Adding labware to slots:**
1. Click an empty slot on the DeckGrid
2. Select labware type (source, destination, or tip rack) from the LabwareEditor panel
3. Choose the specific labware from the catalog
4. For tip racks, set the `connection` field to link it to the correct pipette

**OT-2 Deck Layout:**
```
+-------+-------+-------+
|  10   |  11   | Trash |
+-------+-------+-------+
|   7   |   8   |   9   |
+-------+-------+-------+
|   4   |   5   |   6   |
+-------+-------+-------+
|   1   |   2   |   3   |
+-------+-------+-------+
```

**Tips:**
- Slot 12 is permanently assigned to the trash
- Each slot can hold exactly one piece of labware
- Tip rack `connection` must match a pipette name from `labware_dict.toml`
- Heater-shaker modules can be assigned to slots that support them

## Step 2: Configuration

<!-- Screenshot: The Configuration tab showing basic settings panel (tip reuse, starting tip, head speed) and the expanded Advanced Liquid Handling accordion with pre-aspirate, wicking, delay, push-out, and mixing controls -->
![Configuration](imgs/configuration.png)

Set protocol behavior and liquid handling parameters.

**Basic settings:**
- **Tip reuse** -- `always` (one tip), `never` (new tip each transfer), or `per_source`
- **Starting tip well** -- Which tip position to begin from (e.g., `A1`)
- **Head speed** -- Movement speed in mm/min (100-600, default 400)

**Advanced liquid handling (expandable accordion):**
- Pre-aspirate contact and pre-wetting
- Post-aspirate wicking
- Post-aspirate delay
- Push-out volume
- Mixing settings (location, repetitions, source remixing)

**Help panel:** A contextual help sidebar explains each parameter with scientific rationale. See the [Liquid Handling Guide](liquid_handling_guide.md) for full details.

**Tips:**
- Use the **preset buttons** (Standard, Viscous) to apply recommended parameter sets for common liquid types
- For most aqueous transfers, the Standard preset works well
- For DMSO, glycerol, or oils, switch to the Viscous preset

## Step 3: Transfer Map

<!-- Screenshot: The Transfer Map tab showing the spreadsheet-style CSV editor with columns for Source Labware, Source Well, Volume, Dest Labware, Dest Well, and height columns. Show the live validation panel on the right side highlighting any errors -->
![Transfer Map](imgs/transfer_map.png)

Define individual liquid transfers in a spreadsheet-style editor.

**Required columns:**
| Column | Example |
|--------|---------|
| Source Labware | `tube_rack_96_1500ul_4` |
| Source Well | `A1` |
| Volume (ul) | `50` |
| Dest Labware | `384_ppv_55ul_2` |
| Dest Well | `B3` |

**Labware references** use the format `labware_id_slot` (e.g., `tube_rack_96_1500ul_4` for labware in slot 4).

**Positioning columns** (choose one per source/dest):
- `Source Bottom` / `Dest Bottom` -- Distance from well bottom (mm)
- `Source Top` / `Dest Top` -- Distance from well top (mm, negative = below rim)

**Optional columns:** Mix Volume, Mix Height, Flow Aspirate, Flow Dispense, Air Gap, Air Gap Rate, Tip Action

**Live validation** checks for:
- Invalid labware references (labware not on deck)
- Invalid well names for the selected labware
- Volume exceeding pipette capacity
- Conflicting height columns (both Height and Top set)

**Tips:**
- You can paste CSV data directly from a spreadsheet application
- Use `Tip Action` column (`new`, `keep`, `drop`) to override the global tip reuse strategy for specific rows
- In `multi` mode, specifying well `A1` transfers the entire column (A1-H1)

## Step 4: Review & Execute

<!-- Screenshot: The Review & Execute tab showing the configuration summary card, preflight checklist with green checkmarks, execution toggle checkboxes (Simulate, Send to Opentrons, Copy to Clipboard), the Shell Runner Windows Folders section with path inputs, and the Run Workflow button -->
![Review & Execute](imgs/review_execute.png)

Review configuration and run the protocol pipeline.

**Configuration summary:** Read-only overview of all settings, deck layout, and transfer count.

**Preflight checklist:** Automated validation that checks:
- All labware references in CSV match deck slots
- Volumes are within pipette range
- No conflicting height columns
- Tip racks are connected to pipettes
- Required settings are populated

**Execution toggles:**
- **Simulate** -- Run `opentrons_simulate` to validate the protocol
- **Send to Opentrons** -- Deploy protocol to the Opentrons App directory
- **Copy to Clipboard** -- Copy the generated protocol to clipboard

**Opentrons App Directory** (required for simulation and deployment):
- **Opentrons App directory** -- Single field pointing to the root Opentrons data directory (e.g., `C:\Users\you\AppData\Roaming\Opentrons`). The labware path (`/labware`) and protocol deployment path (`/protocols`) are auto-derived from this root.
- Click **Save as default** to persist the path to `shell_settings.json`

> **Migration note:** Older configurations with separate `labware_path_win` and `target_protocol_src_win` fields are automatically migrated to the single `opentrons_dir_win` field on first load.

**Running the workflow:**
1. Ensure the preflight checklist passes (all green)
2. Enable desired execution toggles
3. Click **Run Workflow**
4. Monitor progress in the real-time output display

**Tips:**
- Always simulate before deploying to the robot
- Windows paths are automatically converted to WSL format
- Use the **Browse** buttons for folder picker dialogs instead of typing paths manually
- The shell settings are shared between the GUI and CLI workflows
