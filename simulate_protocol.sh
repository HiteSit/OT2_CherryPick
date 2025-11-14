#!/bin/bash
# Usage: ./simulate_protocol.sh <csv_file> [--send-to-opentrons]
# Runs helper script to update protocol, then simulates with custom labware

# Configuration selector - change this to switch machines
MACHINE_CONFIG="local"

# Utility functions removed - no longer creating new UUID folders

# Function to setup environment variables based on machine configuration
setup_environment() {
    case "$MACHINE_CONFIG" in
        "local")
            # Configure Windows paths - will be auto-converted to WSL format
            LABWARE_PATH_WIN="C:\Users\ricca\AppData\Roaming\Opentrons\labware"
            TARGET_PROTOCOL_SRC_WIN="C:\Users\ricca\AppData\Roaming\Opentrons\protocols\78a4cef9-4296-4bb8-b0d7-073162f7c40f\src"
            ;;
        "remote")
            # Configure Windows paths - will be auto-converted to WSL format
            LABWARE_PATH_WIN="C:\Users\opentrons_PC\AppData\Roaming\Opentrons\labware"
            TARGET_PROTOCOL_SRC_WIN="C:\Users\opentrons_PC\AppData\Roaming\Opentrons\protocols\some-uuid\src"
            ;;
        *)
            echo "Unknown machine configuration: $MACHINE_CONFIG"
            echo "Available configurations: local, remote"
            exit 1
            ;;
    esac

    # Allow runtime overrides via environment variables provided by the GUI/backend
    if [ -n "${LABWARE_PATH_WIN_OVERRIDE:-}" ]; then
        LABWARE_PATH_WIN="$LABWARE_PATH_WIN_OVERRIDE"
    fi
    if [ -n "${TARGET_PROTOCOL_SRC_WIN_OVERRIDE:-}" ]; then
        TARGET_PROTOCOL_SRC_WIN="$TARGET_PROTOCOL_SRC_WIN_OVERRIDE"
    fi

    # Auto-convert Windows paths to WSL format
    if [ -n "$LABWARE_PATH_WIN" ]; then
        if command -v wslpath &> /dev/null; then
            export LABWARE_PATH=$(wslpath "$LABWARE_PATH_WIN")
        else
            # Fallback manual conversion if wslpath is not available
            export LABWARE_PATH=$(echo "$LABWARE_PATH_WIN" | sed 's|^C:\\|/mnt/c/|' | sed 's|\\|/|g')
        fi
    fi

    if [ -n "$TARGET_PROTOCOL_SRC_WIN" ]; then
        if command -v wslpath &> /dev/null; then
            export TARGET_PROTOCOL_SRC=$(wslpath "$TARGET_PROTOCOL_SRC_WIN")
        else
            # Fallback manual conversion if wslpath is not available
            export TARGET_PROTOCOL_SRC=$(echo "$TARGET_PROTOCOL_SRC_WIN" | sed 's|^C:\\|/mnt/c/|' | sed 's|\\|/|g')
        fi
    fi
}

# Setup the environment
setup_environment

# Parse command line arguments
CSV_FILE=""
SEND_TO_OPENTRONS=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --send-to-opentrons)
            SEND_TO_OPENTRONS=true
            shift
            ;;
        -*)
            echo "Unknown option $1"
            exit 1
            ;;
        *)
            CSV_FILE="$1"
            shift
            ;;
    esac
done

if [ -z "$CSV_FILE" ]; then
  echo "Usage: $0 <csv_file> [--send-to-opentrons]"
  echo ""
  echo "Examples:"
  echo "  ./simulate_protocol.sh data.csv                      # Normal simulation"
  echo "  ./simulate_protocol.sh data.csv --send-to-opentrons  # Simulate + overwrite configured protocol"
  echo ""
  echo "This will:"
  echo "  1. Run helper_cherry_pick.py to update the protocol with current TOML/CSV"
  echo "  2. Simulate the protocol with custom labware from $LABWARE_PATH"
  echo "  3. Copy protocol to clipboard if simulation succeeds"
  echo "  4. If --send-to-opentrons: Overwrite protocol at TARGET_PROTOCOL_SRC ($TARGET_PROTOCOL_SRC)"
  echo ""
  echo "Configuration: Currently using '$MACHINE_CONFIG' machine setup"
  echo "To change: Edit MACHINE_CONFIG variable at top of script"
  exit 1
fi

# Validate TARGET_PROTOCOL_SRC if --send-to-opentrons is used
if [ "$SEND_TO_OPENTRONS" = true ]; then
    if [ -z "$TARGET_PROTOCOL_SRC" ]; then
        echo "Error: TARGET_PROTOCOL_SRC is not configured in setup_environment()"
        echo "Please set TARGET_PROTOCOL_SRC to point to the desired protocol src directory"
        exit 1
    fi

    if [ ! -d "$TARGET_PROTOCOL_SRC" ]; then
        echo "Error: TARGET_PROTOCOL_SRC directory does not exist: $TARGET_PROTOCOL_SRC"
        echo "Please update TARGET_PROTOCOL_SRC in setup_environment() to point to a valid protocol src directory"
        exit 1
    fi

    # Check if there's exactly one Python file in the target directory
    PYTHON_FILES=$(find "$TARGET_PROTOCOL_SRC" -maxdepth 1 -name "*.py" -type f)
    PYTHON_FILE_COUNT=$(echo "$PYTHON_FILES" | grep -c .)

    if [ $PYTHON_FILE_COUNT -eq 0 ]; then
        echo "Error: No Python files found in TARGET_PROTOCOL_SRC: $TARGET_PROTOCOL_SRC"
        exit 1
    elif [ $PYTHON_FILE_COUNT -gt 1 ]; then
        echo "Error: Multiple Python files found in TARGET_PROTOCOL_SRC: $TARGET_PROTOCOL_SRC"
        echo "Found files:"
        echo "$PYTHON_FILES"
        exit 1
    fi

    TARGET_PYTHON_FILE="$PYTHON_FILES"
    echo "Windows path configured: $TARGET_PROTOCOL_SRC_WIN"
    echo "WSL path converted: $TARGET_PROTOCOL_SRC"
    echo "Target protocol file: $TARGET_PYTHON_FILE"
fi

echo "=== Using $MACHINE_CONFIG configuration ==="

echo "=== Step 1: Updating protocol with helper ==="
uv run python helper_cherry_pick.py -l labware_dict.toml -s settings.toml -c "$CSV_FILE" -p CherryPick_OT2.py

echo ""
echo "=== Step 2: Running protocol simulation ==="
opentrons_simulate --custom-labware $LABWARE_PATH CherryPick_OT2.py

# Check if simulation succeeded and copy to clipboard if it did
if [ $? -eq 0 ]; then
    echo ""
    echo "=== Simulation successful! Copying CherryPick_OT2.py to clipboard ==="
    if cat CherryPick_OT2.py | /mnt/c/Windows/System32/clip.exe 2>/dev/null; then
        echo "Protocol copied to clipboard ✓"
    else
        echo "Failed to copy to clipboard - but simulation was successful"
        echo "Protocol file: $(pwd)/CherryPick_OT2.py"
    fi

    # If --send-to-opentrons flag is set, overwrite existing protocol
    if [ "$SEND_TO_OPENTRONS" = true ]; then
        echo ""
        echo "=== Step 3: Overwriting existing protocol ==="

        # Get the filename from the target path for logging
        TARGET_FILENAME=$(basename "$TARGET_PYTHON_FILE")

        # Overwrite the target file with our protocol
        cp "CherryPick_OT2.py" "$TARGET_PYTHON_FILE"

        echo "✓ Protocol overwritten successfully:"
        echo "   Target: $TARGET_PYTHON_FILE"
        echo "   Original filename: $TARGET_FILENAME (preserved)"
        echo "   Configuration: TARGET_PROTOCOL_SRC=$TARGET_PROTOCOL_SRC"
        echo ""
        echo "The protocol should now be updated in the Opentrons App!"
        echo "Note: You may need to refresh or reload the protocol in the app."
    fi
else
    echo ""
    echo "=== Simulation failed - protocol NOT copied to clipboard ==="
fi
