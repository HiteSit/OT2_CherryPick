# MCP Tools Reference

Reference for the OT2 CherryPick Model Context Protocol server.

Run the server from the repository root:

```bash
uv run ot2-mcp-server
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENTRONS_DIR` | recommended | Root Opentrons App data directory. Labware and protocol paths are derived from `{OPENTRONS_DIR}/labware` and `{OPENTRONS_DIR}/protocols`. |
| `OT2_PROJECT_DIR` | no | Persistent workspace directory. Defaults to the process working directory or an auto-created workspace depending on launch context. |

## Project Tools

### `ot2_initialize_project`

Copy template files into the active project workspace: `settings.toml`, `labware_dict.toml`, `CherryPick_OT2.py`, and example CSVs.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| none | - | - | No parameters. |

### `ot2_get_project_directory`

Return the active project directory and whether it was auto-created.

### `ot2_set_project_directory`

Switch the active project directory at runtime. The directory is created if it does not exist.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `path` | string | yes | Absolute path to the project directory. |
| `initialize_templates` | boolean | no | Copy templates into the new directory. Defaults to `true`. |

### `ot2_list_projects`

List the active project, recent project history, and optionally scan a parent directory for project folders.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `scan_parent_directory` | string | no | Parent directory to scan for subdirectories containing `settings.toml`. |

### `ot2_export_project_archive`

Create a ZIP archive of the current project workspace.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `as_base64` | boolean | no | Include archive contents inline as base64. Defaults to `false`. |

## Configuration Tools

### `ot2_update_settings`

Update one value in `settings.toml` by dotted path or shorthand alias.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `path` | string | yes | Dotted path or alias. |
| `value` | string | yes | New value. Booleans and numbers can be passed as text and are parsed. |
| `settings_path` | string | no | Settings file path. Defaults to `settings.toml`. |

Examples:

```text
ot2_update_settings(path="mode", value="multi_X1")
ot2_update_settings(path="speed", value="200")
ot2_update_settings(path="settings.liquid_handling.delays.post_aspirate", value="2")
```

### `ot2_batch_update_settings`

Update multiple `settings.toml` values in one atomic operation.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `updates` | array | yes | List of `{ "path": "...", "value": "..." }` objects. |
| `settings_path` | string | no | Settings file path. Defaults to `settings.toml`. |

### `ot2_apply_liquid_preset`

Apply a preset defined in `settings.toml` by copying preset values into the active liquid-handling sections and setting `active_preset`.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `preset_name` | string | yes | Built-in default template presets are `standard` and `viscous`. Custom presets may exist in a project. |
| `settings_path` | string | no | Settings file path. Defaults to `settings.toml`. |

Volatile/slippery handling is manual tuning in the default template, not a built-in preset.

### `ot2_list_settings`

List all setting paths and current values from `settings.toml`.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `settings_path` | string | no | Settings file path. Defaults to `settings.toml`. |

### `ot2_add_deck_entry`

Append labware, tip rack, or module entries to `settings.working_plate`.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `entry_type` | string | yes | `"reservoir"`, `"tip"`, or `"module"`. |
| `labware_id` | string | yes | Labware ID or load name. |
| `position_rack` | string | yes | OT-2 deck slot. |
| `connection` | string | tip only | Pipette name such as `Pipette_8` or `Pipette_1`. |
| `mode` | string | tip in dual mode | `multi`, `multi_X1`, or `single_X1`. |
| `module_type` | string | module only | Currently `heaterShaker`. |
| `adapter_id` | string | module only | Adapter loaded on the module. |
| `target_temperature` | integer | no | `0` disables heating. |
| `target_shake_speed` | integer | no | `0` disables shaking. |
| `persist_after_protocol` | boolean | no | Keep module state active after protocol end. |
| `offset_x`, `offset_y`, `offset_z` | number | no | Per-slot offsets in mm. |

If the current deck is still the project template default, the first add may auto-clear the template entries before appending the requested entry.

### `ot2_remove_deck_entry`

Remove a deck entry by `position_rack`.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `position_rack` | string | yes | Slot number to remove. |

### `ot2_clear_deck`

Remove all deck entries from `settings.working_plate`.

## CSV Tools

### `ot2_generate_csv_template`

Create a CSV skeleton under `CSVs/`.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `filename` | string | yes | Output CSV filename. |
| `transfers` | integer | yes | Number of placeholder transfer rows. |
| `source_labware` | string | yes | Source reference such as `tube_rack_96_1500ul_4`. |
| `dest_labware` | string | yes | Destination reference such as `384_ppv_55ul_2`. |
| `default_volume` | number | no | Default `Volume (ul)`. |
| `source_height` | number | no | Default `Source Bottom`. |
| `dest_top` | number | no | Default `Dest Top`. |

### `ot2_upload_csv_content`

Save CSV text into the project `CSVs/` directory.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `csv_content` | string | yes | Raw CSV content. |
| `filename` | string | yes | Output filename. |
| `output_dir` | string | no | Output directory. Defaults to `CSVs`. |

Required columns are `Source Labware`, `Source Well`, `Dest Labware`, `Dest Well`, `Tip Action`, and at least one of `Volume (ul)` or `Distribution Volume (ul)`.

### `ot2_list_csv_files`

List CSV files available in the active project.

### `ot2_insert_home_rows`

Insert HOME control rows into an existing CSV every N transfer rows.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `csv_path` | string | yes | CSV file to modify. |
| `every_n_transfers` | integer | yes | Insert HOME after this many transfer rows. |

Rows immediately after inserted HOME rows are forced to `Tip Action: new`.

## Protocol, Simulation, and Validation

### `ot2_generate_protocol`

Compile TOML configuration and a CSV transfer map into `CherryPick_OT2.py`.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `csv_path` | string | yes | CSV file path, for example `CSVs/transfers.csv`. |
| `settings_path` | string | no | Settings TOML path. |
| `labware_path` | string | no | Labware TOML path. |
| `protocol_path` | string | no | Protocol file to update. |
| `offset_db_path` | string | no | Offset database path. |
| `response_format` | string | no | Tool response format. |

### `ot2_validate_configuration`

Run pre-flight checks before generation.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `csv_path` | string | yes | CSV file to validate. |
| `settings_path` | string | no | Settings TOML path. |
| `labware_path` | string | no | Labware TOML path. |

### `ot2_simulate_protocol`

Run `opentrons_simulate` against a compiled protocol.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `protocol_path` | string | no | Defaults to `CherryPick_OT2.py`. |
| `labware_env_path` | string | no | Custom labware path override. |
| `response_format` | string | no | Tool response format. |

Simulation uses `{OPENTRONS_DIR}/labware` when available and can fall back to `LABWARE_PATH`.

## Deployment and Workflow

### `ot2_deploy_to_opentrons`

Deploy the compiled protocol to the Opentrons App protocol directory and/or clipboard.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `protocol_path` | string | no | Defaults to `CherryPick_OT2.py`. |
| `target_path` | string | no | Explicit deployment target. |
| `opentrons_dir` | string | no | Root Opentrons App directory for auto-UUID deployment. |
| `copy_to_clipboard` | boolean | no | Copy protocol text to clipboard. |
| `clipboard_command` | string | no | Clipboard command override. |

When `opentrons_dir` or `OPENTRONS_DIR` is available, deployment scans existing protocol UUID folders by `protocolName` and reuses the matching slot if one exists.

### `ot2_full_workflow`

Run the complete pipeline: validate, generate, simulate, and optionally deploy.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `csv_path` | string | yes | CSV file path. |
| `settings_path` | string | no | Settings TOML path. |
| `labware_path` | string | no | Labware TOML path. |
| `protocol_path` | string | no | Protocol path. |
| `offset_db_path` | string | no | Offset database path. |
| `simulate` | boolean | no | Run simulation. Defaults to `true`. |
| `labware_env_path` | string | no | Custom labware path override. |
| `deploy` | boolean | no | Deploy after simulation. Defaults to `false`. |
| `deployment_target` | string | no | Explicit deployment target. |
| `opentrons_dir` | string | no | Root Opentrons App directory. |
| `copy_to_clipboard` | boolean | no | Copy generated protocol to clipboard. |
| `clipboard_command` | string | no | Clipboard command override. |
| `response_format` | string | no | `json`, `markdown`, or `concise`. |

## Labware and Offsets

### `ot2_add_labware_definition`

Add or update an offset entry in `offset_database.toml`.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `labware_id` | string | yes | Labware identifier. |
| `position_rack` | string | yes | Deck slot number. |
| `offset_x`, `offset_y`, `offset_z` | number | no | Offset values in mm. |

### `ot2_scan_available_labware`

List custom and official labware available for deck setup.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `custom_labware_path` | string | no | Custom labware directory. Defaults to `{OPENTRONS_DIR}/labware` when possible. |

### `ot2_get_labware_offset`

Retrieve one offset entry.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `labware_id` | string | yes | Labware identifier. |
| `position_rack` | string | yes | Deck slot number. |

### `ot2_list_labware_offsets`

List all offsets stored in `offset_database.toml`.

### `ot2_delete_labware_offset`

Delete one offset entry.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `labware_id` | string | yes | Labware identifier. |
| `position_rack` | string | yes | Deck slot number. |

### `ot2_manage_official_labware`

Manage the official labware allowlist.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `action` | string | yes | `add`, `remove`, or `list`. |
| `labware_id` | string | for add/remove | Official labware load name. |

## GUI Sync Tools

### `ot2_create_shell_settings`

Create `shell_settings.json` with the Windows Opentrons App root path used by the GUI.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `opentrons_dir_win` | string | yes | Windows path such as `C:\Users\<name>\AppData\Roaming\Opentrons`. |

### `ot2_sync_to_gui`

Push selected project files into the running Docker GUI workspace.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `files` | array | no | Optional list such as `["settings.toml", "CSVs"]`. Defaults to all supported sync files. |

This is a one-way sync from the MCP project to the GUI workspace. It preserves GUI-only CSVs and does not overwrite `offset_database.toml`.

## Shorthand Aliases

Aliases accepted by `ot2_update_settings` and `ot2_batch_update_settings`:

| Alias | Full path |
|-------|-----------|
| `mode`, `pipette_mode` | `settings.general.mode` |
| `speed`, `head_speed` | `settings.general.head_speed.speed` |
| `starting_tip`, `starting_tip_well` | `settings.general.starting_tip_well` |
| `protocol_name` | `settings.general.protocol_name` |
| `pre_aspirate`, `pre_aspirate_contact` | `settings.liquid_handling.pre_aspirate_contact.enabled` |
| `pre_aspirate_volume`, `pre_wet_volume` | `settings.liquid_handling.pre_aspirate_contact.aspirate_volume` |
| `wick`, `wicking`, `tip_wicking` | `settings.liquid_handling.post_aspirate_wick.enabled` |
| `delay`, `post_aspirate_delay`, `aspirate_delay` | `settings.liquid_handling.delays.post_aspirate` |
| `push_out`, `pushout` | `settings.liquid_handling.push_out.enabled` |
| `push_out_volume`, `pushout_volume` | `settings.liquid_handling.push_out.volume_ul` |
| `mixing`, `mixing_enabled` | `settings.liquid_handling.mixing.enabled` |
| `mixing_location` | `settings.liquid_handling.mixing.location` |
| `mixing_reps`, `mixing_repetitions` | `settings.liquid_handling.mixing.repetitions` |
| `source_remixing` | `settings.liquid_handling.mixing.source_remixing` |
| `active_preset` | `settings.liquid_handling.active_preset` |

## Resources

| URI | Description |
|-----|-------------|
| `config://settings` | Current `settings.toml` content. |
| `config://labware` | Current `labware_dict.toml` content. |
| `config://offsets` | Current `offset_database.toml` content or a fallback message if absent. |
| `status://deck-layout` | Deck layout summary. |
| `status://liquid-handling-config` | Active liquid-handling summary. |
| `status://project-directory` | Active project directory status. |
| `files://csvs` | Available project CSV files. |
| `files://archives` | Available project archive ZIP files. |
| `logs://last-simulation` | Most recent simulation log. |

## Prompts

| Prompt | Description |
|--------|-------------|
| `setup_new_experiment` | Step-by-step setup for a new OT-2 cherry-pick experiment. |
| `optimize_liquid_handling` | Problem-driven manual liquid-handling tuning. |
| `recipe_dilution` | Standard reservoir-to-384 dilution recipe with fixed deck pattern and multi-channel fill plan. |
| `switch_project` | Guided project-directory switch. |
