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
            # >>> EDIT THESE to match your Opentrons installation <<<
            LABWARE_PATH_WIN="C:\Users\YOUR_USERNAME\AppData\Roaming\Opentrons\labware"
            TARGET_PROTOCOL_SRC_WIN="C:\Users\YOUR_USERNAME\AppData\Roaming\Opentrons\protocols\YOUR_PROTOCOL_UUID\src"
            ;;
        "remote")
            # Configure Windows paths - will be auto-converted to WSL format
            # >>> EDIT THESE to match your remote machine's Opentrons installation <<<
            LABWARE_PATH_WIN="C:\Users\YOUR_USERNAME\AppData\Roaming\Opentrons\labware"
            TARGET_PROTOCOL_SRC_WIN="C:\Users\YOUR_USERNAME\AppData\Roaming\Opentrons\protocols\YOUR_PROTOCOL_UUID\src"
            ;;
        *)
            echo "Unknown machine configuration: $MACHINE_CONFIG"
            echo "Available configurations: local, remote"
            exit 1
            ;;
    esac

    # Allow runtime overrides via environment variables provided by the GUI/backend
    # OPENTRONS_DIR_WIN_OVERRIDE supersedes individual path overrides
    if [ -n "${OPENTRONS_DIR_WIN_OVERRIDE:-}" ]; then
        LABWARE_PATH_WIN="${OPENTRONS_DIR_WIN_OVERRIDE}\\labware"
        # For deployment, we create a new UUID-based directory under protocols/
        OPENTRONS_DIR_WIN="$OPENTRONS_DIR_WIN_OVERRIDE"
    fi
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
        -* )
            echo "Unknown option $1"
            exit 1
            ;;
        * )
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

# Validate deployment configuration if --send-to-opentrons is used
if [ "$SEND_TO_OPENTRONS" = true ]; then
    if [ -n "${OPENTRONS_DIR_WIN:-}" ]; then
        # Auto-UUID deployment mode: create new protocol directory
        if command -v wslpath &> /dev/null; then
            OPENTRONS_DIR_WSL=$(wslpath "$OPENTRONS_DIR_WIN")
        else
            OPENTRONS_DIR_WSL=$(echo "$OPENTRONS_DIR_WIN" | sed 's|^C:\\|/mnt/c/|' | sed 's|\\|/|g')
        fi
        if [ ! -d "$OPENTRONS_DIR_WSL" ]; then
            echo "Error: Opentrons directory does not exist: $OPENTRONS_DIR_WSL"
            exit 1
        fi
        PROTOCOL_UUID=$(cat /proc/sys/kernel/random/uuid 2>/dev/null || python3 -c "import uuid; print(uuid.uuid4())")
        TARGET_PROTOCOL_SRC="${OPENTRONS_DIR_WSL}/protocols/${PROTOCOL_UUID}/src"
        TARGET_ANALYSIS_DIR="${OPENTRONS_DIR_WSL}/protocols/${PROTOCOL_UUID}/analysis"
        mkdir -p "$TARGET_PROTOCOL_SRC" "$TARGET_ANALYSIS_DIR"
        TARGET_PYTHON_FILE="${TARGET_PROTOCOL_SRC}/CherryPick_OT2.py"
        DEPLOY_MODE="uuid"
        echo "Auto-UUID deployment mode"
        echo "  Opentrons dir: $OPENTRONS_DIR_WSL"
        echo "  UUID: $PROTOCOL_UUID"
        echo "  Target: $TARGET_PYTHON_FILE"
    elif [ -n "${TARGET_PROTOCOL_SRC:-}" ]; then
        # Legacy mode: overwrite existing protocol file
        if [ ! -d "$TARGET_PROTOCOL_SRC" ]; then
            echo "Error: TARGET_PROTOCOL_SRC directory does not exist: $TARGET_PROTOCOL_SRC"
            echo "Please update TARGET_PROTOCOL_SRC in setup_environment() to point to a valid protocol src directory"
            exit 1
        fi
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
        DEPLOY_MODE="legacy"
        echo "Legacy deployment mode"
        echo "  Windows path: $TARGET_PROTOCOL_SRC_WIN"
        echo "  WSL path: $TARGET_PROTOCOL_SRC"
        echo "  Target file: $TARGET_PYTHON_FILE"
    else
        echo "Error: No deployment target configured."
        echo "Set OPENTRONS_DIR_WIN or TARGET_PROTOCOL_SRC_WIN in setup_environment()"
        exit 1
    fi
fi

echo "=== Using $MACHINE_CONFIG configuration ==="

echo "=== Step 1: Updating protocol with helper ==="
uv run python helper_cherry_pick.py -l labware_dict.toml -s settings.toml -c "$CSV_FILE" -p CherryPick_OT2.py

echo ""
echo "=== Step 2: Running protocol simulation ==="
opentrons_simulate --custom-labware $LABWARE_PATH CherryPick_OT2.py
SIM_EXIT_CODE=$?

# Check if simulation succeeded and copy to clipboard if it did
if [ $SIM_EXIT_CODE -eq 0 ]; then
    echo ""
    echo "=== Simulation successful! Copying CherryPick_OT2.py to clipboard ==="
    if cat CherryPick_OT2.py | /mnt/c/Windows/System32/clip.exe 2>/dev/null; then
        echo "Protocol copied to clipboard ✓"
    else
        echo "Failed to copy to clipboard - but simulation was successful"
        echo "Protocol file: $(pwd)/CherryPick_OT2.py"
    fi

    # If --send-to-opentrons flag is set, deploy the protocol
    if [ "$SEND_TO_OPENTRONS" = true ]; then
        echo ""
        echo "=== Step 3: Deploying protocol ==="

        cp "CherryPick_OT2.py" "$TARGET_PYTHON_FILE"

        if [ "$DEPLOY_MODE" = "uuid" ]; then
            echo "✓ Protocol deployed successfully (new UUID):"
            echo "   UUID: $PROTOCOL_UUID"
            echo "   Target: $TARGET_PYTHON_FILE"
        else
            TARGET_FILENAME=$(basename "$TARGET_PYTHON_FILE")
            echo "✓ Protocol overwritten successfully:"
            echo "   Target: $TARGET_PYTHON_FILE"
            echo "   Original filename: $TARGET_FILENAME (preserved)"
        fi
        echo ""
        echo "The protocol should now be available in the Opentrons App!"
        echo "Note: You may need to refresh or reload the protocol in the app."
    fi
else
    echo ""
    echo "=== Simulation failed - protocol NOT copied to clipboard ==="
    exit $SIM_EXIT_CODE
fi
