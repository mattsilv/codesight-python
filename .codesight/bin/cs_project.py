#!/usr/bin/env python
"""
CodeSight project setup and analysis utilities.
"""
import json
import os
import re
import sys
from collections import defaultdict
from operator import itemgetter
from pathlib import Path
import importlib.util

# Import version from _version.py
script_dir = Path(__file__).parent.parent
spec = importlib.util.spec_from_file_location("_version", script_dir / "_version.py")
version_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(version_module)
__version__ = version_module.__version__


def check_gitignore_for_codesight(project_dir):
    """Check if .gitignore exists and contains .codesight"""
    gitignore_path = project_dir / '.gitignore'
    if not gitignore_path.exists():
        return False
    
    with open(gitignore_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Check for .codesight or .codesight/ in the gitignore
    return '.codesight/' in content or '.codesight' in content


def initialize_codesight(current_dir, script_dir):
    """Initialize CodeSight in the current project"""
    print(f"Initializing CodeSight in {current_dir}...")
    
    # Create project config
    config_path = current_dir / '.codesight-config.json'
    
    # Default project config
    default_config = {
        "default_directory": ".",
        "always_dogfood": False,
        "token_limit": 100000
    }
    
    # Write project config
    with open(config_path, 'w') as f:
        json.dump(default_config, f, indent=2)
    
    # Create .codesight directory if needed
    codesight_dir = current_dir / '.codesight'
    if not codesight_dir.exists():
        codesight_dir.mkdir(exist_ok=True)
    
    # Try to import required dependencies directly
    missing_deps = []
    for module in ["tiktoken", "pathspec", "pyperclip", "humanize"]:
        try:
            __import__(module)
        except ImportError:
            missing_deps.append(module)
    
    # Check for virtual environment
    venv_dir = current_dir / '.venv'
    in_venv = venv_dir.exists() and 'VIRTUAL_ENV' in os.environ
    
    # If there are missing dependencies, try to install them automatically
    if missing_deps:
        # Import here to avoid circular imports
        from .cs_package import auto_install_dependencies
        
        if in_venv:
            print(f"Virtual environment detected at: {venv_dir}")
            if auto_install_dependencies(missing_deps, in_venv=True):
                print("✅ All dependencies installed successfully.")
            else:
                print(f"\nPlease activate your virtual environment and try again:")
                print(f"source {venv_dir}/bin/activate")
                print(f"Then run 'cs -i' again.")
        else:
            # Try to auto-install even if not in venv
            if auto_install_dependencies(missing_deps):
                print("✅ All dependencies installed successfully.")
            else:
                if venv_dir.exists():
                    print(f"\nVirtual environment detected at: {venv_dir}")
                    print(f"You may need to activate it first:")
                    print(f"source {venv_dir}/bin/activate")
                    print(f"Then run 'cs -i' again.")
    
    # Check if .gitignore has .codesight exclusion
    if (current_dir / '.git').exists() and not check_gitignore_for_codesight(current_dir):
        print("\n⚠️  WARNING: .codesight/ is not excluded in your .gitignore file!")
        print("   To avoid accidentally committing CodeSight files, add this line to your .gitignore:")
        print("   .codesight/\n")
        
        # Ask user if they want to automatically add it
        response = input("Would you like to automatically add .codesight/ to your .gitignore? [y/N]: ").strip().lower()
        if response == 'y' or response == 'yes':
            gitignore_path = current_dir / '.gitignore'
            
            # Create .gitignore if it doesn't exist
            if not gitignore_path.exists():
                with open(gitignore_path, 'w', encoding='utf-8') as f:
                    f.write("# CodeSight generated files\n.codesight/\n")
            else:
                with open(gitignore_path, 'a', encoding='utf-8') as f:
                    f.write("\n# CodeSight generated files\n.codesight/\n")
            
            print("Added .codesight/ to .gitignore file.")
    
    print(f"Created project config at {config_path}")
    print("You can now run 'cs' without arguments to analyze this project.")


def find_repo_root(path):
    """Find the repository root by looking for .git directory"""
    current = path
    while current != current.parent:
        if (current / '.git').exists():
            return current
        current = current.parent
    return path  # Default to current if not found


def is_in_codesight_project(path):
    """Determine if we're in the CodeSight project"""
    if path.name == 'codesight-python':
        return True
    if (path / '.codesight').exists() and len(list(path.glob('*'))) < 15:
        return True
    return False


def load_config(config_path):
    """Load config or create default"""
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except:
            pass
    
    # Default config
    default_config = {
        "always_dogfood": False,
        "token_limit": 100000
    }
    
    # Write default config
    with open(config_path, 'w') as f:
        json.dump(default_config, f, indent=2)
    
    return default_config


def create_or_edit_config(config_path, is_project_config=False):
    """Create or edit the config file"""
    config = load_config(config_path)
    
    print("CodeSight Configuration:")
    print("========================")
    print(f"Editing {'project-specific' if is_project_config else 'global'} configuration")
    
    # For project configs, allow setting default directory
    if is_project_config:
        default_dir = config.get('default_directory', '.')
        new_dir = input(f"Default directory to analyze [{default_dir}]: ").strip()
        if new_dir:
            config['default_directory'] = new_dir
        elif 'default_directory' not in config:
            config['default_directory'] = default_dir
    
    # Update config interactively
    config['always_dogfood'] = input_yes_no(
        "Always run in dogfood mode? (y/n): ", 
        config.get('always_dogfood', False)
    )
    
    config['token_limit'] = input_number(
        "Token limit (default: 100000): ", 
        config.get('token_limit', 100000)
    )
    
    # Write updated config
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"\nConfiguration saved to {config_path}")
    
    if is_project_config:
        print("To analyze this project, simply run 'cs' without arguments.")


def input_yes_no(prompt, default):
    """Get yes/no input with default"""
    default_str = 'y' if default else 'n'
    val = input(f"{prompt} [{default_str}] ").strip().lower()
    if not val:
        return default
    return val.startswith('y')


def input_number(prompt, default):
    """Get number input with default"""
    val = input(f"{prompt} [{default}] ").strip()
    if not val:
        return default
    try:
        return int(val)
    except ValueError:
        print("Invalid number, using default.")
        return default


def update_bug_description(script_dir, bug_description):
    """Update the bugfix template with the provided description"""
    bugfix_path = script_dir / 'prompts' / 'bugfix.md'
    
    if not bugfix_path.exists():
        print(f"Warning: Bugfix template not found at {bugfix_path}")
        return
    
    content = bugfix_path.read_text()
    
    # Replace placeholders with the bug description
    content = content.replace('PLACEHOLDER_BUG_DESCRIPTION', bug_description)
    content = content.replace('PLACEHOLDER_EXPECTED_BEHAVIOR', 
                             "Expected behavior should be inferred from the bug description.")
    content = content.replace('PLACEHOLDER_REPRODUCTION_STEPS',
                             "Please analyze the code to determine reproduction steps.")
    
    # Write to a temporary file that will be used just for this run
    temp_path = script_dir / 'prompts' / 'bugfix_temp.md'
    temp_path.write_text(content)
    
    # Back up the original
    backup_path = script_dir / 'prompts' / 'bugfix_original.md'
    if not backup_path.exists():
        bugfix_path.rename(backup_path)
    
    # Use the temporary file
    temp_path.rename(bugfix_path)


def analyze_token_usage(directory, limit=10):
    """
    Analyze token usage in files within a directory.
    
    Args:
        directory: Path to the directory to analyze
        limit: Maximum number of files to show in results
        
    Returns:
        A tuple of (total_tokens, file_tokens) where:
        - total_tokens is the total number of tokens across all files
        - file_tokens is a list of (file_path, tokens) tuples sorted by token count
    """
    try:
        # First, ensure tiktoken is available
        try:
            import tiktoken
        except ImportError:
            print("\nMissing required dependency: tiktoken")
            print("Please install it with: pip install tiktoken")
            sys.exit(1)
            
        from pathlib import Path
        import pathspec
        
        # Use the same encoder as collect_code.py
        encoder = tiktoken.get_encoding("cl100k_base")
        
        # Get project root directory
        project_dir = Path(directory).resolve()
        
        # Load the same exclusion patterns used by collect_code.py
        # This ensures the token analysis only counts files that would be included in llm.txt
        exclusion_spec = None
        
        # Start with standard excludes
        standard_excludes = [
            # Hidden files and directories
            r"^\.",
            r"/\.",
            # Version control
            r"\.git/",
            # Build artifacts
            r"__pycache__/",
            r"build/",
            r"dist/",
            r"\.egg-info/",
            # Virtual environments
            r"\.env/",
            r"\.venv/",
            r"venv/",
            r"env/",
            # Data files (global exclusions)
            r"\.csv$",
            r"\.tsv$",
            r"\.sqlite$",
            r"\.db$",
            r"\.sql$",
            r"\.zip$",
            r"\.gz$",
            r"\.tar$",
            r"\.rar$",
            r"\.7z$",
            r"\.dat$",
            r"\.bin$",
            r"\.npy$",
            r"\.npz$",
            r"\.pkl$",
            r"\.pickle$",
            r"\.parquet$",
            r"\.h5$",
            r"\.hdf5$",
            r"\.json$",
            r"\.xml$",
            r"\.yaml$",
            r"\.yml$",
            # Images
            r"\.jpg$",
            r"\.jpeg$",
            r"\.png$",
            r"\.gif$",
            r"\.bmp$",
            r"\.svg$",
            r"\.ico$",
            # Other binary formats
            r"\.pdf$",
            r"\.doc$",
            r"\.docx$",
            r"\.xls$",
            r"\.xlsx$",
            r"\.ppt$",
            r"\.pptx$",
        ]
        
        # Check for .gitignore patterns
        gitignore_path = project_dir / '.gitignore'
        patterns = ['.git']  # Always ignore .git
        
        if gitignore_path.is_file():
            with gitignore_path.open('r', encoding='utf-8') as f:
                patterns.extend(f.readlines())
        
        # Add standard exclusions
        patterns.extend(standard_excludes)
        
        # Add test directories (these are excluded by default in collect_code.py)
        test_excludes = [
            'test/',
            'tests/',
            '*_test.py',
            'test_*.py',
        ]
        patterns.extend(test_excludes)
        
        # ALWAYS exclude the output file and prompts to prevent recursive processing
        output_excludes = [
            'llm.txt',
            '*/llm.txt',
            '.codesight/llm.txt',
            # Exclude prompts directory (templates don't need to be analyzed)
            'prompts/',
            '*/prompts/',
            '.codesight/prompts/',
        ]
        patterns.extend(output_excludes)
        
        # Common config files and structural files (excluded by default)
        structural_excludes = [
            # Common config files
            '*.toml',
            'setup.py',
            'setup.cfg',
            'requirements.txt',
            'LICENSE',
            'Dockerfile',
            'docker-compose.yml',
            'Makefile',
            # Structural files with minimal content
            '__init__.py',
            '*/__init__.py',
            '__main__.py',
            '*/__main__.py',
            'conftest.py',
            '*/conftest.py',
        ]
        patterns.extend(structural_excludes)
        
        # Create pathspec from patterns (same as collect_code.py)
        exclusion_spec = pathspec.PathSpec.from_lines(pathspec.patterns.GitWildMatchPattern, patterns)
        
        # Get list of all files
        all_files = list(project_dir.rglob("*"))
        
        # Process files
        file_tokens = []
        dir_tokens = defaultdict(int)
        total_tokens = 0
        processed_files = 0
        skipped_files = 0
        
        for file_path in all_files:
            # Skip directories and non-files
            if not file_path.is_file():
                continue
                
            # Get relative path for easier display
            rel_path = file_path.relative_to(project_dir)
            str_path = str(rel_path)
            
            # Skip if file matches exclusion patterns (using same logic as collect_code.py)
            if exclusion_spec.match_file(str_path):
                skipped_files += 1
                continue
            
            # Skip binary files (rough check)
            try:
                # Try to read the first 1024 bytes as text
                with open(file_path, 'r', encoding='utf-8', errors='strict') as f:
                    f.read(1024)
            except (UnicodeDecodeError, IsADirectoryError):
                skipped_files += 1
                continue
                
            # Read file and count tokens
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    tokens = len(encoder.encode(content))
                    file_tokens.append((rel_path, tokens))
                    
                    # Update parent directory stats
                    parent_dir = rel_path.parent
                    dir_tokens[parent_dir] += tokens
                    
                    total_tokens += tokens
                    processed_files += 1
            except Exception as e:
                skipped_files += 1
                continue
                
        # Sort files by token count (descending)
        file_tokens.sort(key=itemgetter(1), reverse=True)
        
        # Sort directories by token count (descending)
        dir_tokens_list = [(d, t) for d, t in dir_tokens.items()]
        dir_tokens_list.sort(key=itemgetter(1), reverse=True)
        
        return {
            'total_tokens': total_tokens,
            'processed_files': processed_files,
            'skipped_files': skipped_files,
            'file_tokens': file_tokens[:limit],
            'dir_tokens': dir_tokens_list[:limit]
        }
    except Exception as e:
        print(f"Error analyzing token usage: {e}")
        return None