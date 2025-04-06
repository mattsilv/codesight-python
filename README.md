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

#### Option 1: Install and run from the repository root

```bash
# Install uv if needed
pip install uv

# From repository root (/Users/m/gh/codesight-python/)
cd /Users/m/gh/codesight-python/

# Create and activate virtual environment
uv venv
source .venv/bin/activate  # On Unix/Mac
# OR 
.venv\Scripts\activate     # On Windows

# Install required dependencies
uv pip install tiktoken openai pytest typer more-itertools humanize pathspec

# Run CodeSight from the repository root
python .codesight/collect_code.py . --dogfood --prompt improvement
```

#### Option 2: Install and run from within the .codesight directory (RECOMMENDED)

```bash
# Install uv if needed
pip install uv

# Navigate to the .codesight directory
cd /Users/m/gh/codesight-python/.codesight/

# Create and activate virtual environment
uv venv
source .venv/bin/activate  # On Unix/Mac
# OR 
.venv\Scripts\activate     # On Windows

# Install required dependencies
uv pip install tiktoken openai pytest typer more-itertools humanize pathspec

# Run CodeSight (use "." to analyze the current directory)
python collect_code.py . --dogfood --prompt improvement

# OR analyze the parent directory (repository root)
python collect_code.py .. --dogfood --prompt improvement
```

> **Recommended approach**: Option 2 (running from within `.codesight/`) is often cleaner as it avoids nested `.codesight` directories and path resolution issues in dogfood mode.

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
# RECOMMENDED: From within .codesight directory
cd /Users/m/gh/codesight-python/.codesight/
python collect_code.py . --dogfood --prompt improvement

# Alternative: From repository root (but may cause nested .codesight directories)
cd /Users/m/gh/codesight-python/
python .codesight/collect_code.py . --dogfood --prompt improvement
```

This special mode will include the `.codesight` directory (normally excluded) while preventing infinite recursion.

> **Note**: Running from within the `.codesight` directory is strongly recommended for dogfood mode to avoid issues with nested directories and path resolution. The script has been updated to better handle this case.

## Quick Start with `cs` Command

For convenience, CodeSight provides a simple `cs` command that handles all the complexity:

```bash
# Install the cs command globally (one-time setup, no sudo needed in most cases)
.codesight/bin/install.sh

# Setup for a specific project
cd /path/to/your/project
cs -i                   # Initialize project config

# Then simply use:
cs                      # Analyze project with one command!
```

### Advanced Usage

```bash
cs -b "Bug description" # Analyze with bug mode and description
cs -c                   # Configure settings (global or project-specific)
cs path/to/project      # Analyze a specific project
```

### Features of the `cs` Command

- **Zero-argument operation**: Just type `cs` in your project
- **Project-specific configuration**: Creates `.codesight-config.json` in your project
- **Automatic environment management**: Creates and activates virtual environments
- **Smart project detection**: Auto-detects CodeSight project for dogfood mode
- **Global + project configs**: Project settings override global ones
- **Quick bug analysis**: `cs -b "Description of the bug"` for immediate debugging

### Cross-Platform Support

Currently optimized for macOS. Future enhancements will include Windows compatibility.

## Output

- Results are saved to `.codesight/llm.txt`
- Content is also copied to your clipboard automatically

See the [.codesight/README.md](.codesight/README.md) for more detailed usage instructions.

## License

MIT License - see the [LICENSE](LICENSE) file for details.