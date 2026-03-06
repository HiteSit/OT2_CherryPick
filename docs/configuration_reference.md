# Configuration Reference

Complete reference for all configuration files in the OT2 CherryPick system.

## settings.toml

The main protocol configuration file. Controls pipette mode, tip management, liquid handling parameters, and deck layout.

### General Settings

```toml
[settings.general]
protocol_name = "CherryPick_Protocol"
mode = "single_X1"
starting_tip_well = "A1"
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `protocol_name` | string | `"CherryPick_Protocol"` | Name embedded in the generated protocol |
| `mode` | string | `"single_X1"` | Pipette mode (see [Pipette Modes](#pipette-modes)) |
| `starting_tip_well` | string | `"A1"` | First tip position to use |

#### Head Speed

```toml
[settings.general.head_speed]
speed = 400
```

| Field | Type | Default | Range | Description |
|-------|------|---------|-------|-------------|
| `speed` | integer | `400` | 100-600 | Gantry movement speed in mm/min |

Reduce to 200-300 for volatile or slippery solvents (chloroform, hexane) that may drip during fast movement.

### Liquid Handling

```toml
[settings.liquid_handling]
active_preset = "standard"
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `active_preset` | string | `"standard"` | Active liquid preset name |

#### Pre-Aspirate Contact

```toml
[settings.liquid_handling.pre_aspirate_contact]
enabled = false
position_offset_percent = 20
aspirate_volume = 0
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | boolean | `false` | Touch liquid surface before aspirating |
| `position_offset_percent` | integer | `20` | Offset from well center (%) |
| `aspirate_volume` | number | `0` | Pre-wet volume in uL (0 = contact only) |

#### Post-Aspirate Wicking

```toml
[settings.liquid_handling.post_aspirate_wick]
enabled = true
radius = 1
v_offset_mm = -1.5
speed = 20
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | boolean | `true` | Touch well wall after aspirating to remove droplets |
| `radius` | number | `1` | Touch radius in mm (larger = closer to wall) |
| `v_offset_mm` | number | `-1.5` | Height relative to well top (negative = below rim) |
| `speed` | number | `20` | Touch speed in mm/s |

#### Delays

```toml
[settings.liquid_handling.delays]
post_aspirate = 0
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `post_aspirate` | number | `0` | Wait time after aspiration in seconds |

Recommended: 0s for water/buffers, 2-3s for DMSO/glycerol, 3-5s for oils.

#### Push-Out

```toml
[settings.liquid_handling.push_out]
enabled = true
volume_ul = 5
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | boolean | `true` | Push extra air to expel residual liquid |
| `volume_ul` | number | `5` | Push-out volume in uL (recommended 3-10) |

Not applied when mixing follows dispense.

#### Mixing

```toml
[settings.liquid_handling.mixing]
enabled = true
location = "destination"
repetitions = 3
source_remixing = false
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | boolean | `true` | Enable post-dispense mixing |
| `location` | string | `"destination"` | Where to mix: `"source"`, `"destination"`, or `"none"` |
| `repetitions` | integer | `3` | Number of mix cycles |
| `source_remixing` | string | `"once"` | Re-mix source: `"once"` (first aspiration only) or `"always"` (every aspiration) |

#### Presets

Presets are defined inline in settings.toml under `[settings.liquid_handling.presets.*]`. See the [Liquid Handling Guide](liquid_handling_guide.md) for details on each preset.

### Deck Layout (Working Plate Array)

```toml
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

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | yes | `"source"`, `"reservoir"`, `"destination"`, `"tip"`, or `"module"` |
| `labware_id` | string | yes | Labware identifier (must match Opentrons load name or labware catalog) |
| `position_rack` | string | yes | Deck slot number (1-11, must be unique) |
| `connection` | string | tip only | Pipette name this tip rack is assigned to |
| `mode` | string | no | For dual mode: which pipette uses this labware |
| `module_type` | string | module only | Module type (`"heaterShaker"`) |
| `adapter_id` | string | module only | Adapter loaded on the module |
| `target_temperature` | number | module only | Target temperature in °C (0 = disabled, min 30°C when enabled) |
| `target_shake_speed` | number | module only | Target shake speed in RPM (0 = disabled, range 200-3000) |
| `persist_after_protocol` | boolean | module only | Keep module running after protocol ends |
| `offset_x/y/z` | number | no | Per-slot offset override (takes precedence over offset_database.toml) |

**Deck slot map:**
```
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

## Pipette Modes

| Mode | Pipette | Tips Active | CSV Row Behavior |
|------|---------|-------------|------------------|
| `single_X1` | Single-channel | 1 | 1 row = 1 individual transfer |
| `multi_X1` | 8-channel (single nozzle via `SINGLE` layout, start `H1`) | 1 | 1 row = 1 individual transfer |
| `multi` | 8-channel (all nozzles) | 8 | 1 row = full column transfer (A1 means A1-H1) |
| `dual` | Both pipettes | Per-row | CSV `Mode` column selects which pipette per transfer |

**Note:** `multi` mode only works with 96-well and 384-well plates.

## labware_dict.toml

Defines available pipettes. Labware calibration offsets are now stored separately in `offset_database.toml`.

### Pipette Definitions

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
| `name` | string | Internal reference name (used in `connection` field of tip racks) |
| `opentrons_id` | string | Opentrons API pipette identifier |
| `channels` | integer | Number of channels (1 or 8) |
| `volume_range` | array | `[min, max]` volume in uL |
| `preferred_mount` | string | `"left"` or `"right"` |
| `tip_connections` | array | List of compatible tip rack labware IDs |

## offset_database.toml

Per-labware, per-slot calibration offsets. Managed via MCP tools or the GUI.

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
| `labware_id` | string | Labware identifier |
| `position_rack` | string | Deck slot number |
| `offset_x` | number | X adjustment in mm (negative = left, positive = right) |
| `offset_y` | number | Y adjustment in mm (negative = front, positive = back) |
| `offset_z` | number | Z adjustment in mm (negative = down, positive = up) |
| `last_calibrated` | string | Date of last calibration (optional) |
| `notes` | string | Free-text notes (optional) |

## Environment Variables

### `OPENTRONS_DIR`

The single root directory for Opentrons App data. The system auto-derives subdirectories from it:

| Subdirectory | Purpose |
|--------------|---------|
| `{OPENTRONS_DIR}/labware/` | Custom labware JSON definitions (used by simulation and labware scanning) |
| `{OPENTRONS_DIR}/protocols/` | Protocol deployment target (auto-UUID directories) |

**Expected directory structure:**
```
{OPENTRONS_DIR}/
├── labware/              ← Custom labware JSON files
│   ├── my_custom_plate.json
│   └── ...
└── protocols/            ← Protocol directories (one per import)
    ├── {uuid-1}/
    │   ├── src/
    │   │   └── CherryPick_OT2.py
    │   └── analysis/
    │       └── {timestamp_ms}.json
    └── {uuid-2}/
        └── ...
```

**Configuration per workflow:**

| Workflow | How to set |
|----------|-----------|
| Docker | `OPENTRONS_DIR_HOST` / `OPENTRONS_DIR_MOUNT` in `.env` |
| MCP server | `OPENTRONS_DIR` env var in MCP config (`.mcp.json` or `claude_desktop_config.json`) |
| GUI | Single `opentrons_dir_win` field in shell settings (Windows path, auto-converted to WSL) |
| CLI script | Hardcoded paths in `simulate_protocol.sh` |

**Legacy fallback:** If `OPENTRONS_DIR` is not set, the simulation tool falls back to the `LABWARE_PATH` environment variable for custom labware location.

### `OT2_PROJECT_DIR`

Optional. Sets the persistent workspace directory for the MCP server. When not set, the server uses the current working directory.

## CSV Transfer Format

### Required Columns

| Column | Description | Example |
|--------|-------------|---------|
| `Source Labware` | Labware ID + slot | `tube_rack_96_1500ul_4` |
| `Source Well` | Well position | `A1`, `H12` |
| `Volume (ul)` | Transfer volume | `50`, `100.5` |
| `Dest Labware` | Labware ID + slot | `384_ppv_55ul_2` |
| `Dest Well` | Destination well | `B1`, `P24` |

Labware references use the format `{labware_id}_{slot_number}`.

### Positioning Columns

Choose **one** per source and **one** per destination. Using both Height and Top for the same end causes an error.

| Column | Description | Example |
|--------|-------------|---------|
| `Source Bottom` | Distance from well bottom (mm) | `2`, `5.5` |
| `Source Top` | Distance from well top (mm, negative = below rim) | `-5`, `-2.0` |
| `Dest Bottom` | Distance from well bottom (mm) | `1`, `2.5` |
| `Dest Top` | Distance from well top (mm, negative = below rim) | `-3`, `-7.5` |
| `Mix Height` | Mixing height from bottom (mm) | `1.5`, `3.0` |

### Optional Columns

| Column | Default | Description |
|--------|---------|-------------|
| `Mix Volume` | `0` | Volume to mix after dispense (uL). 0 = no mixing. |
| `Flow Aspirate` | `1.0` | Aspiration speed multiplier (0.5 = half speed, 2.0 = double) |
| `Flow Dispense` | `1.0` | Dispense speed multiplier |
| `Air Gap` | `0` | Air gap volume after aspiration (uL), prevents dripping |
| `Air Gap Rate` | `1.0` | Air gap aspiration speed multiplier |

### Tip Management Column

| Column | Default | Description |
|--------|---------|-------------|
| `Tip Action` | auto | Per-row override: `new` (pick up), `keep` (reuse), `drop` (return) |

When omitted, tip behavior follows the global `tip_reuse` setting.

### Distribution Columns

The system supports **distribution mode**: transferring from one source well to multiple destination wells in a single operation using the Opentrons `pipette.distribute()` API.

A row is treated as a distribution row if `|` appears in `Dest Well` or the `Distribution Volume (ul)` column has a value.

| Column | Description | Example |
|--------|-------------|---------|
| `Dest Well` | Pipe-delimited destinations | `A1\|B1\|C1\|D1` |
| `Distribution Volume (ul)` | Volume per destination well (replaces `Volume (ul)`) | `10` |
| `Distribution` | Volume pattern (optional) | `equal`, `geometric:2.0`, `geometric:2.0:desc` |

**Volume patterns:**
- `equal` (default) — Same volume to each destination
- `geometric:factor` — Each well gets `factor` times the previous (ascending)
- `geometric:factor:desc` — Descending geometric series

### HOME Control Rows

Insert a row where **all non-empty columns contain `HOME`** (case-insensitive) to trigger a mid-protocol `protocol.home()` call. This re-homes all robot axes to correct positional drift during long runs.

**Rules:**
- The robot drops any held tip before homing (firmware requirement)
- The row **immediately after** a HOME row must have `Tip Action: new`
- Use periodically in overnight protocols with hundreds of transfers

### Dual Mode Column

| Column | Description |
|--------|-------------|
| `Mode` | Which pipette to use for this row: `single_x1`, `multi`, or `multi_x1` (required in `dual` mode) |
