# Configuration Reference

Complete reference for the OT2 CherryPick configuration files and CSV transfer format.

## Authoritative Files

| File or directory | Purpose |
|-------------------|---------|
| `settings.toml` | Main protocol configuration: mode, liquid handling, modules, deck entries, tip racks |
| `labware_dict.toml` | Pipette catalog and compatible tip rack mappings |
| `offset_database.toml` | Optional per-labware, per-slot calibration offsets |
| `CSVs/*.csv` | Transfer maps used to generate protocols |
| `tests/e2e/configs/*/settings.toml` | Tested example configurations for specific modes and features |
| GUI workspace | Docker GUI working copy, controlled by `OT2_GUI_WORKSPACE` and `OT2_PROJECT_DIR` |

The root templates are the best source for current default values. The generated protocol embeds the TOML and CSV data into `CherryPick_OT2.py`, so the OT-2 does not need the original files at runtime.

## settings.toml

The main protocol configuration file. It controls pipette mode, liquid handling parameters, deck layout, hardware modules, and tip rack assignment.

### General Settings

```toml
[settings.general]
protocol_name = ""
mode = "multi"
starting_tip_well = "H1"

[settings.general.head_speed]
speed = 400
```

| Field | Type | Template default | Description |
|-------|------|------------------|-------------|
| `protocol_name` | string | `""` | Optional protocol name embedded in generated metadata. Empty string preserves the protocol's built-in default name. |
| `mode` | string | `"multi"` | Pipette mode. See [Pipette Modes](#pipette-modes). |
| `starting_tip_well` | string | `"H1"` | Starting well for `multi_X1`, where the 8-channel pipette uses one nozzle. |
| `head_speed.speed` | number | `400` | Gantry movement speed in mm/min. Lower values such as 200-300 are useful for volatile or drip-prone liquids. |

### Liquid Handling

```toml
[settings.liquid_handling]
active_preset = ""
```

| Field | Type | Template default | Description |
|-------|------|------------------|-------------|
| `active_preset` | string | `""` | Preset name to apply at runtime. Empty string means use the individual settings exactly as written. |

`active_preset` is not just a label. When set, the runtime copies values from `[settings.liquid_handling.presets.<name>]` over the individual liquid-handling sections before executing transfers.

#### Pre-Aspirate Contact

```toml
[settings.liquid_handling.pre_aspirate_contact]
enabled = false
position_offset_percent = 20
aspirate_volume = 20
```

| Field | Type | Template default | Description |
|-------|------|------------------|-------------|
| `enabled` | boolean | `false` | Touch liquid surface before the main aspiration. |
| `position_offset_percent` | number | `20` | Safety offset applied around the CSV aspiration position. |
| `aspirate_volume` | number | `20` | Pre-wet volume in uL. Use `0` for contact-only behavior. |

#### Post-Aspirate Wicking

```toml
[settings.liquid_handling.post_aspirate_wick]
enabled = false
radius = 1
v_offset_mm = -1.5
speed = 20
```

| Field | Type | Template default | Description |
|-------|------|------------------|-------------|
| `enabled` | boolean | `false` | Touch the well wall after aspirating to remove droplets from the outside of the tip. |
| `radius` | number | `1` | Touch radius. Larger values move closer to the wall. |
| `v_offset_mm` | number | `-1.5` | Height relative to well top. Negative values move below the rim. |
| `speed` | number | `20` | Touch-tip speed. |

#### Delays

```toml
[settings.liquid_handling.delays]
post_aspirate = 0
```

| Field | Type | Template default | Description |
|-------|------|------------------|-------------|
| `post_aspirate` | number | `0` | Seconds to wait after aspiration before moving the tip. |

#### Push-Out

```toml
[settings.liquid_handling.push_out]
enabled = true
volume_ul = 20
```

| Field | Type | Template default | Description |
|-------|------|------------------|-------------|
| `enabled` | boolean | `true` | Push extra air after dispensing to expel residual liquid. |
| `volume_ul` | number | `20` | Push-out volume in uL. |

Push-out is skipped when a transfer is followed by mixing, because the mix cycles already aspirate and dispense through the tip.

#### Mixing

```toml
[settings.liquid_handling.mixing]
enabled = false
location = "destination"
repetitions = 2
source_remixing = "once"
```

| Field | Type | Template default | Description |
|-------|------|------------------|-------------|
| `enabled` | boolean | `false` | Enable CSV-driven mixing behavior. |
| `location` | string | `"destination"` | `"destination"`, `"source"`, or `"none"`. |
| `repetitions` | integer | `2` | Number of aspirate/dispense cycles. |
| `source_remixing` | string | `"once"` | For source mixing: `"once"` per source well or `"always"` before every aspiration. |

`Mix Volume` and `Mix Height` in the CSV are interpreted according to `location`.

#### Presets

Built-in presets in the root template:

| Preset | Intended use |
|--------|--------------|
| `standard` | Aqueous liquids: contact, wicking, destination mixing, no delay, no push-out |
| `viscous` | DMSO/glycerol/oils: contact, wicking, post-aspirate delay, push-out, stronger destination mixing |

Custom presets can be added by the GUI or by editing `settings.toml` under `[settings.liquid_handling.presets.<name>]`.

There is no built-in volatile/slippery preset in the default template. For volatile solvents, use custom settings: lower head speed, optional pre-wetting, and slower CSV flow-rate multipliers.

### Deck Layout

Deck entries are stored as an array of `[[settings.working_plate]]` tables.

```toml
[[settings.working_plate]]
type = "reservoir"
labware_id = "tube_rack_96_1500ul"
position_rack = "4"

[[settings.working_plate]]
type = "tip"
labware_id = "opentrons_96_tiprack_300ul"
connection = "Pipette_8"
mode = "multi"
position_rack = "1"
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | yes | `"source"`, `"reservoir"`, `"destination"`, `"tip"`, or `"module"`. |
| `labware_id` | string | usually | Opentrons load name or custom labware ID. Empty is allowed for a module without loaded labware. |
| `position_rack` | string | yes | OT-2 deck slot number. |
| `connection` | string | tip only | Pipette name using this tip rack, for example `Pipette_8`. |
| `mode` | string | tip in dual mode | Tip rack allocation for `multi`, `multi_X1`, or `single_X1`. |
| `offset_x`, `offset_y`, `offset_z` | number | no | Per-entry calibration offset. Overrides `offset_database.toml` for the same labware and slot. |

**Physical OT-2 deck map:**

```text
+-------+-------+-------+
|  10   |  11   | Trash |
+-------+-------+-------+
|   7   |   8   |   9   |
+-------+-------+-------+
|   4   |   5   |   6   |
+-------+-------+-------+
|   1   |   2   |   3   |
+-------+-------+-------+
```

### Heater-Shaker Module Entries

```toml
[[settings.working_plate]]
type = "module"
module_type = "heaterShaker"
position_rack = "10"
adapter_id = "opentrons_universal_flat_adapter"
labware_id = ""
target_temperature = 0
target_shake_speed = 0
persist_after_protocol = true
```

| Field | Type | Description |
|-------|------|-------------|
| `module_type` | string | Currently `"heaterShaker"`. |
| `adapter_id` | string | Adapter loaded on the module. |
| `labware_id` | string | Labware mounted on the adapter, if any. |
| `target_temperature` | number | `0` disables heating; non-zero values request heating. |
| `target_shake_speed` | number | `0` disables shaking; non-zero values request shaking. |
| `persist_after_protocol` | boolean | Keep module state active after the protocol ends. |

Module labware is background-only in the current workflow. Do not reference module labware as a CSV source or destination.

## Pipette Modes

| Mode | Pipette behavior | CSV row behavior |
|------|------------------|------------------|
| `single_X1` | Single-channel pipette | One row is one individual transfer. |
| `multi_X1` | 8-channel pipette in single-nozzle layout | One row is one individual transfer using one nozzle. |
| `multi` | 8-channel pipette using all nozzles | One row is a full column-style transfer. |
| `dual` | Both pipettes available | CSV `Mode` column selects `single_X1`, `multi_X1`, or `multi` per row. |

In `multi` mode, use only compatible 96-well or 384-well geometries. For 96-well plates, row `A` represents the full column. For 384-well plates, `A` and `B` row starts map to the two interleaved 8-channel row groups.

## labware_dict.toml

`labware_dict.toml` defines available pipettes. General labware definitions are no longer stored here; labware is referenced by Opentrons load names or discovered custom JSON definitions.

```toml
[[pipettes]]
name = "Pipette_8"
opentrons_id = "p300_multi_gen2"
channels = 8
volume_range = [30, 300]
preferred_mount = "right"
tip_connections = ["opentrons_96_tiprack_300ul"]
```

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Internal reference name, used by tip rack `connection`. |
| `opentrons_id` | string | Opentrons API pipette identifier. |
| `channels` | integer | Number of channels. |
| `volume_range` | array | `[min, max]` volume in uL. |
| `preferred_mount` | string | `"left"` or `"right"`. |
| `tip_connections` | array | Compatible tip rack labware IDs. |

## offset_database.toml

`offset_database.toml` stores reusable calibration offsets by labware and slot. A direct `offset_x/y/z` on a `settings.working_plate` entry takes precedence over the database entry.

```toml
[[offsets]]
labware_id = "nest_96_wellplate_200ul_flat"
position_rack = "4"
offset_x = -0.50
offset_y = 0.80
offset_z = -0.30
last_calibrated = "2024-01-15"
notes = "Calibrated after replacement"
```

| Field | Type | Description |
|-------|------|-------------|
| `labware_id` | string | Labware identifier. |
| `position_rack` | string | Deck slot number. |
| `offset_x` | number | X adjustment in mm. |
| `offset_y` | number | Y adjustment in mm. |
| `offset_z` | number | Z adjustment in mm. |
| `last_calibrated` | string | Optional date. |
| `notes` | string | Optional free-text note. |

## Environment Variables

### `OPENTRONS_DIR`

Root Opentrons App data directory. The system derives these paths from it:

| Subdirectory | Purpose |
|--------------|---------|
| `{OPENTRONS_DIR}/labware/` | Custom labware JSON definitions used by scanning and simulation. |
| `{OPENTRONS_DIR}/protocols/` | Protocol deployment target with UUID-style Opentrons App folders. |

**Per workflow:**

| Workflow | How to set |
|----------|------------|
| Docker | `OPENTRONS_DIR_HOST` and `OPENTRONS_DIR_MOUNT` in `docker/.env`. |
| MCP server | `OPENTRONS_DIR` in the MCP server environment. |
| GUI | `opentrons_dir_win` in `shell_settings.json`, set through Deck Setup. |
| CLI | Environment variable or explicit command arguments, depending on the command. |

If `OPENTRONS_DIR` is not set, some simulation paths can fall back to `LABWARE_PATH` for custom labware discovery.

### `OT2_PROJECT_DIR`

Optional persistent workspace directory for the MCP server and Docker backend. If unset, the active process working directory is used.

## CSV Transfer Format

### Required Columns

| Column | Description | Example |
|--------|-------------|---------|
| `Source Labware` | Source labware reference in `{labware_id}_{slot}` format | `tube_rack_96_1500ul_4` |
| `Source Well` | Source well | `A1` |
| `Dest Labware` | Destination labware reference in `{labware_id}_{slot}` format | `384_ppv_55ul_2` |
| `Dest Well` | Destination well or pipe-delimited destination list | `B1` |
| `Tip Action` | Per-row tip behavior | `new` |

Each transfer row also needs one volume column:

| Column | Description |
|--------|-------------|
| `Volume (ul)` | Ordinary one-source-to-one-destination transfer volume. |
| `Distribution Volume (ul)` | Per-destination volume for distribution rows. |

Use `Tip Action` consistently. The CSV upload MCP tool requires it, and it is the current mechanism for tip reuse.

### Positioning Columns

Choose one source positioning column and one destination positioning column.

| Column | Description | Example |
|--------|-------------|---------|
| `Source Bottom` | Distance from source well bottom in mm | `2` |
| `Source Top` | Offset from source well top in mm; negative goes down | `-5` |
| `Dest Bottom` | Distance from destination well bottom in mm | `1` |
| `Dest Top` | Offset from destination well top in mm; negative goes down | `-3` |
| `Mix Height` | Mixing height in mm, interpreted at source or destination depending on settings | `2` |

### Optional Columns

| Column | Default | Description |
|--------|---------|-------------|
| `Mix Volume` | `0` | Mix volume in uL. |
| `Flow Aspirate` | `1.0` | Aspiration speed multiplier. |
| `Flow Dispense` | `1.0` | Dispense speed multiplier. |
| `Air Gap` | `0` | Air gap volume in uL after aspiration. |
| `Air Gap Rate` | `1.0` | Air gap aspiration multiplier for ordinary transfer rows. |
| `Distribution` | `equal` | Distribution volume pattern. |
| `Mode` | none | Required in `dual` mode to select the pipette behavior per row. |

### Tip Action

| Value | Behavior |
|-------|----------|
| `new` | Pick up a fresh tip before the transfer. |
| `keep` | Keep using the current tip when possible. |
| `drop` | Drop the tip after the transfer. |

`keep` is not appropriate immediately after a HOME row because homing drops the current tip.

### Distribution Rows

Distribution mode transfers one source well to multiple destination wells in one operation.

A row is treated as distribution when `Dest Well` contains `|` or when `Distribution Volume (ul)` is populated.

| Column | Description | Example |
|--------|-------------|---------|
| `Dest Well` | Pipe-delimited destination wells | `A1|B1|C1|D1` |
| `Distribution Volume (ul)` | Volume per destination well | `10` |
| `Distribution` | Pattern | `equal`, `geometric:2.0`, `geometric:2.0:desc` |

**Important constraints:**
- Use `Distribution Volume (ul)` for distribution rows.
- Destination mixing is not supported for distribution rows because the Opentrons `distribute()` API ignores destination `mix_after`.
- `Air Gap` can be used; `Air Gap Rate` is only meaningful for ordinary transfer rows.
- In `multi` mode, pipe-delimited destination wells must be compatible with the 8-channel row group.

### HOME Control Rows

Insert a row where all non-empty columns contain `HOME` to trigger `protocol.home()` mid-protocol.

Rules:
- HOME is case-insensitive.
- The robot drops any held tip before homing.
- The transfer row immediately after HOME must use `Tip Action: new`.
- The MCP tool `ot2_insert_home_rows` can insert HOME rows and force the following `Tip Action` values to `new`.

### Dual Mode Column

When `settings.general.mode = "dual"`, the CSV needs a `Mode` column.

| Value | Meaning |
|-------|---------|
| `single_X1` | Use the single-channel pipette. |
| `multi_X1` | Use one nozzle of the 8-channel pipette. |
| `multi` | Use all nozzles of the 8-channel pipette. |

Each `Mode` value should have a matching tip rack entry in `settings.working_plate`.
