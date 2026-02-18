# Test 3: full-multi-column-transfer

## Scenario
Full multi-channel mode transferring entire columns from 96-tube rack to 384-well plate, 6 column transfers.

## User Prompt
"I need to do full-column transfers using the 8-channel pipette in multi mode with standard preset. Set tip_reuse to always since it is the same buffer."

## Settings Applied
- **Mode:** multi (full 8-channel, all 8 tips)
- **Preset:** standard (contact, wicking, no delays, no push-out)
- **Tip Reuse:** always
- **Head Speed:** 400 mm/min

## Deck Layout
| Slot | Labware | Type |
|------|---------|------|
| 4 | tube_rack_96_1500ul | source |
| 2 | 384_ppv_55ul | destination |
| 5 | opentrons_96_tiprack_300ul | tip (Pipette_8) |

## CSV
- File: `CSVs/test_multi_columns.csv`
- 6 column transfers, 40 uL uniform volume
- Each row = 8 simultaneous well transfers (entire column)
- Source columns 1-6 to destination odd columns 1,3,5,7,9,11

## Result: PASS

- Validation: OK
- Generation: OK (JSON size: 3011 bytes)
- Simulation: OK (exit code 0)
- All 6 column transfers completed successfully
- Multi mode confirmed: "Multi mode: A1 -> 8 source wells, A1 -> 8 dest wells" for each transfer
- tip_reuse=always confirmed: single tip pickup at start, tip returned at end ("Returning tip")
- Wicking (touch tip) observed after each aspiration
