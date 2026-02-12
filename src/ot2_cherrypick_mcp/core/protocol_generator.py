"""
Protocol generation core functionality.

This module contains the core functions for converting TOML configuration files
and CSV transfer maps into embedded JSON configuration for OT-2 protocols.

Extracted from helper_cherry_pick.py for cleaner architecture and proper packaging.
"""

from __future__ import annotations

import json
import re
from typing import Dict, Any

try:
    import toml
except ImportError:
    import tomllib as toml  # Python 3.11+ fallback


def read_toml_file(filepath: str) -> Dict[str, Any]:
    """Read and parse a TOML file.

    Args:
        filepath: Path to TOML file

    Returns:
        dict: Parsed TOML data

    Raises:
        FileNotFoundError: If file doesn't exist
        Exception: If TOML parsing fails
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            if hasattr(toml, 'load'):
                return toml.load(f)
            else:
                # tomllib requires binary mode
                with open(filepath, 'rb') as fb:
                    return toml.load(fb)
    except FileNotFoundError:
        raise FileNotFoundError(f"TOML file not found: {filepath}")
    except Exception as e:
        raise Exception(f"Error reading TOML file {filepath}: {e}")


def read_csv_file(filepath: str) -> str:
    """Read a CSV file as string with proper newline escaping for JSON.

    Args:
        filepath: Path to CSV file

    Returns:
        str: CSV content with escaped newlines for JSON embedding

    Raises:
        FileNotFoundError: If file doesn't exist
        Exception: If file reading fails
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            # Escape newlines for JSON embedding - this is critical!
            content = content.replace('\n', '\\n')
            return content
    except FileNotFoundError:
        raise FileNotFoundError(f"CSV file not found: {filepath}")
    except Exception as e:
        raise Exception(f"Error reading CSV file {filepath}: {e}")


def create_json_config(
    labware_toml: str,
    settings_toml: str,
    csv_file: str,
    verbose: bool = True
) -> str:
    """Create the JSON configuration from TOML and CSV files.

    Args:
        labware_toml: Path to labware dictionary TOML
        settings_toml: Path to settings TOML
        csv_file: Path to CSV transfer file
        verbose: Print progress messages (default True for CLI compatibility)

    Returns:
        str: Compact JSON configuration string

    Raises:
        FileNotFoundError: If any input file is missing
        Exception: If parsing fails
    """
    if verbose:
        print(f"Reading configuration files...")
        print(f"  - Labware TOML: {labware_toml}")
        print(f"  - Settings TOML: {settings_toml}")
        print(f"  - CSV file: {csv_file}")

    # Read the TOML files
    labware_dict = read_toml_file(labware_toml)
    sample_settings = read_toml_file(settings_toml)

    # Read the CSV file
    csv_data = read_csv_file(csv_file)

    if verbose:
        print("✓ Successfully read all configuration files")

    # Create the combined configuration
    config = {
        "labware_dict": labware_dict,
        "settings": sample_settings,
        "csv_data": csv_data
    }

    # Convert to compact JSON string with proper escaping
    json_string = json.dumps(config, separators=(',', ':'), ensure_ascii=True)

    return json_string


def update_protocol_file(
    protocol_file: str,
    json_config: str,
    verbose: bool = True
) -> bool:
    """Update the cherry_pick_protocol.py with the new JSON configuration.

    Args:
        protocol_file: Path to protocol file to update
        json_config: JSON configuration string to embed
        verbose: Print progress messages (default True for CLI compatibility)

    Returns:
        bool: True if successful

    Raises:
        FileNotFoundError: If protocol file doesn't exist
        ValueError: If get_values() pattern not found
        Exception: If file operations fail
    """
    if verbose:
        print(f"Reading {protocol_file}...")

    try:
        with open(protocol_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"Protocol file not found: {protocol_file}")
    except Exception as e:
        raise Exception(f"Error reading protocol file: {e}")

    # Find and replace the JSON loads line in get_values function
    # Pattern matches: _all_values = json.loads("""any JSON string here""")
    # Handle both single-line and multi-line JSON
    pattern = r'(_all_values = json\.loads\(\"\"\").*?(\"\"\")\)'

    # Create the replacement with the new JSON config
    # Use json.dumps to properly escape the JSON for embedding in triple quotes
    escaped_json = json_config.replace('\\', '\\\\').replace('"""', '\\"""')
    replacement = f'\\g<1>{escaped_json}\\g<2>)'

    # Perform the replacement
    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

    # Check if replacement was made
    if new_content == content:
        # Check if the current JSON is already up to date
        if json_config in content:
            if verbose:
                print("✓ Protocol file is already up to date with current configuration")
            return True
        else:
            raise ValueError("No replacement was made. The get_values() function pattern might not match.")

    # Patch metadata protocolName if protocol_name is configured
    try:
        config = json.loads(json_config)
        protocol_name = config.get('settings', {}).get('settings', {}).get('general', {}).get('protocol_name', '')
        if protocol_name:
            metadata_pattern = r"('protocolName'\s*:\s*')([^']*)(')";
            new_content = re.sub(metadata_pattern, lambda m: m.group(1) + protocol_name + m.group(3), new_content)
            if verbose:
                print(f"✓ Updated protocol name to: {protocol_name}")
    except (json.JSONDecodeError, AttributeError):
        pass  # If JSON parsing fails, skip metadata patching

    if verbose:
        print(f"Writing updated {protocol_file}...")

    try:
        with open(protocol_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        if verbose:
            print("✓ Successfully updated protocol file")
        return True
    except Exception as e:
        raise Exception(f"Error writing protocol file: {e}")


def generate_protocol(
    labware_toml_path: str,
    settings_toml_path: str,
    csv_path: str,
    protocol_path: str,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    High-level orchestration function for MCP usage.

    Combines all steps: read configs → create JSON → embed in protocol.

    Args:
        labware_toml_path: Path to labware dictionary TOML file
        settings_toml_path: Path to settings TOML file
        csv_path: Path to CSV transfer file
        protocol_path: Path to protocol file to update
        verbose: Print progress messages (default False for MCP library usage)

    Returns:
        dict: {
            'protocol_file': str - Path to updated protocol file
            'json_size': int - Size of embedded JSON config in characters
            'message': str - Success message
        }

    Raises:
        FileNotFoundError: If any input file is missing
        ValueError: If validation or embedding fails
        Exception: If any operation fails

    Example:
        >>> result = generate_protocol(
        ...     'labware_dict.toml',
        ...     'settings.toml',
        ...     'CSVs/experiment.csv',
        ...     'CherryPick_OT2.py',
        ...     verbose=False
        ... )
        >>> print(result['message'])
        Protocol generated successfully
    """
    # Create JSON configuration from TOML + CSV
    json_config = create_json_config(
        labware_toml_path,
        settings_toml_path,
        csv_path,
        verbose=verbose
    )

    # Embed JSON in protocol file
    update_protocol_file(protocol_path, json_config, verbose=verbose)

    # Return structured result for MCP
    return {
        'protocol_file': protocol_path,
        'json_size': len(json_config),
        'message': 'Protocol generated successfully'
    }
