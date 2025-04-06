# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Environment Commands
- Setup venv: `cd .codesight && uv venv`
- Install package: `uv pip install -e .`
- Run CodeSight: `python .codesight/collect_code.py . --dogfood`

## Important Notes for CodeSight Development
- ALWAYS use the `--dogfood` flag when testing CodeSight on itself
- This is critical when working on the CodeSight project itself to include the `.codesight` directory in analysis
- Example from project root: `python .codesight/collect_code.py . --dogfood`
- The tool automatically detects when it's running on the CodeSight project
- Without the dogfood flag, CodeSight will exclude itself from analysis by default
- Output is automatically saved to `.codesight/llm.txt`
- When in dogfood mode, nested directories are normal (e.g., `.codesight/.codesight/llm.txt`)

## Custom Prompts
- CodeSight uses custom prompts found in `.codesight/prompts/`
- Use the `--prompt` option to specify which prompt to use:
  - `improvement` (default): For general code improvement suggestions
  - `bugfix`: For diagnosing specific bugs (requires editing the prompt to describe your bug)
- Example: `python .codesight/collect_code.py . --prompt bugfix`
- To create a new prompt type, add a corresponding markdown file in `.codesight/prompts/`

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