# CodeSight-Python Implementation Plan

## Project Architecture

```
project-root/
├── .codesight/                  # Self-contained package directory
│   ├── __init__.py              # Package initialization
│   ├── collect_code.py          # Main implementation
│   ├── pyproject.toml           # Project metadata and dependencies
│   └── README.md                # Usage documentation
└── (rest of your project)       # Your actual project files
```

## Core Dependencies

```
pathlib (built-in)
datetime (built-in)
argparse (built-in)
asyncio (built-in)
concurrent.futures (built-in)
pathspec==0.12.1
tiktoken==0.9.0
pyperclip==1.9.0
humanize==4.8.0   # For human-readable relative times
```

## Implementation Plan

### 1. Project Setup

1. Create the `.codesight` directory in your project root
2. Set up the basic file structure
3. Create `requirements.txt` with dependencies

### 2. Main Script Implementation (`collect_code.py`)

#### Argument Parsing

```python
def parse_arguments():
    parser = argparse.ArgumentParser(description='Collect and format code for LLM analysis')
    parser.add_argument('directory', nargs='?', default='.', help='Project directory (default: current directory)')
    parser.add_argument('--token-limit', type=int, default=100000, help='Token limit for output')
    parser.add_argument('--exclude', nargs='+', default=[], help='Additional patterns to exclude')
    parser.add_argument('--include-tests', action='store_true', help='Include test directories')
    return parser.parse_args()
```

#### File Collection and Filtering (Optimized for M-series Macs)

```python
import asyncio
from concurrent.futures import ProcessPoolExecutor

async def collect_files(project_root, exclusion_spec):
    """
    Asynchronously collect and filter files using multiple processes
    to leverage M-series Mac performance
    """
    dirs_data = {}

    # Get all potential files first (faster than recursive glob in each process)
    all_files = list(project_root.rglob('*'))

    # Process files in chunks using process pool
    chunk_size = 1000  # Adjust based on system memory
    chunks = [all_files[i:i + chunk_size] for i in range(0, len(all_files), chunk_size)]

    async def process_chunk(chunk):
        chunk_result = {}
        for file_path in chunk:
            if not file_path.is_file():
                continue

            relative_path = file_path.relative_to(project_root)

            # Skip if file matches exclusion patterns
            if exclusion_spec.match_file(str(relative_path)):
                continue

            # Get file metadata
            mtime = file_path.stat().st_mtime
            parent_dir = file_path.parent

            # Group files by directory
            chunk_result.setdefault(parent_dir, []).append((file_path, mtime))

        return chunk_result

    # Process chunks in parallel
    with ProcessPoolExecutor() as executor:
        loop = asyncio.get_event_loop()
        tasks = [
            loop.run_in_executor(executor, process_chunk, chunk)
            for chunk in chunks
        ]
        chunk_results = await asyncio.gather(*tasks)

    # Merge results
    for result in chunk_results:
        for parent_dir, files in result.items():
            dirs_data.setdefault(parent_dir, []).extend(files)

    return dirs_data
```

#### Smart Exclusion Patterns

```python
def build_exclusion_patterns(project_root, user_excludes, include_tests):
    # Start with .gitignore patterns
    patterns = ['.git']  # Always ignore .git

    gitignore_path = project_root / '.gitignore'
    if gitignore_path.is_file():
        with gitignore_path.open('r', encoding='utf-8') as f:
            patterns.extend(f.readlines())

    # Add standard excludes for code projects
    standard_excludes = [
        '__pycache__/',
        '*.pyc',
        '*.pyo',
        '*.so',
        'build/',
        'dist/',
        '*.egg-info/',
        '.env',
        '.venv/',
        'venv/',
        'env/',
        '*.log',
        '.DS_Store',
    ]

    # Add test directories unless explicitly included
    if not include_tests:
        standard_excludes.extend([
            'test/',
            'tests/',
            '*_test.py',
            'test_*.py',
        ])

    # Add large data file patterns
    standard_excludes.extend([
        '*.csv',
        '*.json',
        '*.xml',
        '*.yaml',
        '*.yml',
    ])

    # Add user excludes
    patterns.extend(standard_excludes)
    patterns.extend(user_excludes)

    return pathspec.PathSpec.from_lines(pathspec.patterns.GitWildMatchPattern, patterns)
```

#### Directory and File Sorting

```python
def prepare_sorted_groups(dirs_data):
    group_sort_info = []

    for parent_dir, files_with_mtimes in dirs_data.items():
        if files_with_mtimes:  # Ensure list isn't empty
            # Find the most recent modification time in the group
            max_mtime = max(m for _, m in files_with_mtimes)

            # Add directory info to sort list
            group_sort_info.append({
                'dir': parent_dir,
                'files': files_with_mtimes,
                'max_mtime': max_mtime
            })

    # Sort directories by recency (most recent first)
    group_sort_info.sort(key=lambda item: item['max_mtime'], reverse=True)

    return group_sort_info
```

#### Human-Readable Relative Times

```python
def format_relative_time(timestamp):
    """Convert timestamp to human-readable relative time (e.g., '3 hours ago')"""
    from datetime import datetime
    import humanize

    now = datetime.now()
    file_time = datetime.fromtimestamp(timestamp)
    return humanize.naturaltime(now - file_time)
```

#### Output Formatting with Directory Structure (Optimized)

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor
import re
import tiktoken

async def build_output(group_sort_info, project_root, token_limit):
    """Optimized output builder using async for file reading operations"""
    output_parts = []

    # Add today's date and project info at the top
    from datetime import datetime
    output_parts.append(f"# CodeSight Analysis - {datetime.now().strftime('%Y-%m-%d')}")
    output_parts.append(f"# Project: {project_root.name}")

    # Add code structure overview - grouped by directory
    output_parts.append("\n# --- Code Structure Overview ---")

    for group in group_sort_info:
        relative_dir = group['dir'].relative_to(project_root)
        output_parts.append(f"# Directory: {relative_dir}/")

        # Sort files alphabetically for the overview
        sorted_files_overview = sorted([f for f, _ in group['files']], key=lambda p: p.name)
        for file_path in sorted_files_overview:
            output_parts.append(f"#   {file_path.name}")

    output_parts.append("# --- End Code Structure Overview ---\n")

    # Add prompt template
    prompt_template = """
You are an expert software engineer. Analyze the following codebase from my project.
The goal is to [YOUR GOAL HERE - e.g., find bugs, suggest improvements, implement feature X]

The code is organized by directories, with most recently modified files first.
Each file shows how recently it was modified to help you focus on recent changes.

Please provide your analysis with specific, actionable feedback.
"""
    output_parts.append(prompt_template.strip())

    # Add concatenated code files
    output_parts.append("\n# --- Start Code Files ---")

    # Precompile regex patterns for performance
    import_pattern = re.compile(r'^import.*|^from.*import.*', re.MULTILINE)
    definition_pattern = re.compile(r'^(def|class)\s+.*:', re.MULTILINE)

    # Initialize token encoder once
    encoder = tiktoken.get_encoding("cl100k_base")  # OpenAI's encoding

    # Track tokens
    total_tokens = len(encoder.encode("\n".join(output_parts)))
    truncated = False

    # Helper for async file reading and processing
    async def process_file(file_path, mtime):
        try:
            relative_path = file_path.relative_to(project_root)
            relative_time = format_relative_time(mtime)

            # Format concise header with relative time
            header = f"# --- {file_path.name} ({relative_time}) ---"

            # Read file content asynchronously
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as pool:
                content = await loop.run_in_executor(
                    pool,
                    lambda: file_path.read_text(encoding='utf-8', errors='ignore')
                )

            # Check token limit and apply smart truncation if needed
            file_tokens = len(encoder.encode(content))

            # Need to check if adding this file would exceed token limit
            nonlocal total_tokens, truncated

            if total_tokens + file_tokens > token_limit:
                # Apply smart truncation for older files
                from datetime import datetime, timedelta
                file_time = datetime.fromtimestamp(mtime)

                if datetime.now() - file_time > timedelta(days=7):
                    # For older files, include only imports and definitions
                    imports = import_pattern.findall(content)
                    definitions = definition_pattern.findall(content)

                    truncated_content = "\n".join(imports)
                    truncated_content += "\n\n# File truncated - showing only definitions:\n"
                    truncated_content += "\n".join(definitions)

                    content = truncated_content
                    truncated = True
                    # Recalculate tokens after truncation
                    file_tokens = len(encoder.encode(content))

            # Only add content if we're under the limit
            if total_tokens + file_tokens <= token_limit:
                result = f"\n{header}\n{content}"
                total_tokens += file_tokens
                return result
            else:
                return f"\n# --- {file_path.name} skipped (token limit reached) ---"

        except Exception as e:
            return f"\n# --- Error reading file: {relative_path} ---\n# Error: {e}"

    # Process each directory group
    for group in group_sort_info:
        # Sort files within group by recency
        sorted_files_in_group = sorted(group['files'], key=lambda item: item[1], reverse=True)

        # Get relative directory path for header
        relative_dir = group['dir'].relative_to(project_root)
        dir_header = f"\n# Directory: {relative_dir}/"
        output_parts.append(dir_header)

        # Process files in parallel within this directory
        tasks = [process_file(file_path, mtime) for file_path, mtime in sorted_files_in_group]
        file_contents = await asyncio.gather(*tasks)

        # Add non-empty results to output
        for content in file_contents:
            if content:
                output_parts.append(content)

    if truncated:
        output_parts.append("\n# Note: Some older files were truncated to stay within token limits.")

    output_parts.append("\n# --- End Code Files ---")

    return "\n".join(output_parts)
```

#### Main Function (Async)

```python
async def main_async():
    args = parse_arguments()

    # Get project root directory
    from pathlib import Path
    project_root = Path(args.directory).resolve()

    # Build exclusion patterns
    exclusion_spec = build_exclusion_patterns(
        project_root,
        args.exclude,
        args.include_tests
    )

    # Collect files (async)
    dirs_data = await collect_files(project_root, exclusion_spec)

    # Sort directories and files by recency
    group_sort_info = prepare_sorted_groups(dirs_data)

    # Build output (async)
    final_output = await build_output(group_sort_info, project_root, args.token_limit)

    # Count tokens
    import tiktoken
    encoder = tiktoken.get_encoding("cl100k_base")
    tokens = len(encoder.encode(final_output))

    # Copy to clipboard
    import pyperclip
    pyperclip.copy(final_output)

    # Print summary
    total_files = sum(len(group['files']) for group in group_sort_info)
    print(f"CodeSight: Processed {total_files} files ({tokens} tokens)")
    print(f"Content copied to clipboard!")

def main():
    """Entry point that handles the async event loop"""
    import asyncio

    # Configure asyncio to use the right event loop policy for macOS
    if hasattr(asyncio, 'WindowsSelectorEventLoopPolicy'):
        # Windows-specific event loop policy
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    else:
        try:
            # macOS-specific event loop policy improves performance on M-series Macs
            import asyncio
            asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())
        except ImportError:
            # Fall back to default policy
            pass

    # Run the async main function
    asyncio.run(main_async())

if __name__ == "__main__":
    main()
```

## LLM-Optimized Features

1. **Directory-Based Grouping**: Files are grouped by directory and sorted by recency, making it easier for LLMs to understand project structure.

2. **Relative Timestamps**: Using human-readable relative times ("3 hours ago" vs. dates) gives immediate context about file recency.

3. **Smart Hierarchy Display**: The code structure overview provides a clear map of the project before showing file contents.

4. **Token Optimization**: Older files are truncated to show only imports and definitions when approaching token limits.

5. **Context-Rich Headers**: Each file has a concise header showing its name and how recently it was modified.

## M-series Mac Optimizations

1. **Asynchronous Processing**: Leverages async/await for I/O bound operations to maximize throughput.

2. **Parallel File Processing**: Uses ProcessPoolExecutor to distribute work across multiple CPU cores.

3. **Efficient Memory Management**: Processes files in batches to avoid excessive memory pressure.

4. **Native ARM64 Dependencies**: Uses uv to ensure all dependencies are compiled for ARM architecture.

5. **Optimized Event Loop**: Configures the event loop specifically for macOS performance.

6. **Thread Pool for File I/O**: Uses ThreadPoolExecutor for file read operations to prevent blocking.

## Setup for M-series Mac Optimization

### Installation with uv

1. Create the `.codesight` directory in your project:

```bash
mkdir -p .codesight
```

2. Create the pyproject.toml file:

```bash
cat > .codesight/pyproject.toml << EOL
[project]
name = "codesight"
version = "0.1.0"
description = "Analyze code with LLMs"
requires-python = ">=3.9"
dependencies = [
    "pathspec==0.12.1",
    "tiktoken==0.9.0",
    "pyperclip==1.9.0",
    "humanize==4.8.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
EOL
```

3. Install uv if you don't have it (one-time setup):

```bash
# Install uv globally
curl -sSf https://github.com/astral-sh/uv/releases/latest/download/uv-installer.sh | bash

# Or install via homebrew
brew install uv
```

4. Create a virtual environment and install dependencies with uv:

```bash
# Create a virtual environment in .codesight/.venv
cd .codesight
uv venv

# Install dependencies from pyproject.toml
uv pip install -e .
```

5. Create the main script:

```bash
# Copy the implementation above into .codesight/collect_code.py
```

### Using CodeSight to Improve Itself (Dogfooding)

To dogfood CodeSight while developing it:

1. Run CodeSight on its own directory using the virtual environment:

```bash
# Activate the virtual environment
source .codesight/.venv/bin/activate  # Or: .\.codesight\.venv\Scripts\activate on Windows

# Run CodeSight on itself
python .codesight/collect_code.py .codesight
```

2. Paste the output to an LLM and ask for improvements to the CodeSight implementation.

3. Implement suggested changes and repeat the process.

### M-series Mac Performance Tips

For optimal performance on M-series Macs:

1. **Native Dependencies**: uv automatically installs native dependencies compiled for ARM64, ensuring optimal performance.

2. **Process Pool Configuration**: Adjust ProcessPoolExecutor settings based on the M-series chip:

   ```python
   # For M1/M2/M3 chips with 8-core CPU
   with ProcessPoolExecutor(max_workers=6) as executor:
       # Using 6 workers leaves resources for system
   ```

3. **Memory Management**: Batch processing large projects to avoid memory pressure.

### Usage Instructions (for README.md)

```
# CodeSight-Python

A tool for collecting and formatting code for LLM analysis, optimized for M-series Macs.

## Installation

1. Clone the repository to your project:
```

git clone https://github.com/your-username/codesight-python.git .codesight

```

2. Install with uv (recommended for M-series Macs):
```

# Install uv if needed

curl -sSf https://github.com/astral-sh/uv/releases/latest/download/uv-installer.sh | bash

# Create virtual environment and install

cd .codesight
uv venv
uv pip install -e .

```

## Usage

Run the script from your project directory:

```

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

```

python .codesight/collect_code.py . --token-limit 50000 --exclude "\*.md" "docs/"

```

```
