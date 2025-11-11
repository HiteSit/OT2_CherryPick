# CherryPick OT-2 Protocol Examples

**Common Use Cases and Complete Protocol Examples**

---

## Table of Contents

1. [Use Case 1: Simple Cherry-Picking](#use-case-1-simple-cherry-picking-96-well-to-384-well)
2. [Use Case 2: Multiple Source Plates with Mixing](#use-case-2-multiple-source-plates-with-mixing)
3. [Use Case 3: Viscous Liquid Handling](#use-case-3-viscous-liquid-handling-dmso)
4. [Use Case 4: Multi-Channel Column Transfers](#use-case-4-multi-channel-column-transfers)
5. [Use Case 5: Variable Volume Cherry-Picking](#use-case-5-variable-volume-cherry-picking)

---

## Use Case 1: Simple Cherry-Picking (96-well to 384-well)

**Scenario:** Transfer 50µL from 24 source tubes to specific wells in a 384-well plate.

**settings.toml:**
```toml
[settings.general]
tip_reuse = "per_source"
mode = "single_X1"

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

**CSV:**
```csv
Source Labware,Source Well,Volume (ul),Dest Labware,Dest Well,Source Height,Dest Top
tube_rack_96_1500ul_4,A1,50,384_ppv_55ul_2,A1,2,-5
tube_rack_96_1500ul_4,A2,50,384_ppv_55ul_2,B1,2,-5
tube_rack_96_1500ul_4,A3,50,384_ppv_55ul_2,C1,2,-5
...
```

**Run:**
```bash
./simulate_protocol.sh CSVs/cherry_pick_24.csv
```

---

## Use Case 2: Multiple Source Plates with Mixing

**Scenario:** Transfer samples from 2 tube racks, mix after dispense.

**settings.toml:**
```toml
[[settings.working_plate]]
type = "source"
labware_id = "tube_rack_96_1500ul"
position_rack = "1"

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

**CSV:**
```csv
Source Labware,Source Well,Volume (ul),Dest Labware,Dest Well,Source Height,Dest Top,Mix Volume
tube_rack_96_1500ul_1,A1,30,384_ppv_55ul_2,A1,2,-2,20
tube_rack_96_1500ul_1,A2,30,384_ppv_55ul_2,A2,2,-2,20
tube_rack_96_1500ul_4,A1,30,384_ppv_55ul_2,B1,2,-2,20
tube_rack_96_1500ul_4,A2,30,384_ppv_55ul_2,B2,2,-2,20
```

---

## Use Case 3: Viscous Liquid Handling (DMSO)

**Scenario:** Transfer DMSO stock solutions with slow aspiration and push-out.

**settings.toml:**
```toml
[settings.general]
tip_reuse = "never"
mode = "single_X1"

# Manual configuration for viscous liquids
[settings.liquid_handling.pre_aspirate_contact]
enabled = true
position_offset_percent = 20
aspirate_volume = 0

[settings.liquid_handling.post_aspirate_wick]
enabled = true
radius = 0.8
v_offset_mm = -1.5
speed = 20

[settings.liquid_handling.delays]
post_aspirate = 2.0                 # Wait 2 seconds for liquid to settle

[settings.liquid_handling.push_out]
enabled = true
volume_ul = 5                       # Force out remaining liquid
```

**CSV:**
```csv
Source Labware,Source Well,Volume (ul),Dest Labware,Dest Well,Source Top,Dest Top,Flow Aspirate,Flow Dispense
tube_rack_96_1500ul_4,A1,10,384_ppv_55ul_2,A1,-2,-3,0.3,0.5
tube_rack_96_1500ul_4,A2,10,384_ppv_55ul_2,A2,-2,-3,0.3,0.5
```

**Note:** Slow flow rates (0.3, 0.5) prevent shearing viscous liquids.

---

## Use Case 4: Multi-Channel Column Transfers

**Scenario:** Transfer entire columns from one 96-well plate to another.

**settings.toml:**
```toml
[settings.general]
tip_reuse = "per_source"
mode = "multi"                      # Full 8-channel mode

[[settings.working_plate]]
type = "source"
labware_id = "corning_96_wellplate_360ul_flat"
position_rack = "1"

[[settings.working_plate]]
type = "destination"
labware_id = "corning_96_wellplate_360ul_flat"
position_rack = "2"

[[settings.working_plate]]
type = "tip"
labware_id = "opentrons_96_tiprack_300ul"
connection = "Pipette_8"
position_rack = "5"
```

**CSV:**
```csv
Source Labware,Source Well,Volume (ul),Dest Labware,Dest Well,Source Height,Dest Height
corning_96_wellplate_360ul_flat_1,A1,100,corning_96_wellplate_360ul_flat_2,A1,1,1
corning_96_wellplate_360ul_flat_1,A2,100,corning_96_wellplate_360ul_flat_2,A2,1,1
corning_96_wellplate_360ul_flat_1,A3,100,corning_96_wellplate_360ul_flat_2,A3,1,1
```

**Note:** In `multi` mode, each row transfers 8 wells (A1-H1, A2-H2, etc.).

---

## Use Case 5: Variable Volume Cherry-Picking

**Scenario:** Different volumes for each transfer, custom heights.

**CSV:**
```csv
Source Labware,Source Well,Volume (ul),Dest Labware,Dest Well,Source Height,Dest Top,Air Gap,Tip Action
tube_rack_96_1500ul_4,A1,25,384_ppv_55ul_2,A1,3,-4,10,new
tube_rack_96_1500ul_4,A2,50,384_ppv_55ul_2,B1,5,-4,10,new
tube_rack_96_1500ul_4,A3,75,384_ppv_55ul_2,C1,7,-4,10,new
tube_rack_96_1500ul_4,A4,100,384_ppv_55ul_2,D1,10,-4,10,new
```

**Note:** Source height increases with volume (more liquid = higher position).

---

**[← Back to Main Tutorial](USER_TUTORIAL.md)** | **[See Complete Workflow Example →](APPENDIX.md)**
