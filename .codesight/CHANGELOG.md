# CodeSight Python Changelog

## v0.1.8 (2025-04-06)

### Added
- New command `cs -t` or `cs --tokens` to show top files by token count
- Comprehensive table showing files and directories with highest token usage
- Percentage breakdown of token usage across the project
- Better token optimization with expanded exclusion patterns

### Changed
- Improved file exclusion patterns to automatically ignore data files
- Added extensive list of data file extensions to global exclusions
- Enhanced visibility into token usage to help users optimize their projects

## v0.1.7 (2025-04-06)

### Added
- Automatic dependency installation during initialization and runtime
- Support for multiple package managers (pip, python -m pip, uv)
- Smart detection of virtual environments and installation context

### Changed
- Proactive dependency management that tries to install dependencies automatically
- Improved user experience with less manual steps required

### Fixed
- Fixed installation workflow to handle dependencies without user intervention
- Better handling of virtual environment detection and activation

## v0.1.6 (2025-04-06)

### Changed
- Simplified dependency management to work with all Python environments
- Improved cross-compatibility with different package managers (pip, uv)
- More user-friendly error messages for missing dependencies

### Fixed
- Fixed installation errors on systems without pip available
- Removed complex subprocess calls that could fail in certain environments
- Better support for virtual environments

## v0.1.5 (2025-04-06)

### Added
- Dependency validation and auto-installation during runtime
- Improved dependency management for global installations

### Fixed
- Missing dependency issues in fresh installations
- Added automatic installation of pyperclip dependency
- More robust dependency checking before running commands

## v0.1.4 (2025-04-06)

### Added
- Centralized version management with single source of truth
- Automatic version updating in documentation

### Changed
- Improved installation and upgrade process
- Better version detection during installation
- Enhanced documentation for clear installation instructions

### Fixed
- Version synchronization across all components

## v0.1.3 (2025-04-06)

### Added
- Better path resolution in uninstallation script
- Protection for development repositories during uninstallation

### Fixed
- Fixed uninstallation path issues
- Improved documentation for uninstall commands

## v0.1.2 (2025-04-06)

### Changed
- Updated documentation for global installation locations
- Improved error handling during installation

## v0.1.1 (2025-04-06)

### Added
- New `--include-structural` flag to optionally include structural files like __init__.py
- XDG-compliant configuration system for better cross-platform support
- Token optimization features to reduce output size

### Changed
- Improved file exclusion logic to prevent recursive processing
- More concise file structure representation in output
- Automatically exclude configuration files (.gitignore, etc.)
- Exclude backup files (*.bak) from processing
- Better error handling and path validation

### Fixed
- Fixed recursive processing of llm.txt file
- Fixed path handling in developer mode configuration

## v0.1.0 (2025-04-01)

- Initial release