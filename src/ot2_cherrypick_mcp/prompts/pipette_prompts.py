"""
Pipette configuration prompts for MCP server.

Provides workflow guidance for switching pipette modes and configuring tip strategies.
"""

from fastmcp import FastMCP

__all__ = ["register_pipette_prompts"]


def register_pipette_prompts(mcp: FastMCP) -> None:
    """Register pipette configuration prompts with the FastMCP app."""

    @mcp.prompt
    def switch_to_multi_channel(mode: str = "multi") -> str:
        """
        Configure the protocol to use an 8-channel pipette.

        Args:
            mode: Either "multi" (full 8-tip operation) or "multi_X1" (single tip from 8-channel hardware)

        User intent: "I want to use my 8-channel pipette" or "Switch to multi-channel mode"
        """

        mode_explanation = {
            "multi": """
**Multi Mode (Full 8-Channel)**
- Uses all 8 tips simultaneously
- Each CSV row = 8 transfers (entire column)
- Example: Source Well "A1" → Transfers A1, B1, C1, D1, E1, F1, G1, H1
- **CRITICAL:** Only works with 96-well and 384-well plates (NOT tubes)
- Best for: High-throughput plate-to-plate transfers
""",
            "multi_X1": """
**Multi_X1 Mode (Single Tip from 8-Channel)**
- Uses only H1 tip from 8-channel pipette
- Each CSV row = 1 individual transfer (same as single mode)
- Example: Source Well "A1" → Transfers only A1
- Works with any labware type
- Best for: When you have 8-channel hardware but need single-tip precision
""",
        }

        if mode == "multi":
            csv_explanation = """
- CSV Row: "A1" → Transfers: A1, B1, C1, D1, E1, F1, G1, H1 (entire column 1)
- CSV Row: "B5" → Transfers: B5, C5, D5, E5, F5, G5, H5, A6 (column 5, starting at B)
- **Important:** 10 CSV rows = 80 individual transfers (10 × 8)
"""
            multiplication = "× 8 (each row = 8 transfers)"
            compatibility_check = """
**CRITICAL for multi mode:**
- Source labware MUST be 96-well or 384-well plates
- Destination labware MUST be 96-well or 384-well plates
- Tube racks and other labware are NOT compatible

**Decision Point:**
- Read `status://deck-layout` to see current labware
- IF current labware includes tubes or non-standard labware:
  - STOP and inform user: "Multi mode requires 96 or 384-well plates. Current labware is incompatible. Please either:"
    - "1. Use multi_X1 mode instead (supports all labware)"
    - "2. Change labware to 96 or 384-well plates first using configure_deck_layout prompt"
- ELSE:
  - Proceed to Step 3
"""
        else:  # multi_X1
            csv_explanation = """
- CSV Row: "A1" → Transfer: A1 only (same as single mode)
- CSV Row: "B5" → Transfer: B5 only
- **Important:** 10 CSV rows = 10 individual transfers (1:1 mapping)
"""
            multiplication = "× 1 (each row = 1 transfer)"
            compatibility_check = """
**Multi_X1 compatibility:**
- Works with ALL labware types (plates, tubes, reservoirs)
- No restrictions
- Proceed to Step 3
"""

        return f"""
## Goal
Switch from single-channel to {mode} pipette operation

## Understanding the Mode

{mode_explanation[mode]}

## Prerequisites
- Project already initialized (settings.toml and labware_dict.toml exist)
- Deck layout configured in settings.toml
- An 8-channel pipette defined in labware_dict.toml

## Workflow

### Step 1: Check Current Deck Layout
- **Tool:** Read `status://deck-layout`
- **Action:** Identify all source and destination labware currently configured

### Step 2: Validate Labware Compatibility

{compatibility_check}

### Step 3: Update Settings
- **Tool:** `update_settings(path="settings.general.mode", value="{mode}")`
- **Action:** Change pipette mode to {mode}
- **Result:** settings.toml now shows `mode = "{mode}"`

### Step 4: Understand CSV Interpretation
**Important:** In {mode} mode, CSV is interpreted as:

{csv_explanation}

**Recommendation:**
- Review your CSV file via `files://csvs` to ensure:
  - Well names match your intended transfers
  - Number of CSV rows matches expected transfer count

### Step 5: Validate Configuration
- **Tool:** `validate_configuration()`
- **Action:** Pre-flight checks for errors before generation
- **Expected outcome:** No errors related to labware compatibility or pipette configuration

### Step 6: Regenerate Protocol
- **Tool:** `generate_protocol(csv_path="CSVs/your_file.csv")`
- **Action:** Regenerate with new pipette mode
- **Result:** CherryPick_OT2.py updated with multi-channel configuration

### Step 7: Simulate to Verify
- **Tool:** `simulate_protocol()`
- **Action:** Test protocol with Opentrons simulator
- **Check:** Read `logs://last-simulation` for any errors

## Common Issues & Solutions

### "No pipette definition for multi mode"
- **Cause:** labware_dict.toml doesn't have an 8-channel pipette defined
- **Fix:** Check `config://labware`, ensure a pipette with `channels = 8` exists
- **If missing:** Use `add_labware_definition` tool to add 8-channel pipette

### "Labware incompatible with multi-channel"
- **Cause:** Trying to use tubes or non-standard labware in multi mode
- **Fix:** Either switch to multi_X1 mode OR change to 96/384-well plates via `configure_deck_layout` prompt

### "Wrong number of transfers executed"
- **Cause:** CSV interpreted as columns in multi mode when you expected individual wells
- **Fix:** Each CSV row = 8 transfers in multi mode. Reduce CSV rows to: (desired transfers) / 8

### Simulation shows "Slot conflict" or "Labware not found"
- **Cause:** Deck layout issues unrelated to multi-channel mode
- **Fix:** Use `troubleshoot_simulation_error` prompt for systematic debugging

## Success Criteria
- ✓ Settings.toml shows `mode = "{mode}"`
- ✓ `validate_configuration()` passes with no errors
- ✓ Protocol simulates successfully (`logs://last-simulation` shows no errors)
- ✓ Expected number of transfers = CSV rows {multiplication}

## Next Steps
After successful mode switch:
1. Review generated protocol via simulation
2. If satisfied: Use `deploy_to_robot` prompt to copy to Opentrons App
3. If errors: Use `troubleshoot_simulation_error` prompt
"""

    @mcp.prompt
    def switch_to_single_channel() -> str:
        """
        Configure the protocol to use a single-channel pipette.

        User intent: "Switch back to single-channel mode" or "I want to use a single-tip pipette"
        """

        return """
## Goal
Switch from multi-channel to single-channel pipette operation

## Understanding Single-Channel Mode

**single_X1 Mode:**
- Uses one tip at a time
- Each CSV row = 1 individual transfer
- Example: Source Well "A1" → Transfers only A1
- Works with ALL labware types (plates, tubes, reservoirs, etc.)
- Best for: Cherry-picking individual samples, maximum flexibility

## Prerequisites
- Project already initialized (settings.toml exists)
- CSV file already created

## Workflow

### Step 1: Update Settings
- **Tool:** `update_settings(path="settings.general.mode", value="single_X1")`
- **Action:** Change pipette mode to single_X1
- **Result:** settings.toml now shows `mode = "single_X1"`

### Step 2: Verify CSV Interpretation
**In single_X1 mode:**
- CSV Row: "A1" → Transfer: A1 only
- CSV Row: "B5" → Transfer: B5 only
- **Important:** 10 CSV rows = 10 individual transfers (1:1 mapping)

**No changes needed to your CSV** - single mode uses standard well-by-well interpretation

### Step 3: Regenerate Protocol
- **Tool:** `generate_protocol(csv_path="CSVs/your_file.csv")`
- **Action:** Regenerate with single-channel configuration
- **Result:** CherryPick_OT2.py updated to use single-channel pipette

### Step 4: Simulate to Verify
- **Tool:** `simulate_protocol()`
- **Action:** Test protocol with Opentrons simulator
- **Check:** Read `logs://last-simulation` to confirm success

## Common Issues & Solutions

### "No pipette definition for single mode"
- **Cause:** labware_dict.toml doesn't have a single-channel pipette defined
- **Fix:** Check `config://labware`, ensure a pipette with `channels = 1` exists
- **If missing:** Use `add_labware_definition` tool to add single-channel pipette

### Simulation shows errors unrelated to pipette mode
- **Cause:** Other configuration issues (deck layout, labware IDs, etc.)
- **Fix:** Use `troubleshoot_simulation_error` prompt for systematic debugging

## Success Criteria
- ✓ Settings.toml shows `mode = "single_X1"`
- ✓ Protocol simulates successfully
- ✓ Transfer count = CSV row count (1:1 mapping)

## Next Steps
- If satisfied: Use `deploy_to_robot` prompt to copy to Opentrons App
- If errors: Use `troubleshoot_simulation_error` prompt
"""

    @mcp.prompt
    def configure_tip_strategy(strategy: str = "per_source") -> str:
        """
        Configure when tips are replaced during protocol execution.

        Args:
            strategy: One of "never", "always", or "per_source"

        User intent: "Change tip replacement strategy" or "Configure when to use new tips"
        """

        strategy_explanations = {
            "never": """
**Never Replace Tips (tip_reuse = "never")**
- New tip for EVERY transfer
- Maximum contamination prevention
- Highest tip consumption
- Best for:
  - Different sample types (cross-contamination risk)
  - Sensitive assays requiring absolute cleanliness
  - Regulatory compliance requirements
- Example: 100 transfers = 100 tips used
""",
            "always": """
**Always Use Same Tip (tip_reuse = "always")**
- ONE tip for ENTIRE protocol
- Minimum contamination prevention
- Lowest tip consumption
- Best for:
  - Transferring identical liquid (e.g., buffer, same reagent)
  - Non-sensitive applications
  - Tip conservation
- **WARNING:** Risk of cross-contamination between different samples
- Example: 100 transfers = 1 tip used
""",
            "per_source": """
**Replace Per Source Labware (tip_reuse = "per_source")**
- New tip when source labware changes
- Balanced contamination prevention
- Moderate tip consumption
- Best for:
  - Multiple source plates with different contents
  - Different reagent types in different source locations
  - Balancing cleanliness and efficiency
- Example: 100 transfers from 3 source plates = 3 tips used
""",
        }

        warnings = {
            "never": """
**Tip Consumption Warning:**
- This strategy uses the most tips
- Ensure sufficient tip racks on deck (check `status://deck-layout`)
- Calculate: (number of CSV rows) × (tips per transfer based on mode)
  - single_X1: 1 tip per row
  - multi: 8 tips per row
  - multi_X1: 1 tip per row
""",
            "always": """
**Cross-Contamination Warning:**
- Using one tip for all transfers risks sample mixing
- ONLY use this if:
  - Transferring identical liquid type
  - Sample identity doesn't matter
  - You understand the contamination risk

**Decision Point:**
- IF transferring different samples or reagents:
  - STOP and inform user: "This strategy risks cross-contamination. Recommend 'per_source' or 'never' instead."
- ELSE IF user confirms same liquid type:
  - Proceed to Step 2
""",
            "per_source": """
**Balanced Approach:**
- Good compromise between cleanliness and efficiency
- Suitable for most workflows
- No special warnings
""",
        }

        return f"""
## Goal
Configure tip replacement strategy to "{strategy}"

## Understanding the Strategy

{strategy_explanations[strategy]}

## Prerequisites
- Project initialized (settings.toml exists)
- Understanding of your sample contamination requirements

## Workflow

### Step 1: Assess Contamination Risk

{warnings[strategy]}

### Step 2: Update Settings
- **Tool:** `update_settings(path="settings.general.tip_reuse", value="{strategy}")`
- **Action:** Change tip reuse strategy
- **Result:** settings.toml now shows `tip_reuse = "{strategy}"`

### Step 3: Verify Tip Rack Availability
- **Tool:** Read `status://deck-layout`
- **Action:** Count how many tip racks are configured
- **Calculate:** Tips needed based on strategy:
  - Strategy "{strategy}" + your CSV transfer count
  - Ensure sufficient tip racks on deck

**If insufficient tips:**
- Use `configure_deck_layout` prompt to add more tip racks
- Or reduce number of transfers
- Or choose more conservative strategy (e.g., "always" instead of "never")

### Step 4: Regenerate Protocol
- **Tool:** `generate_protocol(csv_path="CSVs/your_file.csv")`
- **Action:** Regenerate with new tip strategy
- **Result:** CherryPick_OT2.py updated with tip_reuse configuration

### Step 5: Simulate to Verify
- **Tool:** `simulate_protocol()`
- **Action:** Test protocol to ensure sufficient tips available
- **Check:** Read `logs://last-simulation` for tip-related errors

## Common Issues & Solutions

### "Insufficient tips for protocol"
- **Cause:** Not enough tip racks on deck for chosen strategy
- **Fix:** Either:
  - Add more tip racks via `configure_deck_layout` prompt
  - Change to more conservative strategy ("always" or "per_source")
  - Reduce number of transfers in CSV

### "Tip already attached" or "No tip to drop"
- **Cause:** Tip strategy logic error (rare)
- **Fix:** Re-run `generate_protocol()` to rebuild protocol logic
- **If persists:** Report as potential bug

### Contamination observed during actual run
- **Cause:** Tip strategy too permissive for your application
- **Fix:** Switch to more stringent strategy:
  - "always" → "per_source"
  - "per_source" → "never"

## Success Criteria
- ✓ Settings.toml shows `tip_reuse = "{strategy}"`
- ✓ Protocol simulates successfully
- ✓ No tip-related errors in simulation
- ✓ Tip consumption matches expectations

## Tip Consumption Examples

Assume 50 transfers from 2 source plates:

| Strategy | Tips Used | When to Use |
|----------|-----------|-------------|
| never | 50 tips | Different samples, high sensitivity |
| per_source | 2 tips | Different source contents |
| always | 1 tip | Same liquid type throughout |

## Next Steps
- If satisfied: Use `deploy_to_robot` prompt
- If errors: Use `troubleshoot_simulation_error` prompt
"""
