#!/usr/bin/env python
"""
CodeSight: Collects and formats code for LLM analysis, optimized for M-series Macs.

This module provides functionality to recursively collect code files from a
project, format them with syntax highlighting, and prepare them for analysis
by large language models (LLMs). It's specifically optimized for performance
on Apple M-series processors using process-based parallelism.

Key Features:
- Asynchronous file processing with multiprocessing
- Smart file selection based on recency and relevance
- Automatic token counting and limitation
- Integration with common version control exclusion patterns
- Clipboard integration for easy pasting into LLM interfaces

Usage:
    python collect_code.py [directory] [options]

The output is saved to .codesight/llm.txt by default and copied to clipboard.
"""

from __future__ import annotations

import argparse
import asyncio
import re
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional, Coroutine, Sequence, Pattern, Callable
from dataclasses import dataclass

import humanize
import pathspec
import pyperclip
import tiktoken


@dataclass
class FileMetadata:
    """Metadata for a single file in the project."""
    path: Path
    mtime: float


@dataclass
class DirectoryGroup:
    """Group of files within a directory with metadata."""
    path: Path
    files: list[FileMetadata]
    max_mtime: float

# Constants
CHUNK_SIZE = 1000
DEFAULT_TOKEN_LIMIT = 100_000
TRUNCATION_DAYS_THRESHOLD = 7
DEFAULT_OUTPUT_FILE = '.codesight/llm.txt'
DEFAULT_ENCODING = "cl100k_base"  # OpenAI's encoding


def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments for CodeSight.
    
    Args:
        None
        
    Returns:
        argparse.Namespace: Parsed command line arguments with the following attributes:
            directory (str): Project directory to analyze
            token_limit (int): Maximum token limit for output
            exclude (List[str]): Additional patterns to exclude
            include_tests (bool): Whether to include test directories
            include_structural (bool): Whether to include structural files
            dogfood (bool): Whether to include .codesight directory
            output_file (str): Output file path
            prompt (str): Type of prompt to use
    """
    parser = argparse.ArgumentParser(description='Collect and format code for LLM analysis')
    parser.add_argument('directory', nargs='?', default='.', 
                       help='Project directory (default: current directory)')
    parser.add_argument('--token-limit', type=int, default=DEFAULT_TOKEN_LIMIT, 
                       help=f'Token limit for output (default: {DEFAULT_TOKEN_LIMIT})')
    parser.add_argument('--exclude', nargs='+', default=[], 
                       help='Additional patterns to exclude')
    parser.add_argument('--include-tests', action='store_true', 
                       help='Include test directories')
    parser.add_argument('--include-structural', action='store_true',
                       help='Include structural files like __init__.py, setup.py, etc.')
    parser.add_argument('--dogfood', action='store_true',
                       help='Include .codesight directory (for CodeSight development)')
    parser.add_argument('--output-file', default=DEFAULT_OUTPUT_FILE,
                       help=f'Output file path (default: {DEFAULT_OUTPUT_FILE})')
    parser.add_argument('--prompt', choices=['improvement', 'bugfix'], default='improvement',
                       help='Type of prompt to use (default: improvement)')
    return parser.parse_args()


def build_exclusion_patterns(
    project_root: Path, 
    user_excludes: list[str], 
    include_tests: bool, 
    include_codesight: bool,
    include_structural: bool = False,
    output_file: str = 'llm.txt'
) -> pathspec.PathSpec:
    """
    Build patterns for excluding files from collection.
    
    Args:
        project_root: Root directory of the project
        user_excludes: Additional patterns specified by the user to exclude
        include_tests: Whether to include test directories
        include_codesight: Whether to include the .codesight directory
        include_structural: Whether to include structural files like __init__.py
        output_file: Name of the output file to exclude from processing
        
    Returns:
        pathspec.PathSpec: Compiled exclusion pattern specification
    """
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
    
    # By default, exclude .codesight/ directory unless dogfood mode is on
    if not include_codesight:
        standard_excludes.append('.codesight/')

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
    
    # ALWAYS exclude the output file to prevent recursive processing
    # Both the file name and paths with the file name
    standard_excludes.extend([
        output_file,
        f"*/{output_file}",
        f".codesight/{output_file}",
        # Exclude prompts directory (templates don't need to be analyzed)
        "prompts/",
        "*/prompts/",
        ".codesight/prompts/",
    ])
    
    # Always exclude these configuration files
    standard_excludes.extend([
        ".gitignore",
        "*/.gitignore",
        ".csconfig.json",
        "*/.csconfig.json",
        "*.bak",
        "*/*.bak",
    ])
    
    # Exclude structural files unless explicitly included
    if not include_structural:
        standard_excludes.extend([
            # Common config files
            "*.toml",
            "setup.py",
            "setup.cfg",
            "requirements.txt",
            "LICENSE",
            "Dockerfile",
            "docker-compose.yml",
            "Makefile",
            # Structural files with minimal content
            "__init__.py",
            "*/__init__.py",
            "__main__.py",
            "*/__main__.py",
            "conftest.py",
            "*/conftest.py",
        ])

    # Add user excludes
    patterns.extend(standard_excludes)
    patterns.extend(user_excludes)

    return pathspec.PathSpec.from_lines(pathspec.patterns.GitWildMatchPattern, patterns)


def process_chunk(
    chunk: list[Path], 
    project_root: Path, 
    exclusion_spec: pathspec.PathSpec
) -> dict[Path, list[FileMetadata]]:
    """
    Process a chunk of files to filter and collect metadata.
    
    Args:
        chunk: List of file paths to process
        project_root: Root directory of the project
        exclusion_spec: Compiled exclusion patterns
        
    Returns:
        dict: Mapping of directory paths to lists of FileMetadata objects
    """
    chunk_result: dict[Path, list[FileMetadata]] = {}
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
        
        # Create FileMetadata object
        file_metadata = FileMetadata(path=file_path, mtime=mtime)

        # Group files by directory
        chunk_result.setdefault(parent_dir, []).append(file_metadata)

    return chunk_result


async def collect_files(
    project_root: Path, 
    exclusion_spec: pathspec.PathSpec
) -> dict[Path, list[FileMetadata]]:
    """
    Asynchronously collect and filter files using multiple processes
    to leverage M-series Mac performance.
    
    Args:
        project_root: Root directory of the project
        exclusion_spec: Compiled exclusion patterns
        
    Returns:
        dict: Mapping of directory paths to lists of FileMetadata objects
    """
    dirs_data: dict[Path, list[FileMetadata]] = {}

    # Get all potential files first (faster than recursive glob in each process)
    all_files = list(project_root.rglob('*'))

    # Process files in chunks using process pool
    chunks = [all_files[i:i + CHUNK_SIZE] for i in range(0, len(all_files), CHUNK_SIZE)]

    # Process chunks in parallel
    with ProcessPoolExecutor() as executor:
        loop = asyncio.get_event_loop()
        tasks = [
            loop.run_in_executor(executor, process_chunk, chunk, project_root, exclusion_spec)
            for chunk in chunks
        ]
        chunk_results = await asyncio.gather(*tasks)

    # Merge results
    for result in chunk_results:
        for parent_dir, files in result.items():
            dirs_data.setdefault(parent_dir, []).extend(files)

    return dirs_data


def prepare_sorted_groups(
    dirs_data: dict[Path, list[FileMetadata]]
) -> list[DirectoryGroup]:
    """
    Sort directories and files by recency.
    
    Args:
        dirs_data: Mapping of directory paths to lists of FileMetadata objects
        
    Returns:
        list[DirectoryGroup]: List of directory groups sorted by recency
    """
    directory_groups: list[DirectoryGroup] = []

    for parent_dir, files in dirs_data.items():
        if files:  # Ensure list isn't empty
            # Find the most recent modification time in the group
            max_mtime = max(file.mtime for file in files)

            # Create DirectoryGroup object
            directory_group = DirectoryGroup(
                path=parent_dir,
                files=files,
                max_mtime=max_mtime
            )
            directory_groups.append(directory_group)

    # Sort directories by recency (most recent first)
    directory_groups.sort(key=lambda group: group.max_mtime, reverse=True)

    return directory_groups


def format_relative_time(timestamp: float) -> str:
    """
    Convert timestamp to human-readable relative time (e.g., '3 hours ago').
    
    Args:
        timestamp: Unix timestamp (seconds since epoch)
        
    Returns:
        str: Human-readable relative time string
    """
    now = datetime.now()
    file_time = datetime.fromtimestamp(timestamp)
    return humanize.naturaltime(now - file_time)


async def process_file(
    file_path: Path, 
    mtime: float, 
    project_root: Path, 
    import_pattern: Pattern[str], 
    definition_pattern: Pattern[str],
    token_limit: int, 
    total_tokens: int, 
    truncated: bool,
    encoder: tiktoken.Encoding
) -> tuple[Optional[str], int, bool]:
    """
    Process a single file for output.
    
    Args:
        file_path: Path to the file to process
        mtime: Modification time of the file
        project_root: Root directory of the project
        import_pattern: Regex pattern for matching import statements
        definition_pattern: Regex pattern for matching function/class definitions
        token_limit: Maximum token limit for the output
        total_tokens: Current total token count
        truncated: Whether truncation has been applied to any files
        encoder: Tokenizer for counting tokens
        
    Returns:
        tuple: 
            - Formatted file content or None if skipped
            - Updated total token count
            - Updated truncated flag
    """
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
            
        # Optimize content to reduce tokens
        content = optimize_content(content)

        # Check token limit and apply smart truncation if needed
        file_tokens = len(encoder.encode(content))

        if total_tokens + file_tokens > token_limit:
            # Apply smart truncation for older files
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
            # Create a more compact header format that uses fewer tokens
            result = f"\n{header}\n{content}"
            total_tokens += file_tokens
            return result, total_tokens, truncated
        else:
            return f"\n# {file_path.name}: skipped (token limit)", total_tokens, truncated

    except Exception as e:
        return f"\n# --- Error reading file: {relative_path} ---\n# Error: {e}", total_tokens, truncated
        
def optimize_content(content: str) -> str:
    """
    Optimize file content to reduce token count without losing meaning.
    
    Args:
        content: The raw file content
        
    Returns:
        str: The optimized content with reduced token count
    """
    # Remove duplicate blank lines (more than 2 consecutive newlines)
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    # Trim trailing whitespace at the end of lines
    content = re.sub(r"[ \t]+$", "", content, flags=re.MULTILINE)
    
    # Trim the content but ensure it ends with a newline
    content = content.strip() + '\n'
    
    return content


async def build_output(
    directory_groups: list[DirectoryGroup], 
    project_root: Path, 
    token_limit: int,
    prompt_type: str = 'improvement'
) -> str:
    """
    Optimized output builder using async for file reading operations.
    
    Args:
        directory_groups: List of directory groups sorted by recency
        project_root: Root directory of the project
        token_limit: Maximum token limit for the output
        prompt_type: Type of prompt template to use
        
    Returns:
        str: Formatted output with prompt and code files
    """
    output_parts = []

    # Add prompt from template file based on selected prompt type first
    # This makes it easier to paste directly into an LLM interface
    prompt_filename = f"{prompt_type}.md"
    
    # Check if we're running from within .codesight directory
    current_dir = Path.cwd().name
    script_dir = Path(__file__).parent.name
    in_codesight_dir = current_dir == '.codesight' or script_dir == '.codesight'
    
    # Try multiple possible locations for the prompt file
    possible_prompt_paths = [
        # Current directory / prompts (if we're in .codesight)
        Path('prompts') / prompt_filename,
        # Script directory / prompts
        Path(__file__).parent / 'prompts' / prompt_filename,
        # Project root / .codesight / prompts (standard path)
        project_root / '.codesight' / 'prompts' / prompt_filename
    ]
    
    # Find the first path that exists
    prompt_path = None
    for path in possible_prompt_paths:
        if path.exists():
            prompt_path = path
            break
    
    # If no prompt path exists, use the standard path as fallback
    if not prompt_path:
        prompt_path = project_root / '.codesight' / 'prompts' / prompt_filename
    
    # Use the prompt file if it exists
    if prompt_path.exists():
        prompt_content = prompt_path.read_text(encoding='utf-8')
        output_parts.append(prompt_content)
    else:
        # Fallback to default prompt if file doesn't exist
        prompt_template = """
You are an expert software engineer. Analyze the following codebase from my project.
The goal is to [YOUR GOAL HERE - e.g., find bugs, suggest improvements, implement feature X]

The code is organized by directories, with most recently modified files first.
Each file shows how recently it was modified to help you focus on recent changes.

Please provide your analysis with specific, actionable feedback.
"""
        output_parts.append(prompt_template.strip())
    
    # Add minimal project info after the prompt
    output_parts.append(f"\n# CodeSight: {project_root.name} ({datetime.now().strftime('%Y-%m-%d')})")

    # Add compact code structure overview
    output_parts.append("\n# Files:")

    for group in directory_groups:
        relative_dir = group.path.relative_to(project_root)
        dir_name = str(relative_dir) + "/" if str(relative_dir) != '.' else ""
        
        # Sort files alphabetically for the overview
        sorted_files_overview = sorted(group.files, key=lambda f: f.path.name)
        for file_metadata in sorted_files_overview:
            output_parts.append(f"# - {dir_name}{file_metadata.path.name}")

    # Add concatenated code files
    output_parts.append("\n# --- Start Code Files ---")

    # Precompile regex patterns for performance
    import_pattern = re.compile(r'^import.*|^from.*import.*', re.MULTILINE)
    definition_pattern = re.compile(r'^(def|class)\s+.*:', re.MULTILINE)

    # Initialize token encoder once
    encoder = tiktoken.get_encoding(DEFAULT_ENCODING)

    # Track tokens
    total_tokens = len(encoder.encode("\n".join(output_parts)))
    truncated = False

    # Process each directory group
    for group in directory_groups:
        # Sort files within group by recency
        sorted_files_in_group = sorted(group.files, key=lambda item: item.mtime, reverse=True)

        # Get relative directory path for header
        relative_dir = group.path.relative_to(project_root)
        dir_header = f"\n# Directory: {relative_dir}/"
        output_parts.append(dir_header)

        # Process files in parallel within this directory
        tasks = [
            process_file(
                file_metadata.path, file_metadata.mtime, project_root, 
                import_pattern, definition_pattern,
                token_limit, total_tokens, truncated, encoder
            ) 
            for file_metadata in sorted_files_in_group
        ]
        results = await asyncio.gather(*tasks)
        
        # Update tokens and truncated flag
        for content, new_total_tokens, new_truncated in results:
            if content:
                output_parts.append(content)
                total_tokens = max(total_tokens, new_total_tokens)
                truncated = truncated or new_truncated

    if truncated:
        output_parts.append("\n# Note: Some older files were truncated to stay within token limits.")

    output_parts.append("\n# --- End Code Files ---")

    return "\n".join(output_parts)


async def main_async() -> None:
    """
    Main async function to run CodeSight.
    
    Handles command-line argument parsing, file collection, and output generation.
    
    Returns:
        None
    """
    args = parse_arguments()

    # Get project root directory
    project_root = Path(args.directory).resolve()

    # Determine if we're already in the .codesight directory
    current_dir = Path.cwd().name
    in_codesight_dir = current_dir == '.codesight'
    
    # Auto-detect if we're in the codesight project itself
    is_codesight_project = False
    if project_root.name == "codesight-python" or in_codesight_dir or (project_root / '.codesight').is_dir() and len(list(project_root.glob('*'))) <= 10:
        is_codesight_project = True
        print("Auto-detected CodeSight project - enabling dogfood mode")
    
    # Use dogfood mode if explicitly enabled or auto-detected
    dogfood_mode = args.dogfood or is_codesight_project

    # Get output file name for exclusion (extract the file name without the path)
    output_file_name = Path(args.output_file).name
    
    # Build exclusion patterns
    exclusion_spec = build_exclusion_patterns(
        project_root,
        args.exclude,
        args.include_tests,
        dogfood_mode,
        args.include_structural,
        output_file_name
    )

    # Collect files (async)
    dirs_data = await collect_files(project_root, exclusion_spec)

    # Sort directories and files by recency
    directory_groups = prepare_sorted_groups(dirs_data)

    # Build output (async) with selected prompt type
    final_output = await build_output(directory_groups, project_root, args.token_limit, args.prompt)

    # Count tokens
    encoder = tiktoken.get_encoding(DEFAULT_ENCODING)
    tokens = len(encoder.encode(final_output))

    # Copy to clipboard
    pyperclip.copy(final_output)
    
    # Ensure output always goes to .codesight directory
    output_path = Path(args.output_file)
    
    # If not already an absolute path
    if not output_path.is_absolute():
        # If path doesn't already include .codesight/ prefix
        if not str(output_path).startswith('.codesight/') and output_path.parts[0] != '.codesight':
            # Add .codesight prefix
            output_path = Path('.codesight') / output_path
    
    # Get absolute path
    if not output_path.is_absolute():
        output_file = project_root / output_path
    else:
        output_file = output_path
    
    print(f"Saving output to: {output_file}")
    
    # Create directory if it doesn't exist
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(final_output, encoding='utf-8')

    # Print summary
    total_files = sum(len(group.files) for group in directory_groups)
    print(f"CodeSight: Processed {total_files} files ({tokens} tokens)")
    print(f"Content copied to clipboard!")
    print(f"Output saved to {output_file}")


def main() -> None:
    """
    Entry point function that handles the async event loop.
    
    Sets the appropriate event loop policy based on the platform
    and runs the main async function.
    
    Returns:
        None
    """
    # Configure asyncio to use the right event loop policy for macOS
    if hasattr(asyncio, 'WindowsSelectorEventLoopPolicy'):
        # Windows-specific event loop policy
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    else:
        try:
            # macOS-specific event loop policy improves performance on M-series Macs
            asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())
        except ImportError:
            # Fall back to default policy
            pass

    # Run the async main function
    asyncio.run(main_async())


if __name__ == "__main__":
    main()