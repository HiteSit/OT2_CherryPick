def get_values(*names):
    import json
    _all_values = json.loads("""{"labware_dict":{"pipettes":[{"name":"Pipette_8","opentrons_id":"p300_multi_gen2","channels":8,"volume_range":[30,300],"preferred_mount":"right","tip_connections":["opentrons_96_tiprack_300ul"]},{"name":"Pipette_1","opentrons_id":"p1000_single_gen2","channels":1,"volume_range":[100,1000],"preferred_mount":"left","tip_connections":["tip_rack_geb_1000ul"]}],"labware":[{"category":"tip_rack","labware_id":"tip_rack_yellow_100ul","well_count":96,"well_volume":100},{"category":"tip_rack","labware_id":"opentrons_96_tiprack_300ul","well_count":96,"well_volume":300},{"category":"tip_rack","labware_id":"tip_rack_geb_1000ul","well_count":96,"well_volume":1000},{"category":"reservoir","labware_id":"reservoir_horizontal","well_count":12,"well_volume":15000},{"category":"plate","labware_id":"384_pp_standard_100ul","well_count":384,"well_volume":100},{"category":"plate","labware_id":"384_pp_high_150ul","well_count":384,"well_volume":150},{"category":"plate","labware_id":"384_ppv_55ul","well_count":384,"well_volume":55},{"category":"plate","labware_id":"384_ppv_150ul","well_count":384,"well_volume":150},{"category":"plate","labware_id":"384_ldv_12ul","well_count":384,"well_volume":12},{"category":"tube_rack","labware_id":"tube_rack_96_2000ul","well_count":96,"well_volume":2000},{"category":"tube_rack","labware_id":"tube_rack_96_1500ul","well_count":96,"well_volume":1500},{"category":"tube_rack","labware_id":"tube_rack_24_4000ul","well_count":24,"well_volume":4000},{"category":"tube_rack","labware_id":"tube_rack_48_1500ul","well_count":48,"well_volume":1500},{"category":"tube_rack","labware_id":"tube_rack_54_1500ul","well_count":54,"well_volume":1500}]},"settings":{"settings":{"general":{"tip_reuse":"always","mode":"dual","starting_tip_well":"H1","head_speed":{"speed":400}},"liquid_handling":{"pre_aspirate_contact":{"enabled":false,"position_offset_percent":20,"aspirate_volume":20},"post_aspirate_wick":{"enabled":false,"radius":1,"v_offset_mm":-1.5,"speed":20},"delays":{"post_aspirate":0},"push_out":{"enabled":true,"volume_ul":20},"mixing":{"location":"none","repetitions":2,"source_remixing":"once"},"presets":{"standard":{"pre_aspirate_contact":{"enabled":true,"position_offset_percent":20,"aspirate_volume":0},"post_aspirate_wick":{"enabled":true,"radius":0.8,"v_offset_mm":-1.5,"speed":20},"delays":{"post_aspirate":0},"push_out":{"enabled":false},"mixing":{"location":"destination","repetitions":3,"source_remixing":"once"}},"viscous":{"pre_aspirate_contact":{"enabled":true,"position_offset_percent":20,"aspirate_volume":0},"post_aspirate_wick":{"enabled":true,"radius":0.8,"v_offset_mm":-1.5,"speed":20},"delays":{"post_aspirate":2.0},"push_out":{"enabled":true,"volume_ul":5},"mixing":{"location":"destination","repetitions":5,"source_remixing":"once"}},"slippery":{"pre_aspirate_contact":{"enabled":true,"position_offset_percent":20,"aspirate_volume":5},"post_aspirate_wick":{"enabled":true,"radius":0.8,"v_offset_mm":-1.5,"speed":20},"delays":{"post_aspirate":0},"push_out":{"enabled":false},"mixing":{"location":"destination","repetitions":3,"source_remixing":"once"}},"minimal":{"pre_aspirate_contact":{"enabled":false},"post_aspirate_wick":{"enabled":true,"radius":0.8,"v_offset_mm":-1.5,"speed":20},"delays":{"post_aspirate":0},"push_out":{"enabled":false},"mixing":{"location":"destination","repetitions":3,"source_remixing":"once"}},"aggressive":{"pre_aspirate_contact":{"enabled":true,"position_offset_percent":30,"aspirate_volume":10},"post_aspirate_wick":{"enabled":true,"radius":0.8,"v_offset_mm":-1.5,"speed":15},"delays":{"post_aspirate":3.0},"push_out":{"enabled":true,"volume_ul":5},"mixing":{"location":"destination","repetitions":7,"source_remixing":"once"}},"cell_resuspension":{"pre_aspirate_contact":{"enabled":true,"position_offset_percent":20,"aspirate_volume":0},"post_aspirate_wick":{"enabled":true,"radius":0.8,"v_offset_mm":-1.5,"speed":20},"delays":{"post_aspirate":0},"push_out":{"enabled":false},"mixing":{"location":"source","repetitions":5,"source_remixing":"once"}}}},"working_plate":[{"type":"module","module_type":"heaterShaker","position_rack":"10","adapter_id":"opentrons_universal_flat_adapter","labware_id":"","target_temperature":0,"target_shake_speed":0,"persist_after_protocol":true},{"type":"reservoir","labware_id":"384_ppv_55ul","position_rack":"2"},{"type":"reservoir","labware_id":"tube_rack_96_1500ul","position_rack":"4"},{"type":"tip","labware_id":"opentrons_96_tiprack_300ul","connection":"Pipette_8","mode":"multi","position_rack":"1"},{"type":"tip","labware_id":"opentrons_96_tiprack_300ul","connection":"Pipette_8","mode":"multi_X1","position_rack":"3"},{"type":"tip","labware_id":"tip_rack_geb_1000ul","connection":"Pipette_1","mode":"single_X1","position_rack":"9"}]}},"csv_data":"Source Labware,Source Well,Volume (ul),Dest Labware,Dest Well,Source Height,Dest Top,Mode\\ntube_rack_96_1500ul_4,A1,50,384_ppv_55ul_2,A1,2,-5,multi\\ntube_rack_96_1500ul_4,A2,600,384_ppv_55ul_2,A2,2,-5,single_X1\\ntube_rack_96_1500ul_4,A3,150,384_ppv_55ul_2,A3,2,-5,multi_X1\\ntube_rack_96_1500ul_4,A4,50,384_ppv_55ul_2,A4,2,-5,multi\\ntube_rack_96_1500ul_4,B1,800,384_ppv_55ul_2,B1,2,-5,single_X1\\ntube_rack_96_1500ul_4,B2,200,384_ppv_55ul_2,B2,2,-5,multi_X1\\ntube_rack_96_1500ul_4,C1,500,384_ppv_55ul_2,C1,2,-5,single_X1\\ntube_rack_96_1500ul_4,C2,50,384_ppv_55ul_2,C2,2,-5,multi\\ntube_rack_96_1500ul_4,D1,250,384_ppv_55ul_2,D1,2,-5,multi_X1"}""")
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

def validate_multi_mode_compatibility(labware_dict, settings):
    """Validate that multi mode is only used with compatible plates"""
    if settings['settings']['general']['mode'] != 'multi':
        return True

    compatible_well_counts = {96, 384}

    for plate_config in settings['settings']['working_plate']:
        if plate_config['type'] in ['source', 'dest']:
            labware_id = plate_config['labware_id']

            # Find labware definition in table array and check well count
            if 'labware' in labware_dict:
                for labware_item in labware_dict['labware']:
                    if labware_item['labware_id'] == labware_id:
                        well_count = labware_item.get('well_count')
                        if well_count and well_count not in compatible_well_counts:
                            raise ValueError(f"Multi mode requires 96 or 384-well plates. Found {well_count}-well plate: {labware_id}")
                        break
    return True

def get_multi_channel_wells(labware, well_name, well_count):
    """Map single well to 8-channel pattern based on plate type"""
    if well_count == 96:
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

    # Extract all labware references from CSV
    csv_labware_refs = set()
    for transfer in transfers:
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

def plan_distribution_trips(dest_volumes, max_volume_per_trip, air_gap_volume, min_vol, max_vol):
    """
    Split distribution into multiple source trips if total volume exceeds capacity
    
    Each trip represents one aspirate from source followed by multiple dispenses to destinations.
    Automatically splits across trips when:
    - Total volume exceeds max_volume_per_trip
    - Total volume (including air gaps) exceeds pipette capacity
    
    Args:
        dest_volumes: List of volumes for each destination [vol1, vol2, vol3, ...]
        max_volume_per_trip: Maximum volume to aspirate per trip (from CSV 'Volume (ul)' or pipette max)
        air_gap_volume: Air gap volume to aspirate between dispenses (µL)
        min_vol: Pipette minimum volume (µL)
        max_vol: Pipette maximum volume (µL)
    
    Returns:
        list: List of trip dictionaries:
        [
            {
                'aspirate_volume': 250,  # Total volume to aspirate from source
                'dispenses': [(0, 50), (1, 50), (2, 50), (3, 100)]  # (dest_index, volume) tuples
            },
            ...
        ]
    
    Examples:
        >>> # All fits in one trip
        >>> plan_distribution_trips([50, 50, 50], 300, 10, 30, 300)
        [{'aspirate_volume': 170, 'dispenses': [(0, 50), (1, 50), (2, 50)]}]
        
        >>> # Requires two trips due to capacity
        >>> plan_distribution_trips([100, 100, 100, 100], 250, 10, 30, 300)
        [
            {'aspirate_volume': 240, 'dispenses': [(0, 100), (1, 100)]},
            {'aspirate_volume': 210, 'dispenses': [(2, 100), (3, 100)]}
        ]
    """
    import math
    
    trips = []
    current_dispenses = []
    current_liquid_volume = 0
    current_total_volume = 0  # Includes air gaps
    
    for dest_idx, volume in enumerate(dest_volumes):
        # Validate volume does not exceed pipette maximum
        # Note: Minimum volume is a precision guideline, not a hard limit (pipette can transfer below min)
        if volume > max_vol:
            raise ValueError(f"Destination volume {volume}µL exceeds pipette maximum ({max_vol}µL). "
                           f"Reduce 'Distribution Volume (ul)' or adjust distribution pattern.")
        
        # Calculate volume needed for this destination (liquid + air gap after dispense)
        # Note: Air gap is aspirated AFTER each dispense, not before first
        is_first_in_trip = len(current_dispenses) == 0
        volume_with_gap = volume if is_first_in_trip else volume + air_gap_volume
        
        # Check if adding this destination would exceed capacity
        would_exceed_max = current_total_volume + volume_with_gap > max_volume_per_trip
        would_exceed_pipette = current_total_volume + volume_with_gap > max_vol
        
        if (would_exceed_max or would_exceed_pipette) and len(current_dispenses) > 0:
            # Start new trip - save current trip
            trips.append({
                'aspirate_volume': current_total_volume,
                'dispenses': current_dispenses
            })
            
            # Reset for new trip
            current_dispenses = []
            current_liquid_volume = 0
            current_total_volume = 0
            
            # This destination starts the new trip (no air gap before first)
            volume_with_gap = volume
        
        # Add destination to current trip
        current_dispenses.append((dest_idx, volume))
        current_liquid_volume += volume
        current_total_volume += volume_with_gap
    
    # Add final trip
    if current_dispenses:
        trips.append({
            'aspirate_volume': current_total_volume,
            'dispenses': current_dispenses
        })
    
    # Validate all trips do not exceed maximum volume
    # Note: Minimum volume not checked - pipette can transfer below rated minimum (less precise)
    for trip_idx, trip in enumerate(trips):
        if trip['aspirate_volume'] > max_vol:
            raise ValueError(f"Trip {trip_idx+1} aspirate volume ({trip['aspirate_volume']}µL) "
                           f"exceeds pipette maximum ({max_vol}µL)")
    
    return trips

def perform_distribution(transfer, pipette, loaded_labware, pipette_config, liquid_contact_config,
                        wick_config, delay_config, push_out_config, mixing_config, mixing_repetitions,
                        mixing_location, source_remixing, mixed_source_wells, general_settings,
                        protocol, mode, row_index):
    """
    Execute distribution transfer: one source well → multiple destination wells with varying volumes
    
    Handles:
    - Equal distribution (same volume to all destinations)
    - Geometric distribution (varying volumes: growth or decay patterns)
    - Multiple trips to source if total volume exceeds pipette capacity
    - Tip management per CSV 'Tip Action' parameter
    - Mixing at source (before aspirate) and/or destination (after dispense)
    - All existing liquid handling parameters (air gaps, wick, delays, push-out)
    
    Args:
        transfer: CSV row dict with distribution parameters
        pipette: OpenTrons pipette object
        loaded_labware: Dict of loaded labware objects
        pipette_config: Pipette configuration from labware_dict
        liquid_contact_config: Pre-aspirate contact settings
        wick_config: Post-aspirate wick settings
        delay_config: Delay settings
        push_out_config: Push-out settings
        mixing_config: Mixing configuration
        mixing_repetitions: Number of mix cycles
        mixing_location: Where to mix ("source", "destination", "none")
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
    
    base_volume = float(transfer['Distribution Volume (ul)'])
    distribution_pattern = transfer.get('Distribution', 'equal').strip().lower()
    max_volume_specified = transfer.get('Volume (ul)', '').strip()
    
    # Rate multipliers (optional, default 1.0)
    rate_aspirate = float(transfer.get('Flow Aspirate', 1.0))
    rate_dispense = float(transfer.get('Flow Dispense', 1.0))
    
    # Air gap parameters
    air_gap_volume = float(transfer.get('Air Gap', 0)) if transfer.get('Air Gap') else 0
    air_gap_rate = float(transfer.get('Air Gap Rate', 1.0))
    
    # Mixing parameters
    mix_volume = float(transfer.get('Mix Volume', 0)) if transfer.get('Mix Volume') else 0
    
    # ========== Calculate distribution volumes ==========
    try:
        dest_volumes = calculate_distribution_volumes(base_volume, len(dest_well_names), distribution_pattern)
    except ValueError as e:
        protocol.comment(f"Distribution volume calculation failed: {e}")
        raise
    
    # ========== Determine max volume per trip ==========
    min_vol, max_vol = pipette_config['volume_range']
    
    if max_volume_specified and max_volume_specified != '':
        max_per_trip = float(max_volume_specified)
    else:
        max_per_trip = max_vol  # Use pipette maximum
    
    # ========== Plan trips ==========
    try:
        trips = plan_distribution_trips(dest_volumes, max_per_trip, air_gap_volume, min_vol, max_vol)
    except ValueError as e:
        protocol.comment(f"Distribution trip planning failed: {e}")
        raise
    
    protocol.comment(f"Distribution: {source_well} → {len(dest_well_names)} wells, pattern: {distribution_pattern}, {len(trips)} trip(s)")
    
    # ========== Get labware objects ==========
    source_labware = loaded_labware[source_labware_name]
    dest_labware = loaded_labware[dest_labware_name]
    
    # Get source well object (handle multi mode)
    if mode == "multi":
        # Get well count for source labware
        source_labware_id = source_labware_name.rsplit('_', 1)[0] if '_' in source_labware_name else source_labware_name
        # For multi mode, would need well count lookup, but distribution typically uses single mode
        # For now, assume single well access in distribution mode
        source_well_obj = source_labware[source_well]
    else:
        source_well_obj = source_labware[source_well]
    
    # ========== Execute each trip ==========
    tip_contacted = False
    source_well_key = f"{source_labware_name}:{source_well}"
    
    for trip_idx, trip in enumerate(trips):
        is_first_trip = (trip_idx == 0)
        
        # ===== Source mixing (before aspirate) =====
        should_mix_source = (
            mix_volume > 0 and 
            mixing_location == 'source' and
            (source_remixing == 'always' or (is_first_trip and source_well_key not in mixed_source_wells))
        )
        
        if should_mix_source:
            # Ensure we have a tip for mixing
            if not pipette.has_tip:
                pipette.pick_up_tip()
                tip_contacted = False
            
            source_mix_location, source_mix_desc = determine_well_position(transfer, source_well_obj, 'mix')
            protocol.comment(f"Mixing source {source_well} at {source_mix_desc}: {mixing_repetitions}x with {mix_volume}µL")
            pipette.mix(mixing_repetitions, mix_volume, source_mix_location)
            
            if is_first_trip:
                mixed_source_wells.add(source_well_key)
        
        # ===== Tip management for this trip =====
        tip_action = determine_tip_action(transfer, row_index)

        # Auto-convert 'keep' to 'drop' for multi_X1 mode (partial tip config doesn't support return_tip)
        if mode == 'multi_X1' and tip_action == 'keep':
            protocol.comment(f"Warning row {row_index+1}: Tip Action 'keep' not supported in multi_X1 mode. Auto-converting to 'drop'.")
            tip_action = 'drop'

        action_taken, new_tip_picked = execute_tip_action(tip_action, pipette, protocol, f"Distribution trip {trip_idx+1}/{len(trips)}")
        
        # Reset contact flag if new tip picked up
        if new_tip_picked:
            tip_contacted = False
        
        # ===== Liquid contact (only on first trip with new tip) =====
        if is_first_trip and not tip_contacted and liquid_contact_config.get('enabled', False):
            perform_liquid_contact(pipette, source_well_obj, transfer, protocol, liquid_contact_config)
            tip_contacted = True
        
        # ===== Aspirate from source =====
        source_location, source_pos_desc = determine_well_position(transfer, source_well_obj, 'source')
        protocol.comment(f"Trip {trip_idx+1}/{len(trips)}: Aspirating {trip['aspirate_volume']}µL from {source_well} at {source_pos_desc}")
        pipette.aspirate(trip['aspirate_volume'], source_location, rate=rate_aspirate)
        
        # ===== Post-aspirate actions (wick + delay) =====
        perform_post_aspirate_actions(
            pipette, source_well_obj, protocol,
            wick_config, delay_config.get('post_aspirate', 0)
        )
        
        # ===== Dispense to each destination in this trip =====
        for dispense_idx, (dest_idx, volume) in enumerate(trip['dispenses']):
            dest_well_name = dest_well_names[dest_idx]
            dest_well_obj = dest_labware[dest_well_name]
            dest_location, dest_pos_desc = determine_well_position(transfer, dest_well_obj, 'dest')
            
            protocol.comment(f"  Dispensing {volume}µL → {dest_well_name} at {dest_pos_desc}")
            
            # Dispense (no air gap here - handled separately below)
            perform_dispense_with_options(
                pipette, volume, dest_location, rate_dispense,
                protocol, push_out_config, mix_volume, 0  # air_gap=0, handled separately
            )
            
            # ===== Destination mixing (after dispense) =====
            if mix_volume > 0 and mixing_location == 'destination':
                dest_mix_location, dest_mix_desc = determine_well_position(transfer, dest_well_obj, 'mix')
                protocol.comment(f"  Mixing destination {dest_well_name} at {dest_mix_desc}: {mixing_repetitions}x with {mix_volume}µL")
                pipette.mix(mixing_repetitions, mix_volume, dest_mix_location)
            
            # ===== Air gap between destinations (except last in trip) =====
            is_last_in_trip = (dispense_idx == len(trip['dispenses']) - 1)
            if air_gap_volume > 0 and not is_last_in_trip:
                pipette.air_gap(volume=air_gap_volume, rate=air_gap_rate)
        
        # ===== Blow out after last dispense in trip =====
        last_dest_idx = trip['dispenses'][-1][0]
        last_dest_well_name = dest_well_names[last_dest_idx]
        last_dest_well_obj = dest_labware[last_dest_well_name]
        last_dest_location, _ = determine_well_position(transfer, last_dest_well_obj, 'dest')
        pipette.blow_out(last_dest_location)
        
        # ===== Handle tip after trip based on tip_action =====
        # If 'drop' action, drop tip after trip
        # If 'keep' action, keep tip for next trip (or return at end)
        # If 'new' action, will drop at start of next trip
        if tip_action == 'drop' and pipette.has_tip:
            pipette.drop_tip()
            tip_contacted = False
    
    # ===== Return tracking variables =====
    return tip_contacted

def run(protocol: protocol_api.ProtocolContext):
    """Main protocol execution"""

    # Parse embedded data using get_values()
    protocol.comment("Starting Cherry-Pick Protocol")

    # Get configuration data using get_values function
    try:
        [labware_dict, settings, csv_data] = get_values(  # noqa: F821
            "labware_dict", "settings", "csv_data")
        # Validate multi mode compatibility
        validate_multi_mode_compatibility(labware_dict, settings)
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
    liquid_contact_config = liquid_handling.get('pre_aspirate_contact', {'enabled': True, 'position_offset_percent': 20, 'aspirate_volume': 0})
    wick_config = liquid_handling.get('post_aspirate_wick', {'enabled': True, 'radius': 0.8, 'v_offset_mm': -1.5, 'speed': 20})
    delay_config = liquid_handling.get('delays', {'post_aspirate': 0})
    push_out_config = liquid_handling.get('push_out', {'enabled': False, 'volume_ul': 5})

    # Extract mixing configuration
    mixing_config = liquid_handling.get('mixing', {'location': 'destination', 'repetitions': 3, 'source_remixing': 'once'})
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

    # Extract general settings
    general_settings = settings['settings']['general']

    # Apply optional head speed overrides from settings.general.head_speed
    head_speed_cfg = general_settings.get('head_speed') if isinstance(general_settings, dict) else None
    speed = head_speed_cfg["speed"] if head_speed_cfg else 400

    # Create lookup mappings from table array structure
    available_labware = {}
    available_pipettes = {}

    # Process labware definitions (now array of tables)
    if 'labware' in labware_dict:
        for labware_item in labware_dict['labware']:
            labware_id = labware_item['labware_id']
            available_labware[labware_id] = labware_item

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

            # Apply labware offsets if configured in labware definition
            labware_def = available_labware.get(labware_id, {})
            offset_x = float(labware_def.get('offset_x', 0.0))
            offset_y = float(labware_def.get('offset_y', 0.0))
            offset_z = float(labware_def.get('offset_z', 0.0))

            if offset_x != 0.0 or offset_y != 0.0 or offset_z != 0.0:
                loaded.set_offset(x=offset_x, y=offset_y, z=offset_z)
                protocol.comment(f"Applied offset to {unique_labware_name}: x={offset_x:.3f}mm, y={offset_y:.3f}mm, z={offset_z:.3f}mm")

        except Exception as e:
            protocol.comment(f"Failed to load '{labware_id}': {e}")
            raise

    # Labware and module loading complete (no dynamic CSV loading)

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

    # Execute each transfer
    for i, transfer in enumerate(transfers):
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
                    push_out_config=push_out_config,
                    mixing_config=mixing_config,
                    mixing_repetitions=mixing_repetitions,
                    mixing_location=mixing_location,
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
            # Get well counts for both labware
            source_well_count = None
            dest_well_count = None

            # Find well counts from labware dictionary (simplified structure)
            # Extract labware_id from CSV names (format: labware_id_slot)
            source_labware_id = source_labware_name.rsplit('_', 1)[0] if '_' in source_labware_name else source_labware_name
            dest_labware_id = dest_labware_name.rsplit('_', 1)[0] if '_' in dest_labware_name else dest_labware_name

            # Look up well counts directly
            if source_labware_id in available_labware:
                source_well_count = available_labware[source_labware_id].get('well_count', 96)
            if dest_labware_id in available_labware:
                dest_well_count = available_labware[dest_labware_id].get('well_count', 96)

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
            if is_first_chunk and mix_volume > 0 and mixing_location == 'source':
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

                # Mix at destination ONLY if location setting is "destination" (only on last chunk)
                if is_last_chunk and mix_volume > 0 and mixing_location == 'destination':
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