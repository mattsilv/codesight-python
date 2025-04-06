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

## Options

- `--token-limit N`: Set maximum token count (default: 100000)
- `--exclude PATTERN [PATTERN ...]`: Add exclusion patterns
- `--include-tests`: Include test directories (excluded by default)

## Example

```bash
python .codesight/collect_code.py . --token-limit 50000 --exclude "*.md" "docs/"
```