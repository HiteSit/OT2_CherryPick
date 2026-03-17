"""Centralized test data and scenario definitions for MCP integration tests."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

CSV_BASIC = """\
Source Labware,Source Well,Volume (ul),Dest Labware,Dest Well,Source Bottom,Dest Top,Tip Action
tube_rack_96_1500ul_4,A1,100,384_ppv_55ul_2,B1,2,-5,new
tube_rack_96_1500ul_4,A2,50,384_ppv_55ul_2,B2,2,-5,keep
tube_rack_96_1500ul_4,A3,75,384_ppv_55ul_2,B3,2,-5,keep
tube_rack_96_1500ul_4,A4,25,384_ppv_55ul_2,B4,2,-5,drop
""".strip()

CSV_WITH_MIXING = """\
Source Labware,Source Well,Volume (ul),Dest Labware,Dest Well,Source Bottom,Dest Top,Mix Before,Mix After
tube_rack_96_1500ul_4,A1,120,custom_384_pcr_2,B1,2,-5,Yes,Yes
tube_rack_96_1500ul_4,A2,90,custom_384_pcr_2,B2,2,-5,No,Yes
""".strip()

CSV_WITH_AIR_GAP = """\
Source Labware,Source Well,Volume (ul),Dest Labware,Dest Well,Source Bottom,Dest Top,Source Air Gap,Dest Mix
tube_rack_96_1500ul_4,A1,60,384_ppv_55ul_2,B1,1,-4,5,Yes
""".strip()

# Distribution CSV test data - matches fixtures/distribution/ settings
CSV_DISTRIBUTION_VALID = """\
Source Labware,Source Well,Dest Labware,Dest Well,Distribution Volume (ul),Distribution,Source Bottom,Dest Top,Air Gap,Tip Action
tube_rack_96_1500ul_1,A1,384_pp_standard_100ul_2,A1|B1|A2|B2|A3|B3|A4|B4|A5|B5|A6|B6,10,equal,6,-0.5,20,keep
tube_rack_96_1500ul_1,A2,384_pp_standard_100ul_2,A7|B7|A8|B8|A9|B9|A10|B10|A11|B11|A12|B12,10,equal,6,-0.5,20,keep
tube_rack_96_1500ul_1,A3,384_pp_standard_100ul_2,A13|B13|A14|B14|A15|B15|A16|B16|A17|B17|A18|B18,10,equal,6,-0.5,20,keep
tube_rack_96_1500ul_1,A4,384_pp_standard_100ul_2,A19|B19|A20|B20|A21|B21|A22|B22|A23|B23|A24|B24,10,equal,6,-0.5,20,drop
""".strip()

CSV_DISTRIBUTION_GEOMETRIC = """\
Source Labware,Source Well,Dest Labware,Dest Well,Distribution Volume (ul),Distribution,Source Bottom,Dest Top,Tip Action
tube_rack_96_1500ul_1,A1,384_pp_standard_100ul_2,A1|B1|C1|D1,100,geometric:0.5,6,-0.5,keep
tube_rack_96_1500ul_1,A2,384_pp_standard_100ul_2,E1|F1|G1|H1,50,geometric:2,6,-0.5,keep
""".strip()

CSV_MIXED_MODE = """\
Source Labware,Source Well,Volume (ul),Distribution Volume (ul),Dest Labware,Dest Well,Source Bottom,Dest Top,Distribution,Tip Action
tube_rack_96_1500ul_1,A1,50,,384_pp_standard_100ul_2,A1,6,-0.5,,keep
tube_rack_96_1500ul_1,A2,,25,384_pp_standard_100ul_2,B1|B2|B3|B4,6,-0.5,equal,keep
tube_rack_96_1500ul_1,A3,75,,384_pp_standard_100ul_2,C1,6,-0.5,,keep
""".strip()

CSV_DISTRIBUTION_INVALID_WELLS = """\
Source Labware,Source Well,Dest Labware,Dest Well,Distribution Volume (ul),Distribution,Tip Action
tube_rack_96_1500ul_1,A1,384_pp_standard_100ul_2,A1|INVALID|B1,10,equal,keep
""".strip()

CSV_DISTRIBUTION_MISSING_VOLUME = """\
Source Labware,Source Well,Dest Labware,Dest Well,Distribution,Tip Action
tube_rack_96_1500ul_1,A1,384_pp_standard_100ul_2,A1|B1|C1,equal,keep
""".strip()

CSV_DISTRIBUTION_INVALID_PATTERN = """\
Source Labware,Source Well,Dest Labware,Dest Well,Distribution Volume (ul),Distribution,Tip Action
tube_rack_96_1500ul_1,A1,384_pp_standard_100ul_2,A1|B1|C1,10,invalid_pattern,keep
""".strip()

# Validation test scenarios for parametrized tests
DISTRIBUTION_VALIDATION_SCENARIOS: List[Tuple[str, str, str | None, str]] = [
    # (csv_content, expected_status, expected_error_substr, description)
    (CSV_DISTRIBUTION_VALID, "ok", None, "valid_equal_distribution"),
    (CSV_DISTRIBUTION_GEOMETRIC, "ok", None, "valid_geometric_distribution"),
    (CSV_MIXED_MODE, "ok", None, "mixed_cherrypick_and_distribution"),
    (CSV_DISTRIBUTION_INVALID_WELLS, "ok", None, "invalid_wells_warning_only"),
    (CSV_DISTRIBUTION_MISSING_VOLUME, "error", "volume", "missing_distribution_volume"),
]


UPDATE_SETTINGS_SCENARIOS: List[Tuple[str, str, str, str]] = [
    (
        "settings.general.mode",
        "single_X1",
        'mode = "single_X1"',
        "Use the update_settings tool to set path 'settings.general.mode' to 'single_X1'",
    ),
    (
        "settings.general.head_speed.speed",
        "250",
        "speed = 250",
        "Use the update_settings tool to set path 'settings.general.head_speed.speed' to '250'",
    ),
    (
        "settings.liquid_handling.delays.post_aspirate",
        "2.5",
        "post_aspirate = 2.5",
        "Use the update_settings tool to set path 'settings.liquid_handling.delays.post_aspirate' to '2.5'",
    ),
    (
        "settings.liquid_handling.push_out.enabled",
        "false",
        "enabled = false",
        "Use the update_settings tool to set path 'settings.liquid_handling.push_out.enabled' to 'false'",
    ),
]


LIQUID_PRESET_SCENARIOS: List[Tuple[str, Dict[str, Any]]] = [
    (
        "standard",
        {
            "delays.post_aspirate": 0,
            "push_out.enabled": False,
        },
    ),
    (
        "viscous",
        {
            "delays.post_aspirate": 2.0,
            "push_out.enabled": True,
            "push_out.volume_ul": 5,
        },
    ),
    # Note: slippery and minimal presets are not defined in the default settings.toml.
    # Only standard and viscous presets exist in the current config.
]

CSV_TEMPLATE_SCENARIOS: List[Tuple[str, Dict[str, Any]]] = [
    (
        "basic",
        {
            "transfers": 4,
            "source_labware": "tube_rack_96_1500ul_4",
            "dest_labware": "384_ppv_55ul_2",
            "default_volume": 30.0,
        },
    ),
    (
        "with_source_height",
        {
            "transfers": 8,
            "source_labware": "tube_rack_96_1500ul_4",
            "dest_labware": "custom_96_plate",
            "default_volume": 20.0,
            "source_height": 1.5,
        },
    ),
]

LABWARE_SCENARIOS: List[Tuple[str, Dict[str, Any]]] = [
    (
        "basic_plate",
        {
            "labware_id": "custom_96_plate",
            "category": "plate",
            "well_count": 96,
            "well_volume": 200,
        },
    ),
    (
        "offset_plate",
        {
            "labware_id": "custom_offset_plate",
            "category": "plate",
            "well_count": 384,
            "well_volume": 50,
            "offset_x": -0.5,
            "offset_y": 0.8,
            "offset_z": -0.3,
        },
    ),
]

VALIDATION_ERROR_SCENARIOS: List[Tuple[str, Dict[str, Any], str]] = [
    (
        "missing_csv",
        {
            "csv_path": "nonexistent.csv",
        },
        "CSV transfer map not found",
    ),
]
