"""MCP workflow prompts for guided OT-2 protocol setup and optimization.

This module provides workflow prompts:
1. setup_new_experiment - Complete project setup from initialization to deployment
2. optimize_liquid_handling - Problem-driven liquid handling parameter optimization
3. switch_project - Guide for switching between project directories
"""

from __future__ import annotations

from fastmcp import FastMCP

__all__ = ["register_prompts"]


def register_prompts(mcp: FastMCP) -> None:
    """Register workflow guidance prompts with the FastMCP application."""

    @mcp.prompt(
        name="setup_new_experiment",
        description="Step-by-step guide for setting up a new OT-2 cherry-pick experiment from scratch"
    )
    def setup_experiment_prompt() -> str:
        return """I'll guide you through setting up a complete OT-2 cherry-pick experiment from start to finish.

## 📋 Workflow Overview

We'll go through these steps systematically:
1. **Initialize Project** - Create workspace with template files
2. **Characterize Experiment** - Define liquid types, volumes, labware
3. **Configure Liquid Handling** - Set parameters based on your liquid type
4. **Define Deck Layout** - Assign labware to deck slots
5. **Create Transfer Map** - Generate and fill CSV template
6. **Validate Configuration** - Pre-flight checks before generation
7. **Generate Protocol** - Compile TOML + CSV into executable protocol
8. **Simulate & Deploy** - Test with opentrons_simulate, then deploy

---

## Step 1: Initialize Project

First, let's create your project workspace:

**Action:** I'll run `ot2_initialize_project()` to create:
- `settings.toml` (protocol configuration)
- `labware_dict.toml` (hardware definitions)
- `CherryPick_OT2.py` (protocol template)
- `CSVs/` directory (for transfer maps)

**Status Check:** After initialization, I'll use `ot2_get_project_directory()` to confirm workspace location.

---

## Step 2: Characterize Your Experiment

Please tell me about your experiment:

**Questions I'll ask:**
1. **What liquid are you transferring?**
   - Standard aqueous (water, PBS, media)
   - Viscous (DMSO, glycerol, oils)
   - Volatile/slippery (chloroform, hexane, organic solvents)
   - Cell suspensions or bead slurries
   - Other (describe)

2. **What volume range?**
   - Very small (<5 µL)
   - Small (5-100 µL)
   - Medium (100-500 µL)
   - Large (>500 µL)

3. **What labware will you use?**
   - Source: (e.g., tube rack, reservoir, plate type)
   - Destination: (e.g., 96-well, 384-well, plate type)
   - Tips: (volume range needed)

**Reference:** I'll consult `guide/USER_TUTORIAL.md` and `guide/EXAMPLES.md` to find similar use cases.

---

## Step 3: Configure Liquid Handling Parameters

Based on your liquid type, I'll recommend specific parameters:

**For standard aqueous liquids:**
```
✓ Enable post-aspirate tip wicking (prevent cross-contamination)
✓ Minimal delays (liquids flow quickly)
✓ No push-out needed (water-like viscosity)
```

**For viscous liquids (DMSO, glycerol):**
```
✓ Enable post-aspirate delays (2-3 seconds for settling)
✓ Enable push-out volume (5-10 µL to expel residual)
✓ Reduce head speed (200-300 mm/min to prevent dripping)
✓ Enable tip wicking
```

**For volatile/slippery liquids:**
```
✓ Enable pre-aspirate contact with pre-wet volume (5-10 µL)
✓ Reduce head speed (200 mm/min to prevent vibration)
✓ Recommend Air Gap in CSV (10-20 µL)
✓ Enable tip wicking
```

**For cell suspensions/beads:**
```
✓ Set mixing.location = "source" (mix before aspirating)
✓ Increase mixing repetitions (5-7 cycles)
✓ Use source_remixing = "once" (remix each source well first time only)
```

**Actions:** I'll use `ot2_update_settings()` to configure each parameter individually:
- Example: `ot2_update_settings(path="settings.liquid_handling.delays.post_aspirate", value="2.5")`

**Verification:** Use `status://liquid-handling-config` to see active parameters.

---

## Step 4: Define Deck Layout

I'll guide you through deck slot assignment:

**OT-2 Deck Map:**
```
┌─────┬─────┬─────┬─────┐
│ 10  │  11 │ Trash│     │
├─────┼─────┼─────┤     │
│  7  │  8  │  9  │     │
├─────┼─────┼─────┼─────┘
│  4  │  5  │  6  │
├─────┼─────┼─────┤
│  1  │  2  │  3  │
└─────┴─────┴─────┘
```

**Configuration:**
1. Source labware → slot assignment
2. Destination labware → slot assignment
3. Tip racks → slot assignments (connect to correct pipette)

**Actions:** Use `ot2_update_settings()` for working_plate array:
- `ot2_update_settings(path="settings.working_plate[0].position_rack", value="4")`
- `ot2_update_settings(path="settings.working_plate[1].position_rack", value="2")`

**Verification:** Use `status://deck-layout` to visualize current deck configuration.

---

## Step 5: Create Transfer Map (CSV)

I'll generate a CSV template with proper structure:

**Action:** `ot2_generate_csv_template(csv_path="CSVs/experiment.csv", transfers=100, ...)`

**CSV Columns Generated:**
- `Source Labware` - Reference to source (format: `labware_id_slot`)
- `Source Well` - Well position (e.g., A1, H12)
- `Volume (ul)` - Transfer volume
- `Dest Labware` - Reference to destination
- `Dest Well` - Destination well
- `Source Height` OR `Source Top` - Pipette height (choose one!)
- `Dest Top` - Destination height

**Optional columns you can add:**
- `Mix Volume` - Volume to mix (µL)
- `Flow Aspirate` - Speed multiplier (0.5=slow, 1.5=fast)
- `Flow Dispense` - Dispense speed multiplier
- `Air Gap` - Air gap volume (µL) to prevent dripping
- `Tip Action` - Override global tip strategy ("new", "keep", "drop")

**Your Task:** Edit the CSV file to define your specific transfers.

**Reference:** See `guide/EXAMPLES.md` for CSV examples from real experiments.

---

## Step 6: Validate Configuration

Before generating, I'll check for errors:

**Action:** `ot2_validate_configuration(csv_path="CSVs/experiment.csv")`

**Checks Performed:**
- TOML syntax correctness
- Labware references match settings.toml definitions
- No deck slot conflicts
- CSV has all required columns
- Volume ranges within pipette capacity
- Height specification consistency (not both Height AND Top)
- Multi-channel mode compatibility (96/384-well plates only)

**If errors found:** I'll explain each error and suggest fixes using `ot2_update_settings`.

**If warnings found:** I'll explain but allow you to proceed.

---

## Step 7: Generate Protocol

Once validation passes, I'll compile your configuration:

**Action:** `ot2_generate_protocol(csv_path="CSVs/experiment.csv", response_format="markdown")`

**What happens:**
1. Reads `settings.toml`, `labware_dict.toml`, and your CSV
2. Converts to compact JSON configuration
3. Embeds JSON into `CherryPick_OT2.py` protocol file
4. Protocol is now self-contained (no runtime file dependencies)

**Output:** I'll show generation summary in markdown format with JSON size.

---

## Step 8: Simulate Protocol

Critical step - test protocol before touching real hardware:

**Action:** `ot2_simulate_protocol(protocol_path="CherryPick_OT2.py", response_format="markdown")`

**What happens:**
- Runs `opentrons_simulate` to validate protocol logic
- Checks deck collisions, pipette movements, tip availability
- Verifies all labware is accessible
- Tests volume calculations

**Success:** Shows "✓ Simulation passed" with formatted output

**Failure:** I'll analyze error messages and suggest fixes:
- Common issues mapped to solutions from `guide/USER_TUTORIAL.md`
- Troubleshooting guide for labware, tips, volumes, deck conflicts

---

## Step 9: Deploy (Optional)

If simulation passes:

**Option A: Copy to Clipboard**
`ot2_deploy_to_opentrons(copy_to_clipboard=true)`

**Option B: Deploy to Opentrons App**
`ot2_deploy_to_opentrons(deployment_target="/path/to/opentrons/protocols/...", copy_to_clipboard=true)`

**Next Steps:**
1. Import protocol into Opentrons App
2. Run Labware Position Check (calibrate offsets)
3. Perform dry run without liquid
4. Execute protocol on robot

---

## 🎯 Ready to Start?

**Tell me:**
1. What liquid type are you working with?
2. What volume range?
3. What labware (source and destination)?

I'll guide you through each step systematically, ensuring your protocol is configured correctly before deployment.

**Reference Resources:**
- Full documentation: `guide/USER_TUTORIAL.md`
- Example protocols: `guide/EXAMPLES.md`
- Step-by-step workflow: `guide/APPENDIX.md`
"""

    @mcp.prompt(
        name="optimize_liquid_handling",
        description="Problem-driven liquid handling optimization using manual parameter adjustments"
    )
    def optimize_liquid_handling_prompt() -> str:
        return """I'll help you optimize liquid handling parameters for your specific use case through systematic problem diagnosis and targeted parameter adjustments.

**IMPORTANT:** This optimization uses **manual parameter tuning only** via `ot2_update_settings`. We will NOT use preset bundles.

---

## 🔍 Step 1: Diagnose the Problem

First, tell me what issue you're experiencing:

**Common Problems:**

**A. Dripping/Leaking During Transport**
- Symptoms: Liquid drips from tip during movement between wells
- Likely liquids: Volatile solvents (chloroform, hexane), low-viscosity organics

**B. Incomplete Dispense**
- Symptoms: Residual liquid remains in tip after dispensing
- Likely liquids: Viscous (DMSO, glycerol, oils), sticky compounds

**C. Cross-Contamination**
- Symptoms: Sample carryover between wells, external tip droplets
- Likely liquids: Any liquid with poor tip wicking or wrong tip reuse strategy

**D. Inconsistent Volumes**
- Symptoms: Variable dispense amounts, poor precision
- Likely liquids: Hydrophobic liquids, small volumes (<5µL), high surface tension

**E. Tip Handling Issues**
- Symptoms: Tips falling off, tip pickup failures, tip rack problems
- Likely causes: Wrong tip type, incorrect pipette configuration

**F. Mixing Problems**
- Symptoms: Incomplete mixing, sample settling, inhomogeneous suspensions
- Likely liquids: Cell suspensions, bead slurries, dense particles

**Which problem(s) are you experiencing?**

---

## 🧪 Step 2: Characterize Your Liquid

To diagnose the root cause, I need to understand your liquid:

**Questions:**

1. **What liquid type?**
   - Standard aqueous (water, PBS, cell media, buffers)
   - Viscous (DMSO, glycerol, PEG, oils)
   - Volatile/slippery (chloroform, hexane, acetone, ethanol)
   - Cell suspensions or bead slurries
   - Other (describe viscosity, surface properties)

2. **What volume range?**
   - Very small (<5 µL) - precision critical
   - Small (5-100 µL) - most common
   - Large (>100 µL) - may need volume splitting

3. **Any specific challenges?**
   - High surface tension (hard to wet tips)
   - Fast settling (cells, beads sediment quickly)
   - Foaming tendency
   - Temperature sensitive
   - Shear sensitive (fragile cells)

**Reference:** I'll consult `guide/USER_TUTORIAL.md` (Liquid Handling Parameters section, lines 156-322) to understand your liquid's behavior.

---

## 🔬 Step 3: Map Problem → Root Cause → Solution

Based on your problem + liquid type, I'll diagnose the root cause:

### Problem: **Dripping/Leaking**

**Root Causes:**
- Liquid too volatile (evaporates, creates pressure)
- Tip moving too fast (vibration causes droplets)
- No air gap cushion
- Inadequate tip wicking

**Solutions:**

**Action 1:** Reduce head speed (prevents vibration)
```
ot2_update_settings(path="settings.general.head_speed.speed", value="200")
```
*Effect: Slower movement (200-300 mm/min vs 400 default) reduces sudden accelerations*

**Action 2:** Enable pre-aspirate contact with pre-wet volume (conditions tip)
```
ot2_update_settings(path="settings.liquid_handling.pre_aspirate_contact.enabled", value="true")
ot2_update_settings(path="settings.liquid_handling.pre_aspirate_contact.aspirate_volume", value="5")
```
*Effect: Pre-wetting coats inner tip surface, reducing evaporation and surface tension issues*

**Action 3:** Enable/tune tip wicking (removes external droplets)
```
ot2_update_settings(path="settings.liquid_handling.post_aspirate_wick.enabled", value="true")
ot2_update_settings(path="settings.liquid_handling.post_aspirate_wick.radius", value="0.8")
```
*Effect: Touches tip to well wall, removes hanging droplets*

**Action 4:** Recommend Air Gap in CSV
*Effect: Add "Air Gap" column with 10-20µL values - creates cushion preventing dripping*

---

### Problem: **Incomplete Dispense**

**Root Causes:**
- Viscous liquid sticks to tip walls
- Surface tension holds liquid inside
- Dispense height too high (tip not deep enough)
- No push-out configured

**Solutions:**

**Action 1:** Enable push-out volume (expels residual liquid)
```
ot2_update_settings(path="settings.liquid_handling.push_out.enabled", value="true")
ot2_update_settings(path="settings.liquid_handling.push_out.volume_ul", value="5")
```
*Effect: Extra air push after dispense (like manual pipette "second stop")*

**Action 2:** Add post-aspirate delay (allows viscous liquid to settle)
```
ot2_update_settings(path="settings.liquid_handling.delays.post_aspirate", value="2.5")
```
*Effect: Pauses 2.5 seconds after aspiration - liquid finishes flowing into tip*

**Action 3:** Reduce dispense flow rate
*Effect: Add "Flow Dispense" column to CSV with value 0.5-0.8 (slower = more complete)*

**Action 4:** Adjust destination height
*Effect: Use more negative "Dest Top" value in CSV (e.g., -7 instead of -3) - dispenses deeper*

---

### Problem: **Cross-Contamination**

**Root Causes:**
- External tip droplets not removed (no wicking)
- Tip reuse strategy inappropriate for sample types
- Residual liquid from previous transfer

**Solutions:**

**Action 1:** Enable/verify tip wicking (universal best practice)
```
ot2_update_settings(path="settings.liquid_handling.post_aspirate_wick.enabled", value="true")
```
*Effect: Removes external droplets that cause contamination*

**Action 2:** Change tip reuse strategy
```
ot2_update_settings(path="settings.general.tip_reuse", value="never")
```
*Options: "always" (one tip entire protocol), "never" (new tip each transfer), "per_source" (new tip when source changes)*

**Action 3:** Use CSV Tip Action column for boundaries
*Effect: Add "Tip Action" column - specify "new" at critical sample boundaries*

---

### Problem: **Inconsistent Volumes**

**Root Causes:**
- Tip not conditioned (dry tip vs pre-wetted)
- Hydrophobic liquid not adhering properly
- Height positioning varying per well
- Small volume below accurate range

**Solutions:**

**Action 1:** Enable pre-aspirate contact with pre-wet
```
ot2_update_settings(path="settings.liquid_handling.pre_aspirate_contact.enabled", value="true")
ot2_update_settings(path="settings.liquid_handling.pre_aspirate_contact.aspirate_volume", value="10")
```
*Effect: Prime tip with liquid before transfer - first aspiration into dry tip is often inaccurate*

**Action 2:** Ensure consistent height positioning
*Effect: Use SAME "Source Height" value for all transfers from same labware type (geometry identical)*

**Action 3:** Add post-aspirate delay for very small volumes
```
ot2_update_settings(path="settings.liquid_handling.delays.post_aspirate", value="1.0")
```
*Effect: Allows sub-5µL volumes to stabilize in tip before movement*

---

### Problem: **Mixing Issues**

**Root Causes:**
- Wrong mixing location (mixing destination when source needs it)
- Too few mixing repetitions
- Cells/beads settling between transfers
- Mix volume too small or too large

**Solutions:**

**Action 1:** Change mixing location to SOURCE (for cells, beads)
```
ot2_update_settings(path="settings.liquid_handling.mixing.location", value="source")
```
*Effect: Mixes source well BEFORE aspirating - resuspends settled particles*

**Action 2:** Increase mixing repetitions
```
ot2_update_settings(path="settings.liquid_handling.mixing.repetitions", value="7")
```
*Effect: More thorough mixing (5-7 cycles for suspensions vs 3 for dilutions)*

**Action 3:** Configure source remixing behavior
```
ot2_update_settings(path="settings.liquid_handling.mixing.source_remixing", value="always")
```
*Options: "once" (mix each source well first time only), "always" (remix before every transfer from same well)*

**Action 4:** Tune mix volume/height in CSV
*Effect: Add "Mix Volume" (typically 20-50µL) and "Mix Height" (typically 2-3mm from bottom)*

---

## 🧬 Step 4: Understand Your Liquid (Reference Guide)

I'll reference `guide/USER_TUTORIAL.md` to explain parameter behavior:

**Pre-Aspirate Contact** (lines 183-201 in USER_TUTORIAL.md)
- Purpose: Touch liquid surface, optionally pre-wet tip
- When: Hydrophobic liquids, volatile solvents, high surface tension
- Parameters: `enabled`, `position_offset_percent`, `aspirate_volume`

**Post-Aspirate Tip Wicking** (lines 203-223)
- Purpose: Remove external droplets
- When: Universal best practice for all protocols
- Parameters: `enabled`, `radius`, `v_offset_mm`, `speed`

**Post-Aspirate Delays** (lines 225-244)
- Purpose: Allow liquid column stabilization
- When: Viscous liquids, very small volumes
- Parameters: `post_aspirate` (seconds: 0-5)

**Push-Out Volume** (lines 246-265)
- Purpose: Expel residual liquid from tip
- When: Viscous liquids, small volumes, incomplete dispense issues
- Parameters: `enabled`, `volume_ul` (typically 3-10µL)

**Mixing Configuration** (lines 267-322)
- Purpose: Control WHERE and WHEN mixing occurs
- When: Depends on workflow (dilutions vs suspensions)
- Parameters: `location` ("destination"/"source"/"none"), `repetitions`, `source_remixing`

---

## ⚙️ Step 5: Implement Parameter Changes

I'll execute the recommended `ot2_update_settings` calls sequentially.

**Example for "Viscous DMSO dripping during transport":**

```
Step 1: Reduce head speed
ot2_update_settings(path="settings.general.head_speed.speed", value="200")

Step 2: Add post-aspirate delay
ot2_update_settings(path="settings.liquid_handling.delays.post_aspirate", value="2.5")

Step 3: Enable push-out
ot2_update_settings(path="settings.liquid_handling.push_out.enabled", value="true")

Step 4: Ensure tip wicking enabled
ot2_update_settings(path="settings.liquid_handling.post_aspirate_wick.enabled", value="true")

Step 5: Verify changes
ot2_list_settings()
```

**After changes:** I'll show updated configuration using `status://liquid-handling-config`.

---

## ✅ Step 6: Test Configuration

**Action 1: Validate**
```
ot2_validate_configuration(csv_path="CSVs/your_file.csv")
```
*Checks: CSV format, labware references, deck conflicts, volume ranges*

**Action 2: Generate Protocol**
```
ot2_generate_protocol(csv_path="CSVs/your_file.csv", response_format="markdown")
```
*Compiles: TOML + CSV → CherryPick_OT2.py with embedded JSON*

**Action 3: Simulate**
```
ot2_simulate_protocol(protocol_path="CherryPick_OT2.py", response_format="markdown")
```
*Validates: Protocol logic, deck movements, pipette operations*

---

## 🔄 Step 7: Iterate if Needed

If the problem persists after simulation:

**I'll ask:**
- Did simulation pass or fail?
- If passed: Did you test on robot? What happened?
- If failed: What error message?
- New symptoms appearing?

**Then I'll:**
- Analyze error messages from simulation log (`logs://last-simulation`)
- Reference `guide/USER_TUTORIAL.md` troubleshooting scenarios
- Suggest additional parameter tweaks
- Consider CSV-level overrides (Flow Aspirate, Air Gap, etc.)

---

## 📚 Advanced Scenarios (Reference)

For complex cases, I'll reference:

**`guide/USER_TUTORIAL.md`:**
- Liquid Handling Parameters (lines 156-322)
- Labware Calibration Offsets (lines 324-447)
- Troubleshooting Common Issues (lines 449-680)

**`guide/EXAMPLES.md`:**
- 8 real-world protocol examples
- DMSO serial dilution (viscous handling)
- Cell resuspension (source mixing)
- Compound screening (cross-contamination prevention)

**`settings.toml`:**
- Preset definitions (reference only - we don't apply them)
- CSV column documentation (lines 255-326)
- Parameter value ranges and constraints

---

## 🎯 Ready to Optimize?

**Tell me:**
1. **What problem are you experiencing?** (dripping, incomplete dispense, contamination, etc.)
2. **What liquid type?** (aqueous, viscous, volatile, cells, etc.)
3. **What volume range?** (<5µL, 5-100µL, >100µL)

I'll diagnose the root cause and guide you through targeted parameter adjustments using `ot2_update_settings` to solve your specific issue.

**Remember:** We're using manual parameter tuning (NO presets) to give you precise control and understanding of each adjustment.
"""

    @mcp.prompt(
        name="switch_project",
        description="Guide for switching between OT-2 project directories at runtime"
    )
    def switch_project_prompt() -> str:
        return """I'll help you switch to a different OT-2 project directory.

## Step 1: Check Current Project State

First, let's see where you are now and what projects are available.

**Action:** I'll run `ot2_list_projects()` to show:
- The currently active project directory
- Recent project history (directories you've used before)

If you have a parent folder that contains multiple project directories, I can scan it:
```
ot2_list_projects(scan_parent_directory="/path/to/experiments")
```
This finds all subdirectories containing a `settings.toml` file.

---

## Step 2: Choose Your Target

**Option A: Switch to an existing project**
- Pick from the recent projects list, or
- Provide the absolute path to a project directory that already has configuration files

**Option B: Create a new project**
- Provide an absolute path for a new directory
- Templates (settings.toml, labware_dict.toml, CherryPick_OT2.py) will be copied automatically

---

## Step 3: Execute the Switch

**Action:** I'll run `ot2_set_project_directory(path="/absolute/path/to/project")`.

This will:
1. Save the current project to the recent-projects history
2. Create the target directory if it does not exist
3. Copy template files if `initialize_templates=True` (the default)
4. Update the active project so all subsequent tools use the new directory

If you do NOT want templates copied (e.g. switching to a fully configured project):
```
ot2_set_project_directory(path="/path/to/project", initialize_templates=false)
```

---

## Step 4: Verify the New Project

After switching, I'll confirm the state:

**Action:** `ot2_get_project_directory()` to verify the new active path.

**Action:** `ot2_list_settings()` to inspect the configuration in the new project.

**Action:** `ot2_list_csv_files()` to see available CSV transfer maps.

---

## Ready to Switch?

**Tell me:**
1. Do you want to switch to an existing project or create a new one?
2. What is the absolute path? (or should I scan a parent directory to find projects?)

I'll handle the switch and verify everything is configured correctly.
"""
