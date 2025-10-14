# Opentrons V2 API Documentation

Comprehensive API reference for protocol development with Opentrons Protocol API v2.24 (compatible with ≥v2.16).

### Quick Reference - Minimal Protocol Template

```python
from opentrons import protocol_api

metadata = {
    "apiLevel": "2.16",
    "protocolName": "My Protocol",
    "description": "Protocol description",
    "author": "Your Name"
}
requirements = {"robotType": "OT-2", "apiLevel": "2.16"}

def run(protocol: protocol_api.ProtocolContext):
    # Load labware
    plate = protocol.load_labware('corning_96_wellplate_360ul_flat', 1)
    tiprack = protocol.load_labware('opentrons_96_tiprack_300ul', 2)

    # Load pipette (ALWAYS after labware!)
    pipette = protocol.load_instrument('p300_single_gen2', 'right', tip_racks=[tiprack])

    # Basic operations
    pipette.transfer(100, plate['A1'], plate['B1'])  # Simple transfer
    pipette.distribute(50, plate['A1'], plate.rows()[0])  # One-to-many
    pipette.consolidate(50, plate.rows()[0], plate['A1'])  # Many-to-one
```

### Critical Concepts

**Load Order (MUST FOLLOW):**
1. Labware first: `protocol.load_labware()`
2. Pipettes second: `protocol.load_instrument()`
3. Modules third: `protocol.load_module()`

**Multi-Channel Behavior:**
- 8-channel pipettes act on entire columns via row A only
- `plate['A1']` with 8-channel pipette affects A1-H1 simultaneously
- Use `single_X1` or `multi_X1` mode for per-well cherry picking

**Tip Management:**
- Default: new tip per transfer
- `new_tip='always'` - new tip every time
- `new_tip='once'` - one tip for entire operation
- `new_tip='never'` - manual tip management
- Ensure sufficient tip racks loaded

### Core API Documentation by Category

#### 1. Protocol Context & Setup ⭐ CRITICAL

**URL**: https://docs.opentrons.com/v2/new_protocol_api.html

**Key Methods:**
- `load_labware(name, slot)` - Load plates, tips, reservoirs
- `load_instrument(name, mount, tip_racks=[...])` - Load pipette
- `load_module(name, slot)` - Load temperature/magnetic/shaker module
- `pause(msg)` - Pause with message
- `delay(seconds=None, minutes=None)` - Wait specified time

**Common Pattern:**
```python
# Always this order!
labware = protocol.load_labware('labware_name', slot_number)
pipette = protocol.load_instrument('pipette_name', 'left'|'right', tip_racks=[tiprack])
```

#### 2. Labware Management ⭐ CRITICAL

**URL**: https://docs.opentrons.com/v2/new_labware.html

**Well Selection:**
```python
# Single wells
plate['A1']                      # By name (recommended)
plate.wells()[0]                 # By index
plate.wells_by_name()['A1']      # Explicit dict

# Groups
plate.rows()[0]                  # Row A: [A1, A2, ..., A12]
plate.columns()[0]               # Column 1: [A1, B1, ..., H1]
plate.rows_by_name()['A']        # Row A by name
plate.columns_by_name()['1']     # Column 1 by name

# Advanced
plate.wells()[1:]                # All except A1
plate.columns()[1::2]            # Every other column
```

**Custom Labware:**
Place JSON files in `$LABWARE_PATH` directory and reference by `api_id` in TOML config.

#### 3. Pipette Control ⭐ CRITICAL

**URL**: https://docs.opentrons.com/v2/new_pipette.html

**Core Operations:**
```python
# Manual tip control
pipette.pick_up_tip()
pipette.aspirate(volume, location)
pipette.dispense(volume, location)
pipette.drop_tip()

# Automatic (recommended)
pipette.transfer(volume, source, dest, new_tip='always')
```

**Flow Rate Control:**
```python
pipette.flow_rate.aspirate = 50   # μL/s
pipette.flow_rate.dispense = 100  # μL/s
pipette.flow_rate.blow_out = 200  # μL/s
```

#### 4. Liquid Handling Commands ⭐ CRITICAL

**URL**: https://docs.opentrons.com/v2/new_examples.html

**Transfer Patterns:**
```python
# Simple transfer
pipette.transfer(100, source, dest)

# With options
pipette.transfer(
    100, source, dest,
    mix_before=(3, 50),      # Mix 3x with 50μL before aspirate
    mix_after=(3, 50),       # Mix 3x with 50μL after dispense
    new_tip='always',
    blow_out=True,
    touch_tip=True,
    air_gap=10               # 10μL air gap
)

# Distribute (one-to-many)
pipette.distribute(
    50,
    reservoir['A1'],
    plate.rows()[0],
    disposal_volume=10       # Extra volume for accuracy
)

# Consolidate (many-to-one)
pipette.consolidate(
    50,
    plate.rows()[0],
    reservoir['A1'],
    pre_wet=True             # Wet tip before aspirating
)

# Mix
pipette.mix(repetitions=5, volume=100, location=well)
```

#### 5. Hardware Modules

**URL**: https://docs.opentrons.com/v2/new_modules.html

**Temperature Module:**
```python
temp_mod = protocol.load_module('temperature module gen2', 3)
temp_plate = temp_mod.load_labware('corning_96_wellplate_360ul_flat')
temp_mod.set_temperature(4)          # Set to 4°C
temp_mod.await_temperature(4)        # Wait until reached
temp_mod.deactivate()                # Turn off
```

**Magnetic Module:**
```python
mag_mod = protocol.load_module('magnetic module gen2', 6)
mag_plate = mag_mod.load_labware('nest_96_wellplate_2ml_deep')
mag_mod.engage(height_from_base=5)   # Engage magnets 5mm from base
protocol.delay(minutes=2)            # Wait for beads
mag_mod.disengage()                  # Release magnets
```

**Thermocycler:**
```python
tc_mod = protocol.load_module('thermocycler module')
tc_plate = tc_mod.load_labware('nest_96_wellplate_100ul_pcr_full_skirt')
tc_mod.open_lid()
tc_mod.close_lid()
tc_mod.set_lid_temperature(105)
tc_mod.set_block_temperature(95, hold_time_seconds=30)
```

**Heater-Shaker:**
```python
hs_mod = protocol.load_module('heaterShakerModuleV1', 1)
hs_plate = hs_mod.load_labware('nest_96_wellplate_2ml_deep')
hs_mod.set_and_wait_for_shake_speed(500)  # 500 rpm
hs_mod.set_and_wait_for_temperature(37)   # 37°C
hs_mod.deactivate_shaker()
hs_mod.deactivate_heater()
```

#### 6. Advanced Liquid Handling

**URL**: https://docs.opentrons.com/v2/new_advanced_running.html

**Serial Dilution:**
```python
# Dilute across columns
for i in range(11):
    pipette.transfer(
        50,
        plate.columns()[i],
        plate.columns()[i+1],
        mix_after=(5, 50),
        new_tip='always'
    )
```

**Custom Height Control:**
```python
from opentrons.protocol_api import Well

# Aspirate from bottom
pipette.aspirate(100, source_well.bottom(z=2))  # 2mm from bottom

# Dispense from top
pipette.dispense(100, dest_well.top(z=-5))      # 5mm below top
```

**Liquid Classes (API ≥2.20):**
```python
glycerol_class = protocol.get_liquid_class('glycerol_50')
pipette.transfer_with_liquid_class(
    liquid_class=glycerol_class,
    volume=100,
    source=reservoir['A1'],
    dest=plate.columns()[0]
)
```

#### 7. Runtime Parameters

**URL**: https://docs.opentrons.com/v2/runtime-parameters.html

**Define Parameters:**
```python
def add_parameters(parameters):
    parameters.add_int(
        variable_name='sample_count',
        display_name='Number of Samples',
        description='How many samples to process',
        default=24,
        minimum=1,
        maximum=96,
        unit='samples'
    )

    parameters.add_float(
        variable_name='dilution_factor',
        display_name='Dilution Factor',
        default=10.0,
        minimum=2.0,
        maximum=100.0
    )

    parameters.add_bool(
        variable_name='include_controls',
        display_name='Include Controls',
        default=True
    )

def run(protocol, sample_count, dilution_factor, include_controls):
    # Use parameters in protocol
    for i in range(sample_count):
        # Process with dilution_factor
        pass
```

#### 8. Protocol Simulation & Testing

**URL**: https://docs.opentrons.com/v2/new_simulate.html

**Simulate Protocol:**
```bash
opentrons_simulate protocol.py
opentrons_simulate --custom-labware /path/to/labware protocol.py
```

**Debugging Tips:**
1. Always simulate before hardware run
2. Print well names during development: `print(f"Aspirating from {well}")`
3. Check tip counts: ensure sufficient racks loaded
4. Test edge cases: max volumes, empty wells
5. Monitor flow rates for viscous liquids

#### 9. Common Patterns & Recipes

**PCR Setup:**
```python
temp_mod = protocol.load_module('temperature module gen2', 1)
plate = temp_mod.load_labware('nest_96_wellplate_100ul_pcr_full_skirt')
temp_mod.set_temperature(4)  # Keep cold

pipette.distribute(20, mastermix_tube, plate.wells(), new_tip='once')
pipette.transfer(5, sample_plate.wells(), plate.wells(), new_tip='always')
```

**Magnetic Bead Cleanup:**
```python
mag_mod.engage()
protocol.delay(minutes=5)

# Remove supernatant
pipette.transfer(
    180,
    mag_plate.wells(),
    waste,
    new_tip='always',
    blow_out=True
)

# Wash
pipette.transfer(200, ethanol, mag_plate.wells(), new_tip='always')
protocol.delay(seconds=30)
pipette.transfer(200, mag_plate.wells(), waste, new_tip='always')

mag_mod.disengage()
```

**Plate Stamping (96→384):**
```python
# Map 96-well to 384-well quadrants
for i, source_well in enumerate(source_plate.wells()):
    dest_well = dest_plate.wells()[i * 4]  # Top-left of 2x2 block
    pipette.transfer(5, source_well, dest_well, new_tip='always')
```

### Common Errors & Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| "No tips available" | Tip racks depleted | Load more tip racks or use `new_tip='once'` |
| "Labware not found" | Wrong name | Check exact name in Opentrons Labware Library |
| "Cannot aspirate" | Multi-channel misalignment | Use row A selectors for 8-channel pipettes |
| "Module not found" | Wrong identifier | Use exact: `'temperature module gen2'` |
| "Liquid will overflow" | Volume exceeds well capacity | Reduce volume or split into multiple transfers |

### Quick Command Reference

```python
# Protocol structure
from opentrons import protocol_api
metadata = {'apiLevel': '2.16'}
requirements = {'robotType': 'OT-2', 'apiLevel': '2.16'}
def run(protocol: protocol_api.ProtocolContext):
    pass

# Loading
labware = protocol.load_labware('name', slot)
pipette = protocol.load_instrument('name', 'left'|'right', tip_racks=[tips])
module = protocol.load_module('name', slot)

# Liquid handling
pipette.pick_up_tip()
pipette.aspirate(volume, location)
pipette.dispense(volume, location)
pipette.mix(reps, volume, location)
pipette.blow_out(location)
pipette.touch_tip()
pipette.drop_tip()

# Complex commands
pipette.transfer(volume, source, dest, **options)
pipette.distribute(volume, source, dests, **options)
pipette.consolidate(volume, sources, dest, **options)

# Module control
temp_module.set_temperature(celsius)
mag_module.engage(height_from_base=mm)
heater_shaker.set_and_wait_for_shake_speed(rpm)
thermocycler.set_block_temperature(temp, hold_time_seconds=seconds)

# Timing
protocol.delay(seconds=10)
protocol.delay(minutes=2)
protocol.pause(msg="Replace plate")
```

### Documentation Resources

- **Protocol API**: https://docs.opentrons.com/v2/new_protocol_api.html
- **Labware**: https://docs.opentrons.com/v2/new_labware.html
- **Pipettes**: https://docs.opentrons.com/v2/new_pipette.html
- **Liquid Handling**: https://docs.opentrons.com/v2/new_examples.html
- **Modules**: https://docs.opentrons.com/v2/new_modules.html
- **Advanced**: https://docs.opentrons.com/v2/new_advanced_running.html
- **Simulation**: https://docs.opentrons.com/v2/new_simulate.html
- **Tutorial**: https://docs.opentrons.com/v2/tutorial.html
- **Runtime Parameters**: https://docs.opentrons.com/v2/runtime-parameters.html
- **Labware Library**: https://labware.opentrons.com/