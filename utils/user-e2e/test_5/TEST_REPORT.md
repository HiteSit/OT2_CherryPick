# Test 5: complex-mixing-per-source

## Scenario
Complex cherry-pick with mixing after dispense, per_source tip reuse, 2 different source labwares.

## User Prompt
"I have two different source racks with different reagents and need to cherry-pick into a 384-well plate with mixing after each dispense. Use single_X1 mode with the standard preset but set tip_reuse to per_source so tips change when switching between source racks."

## Settings Applied
- **Mode:** single_X1
- **Preset:** standard (contact, wicking, no delays, no push-out)
- **Tip Reuse:** per_source (new tip when source labware changes)
- **Mixing:** enabled, destination, 3 repetitions
- **Head Speed:** 400 mm/min

## Deck Layout
| Slot | Labware | Type |
|------|---------|------|
| 4 | tube_rack_96_1500ul | source 1 |
| 7 | tube_rack_48_1500ul | source 2 |
| 2 | 384_pp_high_150ul | destination |
| 5 | tip_rack_geb_1000ul | tip (Pipette_1) |

## CSV
- File: `CSVs/test_complex_mixing.csv`
- 8 transfers, volumes 120-200 uL
- First 4 rows from tube_rack_96_1500ul_4, last 4 from tube_rack_48_1500ul_7
- Mix Volume: 100 uL (source 1) and 120 uL (source 2)
- Mix Height: 2 mm from bottom

## Result: PASS

- Validation: OK
- Generation: OK (JSON size: 3320 bytes)
- Simulation: OK (exit code 0)
- All 8 transfers completed successfully
- **per_source tip reuse confirmed:**
  - Tip 1 (A1): used for all 4 transfers from tube_rack_96_1500ul_4
  - Tip dropped after source change
  - Tip 2 (B1): picked up for tube_rack_48_1500ul_7 transfers, kept for all 4, returned at end
- **Mixing confirmed:** 3x mixing at 100 uL (source 1) and 120 uL (source 2) after each dispense
- **Two source labwares** working correctly in same protocol

## Notes
- Original scenario specified `384_ppv_150ul` but this labware JSON is not available in the custom labware directory. Substituted with `384_pp_high_150ul` which exists.
- The `Tip Action` column was set to `new` for the first transfer of each source group and `keep` for subsequent transfers within the same source, matching per_source behavior.
