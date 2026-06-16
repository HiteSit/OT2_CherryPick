# GUI Guide

The OT2 CherryPick web interface is a single 4-step wizard for configuring, validating, and executing OT-2 liquid handling protocols. Launch it with Docker from the `docker/` directory and open [http://localhost](http://localhost) unless you changed `HOST_PORT`.

The GUI edits the same project files used by the MCP and CLI workflow: `settings.toml`, `labware_dict.toml`, `offset_database.toml`, and CSV transfer maps under `CSVs/`.

## Step 1: Deck Setup

![Deck Setup](imgs/deck_setup.png)

**Screenshot caption:** Capture the Deck Setup step with a protocol name filled in, the pipette mode selector visible, the Opentrons App folder saved, several populated deck slots, and the Hardware Catalog section visible below the deck. This screenshot should make it obvious that Step 1 is where the physical OT-2 layout and app data path are configured.

Use this screen to define the physical deck and the protocol identity.

**Main controls:**
- **Protocol Name** -- Optional display name embedded in the generated protocol. Leave blank to use the built-in default protocol name.
- **Pipette Mode** -- Select `single_X1`, `multi_X1`, `multi`, or `dual` before assigning tip racks.
- **Starting Tip Well** -- Shown only for `multi_X1`, where the 8-channel pipette uses one nozzle in `SINGLE` layout. The common start is `H1`.
- **Opentrons Folder** -- Windows path to the root Opentrons App data directory, usually `C:\Users\<you>\AppData\Roaming\Opentrons`. The backend derives `labware/` and `protocols/` from this root.
- **DeckGrid** -- Visual deck editor for OT-2 slots.
- **Hardware Catalog** -- Pipette definitions from `labware_dict.toml`, including compatible tip rack IDs.

**Adding labware to slots:**
1. Click an empty slot on the deck grid.
2. Choose the entry type: source/reservoir/destination, tip rack, or module.
3. Select the labware ID from the available catalog.
4. For tip racks, set `connection` to the pipette name from `labware_dict.toml`.
5. In `dual` mode, also set the tip rack `mode` to `multi`, `multi_X1`, or `single_X1` so each pipette mode has its own tips.
6. Add optional `offset_x`, `offset_y`, and `offset_z` values if the labware needs a slot-specific calibration offset.

![Add Labware Modal](imgs/deck_labware_modal.png)

**Screenshot caption:** Capture the Add Labware modal after clicking an empty slot. Use either a tip rack entry showing `connection` and `mode`, or a module entry showing module fields. If possible, include the offset fields and the "save offset to database" option so the screenshot explains how `settings.toml` and `offset_database.toml` interact.

**Heater-shaker modules:**
- Use `type = "module"` and `module_type = "heaterShaker"`.
- Set `adapter_id` and optional `labware_id`.
- `target_temperature = 0` disables heating; non-zero values request heating.
- `target_shake_speed = 0` disables shaking; non-zero values request shaking.
- `persist_after_protocol` controls whether module settings remain active after the protocol finishes.
- Module labware is background-only in the current protocol model and should not be referenced as a CSV source or destination.

**Deck notes:**
- Each slot should contain at most one configured entry.
- Tip rack `connection` must match a pipette name from `labware_dict.toml`.
- The generated protocol uses the OT-2 trash handling from the protocol code. The current GUI deck grid renders numbered slots, so capture the GUI as it appears rather than forcing a separate trash tile into the screenshot.

## Step 2: Configuration

![Configuration](imgs/configuration.png)

**Screenshot caption:** Capture the Configuration step with Head Speed visible, the Liquid Handling Preset selector open or populated, the "Save as Preset" button visible, and one accordion section expanded. A good default screenshot is the Post-Aspirate Wick or Mixing Settings panel because it shows switches, numeric controls, and help icons in one view.

Use this screen to tune movement speed and liquid-handling behavior. Changes are saved to `settings.toml`.

**Basic settings:**
- **Head Speed** -- Gantry movement speed in mm/min. Lower values such as 200-300 mm/min are useful for volatile or drip-prone liquids.

**Liquid Handling Preset:**
- Built-in presets are `standard` and `viscous`.
- `Custom` clears `active_preset` and uses the individual parameter values as written.
- Changing an individual liquid-handling field while a preset is active clears the active preset and switches the configuration back to custom values.
- **Save as Preset** stores the current liquid-handling settings under `[settings.liquid_handling.presets.<name>]`.

**Advanced liquid handling accordion:**
- **Pre-Aspirate Contact** -- Touch or pre-wet before the main aspiration.
- **Post-Aspirate Wick** -- Touch the well wall after aspirating to remove droplets from the outside of the tip.
- **Delays & Push-Out** -- Add a post-aspirate delay and optional push-out volume.
- **Mixing Settings** -- Enable source or destination mixing, set repetitions, and choose source-remixing behavior.

**Important behavior:**
- `active_preset` is not just a label. At runtime, the selected preset overrides the individual liquid-handling sections.
- Destination mixing is not compatible with distribution rows that use the Opentrons `distribute()` API. Use source mixing, disable mixing, or split the operation into ordinary cherry-pick transfers.
- Volatile/slippery liquids do not have a built-in preset in the default template. Use custom settings: lower head speed, consider pre-wetting, and reduce CSV flow-rate multipliers.

## Step 3: Transfer Map

![Transfer Map](imgs/transfer_map.png)

**Screenshot caption:** Capture the Transfer Map step with a real CSV selected or uploaded, the spreadsheet tab visible, several populated rows, the validation sidebar after pressing "Validate CSV," and the Transfer Preview visible below. The screenshot should show that users can edit CSV content directly inside the browser.

Use this screen to create, upload, edit, save, validate, and preview CSV transfer maps.

**CSV editor controls:**
- **Select CSV file** -- Load an existing workspace CSV.
- **Upload CSV** -- Import a local `.csv` file into the workspace.
- **CSV filename** -- Name used when saving the current editor content.
- **Add Row / Remove Row** -- Append or remove transfer rows in the spreadsheet.
- **Save to workspace** -- Persist the current CSV content under `CSVs/`.
- **Spreadsheet View** -- Table-style editor for routine changes.
- **Text View** -- Raw CSV editor for paste-from-spreadsheet workflows.

**Required columns:**

| Column | Example |
|--------|---------|
| `Source Labware` | `tube_rack_96_1500ul_4` |
| `Source Well` | `A1` |
| `Dest Labware` | `384_ppv_55ul_2` |
| `Dest Well` | `B3` |
| `Tip Action` | `new` |

Each row also needs at least one volume column: `Volume (ul)` for ordinary transfers or `Distribution Volume (ul)` for distribution rows.

**Labware references** use `{labware_id}_{slot_number}`. For example, `tube_rack_96_1500ul_4` references `tube_rack_96_1500ul` in slot 4.

**Positioning columns:**
- Choose one source height column: `Source Bottom` or `Source Top`.
- Choose one destination height column: `Dest Bottom` or `Dest Top`.
- `Mix Height` is used when `Mix Volume` is present and mixing is enabled.

**Optional liquid-handling columns:**
- `Mix Volume`
- `Mix Height`
- `Flow Aspirate`
- `Flow Dispense`
- `Air Gap`
- `Air Gap Rate`
- `Distribution`
- `Mode` for `dual` mode rows

**Tip Action values:**
- `new` -- Drop any current tip if needed and pick up a fresh tip.
- `keep` -- Reuse the current tip when possible.
- `drop` -- Drop the tip after the row.

`Tip Action` is the current tip reuse mechanism. There is no separate global tip-reuse setting in the GUI.

**Manual validation:**
Click **Validate CSV** after editing. The validation panel checks required columns, labware references against the deck, basic well formatting, volume values, height-column conflicts, distribution patterns, multi-channel distribution row compatibility, and HOME-row tip rules.

![Transfer Map Errors](imgs/transfer_map_errors.png)

**Screenshot caption:** Capture the Transfer Map step after loading a deliberately invalid CSV and pressing "Validate CSV." A useful example is one row with an unknown labware reference or invalid volume. Include the red row-numbered messages in the right-hand validation panel.

**Distribution rows:**
- A row is treated as distribution if `Dest Well` contains `|` or `Distribution Volume (ul)` is populated.
- `Distribution Volume (ul)` is the per-destination volume.
- `Distribution` can be `equal`, `geometric:<factor>`, or `geometric:<factor>:desc`.
- `Air Gap` applies to distribution rows; `Air Gap Rate` is only meaningful for ordinary cherry-pick rows.

**HOME control rows:**
- A HOME row has all non-empty cells set to `HOME`.
- The robot drops any held tip before homing.
- The row immediately after HOME must use `Tip Action: new`.

## Step 4: Review & Execute

![Review & Execute Ready](imgs/review_execute_ready.png)

**Screenshot caption:** Capture Review & Execute with a complete deck, settings, and CSV. The Configuration Summary should show the selected mode, head speed, deck counts, CSV name, row count, and active liquid-handling badges. The Pre-flight Checklist should be green and the Run Workflow button should be enabled.

Use this screen to confirm the wizard state and run the protocol pipeline.

**Configuration Summary:**
- Protocol name when set.
- Pipette mode.
- Head speed.
- Starting tip well.
- Deck layout counts.
- Current CSV filename and row count.
- Liquid-handling badges for enabled features.

**Pre-flight Checklist:**
This checklist is a structural readiness check. It confirms that the wizard has source labware, destination labware, tip racks, settings, CSV content, a CSV filename, no duplicate deck slots, and a reasonable deck count.

CSV-specific checks such as labware references, volumes, height-column conflicts, distribution compatibility, and HOME-row rules live in the Step 3 validation panel.

**Execution Options:**
- **Run opentrons_simulate validation** -- Generate the protocol and run the Opentrons simulator.
- **Send to Opentrons deployment path** -- Copy the generated protocol into the configured Opentrons App protocol directory.
- **Advanced Options > Copy protocol to clipboard** -- Copy the generated protocol text to the system clipboard.

Click **Run Workflow** after completing the prior steps.

![Review Execute Blocked](imgs/review_execute_blocked.png)

**Screenshot caption:** Capture Review & Execute with an incomplete setup, such as no CSV loaded or a missing tip rack. The screenshot should show the orange "Cannot execute workflow" warning and failed checklist rows. This is useful for documenting why the button can be disabled.

![Review Execute Results](imgs/review_execute_results.png)

**Screenshot caption:** Capture the post-run results after a successful generate/simulate workflow. Include the Execution Results stepper, generated protocol path, simulation status, execution logs, and any visible simulator output. This screenshot explains what success looks like after clicking Run Workflow.

## Practical Screenshot Checklist

Before taking final screenshots, use one coherent example project:
- A recognizable protocol name, such as `DMSO Cherry Pick Demo`.
- One source labware, one destination labware, and at least one tip rack.
- A valid CSV with 3-5 ordinary transfers and at least one row using `Tip Action: keep`.
- A second intentionally invalid CSV for the error screenshot.
- A visible Opentrons App folder path in Deck Setup.
- A liquid-handling preset or custom setting that produces visible badges in Review & Execute.

Use the exact image names already referenced above so the Markdown renders as soon as the PNG files are added under `docs/imgs/`.
