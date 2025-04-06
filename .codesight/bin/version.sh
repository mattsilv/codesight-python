#!/bin/bash
# Helper script to update version references in README files

# Get the version from _version.py
SCRIPT_DIR="$(dirname "$(dirname "$0")")"
VERSION=$(grep -o '"[0-9]\+\.[0-9]\+\.[0-9]\+"' "$SCRIPT_DIR/_version.py" | tr -d '"')

if [ -z "$VERSION" ]; then
    echo "Error: Could not extract version from _version.py"
    exit 1
fi

# Update README.md if it exists
README_PATH="$SCRIPT_DIR/../README.md"
if [ -f "$README_PATH" ]; then
    echo "Updating version in README.md to $VERSION"
    # Use sed to replace version information in README.md
    sed -i.bak "s/\*\*Version: [0-9]\+\.[0-9]\+\.[0-9]\+\*\*/\*\*Version: $VERSION\*\*/" "$README_PATH"
    rm -f "${README_PATH}.bak"
fi

# Print the current version
echo "$VERSION"