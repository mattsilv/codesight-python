# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Environment Commands
- Setup venv: `cd .codesight && uv venv`
- Install package: `uv pip install -e .`
- Run CodeSight: `python .codesight/collect_code.py .`

## Coding Standards
- Python version: >=3.9
- Indentation: 4 spaces
- Use PEP 8 naming: snake_case for functions/variables, PascalCase for classes
- Type annotations required on all function parameters and returns
- Use docstrings (triple quotes) for all functions and classes
- Imports: stdlib first, then third-party, then local (group by functionality)
- Error handling: Use specific exceptions with descriptive messages
- String formatting: f-strings preferred

## Performance Patterns
- Use ProcessPoolExecutor for CPU-bound tasks
- Use ThreadPoolExecutor for I/O-bound operations
- Implement async/await for concurrent operations
- Batch process large collections to manage memory
- Configure event loops specifically for macOS performance