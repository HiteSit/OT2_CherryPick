def get_values(*names):
    import json
    _all_values = json.loads("""{"labware_dict":{"pipettes":[{"name":"Pipette_8","opentrons_id":"p300_multi_gen2","channels":8,"volume_range":[30,300],"preferred_mount":"right","tip_connections":["tip_rack_yellow_100ul"]},{"name":"Pipette_1","opentrons_id":"p1000_single_gen2","channels":1,"volume_range":[100,1000],"preferred_mount":"left","tip_connections":["tip_rack_yellow_100ul"]}],"labware":[{"category":"tip_rack","labware_id":"tip_rack_yellow_100ul","well_count":96,"well_volume":100},{"category":"tip_rack","labware_id":"opentrons_96_tiprack_300ul","well_count":96,"well_volume":300,"offset_x":0.3,"offset_y":0.1,"offset_z":-0.4},{"category":"reservoir","labware_id":"reservoir_horizontal","well_count":12,"well_volume":15000},{"category":"plate","labware_id":"384_pp_standard_100ul","well_count":384,"well_volume":100},{"category":"plate","labware_id":"384_pp_high_150ul","well_count":384,"well_volume":150},{"category":"plate","labware_id":"384_ppv_55ul","well_count":384,"well_volume":55,"offset_x":-0.5,"offset_y":0.8,"offset_z":-0.3},{"category":"tube_rack","labware_id":"tube_rack_96_2000ul","well_count":96,"well_volume":2000},{"category":"tube_rack","labware_id":"tube_rack_96_1500ul","well_count":96,"well_volume":1500,"offset_x":-0.3,"offset_y":0.9,"offset_z":0.0}]},"settings":{"settings":{"general":{"tip_reuse":"always","mode":"multi","starting_tip_well":"H1","head_speed":{"speed":400}},"liquid_handling":{"pre_aspirate_contact":{"enabled":false,"position_offset_percent":20,"aspirate_volume":0},"post_aspirate_wick":{"enabled":true,"radius":1,"v_offset_mm":-1.5,"speed":20},"delays":{"post_aspirate":0},"push_out":{"enabled":true,"volume_ul":5},"presets":{"standard":{"pre_aspirate_contact":{"enabled":true,"position_offset_percent":20,"aspirate_volume":0},"post_aspirate_wick":{"enabled":true,"radius":0.8,"v_offset_mm":-1.5,"speed":20},"delays":{"post_aspirate":0},"push_out":{"enabled":false}},"viscous":{"pre_aspirate_contact":{"enabled":true,"position_offset_percent":20,"aspirate_volume":0},"post_aspirate_wick":{"enabled":true,"radius":0.8,"v_offset_mm":-1.5,"speed":20},"delays":{"post_aspirate":2.0},"push_out":{"enabled":true,"volume_ul":5}},"slippery":{"pre_aspirate_contact":{"enabled":true,"position_offset_percent":20,"aspirate_volume":5},"post_aspirate_wick":{"enabled":true,"radius":0.8,"v_offset_mm":-1.5,"speed":20},"delays":{"post_aspirate":0},"push_out":{"enabled":false}},"minimal":{"pre_aspirate_contact":{"enabled":false},"post_aspirate_wick":{"enabled":true,"radius":0.8,"v_offset_mm":-1.5,"speed":20},"delays":{"post_aspirate":0},"push_out":{"enabled":false}},"aggressive":{"pre_aspirate_contact":{"enabled":true,"position_offset_percent":30,"aspirate_volume":10},"post_aspirate_wick":{"enabled":true,"radius":0.8,"v_offset_mm":-1.5,"speed":15},"delays":{"post_aspirate":3.0},"push_out":{"enabled":true,"volume_ul":5}}}},"working_plate":[{"type":"source","labware_id":"tube_rack_96_1500ul","position_rack":"4"},{"type":"destination","labware_id":"384_ppv_55ul","position_rack":"2"},{"type":"tip","labware_id":"opentrons_96_tiprack_300ul","connection":"Pipette_8","position_rack":"5"}]}},"csv_data":"Source Labware,Source Well,Volume (ul),Dest Labware,Dest Well,Source Height,Dest Top\\ntube_rack_96_1500ul_4,A1,100,384_ppv_55ul_2,B1,2,-5\\ntube_rack_96_1500ul_4,A2,50,384_ppv_55ul_2,B2,2,-5\\ntube_rack_96_1500ul_4,A3,75,384_ppv_55ul_2,B3,2,-5\\ntube_rack_96_1500ul_4,A4,25,384_ppv_55ul_2,B4,2,-5"}""")
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
        volume: Volume to dispense
        dest_location: Destination location
        rate: Dispense rate multiplier
        protocol: ProtocolContext for logging
        push_out_config: Push-out configuration dict
        mix_volume: Mix volume (affects push-out eligibility)
        air_gap_volume: Air gap volume (affects push-out eligibility)
    """
    # Push-out only when no mixing follows AND no air gaps present (pipette will be empty)
    can_use_push_out = (mix_volume == 0) and push_out_config.get('enabled', False) and (air_gap_volume == 0)

    if can_use_push_out:
        push_out_volume = push_out_config.get('volume_ul', 5)  # Fixed 5µL default
        pipette.dispense(volume, dest_location, rate=rate, push_out=push_out_volume)
    else:
        pipette.dispense(volume, dest_location, rate=rate)


def validate_csv_labware_match(settings, transfers):
    """
    Validate that all CSV labware references exactly match expected names from settings.toml

    Args:
        settings: Settings configuration dict
        transfers: List of transfer dicts from CSV

    Raises:
        ValueError: If any labware mismatch is found
    """
    # Calculate expected labware names from settings.toml
    expected_labware = set()
    for plate_config in settings['settings']['working_plate']:
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

        raise ValueError(error_msg)

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

    # Load labware from settings
    loaded_labware = {}
    used_slots = set()

    for plate_config in settings['settings']['working_plate']:
        slot = plate_config['position_rack']
        labware_id = plate_config['labware_id']  # Now using labware_id
        plate_type = plate_config['type']

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

    # Labware loading complete (no dynamic CSV loading)

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

    # Validate that last transfer doesn't have 'new' tip action
    if transfers:
        last_transfer_tip_action = transfers[-1].get('Tip Action', 'auto').lower().strip()
        if last_transfer_tip_action == 'new':
            raise ValueError("Last transfer cannot have 'new' tip action. Use 'keep' to return tip to rack or 'drop' to discard.")

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
        volume = float(transfer['Volume (ul)'])
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

        # Log essential transfer info only
        protocol.comment(f"Transfer {i+1}/{len(transfers)}: {volume}µL {source_labware_name}[{source_well}] → {dest_labware_name}[{dest_well}]")

        # Check volume is within pipette range
        min_vol, max_vol = pipette_config['volume_range']
        if volume < min_vol or volume > max_vol:
            protocol.comment(f"WARNING: Volume {volume}µL outside range [{min_vol}-{max_vol}]µL")

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

        # Perform liquid contact if tip hasn't contacted yet and contact is enabled
        if not tip_contacted and liquid_contact_config.get('enabled', False):
            perform_liquid_contact(pipette, primary_source_well, transfer, protocol, liquid_contact_config)
            tip_contacted = True

        # Perform transfer
        try:
            # Aspirate
            pipette.aspirate(volume, source_location, rate=rate_aspirate)

            # Post-aspirate actions (wick + delay)
            perform_post_aspirate_actions(
                pipette, primary_source_well, protocol,
                wick_config, delay_config.get('post_aspirate', 0)
            )

            # Air gap if specified
            if air_gap_volume > 0:
                pipette.air_gap(volume=air_gap_volume, rate=air_gap_rate)

            # Dispense with options
            perform_dispense_with_options(
                pipette, volume, dest_location, rate_dispense,
                protocol, push_out_config, mix_volume, air_gap_volume
            )

            # Mix if specified
            if mix_volume > 0:
                if mode == "multi":
                    # Use first destination well for mixing in multi mode
                    mix_location, mix_pos_desc = determine_well_position(transfer, dest_wells[0], 'mix')
                else:
                    mix_location, mix_pos_desc = determine_well_position(transfer, dest_labware[dest_well], 'mix')
                pipette.mix(3, mix_volume, mix_location)

            # Blow out at destination
            pipette.blow_out(dest_location)

            protocol.comment("Transfer complete")

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
            protocol.comment("Returned final tip to rack")
        else:
            # Drop tip (default for 'drop', 'new', or any other action)
            pipette.drop_tip()
            protocol.comment("Dropped final tip")

    protocol.comment(f"Protocol complete: {len(transfers)} transfers")