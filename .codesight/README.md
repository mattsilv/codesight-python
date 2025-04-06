# CodeSight-Python

A tool for collecting and formatting code for LLM analysis, optimized for M-series Macs.

## Installation

1. Install with uv (recommended for M-series Macs):

```bash
# Install uv if needed
curl -sSf https://github.com/astral-sh/uv/releases/latest/download/uv-installer.sh | bash

# Create virtual environment and install
cd .codesight
uv venv
uv pip install -e .
```

## Usage

Run the script from your project directory:

```bash
# Activate the environment first
source .codesight/.venv/bin/activate # Unix/macOS
# or
.\.codesight\.venv\Scripts\activate # Windows

# Run CodeSight
python .codesight/collect_code.py .
```

This will:
1. Collect all code files in your project (respecting .gitignore)
2. Process in parallel for optimal performance on M-series Macs
3. Format them for LLM analysis with relative timestamps
4. Copy the result to your clipboard
5. Save the output to `.codesight/llm.txt`

## Smart Features

- **Auto-excludes itself:** By default, CodeSight excludes the `.codesight` directory from analysis
- **Dogfood mode:** When working on CodeSight itself, automatically includes the `.codesight` directory
- **Output persistence:** Saves analysis to `.codesight/llm.txt` for future reference
- **Custom prompts:** Use targeted prompts for different use cases (improvement suggestions, bug fixes)

## Options

- `--token-limit N`: Set maximum token count (default: 100000)
- `--exclude PATTERN [PATTERN ...]`: Add exclusion patterns
- `--include-tests`: Include test directories (excluded by default)
- `--dogfood`: Include .codesight directory (for CodeSight development)
- `--output-file PATH`: Custom output file path (default: .codesight/llm.txt)
- `--prompt TYPE`: Select prompt type (options: improvement, bugfix, default: improvement)

## Custom Prompts

CodeSight includes different prompt templates for various use cases:

1. **Improvement Analysis** (default):
   - Identifies the top 3 highest-priority improvements for your codebase
   - Provides specific file paths and technical details for each improvement
   - Ready to use as GitHub issues

2. **Bug Fix Analysis**:
   - Helps identify the root cause of specific bugs
   - Requires you to add a description of the bug you're encountering
   - Edit the placeholder sections in `.codesight/prompts/bugfix.md`

To customize prompts or add new ones:
- Edit existing templates in the `.codesight/prompts/` directory
- Add new `.md` files following the same format
- Use them with the `--prompt` option (filename without extension)

## Examples

```bash
# Basic usage with default improvement prompt
python .codesight/collect_code.py . --token-limit 50000 --exclude "*.md" "docs/"

# Use the bugfix prompt
python .codesight/collect_code.py . --prompt bugfix

# Working on CodeSight itself with dogfood mode
python .codesight/collect_code.py . --dogfood --prompt improvement
```