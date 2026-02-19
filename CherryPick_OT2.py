def get_values(*names):
    import json
    _all_values = json.loads("""{"labware_dict":{"pipettes":[{"name":"Pipette_8","opentrons_id":"p300_multi_gen2","channels":8,"volume_range":[30,300],"preferred_mount":"right","tip_connections":["opentrons_96_tiprack_300ul"]},{"name":"Pipette_1","opentrons_id":"p1000_single_gen2","channels":1,"volume_range":[100,1000],"preferred_mount":"left","tip_connections":["tip_rack_geb_1000ul"]}],"labware":[{"category":"tip_rack","labware_id":"tip_rack_yellow_100ul","well_count":96,"well_volume":100},{"category":"tip_rack","labware_id":"opentrons_96_tiprack_300ul","well_count":96,"well_volume":300},{"category":"tip_rack","labware_id":"tip_rack_geb_1000ul","well_count":96,"well_volume":1000},{"category":"reservoir","labware_id":"reservoir_horizontal","well_count":12,"well_volume":15000},{"category":"reservoir","labware_id":"reservoir_vertical","well_count":2,"well_volume":50000},{"category":"plate","labware_id":"384_pp_standard_100ul","well_count":384,"well_volume":100},{"category":"plate","labware_id":"384_pp_high_150ul","well_count":384,"well_volume":150},{"category":"plate","labware_id":"384_ppv_55ul","well_count":384,"well_volume":55},{"category":"plate","labware_id":"384_ppv_150ul","well_count":384,"well_volume":150},{"category":"plate","labware_id":"384_ldv_12ul","well_count":384,"well_volume":12},{"category":"tube_rack","labware_id":"tube_rack_96_2000ul","well_count":96,"well_volume":2000},{"category":"tube_rack","labware_id":"tube_rack_96_1500ul","well_count":96,"well_volume":1500},{"category":"tube_rack","labware_id":"tube_rack_24_4000ul","well_count":24,"well_volume":4000},{"category":"tube_rack","labware_id":"tube_rack_48_1500ul","well_count":48,"well_volume":1500},{"category":"tube_rack","labware_id":"tube_rack_54_1500ul","well_count":54,"well_volume":1500}]},"settings":{"settings":{"general":{"mode":"single_X1","starting_tip_well":"H1","head_speed":{"speed":400}},"liquid_handling":{"pre_aspirate_contact":{"enabled":false,"position_offset_percent":20,"aspirate_volume":0},"post_aspirate_wick":{"enabled":false,"radius":1,"v_offset_mm":-1.5,"speed":20},"delays":{"post_aspirate":0},"push_out":{"enabled":true,"volume_ul":5},"mixing":{"enabled":false,"location":"destination","repetitions":3,"source_remixing":"once"}},"working_plate":[{"type":"reservoir","labware_id":"384_ppv_55ul","position_rack":"2"},{"type":"reservoir","labware_id":"tube_rack_96_1500ul","position_rack":"4"},{"type":"tip","labware_id":"tip_rack_geb_1000ul","connection":"Pipette_1","position_rack":"5"}]}},"csv_data":"Source Labware,Source Well,Source Height,Volume (ul),Dest Labware,Dest Well,Dest Height\\nmissing_labware_1_1,A1,1,5,missing_labware_2_2,B1,1"}""")
    return [_all_values[n] for n in names]


"""
Unified Cherry-pick & Distribution Protocol (CherryPick_OT2)

Supports two transfer modes:
1. CHERRY-PICK MODE: One-to-one transfers (source well → destination well)
2. DISTRIBUTION MODE: One-to-many transfers (source well → multiple destinations)

Distribution features:
- Equal distribution: Same volume to all destinations
- Geometric distribution: Varying volumes with growth/decay patterns (serial dilution)
- Smart refilling: Automatic multi-trip handling when volume exceeds pipette capacity
- Full liquid handling parameter support (air gaps, mixing, wicking, delays)

Pipette modes: single-channel, 8-channel multi, 8-channel single-tip (multi_X1)
Configurable via settings.toml and CSV transfer maps

HOME CONTROL ROW:
A special row where ALL columns contain "HOME" (case-insensitive).
When encountered, the robot re-homes to correct precision drift.
Example: HOME,HOME,HOME,HOME,HOME,HOME,HOME,HOME
Use this in long protocols (100+ transfers) to maintain accuracy.
"""
from opentrons import protocol_api
from opentrons.protocol_api import SINGLE, ALL
import csv
from io import StringIO

# Metadata
metadata = {
    'protocolName': 'Unified Cherry-Pick & Distribution Protocol (CherryPick_OT2)',
    'author': 'Opentrons User',
    'description': 'Cherry-pick and distribution protocol with serial dilution support and configurable liquid handling'
}

requirements = {"robotType": "OT-2", "apiLevel": "2.24"}

def validate_multi_mode_compatibility(settings, loaded_labware):
    """Validate that multi mode is only used with compatible labware.

    Compatible labware includes:
    - 96-well plates (full column access)
    - 384-well plates (every-other-row access)
    - Reservoirs (1, 2, 8, 12 wells) - Opentrons API centers all 8 tips via labware quirks
    """
    if settings['settings']['general']['mode'] != 'multi':
        return True

    # 96/384-well plates + common reservoir well counts (1, 2, 8, 12)
    compatible_well_counts = {1, 2, 8, 12, 96, 384}

    for plate_config in settings['settings']['working_plate']:
        if plate_config['type'] in ['source', 'dest', 'reservoir']:
            labware_id = plate_config['labware_id']
            slot = plate_config['position_rack']
            unique_name = f"{labware_id}_{slot}"
            if unique_name in loaded_labware:
                well_count = len(loaded_labware[unique_name].wells())
                if well_count not in compatible_well_counts:
                    raise ValueError(f"Multi mode requires 96/384-well plates or reservoirs (1,2,8,12 wells). Found {well_count}-well labware: {labware_id}")
    return True

def get_multi_channel_wells(labware, well_name, well_count):
    """Map single well to 8-channel pattern based on plate type.

    For reservoirs (1, 2, 8, 12 wells): Returns single well as list.
    The Opentrons API handles multi-channel centering via 'centerMultichannelOnWells' quirk.
    All 8 tips will center on the single rectangular well automatically.

    For 96-well plates: Returns full column (8 wells).
    For 384-well plates: Returns every-other-row pattern (8 wells).
    """
    # Reservoir handling: 1, 2, 8, or 12 wells
    # Opentrons API centers all 8 tips on the single well via labware quirks
    if well_count in [1, 2, 8, 12]:
        return [labware[well_name]]
    elif well_count == 96:
        # Full column access for 96-well plates
        column_name = well_name[1:]  # Extract column number (A1 → 1)
        return labware.columns_by_name()[column_name]
    elif well_count == 384:
        # Every other row access for 384-well plates
        row_letter = well_name[0]
        column_name = well_name[1:]

        if row_letter in 'ACEGIKMO':  # Odd rows
            # A1 → A1,C1,E1,G1,I1,K1,M1,O1
            target_wells = []
            for row in ['A', 'C', 'E', 'G', 'I', 'K', 'M', 'O']:
                well = f"{row}{column_name}"
                target_wells.append(labware[well])
            return target_wells
        else:  # Even rows BDFHJLNP
            # B1 → B1,D1,F1,H1,J1,L1,N1,P1
            target_wells = []
            for row in ['B', 'D', 'F', 'H', 'J', 'L', 'N', 'P']:
                well = f"{row}{column_name}"
                target_wells.append(labware[well])
            return target_wells
    else:
        raise ValueError(f"Multi mode not supported for {well_count}-well plates")

def is_home_control_row(transfer: dict) -> bool:
    """
    Check if a CSV row is a HOME control row.

    A HOME row has "HOME" (case-insensitive) in ALL non-empty columns.
    This triggers protocol.home() to re-home the robot mid-protocol,
    useful for correcting precision drift during long runs.

    Args:
        transfer: Dictionary representing one CSV row

    Returns:
        True if this is a valid HOME control row, False otherwise
    """
    values = []
    for value in transfer.values():
        if value is None:
            continue
        if isinstance(value, list):
            for item in value:
                item_str = str(item).strip()
                if item_str:
                    values.append(item_str.upper())
            continue
        value_str = str(value).strip()
        if value_str:
            values.append(value_str.upper())

    if not values:
        return False

    return all(v == "HOME" for v in values)


def determine_tip_action(transfer, row_index):
    """
    Determine tip action from CSV - column is REQUIRED.

    Args:
        transfer: CSV row dict
        row_index: Row index for error messages (0-based)

    Returns:
        str: Tip action ('new', 'keep', or 'drop')

    Raises:
        ValueError: If Tip Action column is missing or invalid
    """
    csv_tip_action = transfer.get('Tip Action', '').strip().lower()

    if not csv_tip_action:
        raise ValueError(f"Row {row_index+1}: Missing required 'Tip Action' column. Valid values: new, keep, drop")

    valid_actions = ['new', 'keep', 'drop']
    if csv_tip_action not in valid_actions:
        raise ValueError(f"Row {row_index+1}: Invalid Tip Action '{csv_tip_action}'. Valid options: {valid_actions}")

    return csv_tip_action

def execute_tip_action(tip_action, pipette, protocol, transfer_info=""):
    """Execute the determined tip action (pre-transfer) and return if new tip was picked up"""
    action_taken = ""
    new_tip_picked = False

    if tip_action == 'new':
        if pipette.has_tip:
            pipette.drop_tip()
            action_taken += "Dropped old tip, "
        pipette.pick_up_tip()
        action_taken += "picked up new tip"
        new_tip_picked = True
    elif tip_action == 'keep':
        if not pipette.has_tip:
            pipette.pick_up_tip()
            action_taken = "picked up new tip (none available to keep)"
            new_tip_picked = True
        else:
            action_taken = "keeping current tip"
    elif tip_action == 'drop':
        # For 'drop' action, ensure we have a tip for the transfer but will drop after
        if not pipette.has_tip:
            pipette.pick_up_tip()
            action_taken = "picked up tip (will drop after transfer)"
            new_tip_picked = True
        else:
            action_taken = "keeping tip (will drop after transfer)"

    # Removed verbose tip action logging

    return action_taken, new_tip_picked

def determine_well_position(transfer, well_object, position_type):
    """
    Determine well position (bottom or top) based on CSV columns

    Args:
        transfer: CSV row dict
        well_object: OpenTrons well object
        position_type: 'source', 'dest', or 'mix'

    Returns:
        tuple: (Location object, description string)
    """
    if position_type == 'source':
        height_col = 'Source Height'
        top_col = 'Source Top'
    elif position_type == 'dest':
        height_col = 'Dest Height'
        top_col = 'Dest Top'
    elif position_type == 'mix':
        # Mix always uses Mix Height and bottom positioning for now
        mix_height = float(transfer.get('Mix Height', 2.0)) if transfer.get('Mix Height') else 2.0
        return well_object.bottom(mix_height), f"bottom+{mix_height}mm"
    else:
        raise ValueError(f"Invalid position_type: {position_type}")

    # Get values from CSV (empty string if not present)
    height_val = transfer.get(height_col, '').strip()
    top_val = transfer.get(top_col, '').strip()

    # Check if values exist and are not empty
    has_height = height_val and height_val != ''
    has_top = top_val and top_val != ''

    # Validation: ensure only one is specified
    if has_height and has_top:
        raise ValueError(f"Cannot specify both '{height_col}' and '{top_col}' for same transfer. Choose one positioning method.")

    if has_height:
        offset = float(height_val)
        # Format description: use + for positive, let negative sign show naturally
        sign = '+' if offset >= 0 else ''
        return well_object.bottom(offset), f"bottom{sign}{offset}mm"
    elif has_top:
        offset = float(top_val)
        # Format description: use + for positive, let negative sign show naturally
        sign = '+' if offset >= 0 else ''
        return well_object.top(offset), f"top{sign}{offset}mm"
    else:
        # Default to bottom with 1mm offset if neither specified
        return well_object.bottom(1.0), f"bottom+1mm (default)"

def perform_liquid_contact(pipette, well_object, transfer, protocol, liquid_contact_config):
    """
    Unified liquid contact operation - handles both touch and pre-wet functionality

    Args:
        pipette: OpenTrons pipette object
        well_object: OpenTrons well object
        transfer: CSV row dict
        protocol: ProtocolContext for logging
        liquid_contact_config: Configuration dict from settings
    """
    if not liquid_contact_config.get('enabled', False):
        return

    # Calculate position based on CSV positioning + percentage offset
    base_location, base_desc = determine_well_position(transfer, well_object, 'source')

    # Apply percentage offset from base position for safer contact
    offset_percent = liquid_contact_config.get('position_offset_percent', 20)
    aspirate_volume = liquid_contact_config.get('aspirate_volume', 0)

    # Get the base height/top values to calculate offset
    height_val = transfer.get('Source Height', '').strip()
    top_val = transfer.get('Source Top', '').strip()

    if height_val:  # Bottom positioning
        base_offset = float(height_val)
        contact_offset = base_offset + (base_offset * (offset_percent / 100.0))
        contact_location = well_object.bottom(contact_offset)
        contact_desc = f"bottom+{contact_offset:.1f}mm (base+{offset_percent}%)"
    elif top_val:  # Top positioning
        base_offset = float(top_val)
        # Move percentage closer to top (less negative)
        contact_offset = base_offset * (1 - offset_percent / 100.0)
        contact_location = well_object.top(contact_offset)
        contact_desc = f"top+{contact_offset:.1f}mm ({offset_percent}% closer to top)"
    else:  # Default positioning
        base_default = 1.0
        contact_offset = base_default + (base_default * (offset_percent / 100.0))
        contact_location = well_object.bottom(contact_offset)
        contact_desc = f"bottom+{contact_offset:.1f}mm (default+{offset_percent}%)"

    # Move to contact position
    pipette.move_to(contact_location)

    # Optional aspirate/dispense for pre-wetting
    if aspirate_volume > 0:
        try:
            pipette.aspirate(aspirate_volume, contact_location)
            pipette.dispense(aspirate_volume, contact_location)
        except Exception as e:
            protocol.comment(f"Pre-wet failed, using position touch only: {e}")

    # Return to safe position
    pipette.move_to(well_object.top(0))

def perform_post_aspirate_actions(pipette, source_well, protocol, wick_config, delay_seconds):
    """
    Unified post-aspirate actions: tip wicking and delays

    Args:
        pipette: OpenTrons pipette object
        source_well: OpenTrons well object
        protocol: ProtocolContext for logging
        wick_config: Tip wick configuration dict
        delay_seconds: Seconds to delay after aspiration
    """
    # Post-aspirate delay
    if delay_seconds > 0:
        protocol.delay(seconds=delay_seconds)

    # Tip wicking
    if wick_config.get('enabled', False) and pipette.has_tip:
        radius = float(wick_config.get('radius', 0.8))
        v_offset = float(wick_config.get('v_offset_mm', -1.5))
        speed = float(wick_config.get('speed', 20))

        try:
            pipette.touch_tip(location=source_well, radius=radius, v_offset=v_offset, speed=speed)
        except Exception as err:
            protocol.comment(f"Tip wick skipped: {err}")

def perform_dispense_with_options(pipette, volume, dest_location, rate, protocol, push_out_config, mix_volume, air_gap_volume):
    """
    Unified dispense operation with optional push-out

    Args:
        pipette: OpenTrons pipette object
        volume: Volume to dispense (liquid only)
        dest_location: Destination location
        rate: Dispense rate multiplier
        protocol: ProtocolContext for logging
        push_out_config: Push-out configuration dict
        mix_volume: Mix volume (affects push-out eligibility)
        air_gap_volume: Air gap volume aspirated (must be dispensed to empty tip)
    """
    can_use_push_out = push_out_config.get('enabled', False)

    # Calculate total volume to dispense (liquid + air gap if present)
    # This ensures pipette is empty before push_out, as required by Opentrons API
    total_dispense_volume = volume + air_gap_volume

    if can_use_push_out:
        push_out_volume = push_out_config.get('volume_ul', 5)  # Fixed 5µL default
        pipette.dispense(total_dispense_volume, dest_location, rate=rate, push_out=push_out_volume)
    else:
        pipette.dispense(total_dispense_volume, dest_location, rate=rate)


def validate_csv_labware_match(settings, transfers):
    """
    Validate that all CSV labware references exactly match expected names from settings.toml

    Args:
        settings: Settings configuration dict
        transfers: List of transfer dicts from CSV

    Raises:
        ValueError: If any labware mismatch is found
    """
    # Calculate expected labware names from settings.toml (excluding modules)
    expected_labware = set()
    for plate_config in settings['settings']['working_plate']:
        # Skip modules - they are background-only and not CSV-accessible
        if plate_config.get('type') == 'module':
            continue

        labware_id = plate_config['labware_id']
        slot = plate_config['position_rack']
        expected_name = f"{labware_id}_{slot}"
        expected_labware.add(expected_name)

    # Extract all labware references from CSV (skip HOME control rows)
    csv_labware_refs = set()
    for transfer in transfers:
        # Skip HOME control rows - they don't contain valid labware references
        if is_home_control_row(transfer):
            continue
        csv_labware_refs.add(transfer['Source Labware'])
        csv_labware_refs.add(transfer['Dest Labware'])

    # Check for CSV references that don't exist in settings (this is the error we want to catch)
    csv_only = csv_labware_refs - expected_labware

    if csv_only:
        error_msg = "❌ STRICT LABWARE VALIDATION FAILED\n\n"
        error_msg += "CSV labware references MUST exactly match settings.toml definitions.\n"
        error_msg += "Labware naming convention: {labware_id}_{position_rack}\n\n"

        error_msg += f"❌ CSV references NOT FOUND in settings.toml:\n"
        for labware in sorted(csv_only):
            error_msg += f"   - {labware}\n"
        error_msg += "\n"

        error_msg += f"✓ Available labware from settings.toml:\n"
        for labware in sorted(expected_labware):
            error_msg += f"   - {labware}\n"
        error_msg += "\n"

        error_msg += "FIX: Either:\n"
        error_msg += "1. Update CSV to reference exact labware names from settings.toml, OR\n"
        error_msg += "2. Add missing labware definitions to settings.toml [[settings.working_plate]] sections\n"
        error_msg += "\nNOTE: Hardware modules (type='module') are background-only and cannot be referenced in CSV.\n"

        raise ValueError(error_msg)

def initialize_heater_shaker_module(protocol, plate_config):
    """
    Initialize heater-shaker module with background-only operation
    
    Args:
        protocol: ProtocolContext
        plate_config: Configuration dict from settings.toml [[settings.working_plate]]
    
    Returns:
        dict: Module control object with module reference and config
        
    Raises:
        ValueError: If required fields missing or invalid values
    """
    # Validate required fields
    required_fields = ['module_type', 'position_rack', 'adapter_id', 'labware_id', 
                      'target_temperature', 'target_shake_speed', 'persist_after_protocol']
    missing = [f for f in required_fields if f not in plate_config]
    if missing:
        raise ValueError(f"Heater-shaker module missing required fields: {missing}")
    
    # Validate module type
    module_type = plate_config['module_type']
    if module_type != 'heaterShaker':
        raise ValueError(f"Unsupported module_type: {module_type}. Only 'heaterShaker' supported.")
    
    # Extract configuration
    slot = plate_config['position_rack']
    adapter_id = plate_config['adapter_id']
    labware_id = plate_config['labware_id']
    target_temp = plate_config['target_temperature']
    target_rpm = plate_config['target_shake_speed']
    persist = plate_config['persist_after_protocol']
    
    # Validate temperature range (0 = disabled, 30-95 = active range)
    if target_temp < 0 or (0 < target_temp < 30) or target_temp > 95:
        raise ValueError(f"Invalid target_temperature: {target_temp}. Must be 0 (disabled) or 30-95°C")
    
    # Validate shake speed range (0 = disabled, 200-3000 = active range)
    if target_rpm < 0 or (0 < target_rpm < 200) or target_rpm > 3000:
        raise ValueError(f"Invalid target_shake_speed: {target_rpm}. Must be 0 (disabled) or 200-3000 RPM")
    
    # Load module
    protocol.comment(f"Loading heater-shaker module in slot {slot}")
    hs_mod = protocol.load_module('heaterShakerModuleV1', slot)
    
    # Load adapter and labware
    protocol.comment(f"Loading adapter '{adapter_id}' and labware '{labware_id}' on heater-shaker")
    hs_adapter = hs_mod.load_adapter(adapter_id)
    
    # Close latch (safe even if already closed)
    protocol.comment("Closing heater-shaker latch")
    hs_mod.close_labware_latch()
    
    # Initialize shaking if enabled (blocking command - takes ~5-10 seconds)
    if target_rpm > 0:
        protocol.comment(f"Starting shake at {target_rpm} RPM (blocking until speed reached)")
        hs_mod.set_and_wait_for_shake_speed(target_rpm)
        protocol.comment(f"Shake speed reached: {target_rpm} RPM")
    else:
        protocol.comment("Shaking disabled (target_shake_speed = 0)")
    
    # Initialize heating if enabled (non-blocking - ramps in background)
    if target_temp > 0:
        protocol.comment(f"Starting temperature ramp to {target_temp}°C (non-blocking, parallel operation)")
        hs_mod.set_target_temperature(target_temp)
        protocol.comment(f"Temperature ramping in background to {target_temp}°C")
    else:
        protocol.comment("Heating disabled (target_temperature = 0)")
    
    # Return module control object
    return {
        'module': hs_mod,
        'persist': persist,
        'slot': slot,
        'target_temp': target_temp,
        'target_rpm': target_rpm
    }


def deactivate_modules(modules_list, protocol):
    """
    Deactivate modules at protocol end based on persist_after_protocol setting

    Args:
        modules_list: List of module control dicts from initialize_heater_shaker_module()
        protocol: ProtocolContext for logging
    """
    if not modules_list:
        return

    for mod_ctrl in modules_list:
        module = mod_ctrl['module']
        persist = mod_ctrl['persist']
        target_temp = mod_ctrl['target_temp']
        target_rpm = mod_ctrl['target_rpm']

        if not persist:
            # Deactivate shaker if it was running
            if target_rpm > 0:
                module.deactivate_shaker()

            # Deactivate heater if it was running
            if target_temp > 0:
                module.deactivate_heater()

def reconfigure_pipette_for_mode(pipette_right, mode, tip_racks_by_mode, starting_nozzle, protocol):
    """
    Dynamically reconfigure Pipette_8 between multi and multi_X1 modes.
    
    This function enables mid-protocol switching of nozzle layouts, allowing the same
    8-channel pipette to operate in either full 8-tip mode or single-tip mode.
    
    CRITICAL: Pipette must NOT have a tip attached when calling this function.
    The Opentrons API requires tips to be dropped before reconfiguration.
    
    Args:
        pipette_right: The 8-channel pipette instance
        mode: Target mode ('multi' or 'multi_X1')
        tip_racks_by_mode: Dict mapping mode → list of tip rack objects
        starting_nozzle: Starting nozzle position for single-tip mode (e.g., 'H1')
        protocol: ProtocolContext for logging
        
    Raises:
        ValueError: If mode is invalid or tip racks not configured for requested mode
    """
    if mode not in ['multi', 'multi_X1']:
        raise ValueError(f"Invalid mode for Pipette_8: '{mode}'. Must be 'multi' or 'multi_X1'")
    
    if mode not in tip_racks_by_mode or not tip_racks_by_mode[mode]:
        raise ValueError(f"No tip racks configured for mode '{mode}'")
    
    if mode == 'multi':
        # Full 8-channel mode - all nozzles active
        pipette_right.configure_nozzle_layout(
            style=ALL,
            tip_racks=tip_racks_by_mode['multi']
        )
        protocol.comment(f"🔄 Reconfigured Pipette_8: MULTI mode (8 tips simultaneously)")
        
    elif mode == 'multi_X1':
        # Single-tip mode from 8-channel pipette
        pipette_right.configure_nozzle_layout(
            style=SINGLE,
            start=starting_nozzle,
            tip_racks=tip_racks_by_mode['multi_X1']
        )
        protocol.comment(f"🔄 Reconfigured Pipette_8: MULTI_X1 mode (single tip from {starting_nozzle})")

def split_volume_into_chunks(volume, min_vol, max_vol, air_gap_volume=0):
    """
    Smart volume splitting algorithm with intelligent redistribution and air gap support

    Splits large volumes into multiple chunks that respect pipette min/max limits.
    Uses intelligent redistribution to avoid chunks below minimum volume.
    Accounts for air gap volume in capacity calculations.

    Args:
        volume: Requested transfer volume (µL)
        min_vol: Pipette minimum volume (µL)
        max_vol: Pipette maximum volume (µL)
        air_gap_volume: Air gap volume to include in each chunk (µL), default 0

    Returns:
        list: Sub-volumes to transfer sequentially (liquid only, air gap applied separately)

    Examples:
        >>> split_volume_into_chunks(500, 100, 1000)
        [500]  # No split needed

        >>> split_volume_into_chunks(1500, 100, 1000)
        [1000, 500]  # Simple split, remainder valid

        >>> split_volume_into_chunks(1050, 100, 1000)
        [525.0, 525.0]  # Smart redistribution (not [1000, 50])

        >>> split_volume_into_chunks(3000, 100, 1000)
        [1000, 1000, 1000]  # Even division

        >>> split_volume_into_chunks(1500, 100, 1000, air_gap_volume=100)
        [750.0, 750.0]  # Air gap reduces effective capacity: (1000-100)=900 per chunk

        >>> split_volume_into_chunks(1000, 100, 1000, air_gap_volume=100)
        [500.0, 500.0]  # Each chunk: 500µL liquid + 100µL air = 600µL total
    """
    import math

    # Calculate effective max volume accounting for air gap
    effective_max_vol = max_vol - air_gap_volume

    # Ensure effective max is still above minimum after air gap subtraction
    if effective_max_vol < min_vol:
        raise ValueError(f"Air gap ({air_gap_volume}µL) leaves insufficient capacity. "
                         f"Effective max ({effective_max_vol}µL) < minimum ({min_vol}µL)")

    # No split needed if within effective range
    if volume <= effective_max_vol:
        return [volume]

    # Calculate how many chunks we need
    num_chunks = math.ceil(volume / effective_max_vol)

    # Try naive split: use effective_max_vol chunks + remainder
    full_chunks = int(volume // effective_max_vol)
    remainder = volume % effective_max_vol

    # Check if remainder is valid (above minimum or exactly zero)
    if remainder == 0:
        # Perfect division into effective_max_vol chunks
        return [effective_max_vol] * full_chunks
    elif remainder >= min_vol:
        # Remainder is valid, use it
        return [effective_max_vol] * full_chunks + [remainder]
    else:
        # Remainder too small - redistribute evenly to keep all chunks above minimum
        chunk_size = volume / num_chunks
        return [chunk_size] * num_chunks

def calculate_distribution_volumes(base_volume, num_wells, distribution_pattern):
    """
    Calculate volume for each destination well based on distribution pattern
    
    Args:
        base_volume: Base volume in µL from CSV 'Distribution Volume (ul)'
        num_wells: Number of destination wells
        distribution_pattern: Distribution type string:
            - "equal": Same volume in all wells
            - "geometric:2": 2x growth (20→40→80→160)
            - "geometric:0.5": 0.5x decay / serial dilution (100→50→25→12.5)
            - "geometric:2:desc": 2x descending (160→80→40→20)
    
    Returns:
        list: Volumes for each destination well [vol1, vol2, vol3, ...]
    
    Examples:
        >>> calculate_distribution_volumes(20, 4, "equal")
        [20, 20, 20, 20]
        
        >>> calculate_distribution_volumes(20, 4, "geometric:2")
        [20, 40, 80, 160]
        
        >>> calculate_distribution_volumes(100, 4, "geometric:0.5")
        [100, 50.0, 25.0, 12.5]
        
        >>> calculate_distribution_volumes(20, 4, "geometric:2:desc")
        [160, 80, 40, 20]
    """
    pattern_lower = distribution_pattern.strip().lower()
    
    if pattern_lower == 'equal':
        # Same volume for all destinations
        return [base_volume] * num_wells
    
    elif pattern_lower.startswith('geometric:'):
        # Parse geometric pattern: geometric:factor or geometric:factor:desc
        parts = pattern_lower.split(':')
        
        if len(parts) < 2:
            raise ValueError(f"Invalid geometric pattern: '{distribution_pattern}'. Expected format: 'geometric:factor' or 'geometric:factor:desc'")
        
        try:
            factor = float(parts[1])
        except ValueError:
            raise ValueError(f"Invalid geometric factor: '{parts[1]}'. Must be a number (e.g., 2, 0.5, 1.5)")
        
        if factor <= 0:
            raise ValueError(f"Geometric factor must be > 0, got {factor}")
        
        # Calculate volumes with geometric progression
        volumes = [base_volume * (factor ** i) for i in range(num_wells)]
        
        # Check for descending order
        if len(parts) >= 3 and parts[2] == 'desc':
            volumes.reverse()
        
        return volumes
    
    else:
        raise ValueError(f"Unknown distribution pattern: '{distribution_pattern}'. Valid options: 'equal', 'geometric:factor', 'geometric:factor:desc'")

# plan_distribution_trips() function has been REMOVED
# The built-in pipette.distribute() API handles trip planning automatically via carryover=True parameter

def validate_distribution_wells_for_multi_mode(dest_wells: list, mode: str, row_index: int):
    """
    Validate that destination wells are compatible with multi-channel pipette operation.

    In multi mode (8-channel with all nozzles active), each well name represents a COLUMN operation:
    - 96-well plate: A1 means column 1 (all 8 wells A1-H1)
    - 384-well plate: A1 means column 1 with A-interleaving (A1,C1,E1,G1,I1,K1,M1,O1)
                      B1 means column 1 with B-interleaving (B1,D1,F1,H1,J1,L1,N1,P1)

    For distribution to work correctly with multi-channel:
    - All destination wells MUST have the same row letter (same interleaving pattern)
    - Valid: A1|A2|A3|A4 (all A-row = distribute to columns 1,2,3,4)
    - Valid: B1|B2|B3 (all B-row = distribute to columns 1,2,3 with B-interleaving)
    - INVALID: A1|B2|A3 (mixing rows = physically impossible with 8-channel)

    Args:
        dest_wells: List of destination well names (e.g., ['A1', 'A2', 'A3'])
        mode: Pipette mode ('single_X1', 'multi_X1', 'multi')
        row_index: CSV row index for error messages (0-based)

    Raises:
        ValueError: If wells are incompatible with multi-channel operation
    """
    if mode != 'multi':
        return  # Only validate for full multi-channel mode

    if not dest_wells:
        return

    # Extract row letters from all destination wells
    row_letters = set()
    for well in dest_wells:
        well = well.strip().upper()
        if not well:
            continue
        # Well format is like A1, B12, P24 - first character(s) are row letter(s)
        row_letter = ''.join(c for c in well if c.isalpha())
        if row_letter:
            row_letters.add(row_letter)

    # All wells must have the same row letter for multi-channel distribution
    if len(row_letters) > 1:
        wells_str = '|'.join(dest_wells)
        raise ValueError(
            f"Row {row_index + 2}: Distribution wells '{wells_str}' are incompatible with multi-channel mode. "
            f"Found mixed row letters: {sorted(row_letters)}. "
            f"In multi mode, ALL destination wells must have the SAME row letter (e.g., A1|A2|A3 or B1|B2|B3) "
            f"because each well represents a full column operation. "
            f"Use single_X1 or multi_X1 mode for individual well distribution."
        )

def perform_distribution(transfer, pipette, loaded_labware, pipette_config, liquid_contact_config,
                        wick_config, delay_config, mixing_config, mixing_repetitions,
                        source_remixing, mixed_source_wells, general_settings,
                        protocol, mode, row_index):
    """
    Execute distribution transfer: one source well → multiple destination wells with varying volumes

    Uses built-in pipette.distribute() API for automatic trip planning and execution.

    Handles:
    - Equal distribution (same volume to all destinations)
    - Geometric distribution (varying volumes: growth or decay patterns)
    - Automatic multi-trip handling via distribute() API
    - Tip management per CSV 'Tip Action' parameter
    - Source mixing (before aspirate) if configured
    - Air gap support between destinations

    NOTE: Per-destination mixing is NOT supported in distribution mode (distribute() ignores mix_after).
          Use cherry-pick mode if destination mixing is required.

    Args:
        transfer: CSV row dict with distribution parameters
        pipette: OpenTrons pipette object
        loaded_labware: Dict of loaded labware objects
        pipette_config: Pipette configuration from labware_dict
        liquid_contact_config: Pre-aspirate contact settings
        wick_config: Post-aspirate wick settings
        delay_config: Delay settings
        mixing_config: Mixing configuration
        mixing_repetitions: Number of mix cycles
        source_remixing: How often to remix source ("once", "always")
        mixed_source_wells: Set tracking which source wells have been mixed
        general_settings: General protocol settings
        protocol: ProtocolContext for logging
        mode: Pipette mode (single_X1, multi_X1, multi)
        row_index: CSV row index for error messages (0-based)

    Returns:
        bool: tip_contacted flag (True if tip has contacted liquid)
    """
    # ========== Parse CSV row ==========
    source_labware_name = transfer['Source Labware']
    source_well = transfer['Source Well']
    dest_labware_name = transfer['Dest Labware']
    dest_wells_str = transfer['Dest Well']
    dest_well_names = dest_wells_str.split('|')  # Split pipe-delimited list

    # ========== Validate wells for multi-channel compatibility ==========
    validate_distribution_wells_for_multi_mode(dest_well_names, mode, row_index)

    base_volume = float(transfer['Distribution Volume (ul)'])
    distribution_pattern = transfer.get('Distribution', 'equal').strip().lower()

    # Rate multipliers (optional, default 1.0)
    rate_aspirate = float(transfer.get('Flow Aspirate', 1.0))
    rate_dispense = float(transfer.get('Flow Dispense', 1.0))

    # Air gap parameters
    air_gap_volume = float(transfer.get('Air Gap', 0)) if transfer.get('Air Gap') else 0

    # Mixing parameters
    mix_volume = float(transfer.get('Mix Volume', 0)) if transfer.get('Mix Volume') else 0

    # ========== Calculate distribution volumes ==========
    try:
        dest_volumes = calculate_distribution_volumes(base_volume, len(dest_well_names), distribution_pattern)
    except ValueError as e:
        protocol.comment(f"Distribution volume calculation failed: {e}")
        raise

    protocol.comment(f"Distribution: {source_well} → {len(dest_well_names)} wells, pattern: {distribution_pattern}")

    # ========== Get labware objects ==========
    source_labware = loaded_labware[source_labware_name]
    dest_labware = loaded_labware[dest_labware_name]

    # Get source well object
    source_well_obj = source_labware[source_well]

    # Build destination well objects list
    dest_well_objs = [dest_labware[well_name] for well_name in dest_well_names]

    # ========== Source mixing (before aspirate) ==========
    tip_contacted = False
    source_well_key = f"{source_labware_name}:{source_well}"
    mixing_location = mixing_config.get('location', 'none')
    mixing_enabled = mixing_config.get('enabled', False)

    should_mix_source = (
        mixing_enabled and
        mix_volume > 0 and
        mixing_location == 'source' and
        (source_remixing == 'always' or source_well_key not in mixed_source_wells)
    )

    # Build mix_before tuple for distribute() call
    mix_tuple = None
    if should_mix_source:
        source_mix_location, source_mix_desc = determine_well_position(transfer, source_well_obj, 'mix')
        protocol.comment(f"Mixing source {source_well} at {source_mix_desc}: {mixing_repetitions}x with {mix_volume}µL")
        mix_tuple = (mixing_repetitions, mix_volume, source_mix_location)
        mixed_source_wells.add(source_well_key)

    # ========== Tip management =====
    tip_action = determine_tip_action(transfer, row_index)

    # Auto-convert 'keep' to 'drop' for multi_X1 mode (partial tip config doesn't support return_tip)
    if mode == 'multi_X1' and tip_action == 'keep':
        protocol.comment(f"Warning row {row_index+1}: Tip Action 'keep' not supported in multi_X1 mode. Auto-converting to 'drop'.")
        tip_action = 'drop'

    # Ensure we have a tip for distribution
    if not pipette.has_tip:
        pipette.pick_up_tip()
        tip_contacted = False

    # ========== Liquid contact (optional) =====
    if not tip_contacted and liquid_contact_config.get('enabled', False):
        perform_liquid_contact(pipette, source_well_obj, transfer, protocol, liquid_contact_config)
        tip_contacted = True

    # ========== Get source position ==========
    source_location, source_pos_desc = determine_well_position(transfer, source_well_obj, 'source')

    # ========== Execute distribution using built-in API ==========
    protocol.comment(f"Distributing from {source_well} at {source_pos_desc}")

    # Note: distribute() handles trip planning automatically
    # disposal_volume = 0 (user decision - keep simple)
    pipette.distribute(
        volume=dest_volumes,
        source=source_location,
        dest=dest_well_objs,
        air_gap=air_gap_volume,
        disposal_volume=0,
        mix_before=mix_tuple,
        blow_out=True,
        blowout_location='source well',
        new_tip='never',  # We manage tips manually via tip_action
        carryover=True  # Enable multi-trip if volumes exceed capacity
    )

    # ========== Post-distribution tip management =====
    if tip_action == 'drop' and pipette.has_tip:
        pipette.drop_tip()
        tip_contacted = False
    elif tip_action == 'keep':
        # Keep tip for next operation (or return at protocol end)
        pass

    return tip_contacted

def run(protocol: protocol_api.ProtocolContext):
    """Main protocol execution"""

    # Parse embedded data using get_values()
    protocol.comment("Starting Cherry-Pick Protocol")

    # Get configuration data using get_values function
    # Note: custom protocol_name logged after config is parsed (see below)
    try:
        [labware_dict, settings, csv_data] = get_values(  # noqa: F821
            "labware_dict", "settings", "csv_data")
    except Exception as e:
        raise ValueError(f"Failed to parse configuration: {e}")

    # Parse CSV
    try:
        csv_reader = csv.DictReader(StringIO(csv_data))
        transfers = list(csv_reader)
    except Exception as e:
        raise ValueError(f"Failed to parse CSV: {e}")

    # Validate that CSV labware references exactly match settings.toml definitions
    try:
        validate_csv_labware_match(settings, transfers)
    except Exception as e:
        raise ValueError(f"Labware validation failed: {e}")

    # Extract liquid handling configuration (with defaults)
    liquid_handling = settings['settings'].get('liquid_handling', {})

    # --- Preset resolution ---
    active_preset = liquid_handling.get('active_preset', '')
    if active_preset:
        presets = liquid_handling.get('presets', {})
        if active_preset not in presets:
            raise ValueError(f"Unknown liquid handling preset: '{active_preset}'. Available: {list(presets.keys())}")
        preset_values = presets[active_preset]
        protocol.comment(f"Applying liquid handling preset: {active_preset}")
        # Override individual settings with preset values
        for key in ('pre_aspirate_contact', 'post_aspirate_wick', 'delays', 'push_out', 'mixing'):
            if key in preset_values:
                liquid_handling[key] = preset_values[key]

    liquid_contact_config = liquid_handling.get('pre_aspirate_contact', {'enabled': True, 'position_offset_percent': 20, 'aspirate_volume': 0})
    wick_config = liquid_handling.get('post_aspirate_wick', {'enabled': True, 'radius': 0.8, 'v_offset_mm': -1.5, 'speed': 20})
    delay_config = liquid_handling.get('delays', {'post_aspirate': 0})
    push_out_config = liquid_handling.get('push_out', {'enabled': False, 'volume_ul': 5})

    # Extract mixing configuration
    mixing_config = liquid_handling.get('mixing', {'enabled': False, 'location': 'destination', 'repetitions': 3, 'source_remixing': 'once'})
    mixing_enabled = mixing_config.get('enabled', False)
    mixing_location = mixing_config.get('location', 'destination')
    mixing_repetitions = mixing_config.get('repetitions', 3)
    source_remixing = mixing_config.get('source_remixing', 'once')

    # Validate mixing configuration
    if mixing_location not in ['destination', 'source', 'none']:
        raise ValueError(f"Invalid mixing location: '{mixing_location}'. Must be 'destination', 'source', or 'none'")
    if not isinstance(mixing_repetitions, int) or mixing_repetitions < 1:
        raise ValueError(f"Invalid mixing repetitions: '{mixing_repetitions}'. Must be an integer >= 1")
    if source_remixing not in ['once', 'always']:
        raise ValueError(f"Invalid source_remixing: '{source_remixing}'. Must be 'once' or 'always'")

    # Warn about distribution mode + mixing (mixing is ignored in distribution)
    # Only emit warning if CSV actually contains distribution-mode rows
    if mixing_enabled and mixing_location == 'destination':
        has_distribution_rows = any(
            '|' in t.get('Dest Well', '') or t.get('Distribution Volume (ul)', '').strip() != ''
            for t in transfers
        )
        if has_distribution_rows:
            protocol.comment("⚠️  NOTE: Destination mixing is NOT supported in distribution mode (ignored by distribute() API).")
            protocol.comment("    If you need per-destination mixing, use cherry-pick mode instead.")

    # Extract general settings
    general_settings = settings['settings']['general']

    # Log custom protocol name if configured
    protocol_name = general_settings.get('protocol_name', '')
    if protocol_name:
        protocol.comment(f"Protocol: {protocol_name}")

    # Apply optional head speed overrides from settings.general.head_speed
    head_speed_cfg = general_settings.get('head_speed') if isinstance(general_settings, dict) else None
    speed = head_speed_cfg["speed"] if head_speed_cfg else 400

    # Create lookup mappings from table array structure
    available_pipettes = {}

    # Process pipette definitions (now array of tables)
    if 'pipettes' in labware_dict:
        for pipette_item in labware_dict['pipettes']:
            pipette_name = pipette_item['name']
            available_pipettes[pipette_name] = pipette_item

    # Load labware and modules from settings
    loaded_labware = {}
    used_slots = set()
    modules_to_manage = []  # Track modules for cleanup at protocol end

    for plate_config in settings['settings']['working_plate']:
        slot = plate_config['position_rack']
        plate_type = plate_config.get('type', 'unknown')

        # Check for slot conflicts
        if slot in used_slots:
            raise ValueError(f"Slot conflict: Slot {slot} is already occupied")

        # Handle modules separately
        if plate_type == 'module':
            try:
                module_ctrl = initialize_heater_shaker_module(protocol, plate_config)
                modules_to_manage.append(module_ctrl)
                used_slots.add(slot)
                protocol.comment(f"Module initialized in slot {slot}")
            except Exception as e:
                protocol.comment(f"Failed to initialize module in slot {slot}: {e}")
                raise
            continue  # Skip normal labware loading for modules

        # Normal labware loading
        labware_id = plate_config['labware_id']  # Now using labware_id

        # Create unique labware name using labware_id_position_rack convention
        unique_labware_name = f"{labware_id}_{slot}"

        # Load the labware using the labware_id directly (no more mapping needed)
        try:
            loaded = protocol.load_labware(labware_id, slot)
            loaded_labware[unique_labware_name] = loaded  # Store with unique name for CSV compatibility
            used_slots.add(slot)

            # Apply labware offsets if configured in plate_config (from settings.toml or offset_database)
            offset_x = float(plate_config.get('offset_x', 0.0))
            offset_y = float(plate_config.get('offset_y', 0.0))
            offset_z = float(plate_config.get('offset_z', 0.0))

            if offset_x != 0.0 or offset_y != 0.0 or offset_z != 0.0:
                loaded.set_offset(x=offset_x, y=offset_y, z=offset_z)
                protocol.comment(f"Applied offset to {unique_labware_name}: x={offset_x:.3f}mm, y={offset_y:.3f}mm, z={offset_z:.3f}mm")

        except Exception as e:
            protocol.comment(f"Failed to load '{labware_id}': {e}")
            raise

    # Labware and module loading complete (no dynamic CSV loading)

    # Validate multi mode compatibility now that labware objects are available
    try:
        validate_multi_mode_compatibility(settings, loaded_labware)
    except ValueError as e:
        raise ValueError(f"Multi mode validation failed: {e}")

    # ========== DUAL-PIPETTE MODE DETECTION & SETUP ==========

    # Check if dual-pipette mode is enabled
    mode = general_settings.get('mode', 'single_X1')
    is_dual_mode = (mode == 'dual')

    # Analyze CSV to detect if Mode column exists and extract used modes
    csv_modes = set()
    csv_has_mode_column = False
    if transfers and 'Mode' in transfers[0]:
        csv_has_mode_column = True
        for transfer in transfers:
            transfer_mode = transfer.get('Mode', '').strip()
            if transfer_mode:
                csv_modes.add(transfer_mode)
        if csv_modes:
            is_dual_mode = True  # CSV overrides settings if Mode column present

    protocol.comment(f"Dual-pipette mode: {'ENABLED' if is_dual_mode else 'DISABLED (legacy single-pipette)'}")

    if not is_dual_mode:
        # ========== LEGACY SINGLE-PIPETTE MODE (Backward Compatibility) ==========
        protocol.comment(f"Using legacy mode: {mode}")

        # Determine which pipette to use
        if mode == "single_X1":
            pipette_key = "Pipette_1"
        elif mode in ["multi_X1", "multi"]:
            pipette_key = "Pipette_8"
        else:
            raise ValueError(f"Unknown mode: {mode}. Valid modes: single_X1, multi_X1, multi, dual")

        # Get pipette configuration from table array structure
        if pipette_key not in available_pipettes:
            raise ValueError(f"Pipette '{pipette_key}' not found in pipette definitions")

        pipette_config = available_pipettes[pipette_key]
        pipette_ot_id = pipette_config['opentrons_id']
        mount = pipette_config['preferred_mount']

        # Find connected tip racks
        tip_racks = []

        for plate_config in settings['settings']['working_plate']:
            if plate_config['type'] == 'tip' and 'connection' in plate_config:
                if plate_config['connection'] == pipette_key:
                    # Create unique tip rack name using labware_id_position_rack convention
                    tip_labware_id = plate_config['labware_id']
                    tip_slot = plate_config['position_rack']
                    tip_rack_name = f"{tip_labware_id}_{tip_slot}"

                    if tip_rack_name in loaded_labware:
                        tip_racks.append(loaded_labware[tip_rack_name])

        if not tip_racks:
            raise ValueError(f"No tip racks found for {pipette_key}")

        # Load the single pipette
        try:
            pipette = protocol.load_instrument(pipette_ot_id, mount, tip_racks=tip_racks)
        except Exception as e:
            protocol.comment(f"Failed to load pipette: {e}")
            raise

        # Set Default Speed
        pipette.default_speed = speed

        # Configure single-tip mode if using multi_X1 mode
        if mode == "multi_X1" and pipette_config['channels'] > 1:
            starting_nozzle = settings['settings']['general']['starting_tip_well']
            try:
                pipette.configure_nozzle_layout(
                    style=SINGLE,
                    start=starting_nozzle,
                    tip_racks=tip_racks
                )
            except Exception as e:
                protocol.comment(f"Failed to configure single-tip mode: {e}")
                raise

        # For legacy mode compatibility, set these variables for transfer loop
        pipette_left = None
        pipette_right = None
        if mount == 'left':
            pipette_left = pipette
        else:
            pipette_right = pipette
        tip_racks_by_mode = {}
        active_pipette = pipette
        active_pipette_config = pipette_config
        current_mode = mode

    else:
        # ========== NEW DUAL-PIPETTE MODE ==========

        # Validate CSV modes
        valid_modes = {'multi', 'multi_X1', 'single_X1'}
        invalid_modes = csv_modes - valid_modes
        if invalid_modes:
            raise ValueError(f"Invalid Mode values in CSV: {invalid_modes}. Valid: {valid_modes}")

        protocol.comment(f"CSV modes detected: {', '.join(sorted(csv_modes)) if csv_modes else 'none'}")

        # Organize tip racks by mode
        tip_racks_by_mode = {
            'multi': [],
            'multi_X1': [],
            'single_X1': []
        }

        for plate_config in settings['settings']['working_plate']:
            if plate_config['type'] == 'tip' and 'connection' in plate_config:
                tip_mode = plate_config.get('mode')

                # If no mode field, this is a legacy config - assign based on connection
                if not tip_mode:
                    # Legacy: assign tip rack to all modes for this pipette
                    connection = plate_config['connection']
                    if connection == 'Pipette_1':
                        tip_mode = 'single_X1'
                    elif connection == 'Pipette_8':
                        # In legacy, we don't know if it's multi or multi_X1, so allow both
                        protocol.comment(f"Warning: Tip rack in slot {plate_config['position_rack']} has no 'mode' field - assigning to both multi and multi_X1 (may cause conflicts)")
                        tip_mode = 'multi'  # Default to multi

                tip_labware_id = plate_config['labware_id']
                tip_slot = plate_config['position_rack']
                tip_rack_name = f"{tip_labware_id}_{tip_slot}"

                if tip_rack_name in loaded_labware:
                    tip_racks_by_mode[tip_mode].append(loaded_labware[tip_rack_name])
                    protocol.comment(f"Tip rack {tip_rack_name} assigned to mode: {tip_mode}")

        # Validate: modes used in CSV must have tip racks configured
        for csv_mode in csv_modes:
            if not tip_racks_by_mode[csv_mode]:
                raise ValueError(
                    f"CSV uses '{csv_mode}' mode but no tip racks configured for this mode in settings.toml\n"
                    f"Add [[settings.working_plate]] entries with type='tip', connection='Pipette_X', and mode='{csv_mode}'"
                )

        # Load pipettes based on which modes are used
        pipette_left = None
        pipette_right = None
        starting_nozzle = settings['settings']['general']['starting_tip_well']

        # Load Pipette_1 (left) if single_X1 mode is used
        if 'single_X1' in csv_modes:
            if 'Pipette_1' not in available_pipettes:
                raise ValueError("CSV uses 'single_X1' mode but Pipette_1 not defined in labware_dict.toml")

            pipette_1_config = available_pipettes['Pipette_1']
            pipette_left = protocol.load_instrument(
                pipette_1_config['opentrons_id'],
                'left',
                tip_racks=tip_racks_by_mode['single_X1']
            )
            pipette_left.default_speed = speed
            protocol.comment(f"✓ Loaded Pipette_1 ({pipette_1_config['opentrons_id']}) on LEFT mount for single_X1 mode")

        # Load Pipette_8 (right) if multi or multi_X1 mode is used
        if 'multi' in csv_modes or 'multi_X1' in csv_modes:
            if 'Pipette_8' not in available_pipettes:
                raise ValueError("CSV uses 'multi' or 'multi_X1' mode but Pipette_8 not defined in labware_dict.toml")

            pipette_8_config = available_pipettes['Pipette_8']

            # Determine initial nozzle configuration based on first mode encountered
            # (we'll reconfigure on-the-fly as needed during transfers)
            initial_mode = None
            for transfer in transfers:
                transfer_mode = transfer.get('Mode', '').strip()
                if transfer_mode in ['multi', 'multi_X1']:
                    initial_mode = transfer_mode
                    break

            if not initial_mode:
                # Fallback: prefer multi over multi_X1
                initial_mode = 'multi' if 'multi' in csv_modes else 'multi_X1'

            # Load pipette with initial configuration
            if initial_mode == 'multi':
                pipette_right = protocol.load_instrument(
                    pipette_8_config['opentrons_id'],
                    'right',
                    tip_racks=tip_racks_by_mode['multi']
                )
                pipette_right.default_speed = speed
                pipette_right.configure_nozzle_layout(
                    style=ALL,
                    tip_racks=tip_racks_by_mode['multi']
                )
                protocol.comment(f"✓ Loaded Pipette_8 ({pipette_8_config['opentrons_id']}) on RIGHT mount - MULTI mode (8 tips)")
            else:  # multi_X1
                pipette_right = protocol.load_instrument(
                    pipette_8_config['opentrons_id'],
                    'right',
                    tip_racks=tip_racks_by_mode['multi_X1']
                )
                pipette_right.default_speed = speed
                pipette_right.configure_nozzle_layout(
                    style=SINGLE,
                    start=starting_nozzle,
                    tip_racks=tip_racks_by_mode['multi_X1']
                )
                protocol.comment(f"✓ Loaded Pipette_8 ({pipette_8_config['opentrons_id']}) on RIGHT mount - MULTI_X1 mode ({starting_nozzle})")

            current_mode = initial_mode
        else:
            current_mode = None

        # Verify at least one pipette was loaded
        if pipette_left is None and pipette_right is None:
            raise ValueError("No valid modes found in CSV - at least one transfer with Mode column required in dual mode")

    # Execute transfers
    tip_contacted = False  # Track if current tip has contacted liquid
    last_tip_action = None  # Track the last transfer's tip action for final cleanup
    mixed_source_wells = set()  # Track which source wells have been mixed (for source_remixing='once')
    prev_row_was_home = False  # Track if previous row was HOME control

    # Execute each transfer
    for i, transfer in enumerate(transfers):
        # === HOME CONTROL ROW CHECK ===
        # If all non-empty columns contain "HOME", re-home the robot and skip this row
        if is_home_control_row(transfer):
            protocol.comment(f"Row {i+1}: HOME control - Re-homing robot to correct any precision drift")
            protocol.home()
            prev_row_was_home = True
            continue
        # === END HOME CONTROL CHECK ===

        # === HOME→NEW VALIDATION (Firmware requirement) ===
        # Robot drops tips when homing, so next row MUST pick up new tip
        if prev_row_was_home:
            tip_action = transfer.get('Tip Action', '').strip().lower()
            if tip_action != 'new':
                raise ValueError(
                    f"Row {i+1}: Row after HOME control MUST have Tip Action: new (got '{tip_action or 'empty'}'). "
                    f"This is a firmware requirement - the robot drops tips when homing."
                )
            prev_row_was_home = False
        # === END HOME→NEW VALIDATION ===

        # Parse transfer parameters
        source_labware_name = transfer['Source Labware']
        source_well = transfer['Source Well']
        dest_labware_name = transfer['Dest Labware']
        dest_well_str = transfer['Dest Well']

        # ========== DUAL-PIPETTE MODE SWITCHING ==========
        if is_dual_mode:
            # Get mode for this transfer
            transfer_mode = transfer.get('Mode', '').strip()
            if not transfer_mode:
                raise ValueError(f"Row {i+1}: Missing 'Mode' column value in dual-pipette mode")

            # Mode switch detection for Pipette_8 (multi <-> multi_X1 transitions)
            if transfer_mode in ['multi', 'multi_X1'] and transfer_mode != current_mode:
                protocol.comment(f"Mode switch detected: {current_mode} → {transfer_mode}")

                # CRITICAL: Drop tip before reconfiguring (API requirement)
                if pipette_right and pipette_right.has_tip:
                    protocol.comment("Dropping tip before nozzle reconfiguration")
                    pipette_right.drop_tip()
                    tip_contacted = False

                # Reconfigure nozzle layout
                reconfigure_pipette_for_mode(pipette_right, transfer_mode, tip_racks_by_mode, starting_nozzle, protocol)
                current_mode = transfer_mode

            # Select active pipette for this transfer
            if transfer_mode == 'single_X1':
                active_pipette = pipette_left
                active_pipette_config = available_pipettes['Pipette_1']
            elif transfer_mode in ['multi', 'multi_X1']:
                active_pipette = pipette_right
                active_pipette_config = available_pipettes['Pipette_8']
            else:
                raise ValueError(f"Row {i+1}: Invalid Mode '{transfer_mode}'. Valid: multi, multi_X1, single_X1")

            # Update reference variables for backward compatibility with existing code
            pipette = active_pipette
            pipette_config = active_pipette_config
            mode = transfer_mode

        # ========== DISTRIBUTION MODE DETECTION ==========
        # Distribution mode: one source → multiple destinations with varying volumes
        # Detected by: pipe delimiter in Dest Well (e.g., "B1|B2|B3") OR Distribution Volume column present
        has_pipe_delimiter = '|' in dest_well_str
        has_distribution_volume = transfer.get('Distribution Volume (ul)', '').strip() != ''

        if has_pipe_delimiter or has_distribution_volume:
            # === DISTRIBUTION MODE ===
            # Validate distribution parameters
            if has_pipe_delimiter and not has_distribution_volume:
                raise ValueError(f"Row {i+1}: Pipe-delimited Dest Well '{dest_well_str}' requires 'Distribution Volume (ul)' column")

            if has_distribution_volume and not has_pipe_delimiter:
                protocol.comment(f"Warning row {i+1}: 'Distribution Volume (ul)' without pipe delimiter - treating as single destination")

            # Execute distribution and continue to next transfer
            try:
                tip_contacted = perform_distribution(
                    transfer=transfer,
                    pipette=pipette,
                    loaded_labware=loaded_labware,
                    pipette_config=pipette_config,
                    liquid_contact_config=liquid_contact_config,
                    wick_config=wick_config,
                    delay_config=delay_config,
                    mixing_config=mixing_config,
                    mixing_repetitions=mixing_repetitions,
                    source_remixing=source_remixing,
                    mixed_source_wells=mixed_source_wells,
                    general_settings=general_settings,
                    protocol=protocol,
                    mode=mode,
                    row_index=i
                )
                # Update last_tip_action for final cleanup
                last_tip_action = transfer['Tip Action'].lower().strip()
                continue  # Skip to next CSV row
            except Exception as e:
                protocol.comment(f"Distribution failed at row {i+1}: {e}")
                raise

        # === EXISTING CHERRY-PICK MODE ===
        dest_well = dest_well_str  # Single destination well
        requested_volume = float(transfer['Volume (ul)'])
        mix_volume = float(transfer.get('Mix Volume', 0)) if transfer.get('Mix Volume') else 0

        # Rate multipliers (optional in CSV, default 1.0 = normal speed)
        rate_aspirate = float(transfer.get('Flow Aspirate', 1.0))
        rate_dispense = float(transfer.get('Flow Dispense', 1.0))

        # Air gap parameters (optional in CSV, default 0 = disabled)
        air_gap_volume = float(transfer.get('Air Gap', 0)) if transfer.get('Air Gap') else 0
        air_gap_rate = float(transfer.get('Air Gap Rate', 1.0))

        # Tip action - REQUIRED column in CSV
        tip_action = determine_tip_action(transfer, i)

        # Auto-convert 'keep' to 'drop' for multi_X1 mode (partial tip config doesn't support return_tip)
        if mode == 'multi_X1' and tip_action == 'keep':
            protocol.comment(f"Warning row {i+1}: Tip Action 'keep' not supported in multi_X1 mode. Auto-converting to 'drop'.")
            tip_action = 'drop'

        # Get pipette volume range for splitting algorithm
        min_vol, max_vol = pipette_config['volume_range']

        # Calculate sub-volumes using smart splitting algorithm
        sub_volumes = split_volume_into_chunks(requested_volume, min_vol, max_vol, air_gap_volume)

        # Get labware objects
        source_labware = loaded_labware[source_labware_name]
        dest_labware = loaded_labware[dest_labware_name]

        # Handle well mapping based on mode
        if mode == "multi":
            # Get well counts directly from loaded labware objects
            source_well_count = len(loaded_labware[source_labware_name].wells())
            dest_well_count = len(loaded_labware[dest_labware_name].wells())

            # Get multi-channel well patterns
            source_wells = get_multi_channel_wells(source_labware, source_well, source_well_count)
            dest_wells = get_multi_channel_wells(dest_labware, dest_well, dest_well_count)

            protocol.comment(f"Multi mode: {source_well} → {len(source_wells)} source wells, {dest_well} → {len(dest_wells)} dest wells")

            # Use first well for location (8-channel will handle all wells) with dynamic positioning
            source_location, source_pos_desc = determine_well_position(transfer, source_wells[0], 'source')
            dest_location, dest_pos_desc = determine_well_position(transfer, dest_wells[0], 'dest')
            primary_source_well = source_wells[0]
        else:
            # Single well mode (single_X1, multi_X1) with dynamic positioning
            source_location, source_pos_desc = determine_well_position(transfer, source_labware[source_well], 'source')
            dest_location, dest_pos_desc = determine_well_position(transfer, dest_labware[dest_well], 'dest')
            primary_source_well = source_labware[source_well]

        # Handle tip action based on per-transfer determination
        action_taken, new_tip_picked = execute_tip_action(tip_action, pipette, protocol, f"Transfer {i+1}")

        # Reset contact flag if new tip was picked up
        if new_tip_picked:
            tip_contacted = False

        # Execute transfer in chunks (may be single chunk if volume within range)
        for chunk_idx, chunk_vol in enumerate(sub_volumes):
            is_first_chunk = (chunk_idx == 0)
            is_last_chunk = (chunk_idx == len(sub_volumes) - 1)

            # Perform liquid contact only on first chunk (tip conditioning)
            if is_first_chunk and not tip_contacted and liquid_contact_config.get('enabled', False):
                perform_liquid_contact(pipette, primary_source_well, transfer, protocol, liquid_contact_config)
                tip_contacted = True

            # Source mixing (before aspiration, only on first chunk)
            if is_first_chunk and mixing_enabled and mix_volume > 0 and mixing_location == 'source':
                source_well_key = f"{source_labware_name}:{source_well}"

                # Determine if we should mix based on source_remixing setting
                should_mix_source = (
                    source_remixing == 'always' or
                    (source_remixing == 'once' and source_well_key not in mixed_source_wells)
                )

                if should_mix_source:
                    if mode == "multi":
                        source_mix_location, source_mix_desc = determine_well_position(transfer, source_wells[0], 'mix')
                    else:
                        source_mix_location, source_mix_desc = determine_well_position(transfer, source_labware[source_well], 'mix')

                    pipette.mix(mixing_repetitions, mix_volume, source_mix_location)
                    mixed_source_wells.add(source_well_key)

            # Perform transfer
            try:
                # Aspirate
                pipette.aspirate(chunk_vol, source_location, rate=rate_aspirate)

                # Post-aspirate actions (wick + delay) - applied to every chunk per user preference
                perform_post_aspirate_actions(
                    pipette, primary_source_well, protocol,
                    wick_config, delay_config.get('post_aspirate', 0)
                )

                # Air gap on every chunk (prevents dripping during all transports)
                chunk_air_gap = air_gap_volume
                if chunk_air_gap > 0:
                    pipette.air_gap(volume=chunk_air_gap, rate=air_gap_rate)

                # Dispense with options (pass actual air gap for this chunk)
                perform_dispense_with_options(
                    pipette, chunk_vol, dest_location, rate_dispense,
                    protocol, push_out_config, mix_volume, chunk_air_gap
                )

                # Mix at destination ONLY if enabled and location setting is "destination" (only on last chunk)
                if is_last_chunk and mixing_enabled and mix_volume > 0 and mixing_location == 'destination':
                    if mode == "multi":
                        # Use first destination well for mixing in multi mode
                        dest_mix_location, dest_mix_desc = determine_well_position(transfer, dest_wells[0], 'mix')
                    else:
                        dest_mix_location, dest_mix_desc = determine_well_position(transfer, dest_labware[dest_well], 'mix')
                    pipette.mix(mixing_repetitions, mix_volume, dest_mix_location)

                # Blow out at destination
                pipette.blow_out(dest_location)

            except Exception as e:
                protocol.comment(f"Transfer failed: {e}")
                raise

        # Track the tip action for final cleanup (last transfer determines final behavior)
        last_tip_action = tip_action

        # Handle post-transfer tip dropping if specified
        if tip_action == 'drop' and pipette.has_tip:
            pipette.drop_tip()
            tip_contacted = False  # Reset contact flag when tip is dropped

    # Handle final tips based on mode
    if is_dual_mode:
        # Dual-pipette mode: handle both pipettes independently
        if pipette_left and pipette_left.has_tip:
            # Single-channel pipette can return tips safely
            if last_tip_action == 'keep':
                protocol.comment("Returning final tip from Pipette_1 (left)")
                pipette_left.return_tip()
            else:
                protocol.comment("Dropping final tip from Pipette_1 (left)")
                pipette_left.drop_tip()

        if pipette_right and pipette_right.has_tip:
            # For multi_X1 mode (partial tip configuration), MUST drop (cannot return)
            # For multi mode (full configuration), can return
            if current_mode == 'multi_X1':
                protocol.comment("Dropping final tip from Pipette_8 (multi_X1 mode cannot return tips)")
                pipette_right.drop_tip()
            elif last_tip_action == 'keep':
                protocol.comment("Returning final tip from Pipette_8 (right)")
                pipette_right.return_tip()
            else:
                protocol.comment("Dropping final tip from Pipette_8 (right)")
                pipette_right.drop_tip()
    else:
        # Legacy single-pipette mode
        if pipette.has_tip:
            if last_tip_action == 'keep':
                # Return tip to rack for potential reuse
                pipette.return_tip()
            else:
                # Drop tip (default for 'drop', 'new', or any other action)
                pipette.drop_tip()

    # Deactivate modules based on persist_after_protocol setting
    deactivate_modules(modules_to_manage, protocol)

    protocol.comment(f"Protocol complete: {len(transfers)} transfers")
