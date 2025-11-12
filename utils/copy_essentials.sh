#!/bin/bash
# Copy essential OpenTrons cherry-pick files to target directory
# Usage: ./copy_essentials.sh

# Hardcoded directories (edit these as needed)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_DIR="$(dirname "$SCRIPT_DIR")"
TARGET_DIR="/mnt/domling/Instrument_OT-2/protocols/cherrypick"

# Files and directories to copy (relative to SOURCE_DIR)
ITEMS_TO_COPY=(
    "CSVs"
    "CherryPick_OT2.py"
    "helper_cherry_pick.py"
    "settings.toml"
    "labware_dict.toml"
    "pyproject.toml"
    "simulate_protocol.sh"
    "src/ot2_cherrypick_mcp/core/protocol_generator.py"
    "src/"
    "OT2_UserGuide/*.html"
)

echo "=== OpenTrons Cherry-Pick File Copy Tool ==="
echo "Source directory: $SOURCE_DIR"
echo "Target directory: $TARGET_DIR"
echo ""

# Verify source directory exists
if [ ! -d "$SOURCE_DIR" ]; then
    echo "ERROR: Source directory does not exist: $SOURCE_DIR"
    exit 1
fi

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
    # Check if item contains glob pattern (*)
    if [[ "$item" == *"*"* ]]; then
        # Handle glob pattern
        ITEM_DIR=$(dirname "$item")

        # Create target directory structure
        mkdir -p "$TARGET_DIR/$ITEM_DIR" || {
            echo "ERROR: Failed to create directory $ITEM_DIR"
            exit 1
        }

        # Expand glob and copy matching files
        MATCH_COUNT=0
        for matched_file in $SOURCE_DIR/$item; do
            if [ -e "$matched_file" ]; then
                filename=$(basename "$matched_file")
                echo "  📄 Copying: $ITEM_DIR/$filename"
                cp "$matched_file" "$TARGET_DIR/$ITEM_DIR/" || {
                    echo "ERROR: Failed to copy $matched_file"
                    exit 1
                }
                ((MATCH_COUNT++))
            fi
        done

        if [ $MATCH_COUNT -eq 0 ]; then
            echo "  ⚠️  WARNING: No files matching pattern '$item', skipping"
        fi
    else
        # Handle regular files/directories (existing logic)
        SOURCE_PATH="$SOURCE_DIR/$item"

        if [ -e "$SOURCE_PATH" ]; then
            if [ -d "$SOURCE_PATH" ]; then
                # Copy directory
                echo "  📁 Copying directory: $item"
                cp -r "$SOURCE_PATH" "$TARGET_DIR/" || {
                    echo "ERROR: Failed to copy directory $item"
                    exit 1
                }
            else
                # Copy file with folder structure
                ITEM_DIR=$(dirname "$item")
                if [ "$ITEM_DIR" != "." ]; then
                    # Create subdirectory structure in target
                    echo "  📁 Creating directory structure: $ITEM_DIR"
                    mkdir -p "$TARGET_DIR/$ITEM_DIR" || {
                        echo "ERROR: Failed to create directory $ITEM_DIR"
                        exit 1
                    }
                    echo "  📄 Copying file: $item"
                    cp "$SOURCE_PATH" "$TARGET_DIR/$item" || {
                        echo "ERROR: Failed to copy file $item"
                        exit 1
                    }
                else
                    echo "  📄 Copying file: $item"
                    cp "$SOURCE_PATH" "$TARGET_DIR/" || {
                        echo "ERROR: Failed to copy file $item"
                        exit 1
                    }
                fi
            fi
        else
            echo "  ⚠️  WARNING: $item not found in source, skipping"
        fi
    fi
done

echo ""
echo "✅ Copy complete!"
echo "Files copied to: $TARGET_DIR"
echo ""
echo "Contents of target directory:"
ls -la "$TARGET_DIR"