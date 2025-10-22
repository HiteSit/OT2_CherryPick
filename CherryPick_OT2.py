def get_values(*names):
    import json
    _all_values = json.loads("""{"labware_dict":{"pipettes":[{"name":"Pipette_8","opentrons_id":"p300_multi_gen2","channels":8,"volume_range":[30,300],"preferred_mount":"right","tip_connections":["opentrons_96_tiprack_300ul"]},{"name":"Pipette_1","opentrons_id":"p1000_single_gen2","channels":1,"volume_range":[100,1000],"preferred_mount":"left","tip_connections":["tip_rack_geb_1000ul"]}],"labware":[{"category":"tip_rack","labware_id":"tip_rack_yellow_100ul","well_count":96,"well_volume":100},{"category":"tip_rack","labware_id":"opentrons_96_tiprack_300ul","well_count":96,"well_volume":300,"offset_x":0.3,"offset_y":0.1,"offset_z":-0.4},{"category":"tip_rack","labware_id":"tip_rack_geb_1000ul","well_count":96,"well_volume":1000},{"category":"reservoir","labware_id":"reservoir_horizontal","well_count":12,"well_volume":15000,"offset_x":0.0,"offset_y":0.0,"offset_z":0.0},{"category":"plate","labware_id":"384_pp_standard_100ul","well_count":384,"well_volume":100,"offset_x":0,"offset_y":0.7,"offset_z":0},{"category":"plate","labware_id":"384_pp_high_150ul","well_count":384,"well_volume":150},{"category":"plate","labware_id":"384_ppv_55ul","well_count":384,"well_volume":55,"offset_x":-0.5,"offset_y":0.8,"offset_z":-0.3},{"category":"plate","labware_id":"384_ldv_12ul","well_count":384,"well_volume":12,"offset_x":-0.2,"offset_y":0.6,"offset_z":0.4},{"category":"tube_rack","labware_id":"tube_rack_96_2000ul","well_count":96,"well_volume":2000},{"category":"tube_rack","labware_id":"tube_rack_96_1500ul","well_count":96,"well_volume":1500,"offset_x":-0.3,"offset_y":0.9,"offset_z":0.0},{"category":"tube_rack","labware_id":"tube_rack_24_4000ul","well_count":24,"well_volume":4000},{"category":"tube_rack","labware_id":"tube_rack_48_1500ul","well_count":48,"well_volume":1500},{"category":"tube_rack","labware_id":"tube_rack_54_1500ul","well_count":54,"well_volume":1500}]},"settings":{"settings":{"general":{"tip_reuse":"always","mode":"single_X1","starting_tip_well":"H1","head_speed":{"speed":400}},"liquid_handling":{"pre_aspirate_contact":{"enabled":true,"position_offset_percent":20,"aspirate_volume":10},"post_aspirate_wick":{"enabled":false,"radius":1,"v_offset_mm":-1.5,"speed":20},"delays":{"post_aspirate":2},"push_out":{"enabled":true,"volume_ul":100},"presets":{"standard":{"pre_aspirate_contact":{"enabled":true,"position_offset_percent":20,"aspirate_volume":0},"post_aspirate_wick":{"enabled":true,"radius":0.8,"v_offset_mm":-1.5,"speed":20},"delays":{"post_aspirate":0},"push_out":{"enabled":false}},"viscous":{"pre_aspirate_contact":{"enabled":true,"position_offset_percent":20,"aspirate_volume":0},"post_aspirate_wick":{"enabled":true,"radius":0.8,"v_offset_mm":-1.5,"speed":20},"delays":{"post_aspirate":2.0},"push_out":{"enabled":true,"volume_ul":5}},"slippery":{"pre_aspirate_contact":{"enabled":true,"position_offset_percent":20,"aspirate_volume":5},"post_aspirate_wick":{"enabled":true,"radius":0.8,"v_offset_mm":-1.5,"speed":20},"delays":{"post_aspirate":0},"push_out":{"enabled":false}},"minimal":{"pre_aspirate_contact":{"enabled":false},"post_aspirate_wick":{"enabled":true,"radius":0.8,"v_offset_mm":-1.5,"speed":20},"delays":{"post_aspirate":0},"push_out":{"enabled":false}},"aggressive":{"pre_aspirate_contact":{"enabled":true,"position_offset_percent":30,"aspirate_volume":10},"post_aspirate_wick":{"enabled":true,"radius":0.8,"v_offset_mm":-1.5,"speed":15},"delays":{"post_aspirate":3.0},"push_out":{"enabled":true,"volume_ul":5}}}},"working_plate":[{"type":"module","module_type":"heaterShaker","position_rack":"10","adapter_id":"opentrons_universal_flat_adapter","labware_id":"","target_temperature":95,"target_shake_speed":2000,"persist_after_protocol":true},{"type":"reservoir","labware_id":"reservoir_horizontal","position_rack":"2"},{"type":"source","labware_id":"tube_rack_48_1500ul","position_rack":"3"},{"type":"destination","labware_id":"tube_rack_48_1500ul","position_rack":"5"},{"type":"destination","labware_id":"tube_rack_54_1500ul","position_rack":"6"},{"type":"tip","labware_id":"tip_rack_geb_1000ul","connection":"Pipette_1","position_rack":"1"}]}},"csv_data":"ID,Source Labware,Source Well,Volume (ul),Dest Labware,Dest Well,Source Height,Dest Top,Flow Aspirate,Flow Dispense,Air Gap,Tip Action\\nCAT-B31-A97-NT-097,reservoir_horizontal_2,B1,1021.6,tube_rack_48_1500ul_5,B2,3,-1.5,0.8,0.8,100,keep\\nCAT-B46-A77-OXO-077,reservoir_horizontal_2,B1,1018.8,tube_rack_48_1500ul_5,E2,3,-1.5,0.8,0.8,100,new\\nCAT-B31-A73-NT-073,reservoir_horizontal_2,B1,1096.1,tube_rack_48_1500ul_5,F2,3,-1.5,0.8,0.8,100,new\\nCAT-B31-A20-NT-020,reservoir_horizontal_2,B1,914,tube_rack_48_1500ul_5,A3,3,-1.5,0.8,0.8,100,new\\nCAT-B31-A46-NT-046,reservoir_horizontal_2,B1,1082.8,tube_rack_48_1500ul_5,D3,3,-1.5,0.8,0.8,100,new\\nCAT-B31-A36-NT-036,reservoir_horizontal_2,B1,1159.8,tube_rack_48_1500ul_5,A4,3,-1.5,0.8,0.8,100,new\\nCAT-B31-A49-NT-049,reservoir_horizontal_2,B1,1092.8,tube_rack_48_1500ul_5,C4,3,-1.5,0.8,0.8,100,new\\nCAT-B31-A10-NT-010,reservoir_horizontal_2,B1,1118.3,tube_rack_48_1500ul_5,D4,3,-1.5,0.8,0.8,100,new\\nCAT-B46-A41-OXO-041,reservoir_horizontal_2,B1,1028.5,tube_rack_48_1500ul_5,E4,3,-1.5,0.8,0.8,100,new\\nCAT-B32-A29-NT-129,reservoir_horizontal_2,B1,940.5,tube_rack_48_1500ul_5,A5,3,-1.5,0.8,0.8,100,new\\nCAT-B32-A36-NT-136,reservoir_horizontal_2,C1,982.7,tube_rack_48_1500ul_5,B5,3,-1.5,0.8,0.8,100,new\\nCAT-B31-A8-NT-008,reservoir_horizontal_2,C1,1022.3,tube_rack_48_1500ul_5,C5,3,-1.5,0.8,0.8,100,new\\nCAT-B31-A45-NT-045,reservoir_horizontal_2,C1,1066,tube_rack_48_1500ul_5,D5,3,-1.5,0.8,0.8,100,new\\nCAT-B31-A86-NT-086,reservoir_horizontal_2,C1,949.3,tube_rack_48_1500ul_5,B6,3,-1.5,0.8,0.8,100,new\\nCAT-B31-A99-NT-099,reservoir_horizontal_2,C1,997.6,tube_rack_48_1500ul_5,C6,3,-1.5,0.8,0.8,100,new\\nCAT-B31-A37-NT-037,reservoir_horizontal_2,C1,1131.4,tube_rack_48_1500ul_5,C7,3,-1.5,0.8,0.8,100,new\\nCAT-B32-A1-NT-101,reservoir_horizontal_2,C1,969.4,tube_rack_48_1500ul_5,E7,3,-1.5,0.8,0.8,100,new\\nCAT-B46-A78-OXO-078,reservoir_horizontal_2,C1,1046.9,tube_rack_48_1500ul_5,C8,3,-1.5,0.8,0.8,100,new\\nCAT-B46-A76-OXO-076,reservoir_horizontal_2,C1,1012.4,tube_rack_48_1500ul_5,D8,3,-1.5,0.8,0.8,100,new\\nCAT-B32-A4-NT-104,reservoir_horizontal_2,C1,939.7,tube_rack_48_1500ul_5,E8,3,-1.5,0.8,0.8,100,new\\nCAT-B46-A72-OXO-072,reservoir_horizontal_2,C1,934.3,tube_rack_54_1500ul_6,B1,3,-1.5,0.8,0.8,100,new\\nCAT-B31-A31-NT-031,reservoir_horizontal_2,C1,1041.6,tube_rack_54_1500ul_6,F1,3,-1.5,0.8,0.8,100,new\\nCAT-B32-A49-NT-149,reservoir_horizontal_2,C1,969.6,tube_rack_54_1500ul_6,B2,3,-1.5,0.8,0.8,100,new\\nCAT-B32-A48-NT-148,reservoir_horizontal_2,C1,919.9,tube_rack_54_1500ul_6,E2,3,-1.5,0.8,0.8,100,new\\nCAT-B31-A32-NT-032,reservoir_horizontal_2,C1,1029.4,tube_rack_54_1500ul_6,A3,3,-1.5,0.8,0.8,100,new\\nCAT-B31-A79-NT-079,reservoir_horizontal_2,C1,1040.1,tube_rack_54_1500ul_6,D3,3,-1.5,0.8,0.8,100,new"}""")
    return [_all_values[n] for n in names]


"""
Unified Cherry-pick Protocol (CherryPick_OT)
Combines all liquid handling strategies into configurable physical parameters
Supports single-channel, multi-channel, and multi_X1 modes with custom flow rates
"""
from opentrons import protocol_api
from opentrons.protocol_api import SINGLE
import csv
from io import StringIO

# Metadata
metadata = {
    'protocolName': 'Unified Cherry-Pick Protocol (CherryPick_OT2)',
    'author': 'Opentrons User',
    'description': 'Unified cherry-pick protocol with configurable liquid handling strategies'
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

def determine_tip_action(transfer, global_tip_reuse, source_labware_name, last_source_labware, pipette):
    """Determine tip action for this transfer based on CSV and global settings"""
    # Get CSV-specified tip action (default to 'auto' if column missing)
    csv_tip_action = transfer.get('Tip Action', 'auto').lower().strip()

    # Validate tip action
    valid_actions = ['new', 'keep', 'drop', 'auto']
    if csv_tip_action not in valid_actions:
        raise ValueError(f"Invalid Tip Action '{csv_tip_action}'. Valid options: {valid_actions}")

    # If CSV specifies explicit action, use it
    if csv_tip_action in ['new', 'keep', 'drop']:
        return csv_tip_action

    # If 'auto', apply global strategy
    if global_tip_reuse == 'never':
        return 'new'
    elif global_tip_reuse == 'always':
        return 'keep' if pipette.has_tip else 'new'
    elif global_tip_reuse == 'per_source':
        if source_labware_name != last_source_labware:
            return 'new'
        else:
            return 'keep' if pipette.has_tip else 'new'
    else:
        raise ValueError(f"Unknown global tip_reuse strategy: {global_tip_reuse}")

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
        return well_object.bottom(offset), f"bottom+{offset}mm"
    elif has_top:
        offset = float(top_val)
        return well_object.top(offset), f"top+{offset}mm"
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
    
    # Validate temperature range (0 = disabled, 37-95 = active range)
    if target_temp < 0 or (0 < target_temp < 37) or target_temp > 95:
        raise ValueError(f"Invalid target_temperature: {target_temp}. Must be 0 (disabled) or 37-95°C")
    
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

    # Load pipette based on mode
    mode = general_settings['mode']

    # Determine which pipette to use
    if mode == "single_X1":
        pipette_key = "Pipette_1"
    elif mode in ["multi_X1", "multi"]:
        pipette_key = "Pipette_8"
    else:
        raise ValueError(f"Unknown mode: {mode}. Valid modes: single_X1, multi_X1, multi")

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

    # Load the pipette
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

    # Execute transfers
    tip_reuse = general_settings['tip_reuse']
    last_source_labware = None
    tip_contacted = False  # Track if current tip has contacted liquid
    last_tip_action = None  # Track the last transfer's tip action for final cleanup

    # Pick up tip if always reusing
    if tip_reuse == 'always':
        pipette.pick_up_tip()
        tip_contacted = False  # New tip, needs contact

    # Execute each transfer
    for i, transfer in enumerate(transfers):
        # Parse transfer parameters
        source_labware_name = transfer['Source Labware']
        source_well = transfer['Source Well']
        dest_labware_name = transfer['Dest Labware']
        dest_well = transfer['Dest Well']
        requested_volume = float(transfer['Volume (ul)'])
        mix_volume = float(transfer.get('Mix Volume', 0)) if transfer.get('Mix Volume') else 0

        # Rate multipliers (optional in CSV, default 1.0 = normal speed)
        rate_aspirate = float(transfer.get('Flow Aspirate', 1.0))
        rate_dispense = float(transfer.get('Flow Dispense', 1.0))

        # Air gap parameters (optional in CSV, default 0 = disabled)
        air_gap_volume = float(transfer.get('Air Gap', 0)) if transfer.get('Air Gap') else 0
        air_gap_rate = float(transfer.get('Air Gap Rate', 1.0))

        # Tip action parameter (optional in CSV, default 'auto' = use global setting)
        tip_action_raw = transfer.get('Tip Action', 'auto')
        tip_action = determine_tip_action(transfer, tip_reuse, source_labware_name, last_source_labware, pipette)

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

        # Update last source labware for global 'per_source' strategy
        if tip_reuse == 'per_source':
            last_source_labware = source_labware_name

        # Execute transfer in chunks (may be single chunk if volume within range)
        for chunk_idx, chunk_vol in enumerate(sub_volumes):
            is_first_chunk = (chunk_idx == 0)
            is_last_chunk = (chunk_idx == len(sub_volumes) - 1)

            # Perform liquid contact only on first chunk (tip conditioning)
            if is_first_chunk and not tip_contacted and liquid_contact_config.get('enabled', False):
                perform_liquid_contact(pipette, primary_source_well, transfer, protocol, liquid_contact_config)
                tip_contacted = True

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

                # Mix only after last chunk dispense
                if is_last_chunk and mix_volume > 0:
                    if mode == "multi":
                        # Use first destination well for mixing in multi mode
                        mix_location, mix_pos_desc = determine_well_position(transfer, dest_wells[0], 'mix')
                    else:
                        mix_location, mix_pos_desc = determine_well_position(transfer, dest_labware[dest_well], 'mix')
                    pipette.mix(3, mix_volume, mix_location)

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

    # Handle final tip based on last transfer's tip action
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