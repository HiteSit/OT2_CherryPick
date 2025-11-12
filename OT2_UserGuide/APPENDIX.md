# CherryPick OT-2 Protocol Appendix

**Complete End-to-End Example Workflow**

---

## Complete Example Workflow

Let's walk through creating a protocol from scratch to demonstrate the entire process.

### Scenario

Transfer 30µL from 12 source tubes (in a tube rack at slot 4) to 12 specific wells in a 384-well plate (at slot 2). Aspirate 2mm from bottom of tubes, dispense 2mm below top of wells. Use air gap to prevent dripping.

---

## Step 1: Prepare CSV File

Create `CSVs/my_first_protocol.csv`:

```csv
Source Labware,Source Well,Volume (ul),Dest Labware,Dest Well,Source Height,Dest Top,Air Gap,Tip Action
tube_rack_96_1500ul_4,A1,30,384_ppv_55ul_2,A1,2,-2,10,keep
tube_rack_96_1500ul_4,A2,30,384_ppv_55ul_2,B1,2,-2,10,keep
tube_rack_96_1500ul_4,A3,30,384_ppv_55ul_2,C1,2,-2,10,keep
tube_rack_96_1500ul_4,A4,30,384_ppv_55ul_2,D1,2,-2,10,keep
tube_rack_96_1500ul_4,A5,30,384_ppv_55ul_2,E1,2,-2,10,keep
tube_rack_96_1500ul_4,A6,30,384_ppv_55ul_2,F1,2,-2,10,keep
tube_rack_96_1500ul_4,B1,30,384_ppv_55ul_2,G1,2,-2,10,keep
tube_rack_96_1500ul_4,B2,30,384_ppv_55ul_2,H1,2,-2,10,keep
tube_rack_96_1500ul_4,B3,30,384_ppv_55ul_2,A2,2,-2,10,keep
tube_rack_96_1500ul_4,B4,30,384_ppv_55ul_2,B2,2,-2,10,keep
tube_rack_96_1500ul_4,B5,30,384_ppv_55ul_2,C2,2,-2,10,keep
tube_rack_96_1500ul_4,B6,30,384_ppv_55ul_2,D2,2,-2,10,drop
```

**What each column means:**
- **Source Labware**: `tube_rack_96_1500ul_4` = tube rack at slot 4
- **Source Well**: Position in source tube rack (A1-B6)
- **Volume (ul)**: 30µL for all transfers
- **Dest Labware**: `384_ppv_55ul_2` = 384-well plate at slot 2
- **Dest Well**: Target position in 384-well plate
- **Source Height**: 2mm from bottom of tubes
- **Dest Top**: -2mm (2mm below top of wells)
- **Air Gap**: 10µL air gap to prevent dripping
- **Tip Action**: `keep` for all except last transfer (`drop`)

---

## Step 2: Configure settings.toml

```toml
[settings.general]
tip_reuse = "always"
mode = "multi_X1"
starting_tip_well = "H1"

[settings.general.head_speed]
speed = 400

[settings.liquid_handling.pre_aspirate_contact]
enabled = false
position_offset_percent = 20
aspirate_volume = 0

[settings.liquid_handling.post_aspirate_wick]
enabled = true
radius = 1
v_offset_mm = -1.5
speed = 20

[settings.liquid_handling.delays]
post_aspirate = 0

[settings.liquid_handling.push_out]
enabled = true
volume_ul = 5

[[settings.working_plate]]
type = "source"
labware_id = "tube_rack_96_1500ul"
position_rack = "4"

[[settings.working_plate]]
type = "destination"
labware_id = "384_ppv_55ul"
position_rack = "2"

[[settings.working_plate]]
type = "tip"
labware_id = "opentrons_96_tiprack_300ul"
connection = "Pipette_8"
position_rack = "5"
```

**Configuration explanation:**
- **Mode**: `multi_X1` = Using 8-channel pipette with single tip for cherry-picking
- **Tip reuse**: `always` = Use one tip for entire protocol
- **Starting tip**: `H1` = Use back tip (position 8). Works well for slot 4 (middle row) - either H1 or A1 would work here.
- **Deck layout**: Source at slot 4, destination at slot 2, tips at slot 5

> **💡 Note:** For front row slots (1-3), use H1; for back row slots (7-9), use A1. See USER_TUTORIAL.md for details on deck position constraints.

---

## Step 3: Verify labware_dict.toml

Check that these labware are defined:
- `tube_rack_96_1500ul`
- `384_ppv_55ul`
- `opentrons_96_tiprack_300ul`
- `Pipette_8`

(They should already be present in the default file)

**If any are missing**, add them following the instructions in the main tutorial.

---

## Step 4: Run Simulation

```bash
./simulate_protocol.sh CSVs/my_first_protocol.csv
```

Expected output:
```
=== Using local configuration ===
=== Step 1: Updating protocol with helper ===
Loading labware definitions...
Loading settings...
Processing CSV...
Embedding configuration...

=== Step 2: Running protocol simulation ===
Loading labware: tube_rack_96_1500ul at slot 4
Loading labware: 384_ppv_55ul at slot 2
Loading labware: opentrons_96_tiprack_300ul at slot 5
Configuring Pipette_8 for multi_X1 mode (single tip from 8-channel)
Picking up tip from H1

Transfer 1/12:
  Aspirating 30.0 uL from tube_rack_96_1500ul:A1
  Air gap: 10.0 uL
  Dispensing 30.0 uL into 384_ppv_55ul:A1

Transfer 2/12:
  Aspirating 30.0 uL from tube_rack_96_1500ul:A2
  Air gap: 10.0 uL
  Dispensing 30.0 uL into 384_ppv_55ul:B1

...

Transfer 12/12:
  Aspirating 30.0 uL from tube_rack_96_1500ul:B6
  Air gap: 10.0 uL
  Dispensing 30.0 uL into 384_ppv_55ul:D2
  Dropping tip

=== Simulation successful! ===
Protocol copied to clipboard ✓
```

**What to check:**
- ✅ All 12 transfers listed
- ✅ Correct source and destination wells
- ✅ Volumes match your CSV (30µL)
- ✅ Air gap included (10µL)
- ✅ Tip picked up once, dropped at end
- ✅ No error messages

---

## Step 5: Transfer to OT-2

**Option A: Automatic transfer**
```bash
./simulate_protocol.sh CSVs/my_first_protocol.csv --send-to-opentrons
```

**Option B: Manual paste**
- Protocol is already in your clipboard
- Open Opentrons App
- Paste into protocol editor
- Save

---

## Step 6: Run on Robot

1. **Open Opentrons App**
   - Launch the application on Windows
   - Connect to your OT-2 robot

2. **Load the protocol**
   - Navigate to Protocols tab
   - Select your protocol
   - Verify deck layout preview

3. **Perform deck calibration**
   - Follow Opentrons App prompts
   - Calibrate pipette if needed
   - Run Labware Position Check for each labware

4. **Load physical labware**
   - Place tube rack in slot 4
   - Place 384-well plate in slot 2
   - Place tip rack in slot 5
   - Verify labware is firmly seated

5. **Start run**
   - Click "Run Protocol"
   - Monitor the first few transfers
   - Watch for any positioning issues

6. **Monitor execution**
   - Observe pipette movements
   - Check liquid is being transferred correctly
   - Watch for any errors or warnings

---

## Troubleshooting This Example

### If simulation fails:

**"File not found: CSVs/my_first_protocol.csv"**
- Make sure you created the CSV file in the correct directory
- Check spelling and capitalization

**"Labware not defined"**
- Verify all labware exist in `labware_dict.toml`
- Check `labware_id` spelling matches exactly

**"Slot conflict"**
- Ensure slots 2, 4, and 5 aren't used by other labware in `settings.toml`

### If robot behavior is wrong:

**Pipette misses wells**
- Run Labware Position Check in Opentrons App
- Add calibration offsets to `labware_dict.toml`

**Wrong volume transferred**
- Check CSV values
- Verify pipette is calibrated correctly

**Tip crashes**
- Reduce `Source Height` or make `Dest Top` more negative
- Check labware is seated properly

---

## Success! 🎉

**Congratulations!** You've created and run your first cherry-pick protocol!

### What you've learned:

✅ How to create a CSV file with transfer instructions
✅ How to configure deck layout in settings.toml
✅ How to run simulation and interpret output
✅ How to transfer protocol to the OT-2 machine
✅ How to verify and run the protocol on hardware

### Next steps:

1. **Try modifying the example**
   - Change volumes
   - Add more transfers
   - Experiment with different settings

2. **Explore other use cases**
   - See [EXAMPLES.md](EXAMPLES.md) for more complex scenarios

3. **Read advanced topics**
   - Labware calibration offsets
   - Liquid handling parameters for different liquid types
   - Multi-channel mode strategies

---

**[← Back to Main Tutorial](USER_TUTORIAL.md)** | **[See More Examples →](EXAMPLES.md)**
