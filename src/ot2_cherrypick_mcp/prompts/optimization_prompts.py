"""
Protocol optimization prompts for MCP server.

Provides workflow guidance for fine-tuning transfer parameters like heights, speeds, and flow rates.
"""

from fastmcp import FastMCP

__all__ = ["register_optimization_prompts"]


def register_optimization_prompts(mcp: FastMCP) -> None:
    """Register optimization prompts with the FastMCP app."""

    @mcp.prompt
    def optimize_transfer_parameters(parameter_type: str = "heights") -> str:
        """
        Guide user through optimizing protocol transfer parameters.

        Args:
            parameter_type: Which parameter to optimize - "heights", "head_speed", "flow_rates", or "all"

        User intent: "Optimize transfer heights" or "Adjust head speed" or "Fine-tune flow rates"
        """

        parameter_guides = {
            "heights": """
## Optimizing Aspiration/Dispense Heights

Heights control where the pipette tip positions during aspiration and dispense.

### Source Heights (Aspiration)

**Goal:** Aspirate from optimal depth to:
- Ensure consistent volume
- Avoid debris at bottom
- Avoid air at top

**Recommendations by Labware:**
- **Tubes (1.5mL/2mL):** 2-5mm from bottom
  - Too low → May aspirate debris
  - Too high → May not reach liquid if volume low
- **96-well plates:** 1-2mm from bottom
  - Shallower wells → Less margin for error
- **384-well plates:** 1mm from bottom
  - Very small wells → Must be precise
- **Reservoirs:** 2mm from bottom
  - Large volume → More forgiving

**How to Adjust:**
- **Tool:** Use CSV columns `Source Height` or `Source Top`
- **Method 1 (from bottom):** Set `Source Height` in CSV (mm from well bottom)
- **Method 2 (from top):** Set `Source Top` as negative value (e.g., -5 = 5mm below rim)

**Testing Heights:**
1. Start with recommended values
2. Run protocol on OT-2 with water/dye
3. Observe:
   - Does tip reach liquid consistently?
   - Any debris aspiration?
   - Consistent volumes dispensed?
4. Adjust heights in CSV
5. Regenerate and re-test

### Destination Heights (Dispense)

**Goal:** Dispense at optimal height to:
- Ensure liquid deposits in well (not on edges)
- Avoid splashing
- Consistent deposition

**Recommendations:**
- **Plates (96/384-well):** 1mm from bottom
  - Close to bottom prevents splashing
  - Liquid pools consistently
- **Tubes:** 5mm from bottom
  - Higher dispensing avoids bubbles
  - Prevents tip from bottoming out

**Common Issues:**
- **Splashing:** Destination too high → Lower dispense height
- **Dispensing on edge:** Misaligned calibration → Check labware offsets
- **Bubbles in dest:** Too close to liquid surface → Raise height slightly

""",
            "head_speed": """
## Optimizing Head Movement Speed

Head speed controls how fast the pipette head moves between positions.

**Default:** 400 mm/min

### When to Reduce Speed (200-300 mm/min)

**Use Cases:**
- Working with volatile/slippery solvents (chloroform, hexane, ethanol)
- Viscous liquids that drip during movement
- Delicate labware that might shift
- High-value samples (extra caution)

**Why:**
- Slower movement reduces vibration
- Prevents droplets from escaping tip
- Reduces risk of liquid loss during transit

### When to Increase Speed (500-600 mm/min)

**Use Cases:**
- Aqueous buffers (low volatility)
- High-throughput workflows (time-sensitive)
- Stable labware and liquids

**Why:**
- Faster protocol execution
- No liquid loss risk with aqueous solutions
- Maintain throughput

### How to Adjust Head Speed:

**Tool:** `update_settings(path="settings.general.head_speed.speed", value=NEW_VALUE)`

**Example:**
```python
# Slow down for volatile solvents
update_settings(path="settings.general.head_speed.speed", value=250)

# Speed up for aqueous buffers
update_settings(path="settings.general.head_speed.speed", value=500)
```

**Valid Range:** 100-600 mm/min
- Below 100: Too slow, negligible benefit
- Above 600: Robot safety limits

**Testing:**
1. Set initial speed based on liquid type
2. Run protocol with observation
3. Check for:
   - Droplet loss during movement
   - Liquid dripping from tips
   - Time to completion
4. Adjust as needed

""",
            "flow_rates": """
## Optimizing Flow Rates

Flow rates control aspiration and dispense speeds (how fast liquid enters/exits tip).

**Default:** 1.0× (100% of pipette default flow rate)

### Aspiration Flow Rate

**Slower (<1.0):** Use for viscous liquids
- Viscous DMSO, glycerol, oils → 0.5-0.7×
- Prevents shearing/bubbles
- Allows liquid to fill tip gradually

**Faster (>1.0):** Use for low-viscosity liquids
- Water, buffers → 1.0-1.5×
- Speeds up protocol
- No accuracy loss with thin liquids

### Dispense Flow Rate

**Slower (<1.0):** Use for precise deposition
- Small volumes (<10µL) → 0.7-0.9×
- Viscous liquids → 0.5-0.8×
- Prevents splashing

**Faster (>1.0):** Use for large volumes
- Aqueous, >100µL → 1.0-1.5×
- Faster dispensing
- Still accurate for large volumes

### How to Adjust in CSV:

**Per-transfer control via CSV columns:**
- `Flow Aspirate` - Aspiration speed multiplier (e.g., 0.5, 1.0, 1.5)
- `Flow Dispense` - Dispense speed multiplier

**Example CSV:**
```csv
Source Labware,Source Well,Volume (ul),Dest Labware,Dest Well,Flow Aspirate,Flow Dispense
tube_rack_4,A1,50,plate_2,A1,0.7,0.8
tube_rack_4,A2,100,plate_2,A2,1.0,1.2
```

**Guidelines:**
- Viscous liquids: Both 0.5-0.7×
- Aqueous liquids: Both 1.0-1.5×
- Small volumes: Lower dispense rate
- Leave blank in CSV for default (1.0×)

**Testing Flow Rates:**
1. Start with recommended values
2. Run test transfers
3. Check for:
   - Bubbles during aspiration (too fast)
   - Incomplete dispense (too fast for viscous)
   - Splashing (dispense too fast)
4. Adjust multipliers in CSV
5. Regenerate protocol

""",
        }

        all_parameters_guide = """
## Comprehensive Parameter Optimization

You'll optimize multiple parameters for your specific liquid handling application.

### Step-by-Step Optimization Workflow:

**1. Start with Defaults**
- Heights: Labware-specific recommendations
- Head speed: 400 mm/min
- Flow rates: 1.0× for both aspirate/dispense

**2. Identify Your Liquid Type**
- Aqueous (water, buffers) → Minimal adjustments needed
- Viscous (DMSO, glycerol, oils) → Reduce flow rates, add delays
- Volatile (chloroform, ethanol, hexane) → Reduce head speed, add air gaps

**3. Optimize in This Order:**
a. **Heights first** - Most critical for consistent volumes
b. **Flow rates second** - Affects accuracy and bubbles
c. **Head speed last** - Affects transit dripping

**4. Test Iteratively**
- Change ONE parameter at a time
- Test with representative samples
- Document what works

**5. Fine-Tune Based on Observations**
- Inconsistent volumes → Check heights
- Dripping during movement → Reduce head speed, add air gaps
- Bubbles → Reduce aspiration flow rate
- Splashing → Reduce dispense flow rate, lower dest height

"""

        if parameter_type == "all":
            instructions = all_parameters_guide
            for param_name, param_guide in parameter_guides.items():
                instructions += f"\n{param_guide}\n"
        else:
            instructions = parameter_guides.get(
                parameter_type,
                """
## Parameter Type Not Recognized

Available parameter types:
- "heights" - Aspiration/dispense heights
- "head_speed" - Movement speed between positions
- "flow_rates" - Aspiration/dispense flow rates
- "all" - Comprehensive optimization guide

Please specify one of these parameter types.
""",
            )

        return f"""
## Goal
Optimize transfer parameters: {parameter_type}

{instructions}

## Prerequisites
- Protocol already generated and tested at least once
- Observation of current protocol performance
- Understanding of your liquid properties

## General Workflow

### Step 1: Review Current Settings

**For heights:**
- **Tool:** Read current CSV file via `files://csvs`
- **Check:** Source Height, Dest Height columns

**For head speed:**
- **Tool:** Read `config://settings`
- **Check:** `settings.general.head_speed.speed` value

**For flow rates:**
- **Tool:** Read CSV file
- **Check:** Flow Aspirate, Flow Dispense columns

### Step 2: Make Targeted Adjustments

**Decision Point:**
- IF optimizing heights → Edit CSV file, update height columns
- IF optimizing head_speed → Use `update_settings` tool
- IF optimizing flow_rates → Edit CSV file, update flow columns

### Step 3: Regenerate Protocol
- **Tool:** `generate_protocol(csv_path="CSVs/your_file.csv")`
- **Action:** Rebuild protocol with new parameters
- **Result:** Updated CherryPick_OT2.py

### Step 4: Simulate Changes
- **Tool:** `simulate_protocol()`
- **Action:** Verify no errors introduced
- **Check:** Read `logs://last-simulation`

### Step 5: Test on Robot (Recommended)
- Deploy protocol to OT-2
- Run with water or test samples
- Observe liquid handling performance
- Iterate if needed

## Parameter Interaction Matrix

Parameters interact - changing one may require adjusting others:

| Change | May Require Adjusting |
|--------|----------------------|
| Increase source height | Check if liquid reaches (especially low volumes) |
| Decrease dest height | May cause splashing → reduce dispense flow rate |
| Reduce head speed | Protocol takes longer → no other adjustment needed |
| Increase flow rates | May cause bubbles → add post-aspirate delay |
| Viscous liquid | Reduce ALL flow rates + reduce head speed |
| Volatile liquid | Reduce head speed + add air gaps in CSV |

## Common Parameter Sets by Liquid Type

### Aqueous Buffers (Standard)
```
Source Height: 2mm (tubes) or 1mm (plates)
Dest Height: 1mm
Head Speed: 400 mm/min
Flow Aspirate: 1.0
Flow Dispense: 1.0
```

### Viscous Liquids (DMSO, Glycerol)
```
Source Height: 3mm (deeper for better contact)
Dest Height: 1mm
Head Speed: 300 mm/min (slower)
Flow Aspirate: 0.6 (slower aspiration)
Flow Dispense: 0.7 (slower dispense)
Post-aspirate delay: 2-3 seconds (add via CSV or settings)
```

### Volatile Solvents (Chloroform, Hexane)
```
Source Height: 2mm
Dest Height: 1mm
Head Speed: 250 mm/min (much slower to prevent drips)
Flow Aspirate: 1.0
Flow Dispense: 0.9
Air Gap: 10µL (add via CSV Air Gap column)
```

### Small Volumes (<5µL)
```
Source Height: 1mm (very close to liquid)
Dest Height: 0.5mm (very close to bottom)
Head Speed: 350 mm/min
Flow Aspirate: 0.8 (slower for precision)
Flow Dispense: 0.7 (slower to avoid splashing)
```

## Success Criteria
- ✓ Parameters updated in CSV or settings.toml
- ✓ Protocol regenerates without errors
- ✓ Simulation passes
- ✓ (If tested on robot) Consistent volumes, no dripping, no splashing

## Troubleshooting

### "Parameter out of valid range"
- **Cause:** Value exceeds allowed limits
- **Fix:**
  - Head speed: Keep within 100-600 mm/min
  - Flow rates: Keep within 0.1-3.0 multiplier
  - Heights: Must be positive for Height, negative for Top

### Changes don't seem to take effect
- **Cause:** Forgot to regenerate protocol after editing
- **Fix:** Always run `generate_protocol()` after parameter changes

### Protocol works in simulation but fails on robot
- **Cause:** Physical factors not modeled in simulation
- **Fix:** Test adjustments iteratively on robot with non-critical samples first

## Next Steps
After optimization:
- Document your final parameter values for this liquid type
- Use same parameters for future protocols with similar liquids
- If satisfied: Deploy via `deploy_to_robot` prompt
"""
