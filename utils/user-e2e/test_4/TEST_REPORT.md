# Test 4: large-vol-slippery-single

## Scenario
Large-volume single-channel transfers with slippery preset for volatile solvents, tube rack to tube rack.

## User Prompt
"I am transferring volatile organic solvents (hexane-based) at larger volumes using the single-channel p1000 pipette. Apply the slippery liquid preset. Set mode to single_X1 and tip_reuse to never."

## Settings Applied
- **Mode:** single_X1
- **Preset:** slippery (pre-wet 20uL, slow head speed 200 mm/min, wicking enabled)
- **Tip Reuse:** never
- **Head Speed:** 200 mm/min (reduced for volatile solvents)

## Deck Layout
| Slot | Labware | Type |
|------|---------|------|
| 1 | tube_rack_24_4000ul | source |
| 3 | tube_rack_96_2000ul | destination |
| 6 | tip_rack_geb_1000ul | tip (Pipette_1) |

## CSV
- File: `CSVs/test_slippery_large.csv`
- 6 transfers, volumes 200-500 uL
- Source: tube_rack_24_4000ul_1 (wells A1-B3)
- Destination: tube_rack_96_2000ul_3 (wells A1-B3)

## Result: PASS

- Validation: OK
- Generation: OK (JSON size: 3056 bytes)
- Simulation: OK (exit code 0)
- All 6 transfers completed successfully
- Pre-wetting confirmed: each transfer shows "Aspirating 20.0 uL" then "Dispensing 20.0 uL" before the main aspiration
- Tip wicking (touch tip) observed after each main aspiration
- New tip for each transfer confirmed
- Large volumes (up to 500 uL) within p1000 range
