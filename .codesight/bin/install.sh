#!/bin/bash
# CodeSight installer - Creates symlink in /usr/local/bin

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
CS_SCRIPT="$SCRIPT_DIR/cs"

# Check if already installed
if [ -L "/usr/local/bin/cs" ]; then
    echo "CodeSight already installed. Updating symlink..."
    rm /usr/local/bin/cs
fi

# Create symlink
ln -s "$CS_SCRIPT" /usr/local/bin/cs
chmod +x "$CS_SCRIPT"

echo "CodeSight installed! You can now use 'cs' from anywhere."
echo ""
echo "Usage examples:"
echo "  cs                    # Analyze current directory with improvement prompt"
echo "  cs -b \"Description\"   # Analyze with bug prompt and custom description"
echo "  cs -c                 # Configure CodeSight settings"
echo "  cs path/to/project    # Analyze a specific project"
echo ""
echo "For CodeSight project developers:"
echo "  cd /path/to/codesight-python/.codesight"
echo "  cs .                  # Analyze CodeSight itself (dogfood mode)"