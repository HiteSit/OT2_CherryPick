"""Labware auto-discovery from custom JSON files and official list."""
import json
from pathlib import Path
from typing import Optional


def scan_custom_labware(labware_path: str) -> list[dict]:
    """Scan a directory for Opentrons custom labware JSON files."""
    results = []
    path = Path(labware_path)
    if not path.is_dir():
        return results
    for json_file in sorted(path.glob("*.json")):
        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
            load_name = data["parameters"]["loadName"]
            well_count = len(data.get("wells", {}))
            display_name = data.get("metadata", {}).get("displayName", load_name)
            display_category = data.get("metadata", {}).get("displayCategory", "")
            results.append({
                "labware_id": load_name,
                "well_count": well_count,
                "display_name": display_name,
                "display_category": display_category,
                "source": "custom",
            })
        except (json.JSONDecodeError, KeyError, OSError):
            continue
    return results


def load_official_labware_list(official_list_path: str) -> list[dict]:
    """Load the official Opentrons labware name list."""
    results = []
    path = Path(official_list_path)
    if not path.exists():
        return results
    for line in path.read_text(encoding="utf-8").splitlines():
        name = line.strip()
        if name and not name.startswith("#"):
            results.append({
                "labware_id": name,
                "well_count": None,
                "display_name": name,
                "display_category": "",
                "source": "official",
            })
    return results


def scan_available_labware(
    custom_labware_path: Optional[str] = None,
    official_list_path: Optional[str] = None,
) -> list[dict]:
    """Scan custom labware JSONs and merge with official list."""
    results = []
    seen_ids = set()

    # Custom labware first (takes priority)
    if custom_labware_path:
        for item in scan_custom_labware(custom_labware_path):
            if item["labware_id"] not in seen_ids:
                results.append(item)
                seen_ids.add(item["labware_id"])

    # Official labware (skip duplicates)
    if official_list_path:
        for item in load_official_labware_list(official_list_path):
            if item["labware_id"] not in seen_ids:
                results.append(item)
                seen_ids.add(item["labware_id"])

    return results
