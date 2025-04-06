# CodeSight Python Changelog

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