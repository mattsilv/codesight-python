#!/bin/bash
# CodeSight installer - Creates symlink to make 'cs' available globally

# Make sure we find the real path of this script
if command -v realpath &> /dev/null; then
    # Use realpath if available (most Linux distros)
    REAL_PATH=$(realpath "${BASH_SOURCE[0]}")
    SCRIPT_DIR=$(dirname "$REAL_PATH")
elif command -v readlink &> /dev/null && [[ $(uname) != "Darwin" || $(readlink -f / 2>/dev/null) ]]; then
    # Try readlink -f (works on Linux and some macOS)
    REAL_PATH=$(readlink -f "${BASH_SOURCE[0]}")
    SCRIPT_DIR=$(dirname "$REAL_PATH")
else
    # Fall back to manual resolution for macOS without proper tools
    SOURCE="${BASH_SOURCE[0]}"
    while [ -h "$SOURCE" ]; do
        DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"
        SOURCE="$(readlink "$SOURCE")"
        [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE"
    done
    SCRIPT_DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"
fi

CS_SCRIPT="$SCRIPT_DIR/cs"

# Verify files exist
if [ ! -f "$CS_SCRIPT" ]; then
    echo "Error: CS script not found at $CS_SCRIPT"
    echo "This installer must be run from the .codesight/bin directory"
    exit 1
fi

if [ ! -f "$SCRIPT_DIR/cs.py" ]; then
    echo "Error: cs.py not found at $SCRIPT_DIR"
    echo "This installer must be run from the .codesight/bin directory"
    exit 1
fi

# Make scripts executable
chmod +x "$CS_SCRIPT" "$SCRIPT_DIR/cs.py"

# Determine installation directory based on macOS best practices
# First try /usr/local/bin (preferred), then fall back to ~/bin
if [ -d "/usr/local/bin" ] && [ -w "/usr/local/bin" ]; then
    # User has write access to /usr/local/bin (preferred)
    INSTALL_DIR="/usr/local/bin"
elif [ -d "/opt/homebrew/bin" ] && [ -w "/opt/homebrew/bin" ]; then
    # Homebrew on Apple Silicon
    INSTALL_DIR="/opt/homebrew/bin"
elif [ -d "$HOME/bin" ]; then
    # ~/bin exists, use it
    INSTALL_DIR="$HOME/bin"
else
    # Create ~/bin
    mkdir -p "$HOME/bin"
    INSTALL_DIR="$HOME/bin"
    
    # Add to PATH if needed (check both common shell config files)
    if ! grep -q "$HOME/bin" "$HOME/.bashrc" 2>/dev/null && ! grep -q "$HOME/bin" "$HOME/.zshrc" 2>/dev/null; then
        if [ -f "$HOME/.zshrc" ]; then
            echo 'export PATH="$HOME/bin:$PATH"' >> "$HOME/.zshrc"
            echo "Added $HOME/bin to PATH in .zshrc"
            echo "Run 'source ~/.zshrc' to update your current shell"
        elif [ -f "$HOME/.bashrc" ]; then
            echo 'export PATH="$HOME/bin:$PATH"' >> "$HOME/.bashrc"
            echo "Added $HOME/bin to PATH in .bashrc"
            echo "Run 'source ~/.bashrc' to update your current shell"
        else
            # Create .zshrc if neither exists (macOS default is zsh)
            echo 'export PATH="$HOME/bin:$PATH"' >> "$HOME/.zshrc"
            echo "Created .zshrc and added $HOME/bin to PATH"
            echo "Run 'source ~/.zshrc' to update your current shell"
        fi
    fi
fi

# Check if already installed and remove old installations
if [ -L "$INSTALL_DIR/cs" ]; then
    echo "CodeSight already installed. Updating installation..."
    rm "$INSTALL_DIR/cs"
elif [ -e "$INSTALL_DIR/cs" ]; then
    echo "Warning: $INSTALL_DIR/cs exists but is not a symlink."
    
    # Check if it's a previous version of our wrapper
    if grep -q "CodeSight wrapper script" "$INSTALL_DIR/cs" 2>/dev/null; then
        echo "Detected previous CodeSight installation. Updating..."
        rm "$INSTALL_DIR/cs"
    else
        echo "This appears to be a different program. Backing up to $INSTALL_DIR/cs.bak and replacing..."
        mv "$INSTALL_DIR/cs" "$INSTALL_DIR/cs.bak"
    fi
fi

# Also check for cs-dev
if [ -L "$INSTALL_DIR/cs-dev" ] || [ -e "$INSTALL_DIR/cs-dev" ]; then
    echo "Updating cs-dev script..."
    rm -f "$INSTALL_DIR/cs-dev"
fi

# Use a wrapper script instead of a symlink for better reliability
echo "Creating wrapper script at $INSTALL_DIR/cs..."
cat > "$INSTALL_DIR/cs" << EOF
#!/bin/bash
# CodeSight wrapper script
# Installation path: $(realpath "$CS_SCRIPT" 2>/dev/null || echo "$CS_SCRIPT")
# Installation date: $(date)
"$(realpath "$CS_SCRIPT" 2>/dev/null || echo "$CS_SCRIPT")" "\$@"
EOF
chmod +x "$INSTALL_DIR/cs"

# Create dev script wrapper too
echo "Creating developer wrapper at $INSTALL_DIR/cs-dev..."
cat > "$INSTALL_DIR/cs-dev" << EOF
#!/bin/bash
# CodeSight developer mode wrapper script
# Installation path: $(realpath "$SCRIPT_DIR/cs-dev" 2>/dev/null || echo "$SCRIPT_DIR/cs-dev")
# Installation date: $(date)
"$(realpath "$SCRIPT_DIR/cs-dev" 2>/dev/null || echo "$SCRIPT_DIR/cs-dev")" "\$@"
EOF
chmod +x "$INSTALL_DIR/cs-dev"

# Simple validation
if [ ! -x "$INSTALL_DIR/cs" ]; then
    echo "Error: Failed to create executable wrapper script."
    echo "Try running: sudo ln -sf \"$CS_SCRIPT\" /usr/local/bin/cs"
    exit 1
fi

# Extract version number from cs.py
VERSION=$(grep -o '"[0-9]\+\.[0-9]\+\.[0-9]\+"' "$SCRIPT_DIR/cs.py" | tr -d '"')
echo "CodeSight v${VERSION} installed successfully to $INSTALL_DIR/cs"
echo ""
echo "Usage examples:"
echo "  cs                    # Analyze current directory with improvement prompt"
echo "  cs -b \"Description\"   # Analyze with bug prompt and custom description"
echo "  cs -c                 # Configure CodeSight settings"
echo "  cs -i                 # Initialize CodeSight in the current project"
echo ""
echo "Project setup:"
echo "  cd /path/to/your/project"
echo "  cs -i                 # Initialize project-specific config"
echo "  cs                    # Then just run 'cs' without arguments"
echo ""
echo "For CodeSight project developers:"
echo "  cd /path/to/codesight-python/.codesight"
echo "  cs .                  # Analyze CodeSight itself (dogfood mode)"
echo ""
echo "Debugging:"
echo "  cs --debug            # Show debug information about paths and configuration"