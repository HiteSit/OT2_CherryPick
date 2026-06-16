# Liquid Handling Guide

How to configure liquid handling parameters for accurate and reproducible transfers on the OT-2.

## Presets

Presets apply a coordinated set of liquid-handling parameters. Apply them in the GUI Configuration step, with the MCP tool `ot2_apply_liquid_preset`, or by editing `settings.toml`.

The default template includes two built-in presets:

| Preset | Use for |
|--------|---------|
| `standard` | Water, PBS, buffers, cell media, and other aqueous solutions |
| `viscous` | DMSO, glycerol, oils, PEG solutions, and other high-viscosity liquids |

The GUI can save custom presets under `[settings.liquid_handling.presets.<name>]`. When `active_preset` is set, the runtime uses that preset's values instead of the individual liquid-handling fields. When `active_preset = ""`, the individual fields are used as written.

There is no built-in volatile/slippery preset in the default template. For chloroform, hexane, ethanol, acetone, or other volatile/drip-prone solvents, use custom settings: lower head speed, optional pre-wetting, and slower CSV flow-rate multipliers.

### Standard Preset

**For:** Water, PBS, buffers, cell media, and other aqueous solutions.

| Parameter | Value |
|-----------|-------|
| Pre-aspirate contact | enabled |
| Pre-aspirate volume | 0 uL (contact only) |
| Post-aspirate wicking | enabled |
| Post-aspirate delay | 0 s |
| Push-out | disabled |
| Mixing | enabled, 3 repetitions, destination |

Aqueous liquids have low viscosity and moderate surface tension. They aspirate cleanly, but external droplets can form on the tip. Wicking removes these droplets. No delay or push-out is needed since the liquid flows freely.

### Viscous Preset

**For:** DMSO, glycerol, oils, PEG solutions, and other high-viscosity liquids.

| Parameter | Value |
|-----------|-------|
| Pre-aspirate contact | enabled |
| Pre-aspirate volume | 0 uL |
| Post-aspirate wicking | enabled |
| Post-aspirate delay | 2 s |
| Push-out | enabled, 5 uL |
| Mixing | enabled, 5 repetitions, destination |

Viscous liquids flow slowly and cling to surfaces. The delay allows the liquid column to stabilize inside the tip after the plunger stops. Push-out expels residual liquid that surface tension holds inside the tip. Extra mixing repetitions improve homogeneity after dispensing.

## Parameter Reference

### Pre-Aspirate Contact

```toml
[settings.liquid_handling.pre_aspirate_contact]
enabled = false
position_offset_percent = 20
aspirate_volume = 20
```

**What it does:** Before the main aspiration, the pipette descends to touch the liquid surface and can optionally aspirate a small pre-wetting volume.

**Why it matters:**
- **Pre-wetting** (`aspirate_volume > 0`) coats the inside of the tip. This helps with liquids that cling to dry plastic or evaporate quickly.
- **Contact only** (`aspirate_volume = 0`) touches the liquid without pre-wetting.

**When to use:**
- Pre-wetting: high surface tension liquids, hydrophobic solutions, volatile solvents, or small-volume precision work.
- Contact only: aqueous transfers where the goal is clean positioning without extra aspirate/dispense steps.

### Post-Aspirate Wicking

```toml
[settings.liquid_handling.post_aspirate_wick]
enabled = false
radius = 1
v_offset_mm = -1.5
speed = 20
```

**What it does:** After aspirating, the tip touches the inside wall of the source well to wipe off external droplets.

**Why it matters:** Droplets clinging to the outside of the tip can cause inaccurate delivery, cross-contamination, or dripping during travel.

**Parameters:**
- `radius` -- How close to the wall the touch-tip motion goes.
- `v_offset_mm` -- Height relative to the well top. Negative values position the touch below the rim.
- `speed` -- Slow speeds, often 10-20 mm/s, give better wicking contact.

### Post-Aspirate Delay

```toml
[settings.liquid_handling.delays]
post_aspirate = 0
```

**What it does:** Pauses after aspiration before the tip moves.

**Why it matters:** In viscous liquids, liquid can continue moving into the tip after the plunger stops. A short delay lets the liquid column stabilize.

**Recommended starting values:**

| Liquid Type | Delay |
|-------------|-------|
| Water, PBS, buffers | 0 s |
| DMSO, glycerol | 2-3 s |
| Oils, very viscous solutions | 3-5 s |

### Push-Out Volume

```toml
[settings.liquid_handling.push_out]
enabled = true
volume_ul = 20
```

**What it does:** After dispensing the target volume, pushes additional air through the tip to expel residual liquid.

**Why it matters:** Viscous liquids and small volumes can remain inside the tip. Push-out is similar to pressing a manual pipette to the second stop.

**Guidelines:**
- 3-5 uL: gentle push-out for common viscous workflows.
- 8-10 uL: stronger push-out for very viscous liquids.
- Higher values should be tested carefully in small wells to avoid splashing.

**Note:** Push-out is skipped when mixing follows the dispense, since repeated aspiration/dispense cycles during mixing already clear residual liquid.

### Mixing

```toml
[settings.liquid_handling.mixing]
enabled = false
location = "destination"
repetitions = 2
source_remixing = "once"
```

**What it does:** Repeatedly aspirates and dispenses at the selected location when the CSV row provides `Mix Volume`.

**Parameters:**
- `enabled` -- Master switch for mixing.
- `location` -- `"destination"` mixes after dispensing, `"source"` mixes before aspirating, and `"none"` ignores CSV mix columns.
- `repetitions` -- Number of aspirate/dispense cycles.
- `source_remixing` -- `"once"` mixes each source well only on first use; `"always"` mixes before every aspiration from that source.

**When to use source mixing:**
- Cell suspensions.
- Bead-based assays.
- Any source that settles or separates faster than the run consumes it.

**Distribution limitation:** Destination mixing is not supported for distribution rows because the Opentrons `distribute()` API does not honor destination `mix_after`. For distribution workflows, use source mixing, disable mixing, or use ordinary cherry-pick rows.

## Choosing Parameters by Liquid Type

| Liquid | Starting point | Key adjustments |
|--------|----------------|-----------------|
| Water, PBS | `standard` preset | Defaults usually work well. |
| Cell media | `standard` preset | Use source mixing if cells are suspended. |
| DMSO | `viscous` preset | Defaults usually work well. |
| Glycerol over 50% | `viscous` preset | Increase delay to 3-5 s; test push-out. |
| Mineral oil | `viscous` preset | Increase delay and push-out cautiously. |
| Chloroform, hexane | Custom | Lower head speed, use pre-wetting, slow flow rates. |
| Ethanol, acetone | Custom | Lower head speed and minimize exposed time. |

CSV flow-rate multipliers (`Flow Aspirate`, `Flow Dispense`, and for ordinary rows `Air Gap Rate`) are useful when the same global settings need row-specific tuning.
