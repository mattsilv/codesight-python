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

## Core Workflows

### Use Case 1: Using CodeSight in Your Projects

```bash
# First-time setup in a project
cd /your/project
cs -i                   # Initialize project config and dependencies

# Regular usage
cs                      # Standard analysis with improvement prompt
cs -b "Description"     # Analyze with bug-fixing prompt
cs -c                   # Configure settings

# Update CodeSight
cd /path/to/codesight-python
git pull
.codesight/bin/install.sh
```

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
# Complete uninstallation
cd /path/to/codesight-python
.codesight/bin/uninstall.sh

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
- **Path issues**: Use `cs --debug` to verify installation paths

## License

MIT License - see the [LICENSE](../LICENSE) file for details.