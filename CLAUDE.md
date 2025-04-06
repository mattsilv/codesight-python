# CodeSight Development Guide

## Version Information

Current version: 0.1.10

## Project Overview

CodeSight is a tool for collecting and formatting code from a project to be used with LLMs like Claude. It:

1. Recursively collects code files, respecting .gitignore patterns
2. Formats them with appropriate headers and context
3. Optimizes token usage by prioritizing recent files
4. Outputs the formatted code to both a file and clipboard

## Recent Improvements (v0.1.10)

- Enhanced exclusion patterns to hide high-token files like lock files
- Added comprehensive patterns for dependency lock files (uv.lock, package-lock.json, etc.)
- Improved handling of large generated files (minified JS/CSS, etc.)
- Excluded dependency directories (node_modules, vendor, etc.)
- Optimized token usage reporting by filtering out more non-essential files
- Fixed potential issues with lock files consuming excessive tokens

## Previous Improvements (v0.1.9)

- Added comprehensive test suite to ensure CodeSight reliability
- Enhanced pre-commit hook with robust testing in isolated environments
- Improved imports to support both package and direct script execution
- Fixed dependency handling for better cross-environment compatibility
- Refactored codebase for easier testing and maintenance
- Improved error handling for more reliable operation
- Added update command `cs -u` to update CodeSight globally

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
