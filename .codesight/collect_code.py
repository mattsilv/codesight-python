#!/usr/bin/env python
"""
CodeSight: Collects and formats code for LLM analysis, optimized for M-series Macs.
"""

import argparse
import asyncio
import re
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

import humanize
import pathspec
import pyperclip
import tiktoken


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments for CodeSight."""
    parser = argparse.ArgumentParser(description='Collect and format code for LLM analysis')
    parser.add_argument('directory', nargs='?', default='.', 
                       help='Project directory (default: current directory)')
    parser.add_argument('--token-limit', type=int, default=100000, 
                       help='Token limit for output')
    parser.add_argument('--exclude', nargs='+', default=[], 
                       help='Additional patterns to exclude')
    parser.add_argument('--include-tests', action='store_true', 
                       help='Include test directories')
    return parser.parse_args()


def build_exclusion_patterns(project_root: Path, user_excludes: List[str], 
                           include_tests: bool) -> pathspec.PathSpec:
    """Build patterns for excluding files from collection."""
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


def process_chunk(chunk: List[Path], project_root: Path, 
                 exclusion_spec: pathspec.PathSpec) -> Dict[Path, List[Tuple[Path, float]]]:
    """Process a chunk of files to filter and collect metadata."""
    chunk_result: Dict[Path, List[Tuple[Path, float]]] = {}
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


async def collect_files(project_root: Path, 
                      exclusion_spec: pathspec.PathSpec) -> Dict[Path, List[Tuple[Path, float]]]:
    """
    Asynchronously collect and filter files using multiple processes
    to leverage M-series Mac performance.
    """
    dirs_data: Dict[Path, List[Tuple[Path, float]]] = {}

    # Get all potential files first (faster than recursive glob in each process)
    all_files = list(project_root.rglob('*'))

    # Process files in chunks using process pool
    chunk_size = 1000  # Adjust based on system memory
    chunks = [all_files[i:i + chunk_size] for i in range(0, len(all_files), chunk_size)]

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


def prepare_sorted_groups(dirs_data: Dict[Path, List[Tuple[Path, float]]]) -> List[Dict[str, Any]]:
    """Sort directories and files by recency."""
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


def format_relative_time(timestamp: float) -> str:
    """Convert timestamp to human-readable relative time (e.g., '3 hours ago')"""
    now = datetime.now()
    file_time = datetime.fromtimestamp(timestamp)
    return humanize.naturaltime(now - file_time)


async def process_file(file_path: Path, mtime: float, project_root: Path, 
                   import_pattern: re.Pattern, definition_pattern: re.Pattern,
                   token_limit: int, total_tokens: int, truncated: bool,
                   encoder: tiktoken.Encoding) -> Tuple[Optional[str], int, bool]:
    """Process a single file for output."""
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
            result = f"\n{header}\n{content}"
            total_tokens += file_tokens
            return result, total_tokens, truncated
        else:
            return f"\n# --- {file_path.name} skipped (token limit reached) ---", total_tokens, truncated

    except Exception as e:
        return f"\n# --- Error reading file: {relative_path} ---\n# Error: {e}", total_tokens, truncated


async def build_output(group_sort_info: List[Dict[str, Any]], 
                     project_root: Path, 
                     token_limit: int) -> str:
    """Optimized output builder using async for file reading operations"""
    output_parts = []

    # Add today's date and project info at the top
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

    # Process each directory group
    for group in group_sort_info:
        # Sort files within group by recency
        sorted_files_in_group = sorted(group['files'], key=lambda item: item[1], reverse=True)

        # Get relative directory path for header
        relative_dir = group['dir'].relative_to(project_root)
        dir_header = f"\n# Directory: {relative_dir}/"
        output_parts.append(dir_header)

        # Process files in parallel within this directory
        tasks = [
            process_file(
                file_path, mtime, project_root, 
                import_pattern, definition_pattern,
                token_limit, total_tokens, truncated, encoder
            ) 
            for file_path, mtime in sorted_files_in_group
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
    """Main async function to run CodeSight."""
    args = parse_arguments()

    # Get project root directory
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
    encoder = tiktoken.get_encoding("cl100k_base")
    tokens = len(encoder.encode(final_output))

    # Copy to clipboard
    pyperclip.copy(final_output)

    # Print summary
    total_files = sum(len(group['files']) for group in group_sort_info)
    print(f"CodeSight: Processed {total_files} files ({tokens} tokens)")
    print(f"Content copied to clipboard!")


def main() -> None:
    """Entry point that handles the async event loop"""
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