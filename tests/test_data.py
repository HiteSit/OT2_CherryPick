"""Centralized test data and scenario definitions for MCP integration tests."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

CSV_BASIC = """\
Source Labware,Source Well,Volume (ul),Dest Labware,Dest Well,Source Height,Dest Top
tube_rack_96_1500ul_4,A1,100,384_ppv_55ul_2,B1,2,-5
tube_rack_96_1500ul_4,A2,50,384_ppv_55ul_2,B2,2,-5
tube_rack_96_1500ul_4,A3,75,384_ppv_55ul_2,B3,2,-5
tube_rack_96_1500ul_4,A4,25,384_ppv_55ul_2,B4,2,-5
""".strip()

CSV_WITH_MIXING = """\
Source Labware,Source Well,Volume (ul),Dest Labware,Dest Well,Source Height,Dest Top,Mix Before,Mix After
tube_rack_96_1500ul_4,A1,120,custom_384_pcr_2,B1,2,-5,Yes,Yes
tube_rack_96_1500ul_4,A2,90,custom_384_pcr_2,B2,2,-5,No,Yes
""".strip()

CSV_WITH_AIR_GAP = """\
Source Labware,Source Well,Volume (ul),Dest Labware,Dest Well,Source Height,Dest Top,Source Air Gap,Dest Mix
tube_rack_96_1500ul_4,A1,60,384_ppv_55ul_2,B1,1,-4,5,Yes
""".strip()


UPDATE_SETTINGS_SCENARIOS: List[Tuple[str, str, str, str]] = [
    (
        "settings.general.tip_reuse",
        "never",
        'tip_reuse = "never"',
        "Use the update_settings tool to set path 'settings.general.tip_reuse' to 'never'",
    ),
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
    (
        "slippery",
        {
            "pre_aspirate_contact.aspirate_volume": 5,
            "push_out.enabled": False,
        },
    ),
    (
        "minimal",
        {
            "pre_aspirate_contact.enabled": False,
            "push_out.enabled": False,
        },
    ),
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
