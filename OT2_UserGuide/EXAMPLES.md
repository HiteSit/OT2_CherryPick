# CherryPick OT-2 Protocol Examples

**Common Use Cases and Complete Protocol Examples**

---

## Table of Contents

1. [Use Case 1: Simple Cherry-Picking](#use-case-1-simple-cherry-picking-96-well-to-384-well)
2. [Use Case 2: Multiple Source Plates with Mixing](#use-case-2-multiple-source-plates-with-mixing)
3. [Use Case 3: Viscous Liquid Handling](#use-case-3-viscous-liquid-handling-dmso)
4. [Use Case 4: Multi-Channel Column Transfers](#use-case-4-multi-channel-column-transfers)
5. [Use Case 5: Variable Volume Cherry-Picking](#use-case-5-variable-volume-cherry-picking)
6. [Use Case 6: Cell Suspension / Bead Resuspension](#use-case-6-cell-suspension--bead-resuspension)
7. [Use Case 7: Large Volume Transfers (Automatic Splitting)](#use-case-7-large-volume-transfers-automatic-splitting)

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

## Use Case 6: Cell Suspension / Bead Resuspension

**Scenario:** Transfer cell suspensions that settle quickly. Mix source wells before aspirating to ensure homogeneous samples.

**settings.toml:**
```toml
[settings.general]
tip_reuse = "never"
mode = "single_X1"

[settings.liquid_handling.mixing]
location = "source"              # Mix BEFORE aspirating (not after dispense)
repetitions = 5                  # Thorough mixing for settled suspensions
source_remixing = "once"         # Mix each source well only once (faster)

[settings.liquid_handling.pre_aspirate_contact]
enabled = true
position_offset_percent = 20
aspirate_volume = 0

[settings.liquid_handling.post_aspirate_wick]
enabled = true
radius = 0.8
v_offset_mm = -1.5
speed = 20

[[settings.working_plate]]
type = "source"
labware_id = "tube_rack_96_1500ul"
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
Source Labware,Source Well,Volume (ul),Dest Labware,Dest Well,Source Height,Dest Top,Mix Volume,Mix Height
tube_rack_96_1500ul_1,A1,100,corning_96_wellplate_360ul_flat_2,A1,5,-2,150,3
tube_rack_96_1500ul_1,A1,100,corning_96_wellplate_360ul_flat_2,A2,5,-2,150,3
tube_rack_96_1500ul_1,A2,100,corning_96_wellplate_360ul_flat_2,A3,5,-2,150,3
tube_rack_96_1500ul_1,A2,100,corning_96_wellplate_360ul_flat_2,A4,5,-2,150,3
```

**What happens:**
1. Well A1 is mixed ONCE before first transfer (150µL, 5 times, at 3mm from bottom)
2. First transfer: aspirate from A1 → dispense to dest A1
3. Second transfer: aspirate from A1 again (NO remixing, source_remixing="once") → dispense to dest A2
4. Well A2 is mixed ONCE before its first transfer
5. Subsequent transfers from A2 proceed without remixing

**Key setting:** `location = "source"` moves mixing from destination (default) to source wells.

---

## Use Case 7: Large Volume Transfers (Automatic Splitting)

**Scenario:** Transfer 1500µL using a pipette with 1000µL maximum capacity. The system automatically splits into multiple sub-transfers.

**settings.toml:**
```toml
[settings.general]
tip_reuse = "always"
mode = "single_X1"

[[settings.working_plate]]
type = "source"
labware_id = "tube_rack_96_2000ul"
position_rack = "1"

[[settings.working_plate]]
type = "destination"
labware_id = "tube_rack_96_2000ul"
position_rack = "4"

[[settings.working_plate]]
type = "tip"
labware_id = "tip_rack_geb_1000ul"
connection = "Pipette_1"
position_rack = "5"
```

**CSV:**
```csv
Source Labware,Source Well,Volume (ul),Dest Labware,Dest Well,Source Height,Dest Height
tube_rack_96_2000ul_1,A1,1500,tube_rack_96_2000ul_4,A1,5,2
tube_rack_96_2000ul_1,A2,1800,tube_rack_96_2000ul_4,A2,8,2
tube_rack_96_2000ul_1,A3,2500,tube_rack_96_2000ul_4,A3,12,2
```

**What happens automatically:**
- **Transfer 1 (1500µL):** Split into [1000µL, 500µL] - two sub-transfers
- **Transfer 2 (1800µL):** Split into [900µL, 900µL] - smart redistribution (NOT [1000, 800] because 800 is too close to 1000, wastes aspiration cycles)
- **Transfer 3 (2500µL):** Split into [833.3µL, 833.3µL, 833.3µL] - three even chunks

**With air gap (20µL):**
If you add `Air Gap = 20` to the CSV:
- Effective capacity becomes 1000 - 20 = 980µL per chunk
- Transfer 1 (1500µL): Split into [750µL, 750µL] to stay within 980µL effective max

**Note:** The splitting algorithm is automatic - just specify the desired volume in CSV. The system handles chunking based on pipette limits.

---

**[← Back to Main Tutorial](USER_TUTORIAL.md)** | **[See Complete Workflow Example →](APPENDIX.md)**
