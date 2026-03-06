# MCP Tools Reference

Complete reference for the OT2 CherryPick Model Context Protocol server.

**Run the server:**
```bash
uv run ot2-mcp-server
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENTRONS_DIR` | yes | Root Opentrons App data directory. Labware (`{OPENTRONS_DIR}/labware`) and protocol (`{OPENTRONS_DIR}/protocols`) paths are auto-derived. See [Configuration Reference](configuration_reference.md#environment-variables) for details. |
| `OT2_PROJECT_DIR` | no | Persistent workspace directory. Defaults to current working directory. |

## Tools

### Project Management

#### `ot2_initialize_project`

Copy template files (settings.toml, labware_dict.toml, CherryPick_OT2.py, example CSVs) to the workspace directory.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| -- | -- | -- | No parameters |

#### `ot2_get_project_directory`

Return the active project directory path.

#### `ot2_set_project_directory`

Switch the active project directory at runtime.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `path` | string | yes | Absolute path to the new project directory |

#### `ot2_list_projects`

List active, recent, and discovered projects.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `scan_parent_directory` | boolean | no | Scan parent directory for additional projects |

#### `ot2_export_project_archive`

Export the workspace as a ZIP archive.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| -- | -- | -- | Optionally returns base64-encoded content |

### Configuration

#### `ot2_update_settings`

Update a single setting in settings.toml via dotted path or shorthand alias.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `path` | string | yes | Dotted path or alias (see [Shorthand Aliases](#shorthand-aliases)) |
| `value` | any | yes | New value for the setting |

**Examples:**
```
ot2_update_settings(path="tip_reuse", value="never")
ot2_update_settings(path="speed", value=200)
ot2_update_settings(path="settings.liquid_handling.delays.post_aspirate", value=2)
```

#### `ot2_apply_liquid_preset`

Apply a predefined liquid handling configuration.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `preset_name` | string | yes | Preset name: `standard`, `viscous`, or `slippery` |

#### `ot2_list_settings`

List all settings paths and their current values.

### CSV Management

#### `ot2_generate_csv_template`

Create a CSV skeleton with proper column structure.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| *(various)* | -- | -- | Template parameters for source/dest labware and wells |

#### `ot2_upload_csv_content`

Save CSV text content to a file in the CSVs/ directory.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `csv_content` | string | yes | CSV text content |
| `filename` | string | yes | Output filename (saved to CSVs/) |

### Protocol Generation

#### `ot2_generate_protocol`

Compile TOML configuration and CSV transfer map into CherryPick_OT2.py.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `csv_path` | string | yes | Path to CSV file (e.g., `CSVs/transfers.csv`) |

### Simulation

#### `ot2_simulate_protocol`

Run `opentrons_simulate` to validate the generated protocol without hardware. The custom labware path is auto-derived from `OPENTRONS_DIR/labware`. Falls back to the `LABWARE_PATH` env var if `OPENTRONS_DIR` is not set.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `protocol_path` | string | no | Path to protocol file (defaults to CherryPick_OT2.py) |

### Validation

#### `ot2_validate_configuration`

Run pre-flight checks on TOML and CSV configuration before generating.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `csv_path` | string | yes | Path to CSV file to validate against |

### Deployment

#### `ot2_deploy_to_opentrons`

Deploy the generated protocol to the Opentrons App and/or clipboard. When `OPENTRONS_DIR` is set and no `target_path` is provided, the tool performs **auto-UUID deployment**:

1. Generates a fresh UUID
2. Creates `{OPENTRONS_DIR}/protocols/{uuid}/src/` and `analysis/` directories
3. Copies the protocol to `src/`
4. Runs `opentrons.cli analyze` to produce `analysis/{timestamp_ms}.json`
5. The Opentrons App discovers the protocol automatically on next scan

This means users do not need to manually find or specify UUID protocol directories.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `target_path` | string | no | Opentrons App protocol directory (overrides auto-UUID deployment) |
| `copy_to_clipboard` | boolean | no | Copy protocol to clipboard |

### Labware Management

#### `ot2_add_labware_definition`

Add or update a calibration offset in offset_database.toml.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `labware_id` | string | yes | Labware identifier |
| `position_rack` | string | yes | Deck slot number |
| `offset_x` | number | no | X offset in mm |
| `offset_y` | number | no | Y offset in mm |
| `offset_z` | number | no | Z offset in mm |

#### `ot2_scan_available_labware`

List labware available in the custom labware directory. Defaults to `{OPENTRONS_DIR}/labware` when no path is provided.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `custom_labware_path` | string | no | Path to custom labware directory (defaults to `OPENTRONS_DIR/labware`) |

#### `ot2_get_labware_offset`

Retrieve a single calibration offset.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `labware_id` | string | yes | Labware identifier |
| `position_rack` | string | yes | Deck slot number |

#### `ot2_list_labware_offsets`

List all stored calibration offsets.

#### `ot2_delete_labware_offset`

Delete a calibration offset entry.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `labware_id` | string | yes | Labware identifier |
| `position_rack` | string | yes | Deck slot number |

#### `ot2_manage_official_labware`

Manage the official labware allowlist.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `action` | string | yes | `"add"`, `"remove"`, or `"list"` |
| `labware_id` | string | no | Labware identifier (required for add/remove) |

### Workflow

#### `ot2_full_workflow`

End-to-end pipeline: validation, protocol generation, simulation, and optional deployment.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `csv_path` | string | yes | Path to CSV file |
| `simulate` | boolean | no | Run simulation (default: true) |
| `deploy` | boolean | no | Deploy to Opentrons App |
| `response_format` | string | no | Output format |

## Shorthand Aliases

These aliases can be used as the `path` parameter in `ot2_update_settings` instead of full dotted paths:

| Alias | Full Path |
|-------|-----------|
| `tip_reuse` | `settings.general.tip_reuse` |
| `mode` | `settings.general.mode` |
| `speed` | `settings.general.head_speed.speed` |
| `head_speed` | `settings.general.head_speed.speed` |
| `starting_tip` | `settings.general.starting_tip_well` |
| `protocol_name` | `settings.general.protocol_name` |
| `pre_aspirate` | `settings.liquid_handling.pre_aspirate_contact.enabled` |
| `pre_aspirate_volume` | `settings.liquid_handling.pre_aspirate_contact.aspirate_volume` |
| `wick` | `settings.liquid_handling.post_aspirate_wick.enabled` |
| `wicking` | `settings.liquid_handling.post_aspirate_wick.enabled` |
| `delay` | `settings.liquid_handling.delays.post_aspirate` |
| `post_aspirate_delay` | `settings.liquid_handling.delays.post_aspirate` |
| `push_out` | `settings.liquid_handling.push_out.enabled` |
| `push_out_volume` | `settings.liquid_handling.push_out.volume_ul` |
| `mixing` | `settings.liquid_handling.mixing.enabled` |
| `mixing_location` | `settings.liquid_handling.mixing.location` |
| `mixing_reps` | `settings.liquid_handling.mixing.repetitions` |
| `source_remixing` | `settings.liquid_handling.mixing.source_remixing` |
| `active_preset` | `settings.liquid_handling.active_preset` |

## Resources

Read-only data endpoints accessible via MCP resource URIs.

| URI | Description |
|-----|-------------|
| `config://settings` | Current settings.toml content |
| `config://labware` | Labware catalog (labware_dict.toml) |
| `config://offsets` | Calibration offset database (offset_database.toml) |
| `status://deck-layout` | Visual deck configuration summary |
| `status://liquid-handling-config` | Active liquid handling parameters |
| `files://csvs` | List of available CSV transfer files |
| `logs://last-simulation` | Most recent simulation output |

## Prompts

Guided workflow templates for common tasks.

| Prompt | Description |
|--------|-------------|
| `setup_new_experiment` | Step-by-step experiment configuration wizard |
| `optimize_liquid_handling` | Problem-driven manual parameter tuning for liquid handling |
| `switch_project` | Switch between project directories with context reset |
