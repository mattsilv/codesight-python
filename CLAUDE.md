# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with CodeSight Python for development purposes.

## CodeSight Development Commands

- **Primary developer command**: `cs-dev --debug`
  - IMPORTANT: MUST be run from inside the .codesight directory
  - Automatically handles virtual environment and path resolution
  - Always includes the `--dogfood` flag by default

- **Manual development setup**:
  ```bash
  # Navigate to the .codesight directory first!
  cd /Users/m/gh/codesight-python/.codesight
  
  # Then run cs-dev
  cs-dev --debug
  
  # If you need to activate the environment manually:
  source ../.venv/bin/activate
  ```

## Important Notes for CodeSight Development

- **ALWAYS use `cs-dev` for testing CodeSight on itself**
  - This command ensures proper path resolution and virtual environment management
  - It automatically applies the `--dogfood` flag which is critical for self-analysis
  - MUST run from inside the .codesight directory (NOT from the project root)
  - Never run regular `cs` command on the CodeSight codebase itself
  
- **File Organization Guidelines**:
  - Only CLAUDE.md and LICENSE should exist in the project root directory
  - All CodeSight files (including README.md) should live in the .codesight directory
  - Output files (llm.txt) are always saved to the .codesight directory
  - No duplicate files between root and .codesight directory

- **Understanding dogfood mode**:
  - The tool automatically detects when it's running on the CodeSight project
  - Without dogfood mode, CodeSight will exclude itself from analysis by default
  - Output is always saved to `.codesight/llm.txt`
  - When in dogfood mode, paths are handled specially to prevent recursion issues

- **Troubleshooting**:
  - Always use the `--debug` flag when troubleshooting: `cs-dev --debug`
  - This shows all path resolutions and virtual environment information
  - Check generated `.codesight/llm.txt` file to see analysis output
  
## Internal Architecture

- **bin/cs**: Regular user-facing launcher script (creates project-specific venv)
- **bin/cs-dev**: Developer-specific launcher (maintains single venv in repository root)
- **bin/cs.py**: Python component handling command-line arguments and configuration
- **bin/install.sh**: Installation script creating wrapper scripts in PATH
- **collect_code.py**: Main script that handles code collection and analysis
- **prompts/**: Directory containing markdown templates for different analysis types

## Custom Prompts

- CodeSight uses custom prompts found in `.codesight/prompts/`
- Default prompts included:
  - `improvement.md`: For general code improvement suggestions
  - `bugfix.md`: For diagnosing specific bugs
- To create a new prompt type, add a corresponding markdown file in `.codesight/prompts/`
- When developing prompt templates:
  ```bash
  # Test a specific prompt template
  cs-dev --prompt improvement --debug
  
  # Test with custom prompt
  cs-dev --prompt bugfix --debug
  ```

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

## Installation Debugging

- If your installation is broken, try:
  ```bash
  cd /Users/m/gh/codesight-python
  .codesight/bin/install.sh
  ```
- If that fails, manually create the wrappers:
  ```bash
  mkdir -p ~/bin
  cat > ~/bin/cs << EOF
  #!/bin/bash
  "/Users/m/gh/codesight-python/.codesight/bin/cs" "\$@"
  EOF
  chmod +x ~/bin/cs
  
  cat > ~/bin/cs-dev << EOF
  #!/bin/bash
  "/Users/m/gh/codesight-python/.codesight/bin/cs-dev" "\$@"
  EOF
  chmod +x ~/bin/cs-dev
  ```
- If you need to run commands directly:
  ```bash
  /Users/m/gh/codesight-python/.codesight/bin/cs
  /Users/m/gh/codesight-python/.codesight/bin/cs-dev
  ```