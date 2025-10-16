#!/usr/bin/env python3
"""
Helper script to convert TOML files and CSV to JSON format for cherry_pick_protocol.py
Command-line tool that updates the get_values() function with embedded configuration.

This is now a thin CLI wrapper around the core protocol_generator module.
Core functions moved to src/ot2_cherrypick_mcp/core/protocol_generator.py for cleaner architecture.
"""

import sys
import argparse

# Import core functions from the package
from src.ot2_cherrypick_mcp.core.protocol_generator import (
    read_toml_file,
    read_csv_file,
    create_json_config,
    update_protocol_file,
    generate_protocol,
)


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

    try:
        # Create the JSON configuration
        json_config = create_json_config(args.labware_toml, args.settings_toml, args.csv_file, verbose=True)

        print(f"Generated JSON config ({len(json_config)} characters)")

        if args.verbose:
            print(f"JSON preview: {json_config[:100]}...")
            print()

        # Update the protocol file
        update_protocol_file(args.protocol_file, json_config, verbose=True)

        print("\n✅ Successfully converted to JSON-based configuration!")
        print("The protocol no longer requires the 'toml' package.")
        print(f"Updated file: {args.protocol_file}")
        sys.exit(0)

    except FileNotFoundError as e:
        print(f"\n❌ File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"\n❌ Validation error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
