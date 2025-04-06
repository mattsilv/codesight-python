# CodeSight Python

A Python utility for collecting and formatting code for LLMs, optimized for performance on M-series Macs.

## Features

- Smart exclusion patterns based on .gitignore
- Recency-based directory sorting
- Token optimization for LLMs with truncation for older files
- Asyncio, ProcessPoolExecutor, and ThreadPoolExecutor for optimal performance
- Customizable prompt templates for different analysis types

## Quick Start for Regular Users

```bash
# Install the cs command globally (one-time setup)
cd /Users/m/gh/codesight-python
.codesight/bin/install.sh

# Setup for your project
cd /path/to/your/project
cs -i                   # Initialize project config

# Then simply use:
cs                      # Analyze project with one command!
```

### Using CodeSight

```bash
cs                      # Analyze current project with improvement prompt
cs -b "Bug description" # Analyze with bug mode and description
cs -c                   # Configure settings (global or project-specific)
cs path/to/project      # Analyze a specific project
cs --debug              # Show debug information about paths
```

### Features of the `cs` Command

- **Zero-argument operation**: Just type `cs` in your project
- **Project-specific configuration**: Creates `.codesight-config.json` in your project
- **Automatic environment management**: Creates and activates virtual environments
- **Global + project configs**: Project settings override global ones
- **Quick bug analysis**: `cs -b "Description of the bug"` for immediate debugging

## Output

- Results are saved to `.codesight/llm.txt` in your project
- Content is also copied to your clipboard automatically

## Manual Installation

If you prefer not to use the provided installation script:

```bash
# Navigate to your project directory
cd /path/to/your/project

# Create and activate virtual environment with uv
pip install uv
uv venv
source .venv/bin/activate  # On Unix/Mac
# OR 
.venv\Scripts\activate     # On Windows

# Install required dependencies
uv pip install tiktoken openai typer more-itertools humanize pathspec

# Run CodeSight manually
python /path/to/codesight-python/.codesight/collect_code.py .
```

## Advanced Usage: Custom Prompts

CodeSight includes different prompt templates:

```bash
# For general code improvements (default)
cs --prompt improvement

# For debugging specific issues
cs --prompt bugfix
```

## Cross-Platform Support

Currently optimized for macOS. Future enhancements will include Windows compatibility.

---

## For CodeSight Developers

If you're working on CodeSight itself, please use the dedicated developer mode:

```bash
# Run the developer-specific command
cd /Users/m/gh/codesight-python
cs-dev --debug
```

This special mode will include the `.codesight` directory (normally excluded) while preventing infinite recursion.

For more detailed development instructions, see the [CLAUDE.md](CLAUDE.md) file in this repository.

## Directory Structure for Developers

```
codesight-python/           # Repository root
├── .codesight/             # Python package directory
│   ├── collect_code.py     # Main script
│   ├── bin/                # CLI tools
│   │   ├── cs              # Main CLI script
│   │   ├── cs-dev          # Developer mode script
│   │   ├── cs.py           # Python component of CLI
│   │   └── install.sh      # Installation script
│   ├── prompts/            # Prompt templates
│   │   ├── improvement.md  # Default prompt
│   │   └── bugfix.md       # Bug-fixing prompt
│   └── ... other files
└── README.md, LICENSE, etc.
```

## License

MIT License - see the [LICENSE](LICENSE) file for details.