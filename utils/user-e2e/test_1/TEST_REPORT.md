# Test 1: basic-single-cherry

## Scenario
Basic cherry-pick using single_X1 mode with standard liquid preset, 10 transfers from 96-tube rack to 384-well plate.

## User Prompt
"I need to set up a basic cherry-picking protocol. Use single_X1 mode with the standard liquid preset and tip_reuse set to never. Place a tube_rack_96_1500ul source rack in slot 4, a 384_ppv_55ul destination plate in slot 2, and a tip_rack_geb_1000ul tip rack in slot 5 (connected to Pipette_1). Upload the following CSV as 'test_basic_single.csv' and then run the full workflow with it."

## Settings Applied
- **Mode:** single_X1
- **Preset:** standard (pre-aspirate contact enabled, wicking enabled, no delays, no push-out)
- **Tip Reuse:** never
- **Head Speed:** 400 mm/min

## Deck Layout
| Slot | Labware | Type |
|------|---------|------|
| 4 | tube_rack_96_1500ul | source |
| 2 | 384_ppv_55ul | destination |
| 5 | tip_rack_geb_1000ul | tip (Pipette_1) |

## CSV
- File: `CSVs/test_basic_single.csv`
- 10 transfers, volumes 100-250 uL
- Source: tube_rack_96_1500ul_4 (wells A1-D1)
- Destination: 384_ppv_55ul_2 (wells A1-E2)

## Result: PASS

- Validation: OK (no errors, no warnings)
- Generation: OK (JSON size: 3231 bytes)
- Simulation: OK (exit code 0)
- All 10 transfers completed successfully
- New tip used for each transfer (tip_reuse=never confirmed)
- Pre-aspirate contact and wicking observed in simulation output

## Notes
- The `active_preset` field must be set to empty string (`""`) when preset definitions are not included in settings.toml. Including `active_preset = "standard"` without the `[settings.liquid_handling.presets.standard]` section causes a runtime error in the protocol.
- The `Tip Action` column is required in all CSVs even though the scenario CSV did not include it. Added `new` for all rows to match `tip_reuse=never`.
