#!/bin/bash
# CodeSight installer - Creates symlink in /usr/local/bin

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
CS_SCRIPT="$SCRIPT_DIR/cs"

# Determine installation directory based on macOS best practices
# First try /usr/local/bin (preferred), then fall back to ~/bin
if [ -d "/usr/local/bin" ] && [ -w "/usr/local/bin" ]; then
    # User has write access to /usr/local/bin (preferred)
    INSTALL_DIR="/usr/local/bin"
elif [ -d "$HOME/bin" ]; then
    # ~/bin exists, use it
    INSTALL_DIR="$HOME/bin"
else
    # Create ~/bin
    mkdir -p "$HOME/bin"
    INSTALL_DIR="$HOME/bin"
    
    # Add to PATH if needed
    if ! grep -q "$HOME/bin" "$HOME/.bashrc" && ! grep -q "$HOME/bin" "$HOME/.zshrc"; then
        if [ -f "$HOME/.zshrc" ]; then
            echo 'export PATH="$HOME/bin:$PATH"' >> "$HOME/.zshrc"
            echo "Added $HOME/bin to PATH in .zshrc"
        elif [ -f "$HOME/.bashrc" ]; then
            echo 'export PATH="$HOME/bin:$PATH"' >> "$HOME/.bashrc"
            echo "Added $HOME/bin to PATH in .bashrc"
        fi
        echo "NOTE: You'll need to restart your terminal or run 'source ~/.zshrc' (or ~/.bashrc) for the PATH change to take effect."
    fi
fi

# Check if already installed
if [ -L "$INSTALL_DIR/cs" ]; then
    echo "CodeSight already installed. Updating symlink..."
    rm "$INSTALL_DIR/cs"
fi

# Create symlink
ln -s "$CS_SCRIPT" "$INSTALL_DIR/cs"
chmod +x "$CS_SCRIPT"

echo "CodeSight installed! You can now use 'cs' from anywhere."
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