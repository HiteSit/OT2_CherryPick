/**
 * Help text extracted from USER_TUTORIAL.md
 * Provides inline documentation for UI tooltips and help sections
 */

export const HELP_TEXT = {
  mode: {
    single_X1: "Single-channel pipette - one transfer at a time. Maximum flexibility for cherry-picking.",
    multi_X1: "8-channel pipette in single-tip mode. Cherry-picking with multi-channel hardware. Uses only one tip (configured by starting_tip_well).",
    multi: "8-channel pipette, full 8-tip operation. Each CSV row = 8 simultaneous transfers (entire column). Only works with 96-well and 384-well plates.",
    dual: "Two pipettes (Pipette_1 on left, Pipette_8 on right). CSV 'Mode' column controls which pipette/mode handles each transfer (multi, multi_X1, single_X1)."
  },

  startingTipWell: `Specifies which tip position on the 8-channel pipette to use when operating in multi_X1 mode.

Valid values: Only "A1" or "H1" make sense due to physical geometry:
• H1 (recommended): Uses the last/bottom tip - easier to see and access
• A1: Uses the first/top tip

Physical deck position constraint:
• Front row slots (1, 2, 3): Use "H1" (back tip)
• Back row slots (7, 8, 9): Use "A1" (front tip)
• Middle row slots (4, 5, 6): Either works, "H1" recommended

Note: This setting only matters in multi_X1 mode - ignored in single_X1 and multi modes.`,

  headSpeed: `Movement speed in mm/min (100-600). Default 400 is recommended for most applications.

When to reduce (200-300 mm/min): Working with very slippery or volatile solvents (chloroform, hexane, organic solvents) that tend to leak or drip from the pipette tip during movement. Slower movement reduces vibration and sudden accelerations that cause droplets to escape.

For standard aqueous solutions, the default speed of 400 mm/min should not be changed.`,

  preAspirateContact: {
    enabled: "Touch liquid surface and optionally pre-wet tip before aspirating target volume",
    positionOffsetPercent: `Safety margin for the contact position. The robot moves to a safer position than the CSV-specified aspiration height:
• For Source Height (bottom positioning): Adds 20% more height
• For Source Top (top positioning): Moves 20% closer to top`,
    aspirateVolume: "Volume in µL to aspirate and dispense back for tip conditioning. Set to 0 for position touch only (no pre-wet). Pre-wetting coats inner tip surface with liquid - critical for high surface tension or hydrophobic liquids."
  },

  postAspirateWick: {
    enabled: "After aspirating liquid, touch the inside wall of the well to remove droplets hanging from the outside of the tip. Prevents inaccurate volume delivery, cross-contamination, or dripping during transport.",
    radius: "How far from center to touch, as a fraction of the well radius (0.0 = center, 1.0 = wall edge). Default 0.8 touches near the wall without hitting it.",
    vOffsetMm: "Height relative to well top in millimeters (negative = below rim). Default -1.5mm positions the touch point slightly below the well's top edge.",
    speed: "Touch speed in mm/s. Default 20 mm/s provides gentle contact."
  },

  delays: {
    postAspirate: `Wait time after aspiration (seconds). Pauses after aspirating liquid to allow the liquid column inside the tip to stabilize before moving.

Recommended values:
• Water/buffers: 0 seconds
• DMSO/glycerol: 2-3 seconds
• Oils/very viscous: 3-5 seconds

Rationale: Viscous liquids continue flowing into tip briefly after plunger stops due to viscous flow lag, surface tension effects, and air pressure equilibration.`
  },

  pushOut: {
    enabled: "After dispensing target volume, push out additional air to expel residual liquid. Mimics the 'second stop' on manual pipettes.",
    volumeUl: `Fixed air volume in µL to push after dispense. Default 5µL works for most applications.

Recommended values:
• 3-5µL: Most applications
• 8-10µL: Very viscous liquids
• Don't exceed 10µL (can cause splashing)

Not used when mixing follows dispense (mixing already agitates sufficiently).`
  },

  mixing: {
    enabled: "Master switch to enable/disable mixing functionality. When disabled, all mixing parameters are ignored regardless of other settings. Note: In distribution mode, destination mixing is NOT supported by the Opentrons API - use cherry-pick mode if per-destination mixing is required.",
    location: "Where to perform mixing: at destination well after dispense, at source well before aspiration, or no mixing",
    repetitions: "Number of times to aspirate and dispense for mixing (1-10 typical)",
    sourceRemixing: "When mixing at source: 'once' = mix only on first visit to that well, 'always' = mix every time"
  },

  csvColumns: {
    required: {
      sourceLabware: "Labware ID + slot number (e.g., 'tube_rack_96_1500ul_4'). Must match a labware instance defined in settings.toml",
      sourceWell: "Well position in source labware (e.g., 'A1', 'H12'). Case-sensitive, must be uppercase.",
      volumeUl: "Transfer volume in microliters. Must be within pipette volume range.",
      destLabware: "Destination labware ID + slot (e.g., '384_ppv_55ul_2'). Must match a labware instance defined in settings.toml",
      destWell: "Well position in destination labware (e.g., 'B1', 'P24'). Case-sensitive, must be uppercase."
    },

    heightColumns: `Choose ONE for source (never both), and ONE for destination (never both):

Source Height: Distance from well bottom (mm). Use when you know liquid depth. Example: 2, 5.5, 10

Source Top: Distance from well top (mm, negative goes down). Use when avoiding foam/meniscus. Example: -5, -2.0, -10

Dest Height: Distance from well bottom (mm). Use for dispensing at specific depth. Example: 1, 2.5

Dest Top: Distance from well top (mm, negative goes down). Use when avoiding splashing. Example: -3, -7.5

Best practice: Use consistent heights for same labware type throughout CSV. All wells in same labware have identical geometry.`,

    optional: {
      mixVolume: "Volume to mix after dispense (µL). Default 0 = no mixing. Typical: 20-50µL",
      mixHeight: "Mixing height from bottom (mm). Default 2.0mm. Should be low enough to ensure mixing without splashing.",
      flowAspirate: "Aspiration speed multiplier. Default 1.0 = normal. Use 0.5 for slow (viscous), 1.5 for fast.",
      flowDispense: "Dispense speed multiplier. Default 1.0 = normal. Use 0.8 for slow (gentle), 2.0 for fast.",
      airGap: "Air gap volume to prevent dripping (µL). Default 0. Typical: 5-20µL for preventing cross-contamination during transport.",
      airGapRate: "Air gap aspiration speed multiplier. Default 1.0.",
      tipAction: "Override tip management: 'new' = get fresh tip, 'keep' = reuse current tip, 'drop' = drop tip after this transfer. REQUIRED column - must specify for every transfer."
    }
  },

  deckSlots: `OT-2 Deck Layout:
┌─────┬─────┬─────┬─────┐
│ 10  │  11 │ Trash│     │
├─────┼─────┼─────┤     │
│  7  │  8  │  9  │     │
├─────┼─────┼─────┼─────┘
│  4  │  5  │  6  │
├─────┼─────┼─────┤
│  1  │  2  │  3  │
└─────┴─────┴─────┘

Slots 1-11 are available for labware placement. Slot 12 is the fixed trash bin.`,

  labwareCalibration: `Labware calibration offsets are three-dimensional position adjustments (in millimeters) that fine-tune where the pipette moves relative to each labware.

Coordinate System:
• X-axis: Negative = left, Positive = right
• Y-axis: Negative = front, Positive = back
• Z-axis: Negative = down, Positive = up

Why they're critical: Small variations occur due to manufacturing tolerances, deck positioning, thermal expansion, and wear. These tiny misalignments cause tips crashing into well edges, liquid dispensed onto edges, incomplete aspiration, or cross-contamination.

IMPORTANT: Offsets are position-dependent! The same labware in different deck slots may require different calibration offsets.

Recommended approach: Use Opentrons App Labware Position Check during protocol setup to calibrate each labware instance interactively. The robot saves offsets tied to specific labware type + deck slot + robot, and can reuse them across protocols (v6.0.0+).

Alternative (use with caution): Define offsets in labware_dict.toml. These apply to ALL instances of that labware type regardless of position, and ALWAYS override machine calibration.`
} as const

export type HelpTextKey = keyof typeof HELP_TEXT
