#!/bin/bash
# CodeSight uninstaller - Removes global binaries and optionally configuration

# Print banner
echo "CodeSight Uninstaller"
echo "===================="
echo

# Get the absolute path of this script's directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
# Get the repository root directory (assuming standard structure)
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." &> /dev/null && pwd)"

# Check if running from the development repository
IS_DEV_REPO=false
if [ -d "$REPO_ROOT/.git" ] && [ -f "$REPO_ROOT/README.md" ] && grep -q "CodeSight" "$REPO_ROOT/README.md" 2>/dev/null; then
    IS_DEV_REPO=true
    echo "DEVELOPMENT REPOSITORY DETECTED at $REPO_ROOT"
    echo "This script will NOT remove any development binaries or scripts."
    echo "It will only uninstall externally installed versions of CodeSight."
    echo
fi

# Check for common installation locations
INSTALL_LOCATIONS=(
    "/usr/local/bin"
    "/opt/homebrew/bin"
    "$HOME/bin"
)

# Track if we found and removed anything
REMOVED=false

# Remove from each potential location
for LOCATION in "${INSTALL_LOCATIONS[@]}"; do
    if [ -e "$LOCATION/cs" ]; then
        # If this is a development repository, check if the binary points to it
        if [ "$IS_DEV_REPO" = true ]; then
            TARGET=$(grep -o '".*"' "$LOCATION/cs" 2>/dev/null | tr -d '"' | head -1)
            if [[ "$TARGET" == *"$REPO_ROOT"* ]]; then
                echo "⚠️  SKIPPING cs in $LOCATION (points to development repository)"
                continue
            fi
        fi
        
        echo "Removing cs from $LOCATION"
        rm -f "$LOCATION/cs"
        REMOVED=true
    fi
    
    if [ -e "$LOCATION/cs-dev" ]; then
        # If this is a development repository, check if the binary points to it
        if [ "$IS_DEV_REPO" = true ]; then
            TARGET=$(grep -o '".*"' "$LOCATION/cs-dev" 2>/dev/null | tr -d '"' | head -1)
            if [[ "$TARGET" == *"$REPO_ROOT"* ]]; then
                echo "⚠️  SKIPPING cs-dev in $LOCATION (points to development repository)"
                continue
            fi
        fi
        
        echo "Removing cs-dev from $LOCATION"
        rm -f "$LOCATION/cs-dev"
        REMOVED=true
    fi
done

if [ "$REMOVED" = false ]; then
    echo "No CodeSight installation found in standard locations."
    echo "If installed elsewhere, you may need to remove it manually."
fi

# Ask about removing global configuration
echo
echo "Would you like to remove global configuration too? [y/N]"
read -r REMOVE_CONFIG

if [[ "$REMOVE_CONFIG" =~ ^[Yy]$ ]]; then
    # Remove global cache file
    if [ -f "$HOME/.codesight_update_cache.json" ]; then
        echo "Removing update cache file"
        rm -f "$HOME/.codesight_update_cache.json"
    fi
    
    # Remove global config
    if [ -f "$HOME/.csconfig.json" ]; then
        echo "Removing global configuration"
        rm -f "$HOME/.csconfig.json"
    fi
    
    echo "Global configuration removed."
else
    echo "Global configuration preserved."
fi

echo
echo "CodeSight has been uninstalled from your system."
echo
echo "NOTE: Project-specific .codesight directories and configurations"
echo "in your projects have NOT been removed. You can delete them manually"
echo "if needed from each project directory."

exit 0