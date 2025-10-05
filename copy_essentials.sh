#!/bin/bash
# Copy essential OpenTrons cherry-pick files to target directory
# Usage: ./copy_essentials.sh [target_directory]

# Default target directory (placeholder - change as needed)
DEFAULT_TARGET="/mnt/domling/Instrument_OT-2/protocols/cherry_pick"

# Use provided target or default
TARGET_DIR="${1:-$DEFAULT_TARGET}"

# Files and directories to copy
ITEMS_TO_COPY=(
    "CSVs"
    "scripts_library"
    "CherryPick_OT2.py"
    "helper_cherry_pick.py"
    "settings.toml"
    "simulate_protocol.sh"
    "labware_dict.toml"
)

echo "=== OpenTrons Cherry-Pick File Copy Tool ==="
echo "Target directory: $TARGET_DIR"
echo ""

# Create target directory if it doesn't exist
if [ ! -d "$TARGET_DIR" ]; then
    echo "Creating target directory: $TARGET_DIR"
    mkdir -p "$TARGET_DIR" || {
        echo "ERROR: Failed to create target directory"
        exit 1
    }
fi

# Copy each item
echo "Copying files..."
for item in "${ITEMS_TO_COPY[@]}"; do
    if [ -e "$item" ]; then
        if [ -d "$item" ]; then
            echo "  📁 Copying directory: $item"
            cp -r "$item" "$TARGET_DIR/" || {
                echo "ERROR: Failed to copy directory $item"
                exit 1
            }
        else
            echo "  📄 Copying file: $item"
            cp "$item" "$TARGET_DIR/" || {
                echo "ERROR: Failed to copy file $item"
                exit 1
            }
        fi
    else
        echo "WARNING: $item not found, skipping"
    fi
done

echo ""
echo "✅ Copy complete!"
echo "Files copied to: $TARGET_DIR"
echo ""
echo "Contents of target directory:"
ls -la "$TARGET_DIR"