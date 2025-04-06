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

For the best development experience, use `uv` to manage your virtual environment. **Note the directory structure**:

```
codesight-python/           # Repository root
├── .codesight/             # Python package directory
│   ├── collect_code.py     # Main script
│   ├── prompts/            # Prompt templates
│   └── ... other files
└── README.md, LICENSE, etc.
```

#### If you're at the repository root (codesight-python/):

```bash
# Install uv if needed
pip install uv

# Create and activate virtual environment
uv venv
source .venv/bin/activate  # On Unix/Mac
# OR 
.venv\Scripts\activate     # On Windows

# Install required dependencies
uv pip install tiktoken openai pytest typer more-itertools

# Run CodeSight from the repository root
python .codesight/collect_code.py . --dogfood --prompt improvement
```

#### If you've navigated into the .codesight/ directory:

```bash
# Install uv if needed
pip install uv

# Create and activate virtual environment
uv venv
source .venv/bin/activate  # On Unix/Mac
# OR 
.venv\Scripts\activate     # On Windows

# Install required dependencies
uv pip install tiktoken openai pytest typer more-itertools

# Run CodeSight directly (since you're in the directory with collect_code.py)
python collect_code.py .. --dogfood --prompt improvement
```

## Usage

### Basic Usage 

From the repository root:

```bash
python .codesight/collect_code.py /path/to/project
```

From within the `.codesight` directory:

```bash
python collect_code.py /path/to/project
```

### Custom Prompts

CodeSight includes different prompt templates:

```bash
# From repository root - For general code improvements (default)
python .codesight/collect_code.py /path/to/project --prompt improvement

# From repository root - For debugging specific issues
python .codesight/collect_code.py /path/to/project --prompt bugfix
```

### Dogfood Mode

To analyze CodeSight itself (useful for development):

```bash
# From repository root
python .codesight/collect_code.py . --dogfood --prompt improvement

# From within .codesight directory
python collect_code.py .. --dogfood --prompt improvement
```

This special mode will include the `.codesight` directory (normally excluded) while preventing infinite recursion.

## Output

- Results are saved to `.codesight/llm.txt`
- Content is also copied to your clipboard automatically

See the [.codesight/README.md](.codesight/README.md) for more detailed usage instructions.

## License

MIT License - see the [LICENSE](LICENSE) file for details.