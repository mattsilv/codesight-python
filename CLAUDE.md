# CodeSight Development Guide

## Version Information
Current version: 0.1.8

## Project Overview
CodeSight is a tool for collecting and formatting code from a project to be used with LLMs like Claude. It:
1. Recursively collects code files, respecting .gitignore patterns
2. Formats them with appropriate headers and context
3. Optimizes token usage by prioritizing recent files
4. Outputs the formatted code to both a file and clipboard

## Recent Improvements (v0.1.8)
- New command `cs -t` or `cs --tokens` to show top files by token count
- Comprehensive table showing files and directories with highest token usage
- Percentage breakdown of token usage across the project
- Improved file exclusion patterns to automatically ignore data files
- Added extensive list of data file extensions to global exclusions
- Enhanced visibility into token usage to help users optimize their projects

## Previous Improvements (v0.1.7)
- Automatic dependency installation during initialization and runtime
- Support for multiple package managers (pip, python -m pip, uv)
- Smart detection of virtual environments and installation context
- Proactive dependency management that tries to install dependencies automatically
- Improved user experience with less manual steps required
- Fixed installation workflow to handle dependencies without user intervention
- Better handling of virtual environment detection and activation

## Previous Improvements (v0.1.6)
- Simplified dependency management to work with all Python environments
- Improved cross-compatibility with different package managers (pip, uv)
- More user-friendly error messages for missing dependencies
- Fixed installation errors on systems without pip available
- Removed complex subprocess calls that could fail in certain environments
- Better support for virtual environments

## Previous Improvements (v0.1.5)
- Dependency validation and auto-installation during runtime
- Improved dependency management for global installations
- Fixed missing dependency issues in fresh installations
- Added automatic installation of pyperclip dependency
- More robust dependency checking before running commands

## Previous Improvements (v0.1.4)
- Centralized version management with single source of truth in _version.py
- Automatic version updating in documentation files
- Improved installation and upgrade processes
- Better version detection during installation
- Enhanced uninstallation path resolution and protection for development repositories
- Fixed virtual environment detection and handling
- Added .gitignore checking and automatic updates
- Implemented version checking to notify users of updates

## Running Tests
```bash
cd /Users/m/gh/codesight-python && python -m pytest -xvs
```

## Common Issues and Fixes
- **Virtual environment detection**: Fixed issues with nested venvs by detecting and exiting any existing venv
- **Missing dependencies**: Improved initialization to check for and install required packages
- **Gitignore management**: Added warnings and fixes for projects that don't properly exclude CodeSight files

## Creating a New Release
1. Update `__version__` in `/Users/m/gh/codesight-python/.codesight/_version.py`
2. Run `.codesight/bin/version.sh` to automatically update README.md
3. Update CLAUDE.md with recent improvements 
4. Create a release tag in GitHub using the version number (e.g., v0.1.4)
5. Update release notes with all changes since the previous version