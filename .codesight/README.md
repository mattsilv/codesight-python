# CodeSight Python

A Python utility for collecting and formatting code for LLMs, optimized for performance on M-series Macs.

## Quick Start

```bash
# Install globally
git clone https://github.com/mattsilv/codesight-python.git
cd codesight-python
.codesight/bin/install.sh

# Initialize in your project
cd /path/to/your/project
cs -i

# Run analysis
cs
```

### Installation Details

The install script will place CodeSight in a global location to make it available system-wide:

1. **Installation Locations** (in order of preference):
   - `/usr/local/bin` (if you have write permissions)
   - `/opt/homebrew/bin` (on Apple Silicon Macs with Homebrew)
   - `~/bin` (in your home directory, created if it doesn't exist)

2. **What Gets Installed:**
   - `cs` - The main command for using CodeSight
   - `cs-dev` - Used only for developing CodeSight itself

3. **Verification:**
   After installation, verify with:
   ```bash
   which cs      # Should show the installation path
   cs --version  # Should show the current version
   ```

## Core Workflows

### Use Case 1: Using CodeSight in Your Projects

```bash
# Global installation (one-time)
git clone https://github.com/mattsilv/codesight-python.git
cd codesight-python
.codesight/bin/install.sh    # Installs to system-wide location

# First-time setup in each project
cd /your/project
cs -i                        # Initialize project config and dependencies

# Regular usage
cs                           # Standard analysis with improvement prompt
cs -b "Description"          # Analyze with bug-fixing prompt
cs -c                        # Configure settings

# Update CodeSight (when new versions are available)
cd /path/to/codesight-python
git pull
.codesight/bin/install.sh    # Updates the global installation
```

> **Note:** The `cs` command is installed globally in `/usr/local/bin`, `/opt/homebrew/bin`, or `~/bin`, but each project gets its own `.codesight` directory with project-specific settings and dependencies.

### Use Case 2: Developing CodeSight (Dogfooding Mode)

```bash
# Install for development
cd /path/to/codesight-python
.codesight/bin/install.sh

# Run CodeSight on itself (dogfooding)
cs-dev                  # Analyze CodeSight with itself
cs --dogfood            # Alternative method

# Test changes
make edit-to-code.py
cs-dev --debug          # Test with debugging info

# Update to latest version during development
git pull
.codesight/bin/install.sh
```

### Use Case 3: Uninstall/Reinstall (Clean Slate)

```bash
# Method 1: Complete uninstallation (if you have the source repo)
cd /path/to/codesight-python
.codesight/bin/uninstall.sh

# Method 2: Uninstall from any project with CodeSight installed
cd /path/to/any-project-with-codesight
.codesight/bin/uninstall.sh

# Method 3: Uninstall command (if you can't find the repo or a project)
curl -s https://raw.githubusercontent.com/mattsilv/codesight-python/main/.codesight/bin/uninstall.sh | bash

# Verify removal
which cs                # Should return nothing
which cs-dev            # Should return nothing

# Fresh installation
cd /path/to/codesight-python
.codesight/bin/install.sh
```

## Command Reference

- `cs` - Run analysis on current project
- `cs -i` - Initialize CodeSight in current project
- `cs -b "Bug description"` - Run with bug-fixing prompt
- `cs -c` - Configure settings
- `cs --version` - Show version information
- `cs --debug` - Show debugging information
- `cs-dev` - Developer mode for CodeSight project

## Version Management

CodeSight uses semantic versioning. Check your version with:

```bash
cs --version
```

When a new version is available, you'll see an update notification after running any command.

## Project Structure

```
.codesight/                # Generated in your project
├── .venv/                 # Project-specific virtual environment
├── llm.txt                # Generated output file
└── .codesight-config.json # Project configuration
```

## Common Issues

- **Missing dependencies**: Automatically fixed on run
- **Nested virtual environments**: Automatically detected and handled
- **Command not found**: After installation, you may need to open a new terminal window or run `source ~/.bashrc` or `source ~/.zshrc` if the installer added `~/bin` to your PATH
- **Permission issues during installation**: If you don't have write permissions to `/usr/local/bin`, the installer will fall back to `~/bin`
- **Path issues**: Use `cs --debug` to verify installation paths and see where CodeSight is installed
- **Uninstalling CodeSight**: Run `.codesight/bin/uninstall.sh` from any project where it's installed or directly from the repository

If CodeSight isn't in your PATH after installation, verify installation with:
```bash
# Verify which bin directory was used
ls -la /usr/local/bin/cs     # Standard location
ls -la /opt/homebrew/bin/cs  # Homebrew on Apple Silicon
ls -la ~/bin/cs              # Fallback location

# Check if ~/bin is in your PATH (if that's where it was installed)
echo $PATH | grep -q "$HOME/bin" && echo "~/bin is in PATH" || echo "~/bin is NOT in PATH"
```

## License

MIT License - see the [LICENSE](../LICENSE) file for details.