#!/usr/bin/env python3
"""
Helper script to convert TOML files and CSV to JSON format for cherry_pick_protocol.py
Command-line tool that updates the get_values() function with embedded configuration.
"""

import json
import toml
import re
import sys
import argparse


def read_toml_file(filepath):
    """Read and parse a TOML file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return toml.load(f)
    except Exception as e:
        print(f"Error reading TOML file {filepath}: {e}")
        sys.exit(1)


def read_csv_file(filepath):
    """Read a CSV file as string with proper newline escaping for JSON"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            # Escape newlines for JSON embedding - this is critical!
            content = content.replace('\n', '\\n')
            return content
    except Exception as e:
        print(f"Error reading CSV file {filepath}: {e}")
        sys.exit(1)


def create_json_config(labware_toml, settings_toml, csv_file):
    """Create the JSON configuration from TOML and CSV files"""
    
    print(f"Reading configuration files...")
    print(f"  - Labware TOML: {labware_toml}")
    print(f"  - Settings TOML: {settings_toml}")
    print(f"  - CSV file: {csv_file}")
    
    # Read the TOML files
    labware_dict = read_toml_file(labware_toml)
    sample_settings = read_toml_file(settings_toml)
    
    # Read the CSV file
    csv_data = read_csv_file(csv_file)
    
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


def update_protocol_file(protocol_file, json_config):
    """Update the cherry_pick_protocol.py with the new JSON configuration"""
    
    print(f"Reading {protocol_file}...")
    
    try:
        with open(protocol_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading protocol file: {e}")
        sys.exit(1)
    
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
            print("✓ Protocol file is already up to date with current configuration")
            return True
        else:
            print("⚠️  Warning: No replacement was made. The get_values() function pattern might not match.")
            return False
    
    print(f"Writing updated {protocol_file}...")
    
    try:
        with open(protocol_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("✓ Successfully updated protocol file")
        return True
    except Exception as e:
        print(f"Error writing protocol file: {e}")
        sys.exit(1)


def main():
    """Main execution with command-line argument parsing"""
    parser = argparse.ArgumentParser(
        description='Convert TOML configuration files and CSV to embedded JSON in cherry_pick_protocol.py',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Using default file paths
  python helper_cherry_pick.py
  
  # Specify custom file paths
  python helper_cherry_pick.py -l labware_definitions/labware_dict.toml -s sample_settings.toml -c CSVs/CSV_Personal.csv
  
  # Specify output protocol file
  python helper_cherry_pick.py -p my_protocol.py
        """
    )
    
    parser.add_argument('-l', '--labware-toml', 
                       default='labware_dict.toml',
                       help='Path to labware dictionary TOML file (default: labware_dict.toml)')
    
    parser.add_argument('-s', '--settings-toml',
                       default='sample_settings.toml', 
                       help='Path to sample settings TOML file (default: sample_settings.toml)')
    
    parser.add_argument('-c', '--csv-file',
                       default='CSVs/CSV_Personal.csv',
                       help='Path to CSV transfer file (default: CSVs/CSV_Personal.csv)')
    
    parser.add_argument('-p', '--protocol-file',
                       default='cherry_pick_protocol.py',
                       help='Path to protocol file to update (default: cherry_pick_protocol.py)')
    
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Enable verbose output')
    
    args = parser.parse_args()
    
    print("=== Cherry-Pick Protocol Helper ===")
    print("Converting TOML + CSV → JSON configuration...")
    
    if args.verbose:
        print(f"Configuration:")
        print(f"  Labware TOML: {args.labware_toml}")
        print(f"  Settings TOML: {args.settings_toml}")
        print(f"  CSV file: {args.csv_file}")
        print(f"  Protocol file: {args.protocol_file}")
        print()
    
    # Create the JSON configuration
    json_config = create_json_config(args.labware_toml, args.settings_toml, args.csv_file)
    
    print(f"Generated JSON config ({len(json_config)} characters)")
    
    if args.verbose:
        print(f"JSON preview: {json_config[:100]}...")
        print()
    
    # Update the protocol file
    success = update_protocol_file(args.protocol_file, json_config)
    
    if success:
        print("\n✅ Successfully converted to JSON-based configuration!")
        print("The protocol no longer requires the 'toml' package.")
        print(f"Updated file: {args.protocol_file}")
    else:
        print("\n❌ Failed to update protocol file.")
        sys.exit(1)


if __name__ == "__main__":
    main()