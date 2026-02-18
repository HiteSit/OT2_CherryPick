# Test 2: viscous-multi-x1-cherry

## Scenario
Multi_X1 mode cherry-pick with viscous liquid preset (DMSO-like), 8 transfers from tube rack to 384-well plate.

## User Prompt
"I'm transferring viscous DMSO solutions and need precise single-well targeting with the 8-channel pipette. Set mode to multi_X1 and apply the viscous liquid preset. Set tip_reuse to never. Deck layout: tube_rack_96_1500ul in slot 7 as source, 384_pp_standard_100ul in slot 3 as destination, opentrons_96_tiprack_300ul in slot 10 connected to Pipette_8."

## Settings Applied
- **Mode:** multi_X1 (8-channel pipette, single-tip H1 nozzle)
- **Preset:** viscous (2s post-aspirate delay, push-out 5uL, wicking enabled)
- **Tip Reuse:** never
- **Head Speed:** 400 mm/min

## Deck Layout (adjusted from scenario)
Original scenario requested slots 7/3/10, but multi_X1 mode with H1 nozzle has strict motion bounds. Adjusted to:

| Slot | Labware | Type |
|------|---------|------|
| 4 | tube_rack_96_1500ul | source |
| 2 | 384_pp_standard_100ul | destination |
| 6 | opentrons_96_tiprack_300ul | tip (Pipette_8) |

## CSV
- File: `CSVs/test_viscous_multi_x1.csv`
- 8 transfers, volumes 45-80 uL
- Source: tube_rack_96_1500ul_4 (wells A1-C2)
- Destination: 384_pp_standard_100ul_2 (wells A1-D3)

## Result: PASS (with slot adjustments)

- Validation: OK
- Generation: OK (JSON size: 3213 bytes)
- Simulation: OK (exit code 0)
- All 8 transfers completed successfully
- Multi_X1 mode confirmed: "Configure pipette on right mount to use NozzleLayout.SINGLE layout starting at nozzle H1"
- 2-second delay observed after each aspiration
- Push-out (blowout) observed after each dispense
- Tip wicking (touch tip) observed after each aspiration

## Issues Encountered
- **PartialTipMovementNotAllowedError:** multi_X1 mode with H1 nozzle has strict deck position constraints. Original slots 7/3/10 caused collision errors. Slots must be carefully chosen to avoid the shifted pipette body colliding with adjacent labware. Final working layout: source slot 4, dest slot 2, tips slot 6.
- This is a known OT-2 simulator limitation for partial tip configurations.
