# CodeSight Python

A Python utility for collecting and formatting code for LLMs, optimized for performance on M-series Macs.

## Features

- Smart exclusion patterns based on .gitignore
- Recency-based directory sorting
- Token optimization for LLMs with truncation for older files
- Asyncio, ProcessPoolExecutor, and ThreadPoolExecutor for optimal performance
- Customizable prompt templates for different analysis types

## Installation

### Using pip

```bash
pip install codesight-python
```

### Development Setup with uv (Recommended)

For the best development experience, use `uv` to manage your virtual environment:

```bash
# Install uv (if not already installed)
pip install uv

# Create and activate virtual environment
uv venv
source .venv/bin/activate  # On Unix/Mac
# OR 
.venv\Scripts\activate     # On Windows

# Install dependencies directly (no requirements.txt needed)
uv pip install tiktoken openai pytest typer more-itertools
```

## Usage

Basic usage to analyze a project:

```bash
python .codesight/collect_code.py /path/to/project
```

### Custom Prompts

CodeSight includes different prompt templates for various use cases:

```bash
# For general code improvements (default)
python .codesight/collect_code.py /path/to/project --prompt improvement

# For debugging specific issues
python .codesight/collect_code.py /path/to/project --prompt bugfix
```

### Dogfood Mode

To analyze CodeSight itself (useful for development):

```bash
# Run from the project root directory
python .codesight/collect_code.py . --dogfood --prompt improvement
```

This special mode will include the `.codesight` directory (normally excluded) while preventing infinite recursion.

## Output

- Results are saved to `.codesight/llm.txt`
- Content is also copied to your clipboard automatically

See the [.codesight/README.md](.codesight/README.md) for more detailed usage instructions.

## License

MIT License - see the [LICENSE](LICENSE) file for details.