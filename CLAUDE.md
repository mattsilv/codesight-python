# CodeSight Development Guide

## Version Information
Current version: 0.1.2

## Project Overview
CodeSight is a tool for collecting and formatting code from a project to be used with LLMs like Claude. It:
1. Recursively collects code files, respecting .gitignore patterns
2. Formats them with appropriate headers and context
3. Optimizes token usage by prioritizing recent files
4. Outputs the formatted code to both a file and clipboard

## Recent Improvements (v0.1.2)
- Added precise type hints throughout the codebase
- Used dataclasses for structured metadata instead of nested dictionaries
- Improved module structure with constants and better docstrings
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
1. Update `__version__` in `/Users/m/gh/codesight-python/.codesight/bin/cs.py`
2. Update version in README.md and CLAUDE.md
3. Create a release tag in GitHub using the version number (e.g., v0.2.0)
4. Update release notes with all changes since the previous version