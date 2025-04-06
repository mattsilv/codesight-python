# CodeSight Python Changelog

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