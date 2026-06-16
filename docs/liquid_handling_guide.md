# Liquid Handling Guide

How to configure liquid handling parameters for accurate and reproducible transfers on the OT-2.

## Presets

Presets apply a coordinated set of liquid handling parameters optimized for specific liquid types. Apply them via the GUI (Configuration step), MCP tool (`ot2_apply_liquid_preset`), or by editing `settings.toml` directly.

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

Viscous liquids flow slowly and cling to surfaces. The 2-second delay allows the liquid column to stabilize inside the tip after the plunger stops. Push-out expels residual liquid that surface tension holds inside the tip. Extra mixing repetitions ensure homogeneous dispensing.

## Parameter Reference

### Pre-Aspirate Contact

```toml
[settings.liquid_handling.pre_aspirate_contact]
enabled = false
position_offset_percent = 20
aspirate_volume = 0
```

**What it does:** Before the main aspiration, the pipette descends to touch the liquid surface and optionally aspirates a small pre-wetting volume.

**Why it matters:**
- **Pre-wetting** (`aspirate_volume > 0`) coats the inner tip surface with liquid. The first aspiration into a dry tip is often inaccurate because liquid evaporates from the tip walls and adheres to dry plastic. Pre-wetting "primes" the tip for consistent volumes.
- **Contact only** (`aspirate_volume = 0`) detects the liquid surface to confirm proper positioning.

**When to use:**
- Pre-wetting: High surface tension liquids, hydrophobic solutions, or when maximum accuracy is needed for small volumes
- Contact only: General positioning verification

### Post-Aspirate Wicking

```toml
[settings.liquid_handling.post_aspirate_wick]
enabled = true
radius = 1
v_offset_mm = -1.5
speed = 20
```

**What it does:** After aspirating, the tip touches the inside wall of the well to wipe off external droplets.

**Why it matters:** Droplets clinging to the outside of the tip cause:
- Inaccurate volume delivery (liquid outside the tip does not dispense correctly)
- Cross-contamination (droplets can fall off during gantry movement)
- Dripping onto the deck or other wells

This mimics the manual technique of touching a pipette tip to the side of a vessel after aspirating.

**Parameters:**
- `radius` -- How close to the wall (larger = closer). A value of 1 mm works for most well sizes.
- `v_offset_mm` -- Height relative to the well top. Negative values position the touch below the rim to ensure contact with the wall, not the rim edge.
- `speed` -- Slow speeds (10-20 mm/s) give better wicking contact.

### Post-Aspirate Delay

```toml
[settings.liquid_handling.delays]
post_aspirate = 0
```

**What it does:** Pauses for the specified number of seconds after the plunger finishes aspirating, before the tip moves.

**Why it matters:** In viscous liquids, liquid continues flowing into the tip after the plunger stops due to:
- Viscous flow lag (thick liquids respond slowly to pressure changes)
- Surface tension pulling liquid upward into the tip
- Air pressure equilibration between the liquid and the plunger

Without a delay, moving the tip prematurely can leave behind liquid that was still in transit, reducing the aspirated volume.

**Recommended values:**

| Liquid Type | Delay |
|-------------|-------|
| Water, PBS, buffers | 0 s |
| DMSO, glycerol | 2-3 s |
| Oils, very viscous solutions | 3-5 s |

### Push-Out Volume

```toml
[settings.liquid_handling.push_out]
enabled = true
volume_ul = 5
```

**What it does:** After dispensing the target volume, pushes an additional volume of air through the tip to expel residual liquid.

**Why it matters:** This mimics pressing a manual pipette to the "second stop." Viscous liquids and small volumes cling to the tip interior due to surface tension and adhesion. The extra air push ensures complete delivery.

**Guidelines:**
- 3-5 uL: Suitable for most applications
- 8-10 uL: Very viscous liquids (glycerol, concentrated PEG)
- Do not exceed 10 uL (can cause splashing in small wells)

**Note:** Push-out is automatically skipped when mixing follows the dispense, since repeated aspiration/dispense cycles during mixing already clear residual liquid.

### Mixing

```toml
[settings.liquid_handling.mixing]
enabled = true
location = "destination"
repetitions = 3
source_remixing = "once"
```

**What it does:** After dispensing, repeatedly aspirates and dispenses at the specified location to homogenize the liquid.

**Parameters:**
- `location` -- `"destination"` mixes in the destination well (most common). `"source"` mixes in the source well (useful for cell suspensions that settle). `"none"` disables mixing.
- `repetitions` -- Number of aspirate/dispense cycles. 3 is adequate for aqueous solutions; use 5+ for viscous liquids.
- `source_remixing` -- `"once"` re-mixes the source on the first aspiration only. `"always"` re-mixes before every aspiration. Essential for cell suspensions or solutions with particles that settle between transfers.

**When to use source mixing:**
- Cell suspensions (cells settle within seconds)
- Bead-based assays
- Any heterogeneous solution where components separate over time

## Choosing Parameters by Liquid Type

| Liquid | Preset | Key Adjustments |
|--------|--------|-----------------|
| Water, PBS | Standard | Defaults work well |
| Cell media | Standard | Enable source remixing if cells present |
| DMSO | Viscous | Defaults work well |
| Glycerol (>50%) | Viscous | Increase delay to 3-5 s |
| Mineral oil | Viscous | Increase delay to 3-5 s, push-out to 8 uL |
| Chloroform, hexane | Custom | Reduce head speed to 200, use pre-wetting, slow flow rates |
| Ethanol, acetone | Custom | Reduce head speed to 200-300, volatile liquids evaporate quickly |

For volatile or slippery solvents, there is no built-in preset. Reduce `head_speed` to 200-300 mm/min to minimize dripping during movement, and use slow flow rate multipliers (0.3-0.5) in the CSV.
