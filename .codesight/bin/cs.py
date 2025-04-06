#!/usr/bin/env python
"""
CodeSight CLI - Quick shortcut for running CodeSight
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path
import subprocess
import urllib.request
from urllib.error import URLError
import importlib.util
import re
from operator import itemgetter
from collections import defaultdict

# Import version from _version.py
script_dir = Path(__file__).parent.parent
spec = importlib.util.spec_from_file_location("_version", script_dir / "_version.py")
version_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(version_module)
__version__ = version_module.__version__

def check_for_updates():
    """Check GitHub for newer versions of CodeSight and return update info if available"""
    # Cache file for update checks to avoid too frequent API calls
    cache_file = Path.home() / '.codesight_update_cache.json'
    cache_valid_hours = 24  # Check for updates once per day
    
    # Current time
    current_time = time.time()
    
    # Check cache first
    try:
        if cache_file.exists():
            with open(cache_file, 'r') as f:
                cache = json.load(f)
                
            # If cache is still valid and we already checked
            if current_time - cache.get('last_check', 0) < cache_valid_hours * 3600:
                if cache.get('update_available') and cache.get('latest_version'):
                    return {
                        'update_available': True,
                        'current_version': __version__,
                        'latest_version': cache['latest_version']
                    }
                return None  # No update available
    except:
        # If there's any issue with the cache, just continue
        pass
        
    # If we get here, either the cache is expired or doesn't exist
    try:
        # GitHub API - latest release
        url = "https://api.github.com/repos/anthropics/codesight-python/releases/latest"
        request = urllib.request.Request(
            url,
            headers={"Accept": "application/vnd.github.v3+json", "User-Agent": f"CodeSight/{__version__}"}
        )
        
        with urllib.request.urlopen(request, timeout=2) as response:
            if response.getcode() == 200:
                data = json.loads(response.read().decode())
                latest_version = data.get('tag_name', '').lstrip('v')
                
                # Compare versions (simple string comparison works for semantic versioning)
                if latest_version and latest_version > __version__:
                    # Update cache
                    cache_data = {
                        'last_check': current_time,
                        'update_available': True,
                        'latest_version': latest_version
                    }
                    with open(cache_file, 'w') as f:
                        json.dump(cache_data, f)
                        
                    return {
                        'update_available': True,
                        'current_version': __version__,
                        'latest_version': latest_version
                    }
        
        # If we get here, no update is available
        cache_data = {
            'last_check': current_time,
            'update_available': False
        }
        with open(cache_file, 'w') as f:
            json.dump(cache_data, f)
            
        return None
            
    except (URLError, Exception) as e:
        # On connection error, just continue without update check
        # Don't bother the user with network errors
        return None

def main():
    # Define CLI arguments
    parser = argparse.ArgumentParser(description=f'CodeSight v{__version__} - Code analysis tool')
    parser.add_argument('directory', nargs='?', default='.', 
                        help='Directory to analyze (default: current directory)')
    parser.add_argument('-b', '--bug', nargs='?', const='', 
                        help='Run in bug mode with optional description')
    parser.add_argument('-c', '--config', action='store_true',
                        help='Create or edit config file')
    parser.add_argument('-i', '--init', action='store_true',
                        help='Initialize CodeSight in the current project')
    parser.add_argument('-t', '--tokens', action='store_true',
                        help='Show top files by token count to identify optimization opportunities')
    parser.add_argument('--no-venv', action='store_true',
                        help='Skip virtual environment activation')
    parser.add_argument('-v', '--version', action='store_true',
                        help='Show version information')
    
    args = parser.parse_args()
    
    # Show version if requested
    if args.version:
        print(f"CodeSight version {__version__}")
        sys.exit(0)
    
    # Paths
    script_dir = Path(__file__).parent.parent
    current_dir = Path.cwd()
    
    # Handle token analysis if requested
    if args.tokens:
        # Use configured directory if none specified and config has a default
        directory = args.directory
        
        # Check for project-specific config
        project_config_path = current_dir / '.codesight-config.json'
        global_config_path = script_dir / '.csconfig.json'
        config_path = project_config_path if project_config_path.exists() else global_config_path
        config = load_config(config_path)
        
        if directory == '.' and config.get('default_directory'):
            directory = config.get('default_directory')
            
        print(f"Analyzing token usage in {directory}...")
        print("This may take a moment for large projects...")
        
        # Check for missing dependencies before running
        try:
            import tiktoken
        except ImportError:
            print("\nMissing required dependency: tiktoken")
            if auto_install_dependencies(["tiktoken"]):
                print("✅ Successfully installed tiktoken.")
                try:
                    import tiktoken
                except ImportError:
                    print("⚠️ Failed to import tiktoken even after installation.")
                    print("Please try again after restarting the script.")
                    sys.exit(1)
            else:
                print("⚠️ Failed to install dependencies automatically.")
                print("Please install them manually and try again.")
                sys.exit(1)
                
        # Run token analysis
        results = analyze_token_usage(directory)
        
        if not results:
            print("Failed to analyze token usage.")
            sys.exit(1)
            
        # Display results in a nicely formatted table
        total = results['total_tokens']
        processed = results['processed_files']
        skipped = results['skipped_files']
        
        print("\n" + "=" * 70)
        print(f"Token Usage Analysis - Top Files by Token Count")
        print("=" * 70)
        print(f"Total token count: {total:,}")
        print(f"Files processed: {processed}")
        print(f"Files skipped: {skipped}")
        print("=" * 70)
        
        # Display top files table
        print("\nTop files by token count:")
        print("-" * 70)
        print(f"{'File':<50} | {'Tokens':>8} | {'% of Total':>10}")
        print("-" * 70)
        
        for file_path, tokens in results['file_tokens']:
            percentage = (tokens / total) * 100 if total > 0 else 0
            file_str = str(file_path)
            if len(file_str) > 48:
                file_str = "..." + file_str[-45:]
            print(f"{file_str:<50} | {tokens:>8,} | {percentage:>9.2f}%")
            
        # Display top directories table
        print("\nTop directories by token count:")
        print("-" * 70)
        print(f"{'Directory':<50} | {'Tokens':>8} | {'% of Total':>10}")
        print("-" * 70)
        
        for dir_path, tokens in results['dir_tokens']:
            percentage = (tokens / total) * 100 if total > 0 else 0
            dir_str = str(dir_path) if str(dir_path) != "." else "(root)"
            if len(dir_str) > 48:
                dir_str = "..." + dir_str[-45:]
            print(f"{dir_str:<50} | {tokens:>8,} | {percentage:>9.2f}%")
            
        print("\nNOTE: The following file types are automatically excluded to reduce token usage:")
        print("- Database files (.db, .sqlite, .sql)")
        print("- Compressed files (.zip, .gz, .tar, .rar, .7z)")
        print("- Data files (.csv, .json, .xml, .yaml, .yml, .npy, .pkl, etc.)")
        print("- Binary/image files (.jpg, .png, .pdf, .doc, etc.)")
        print("\nTip: Add exclusion patterns to .gitignore to exclude more file types.")
        print("\nTo customize exclusions further, use a project-specific config:")
        print("  cs -c")
        
        # Check for updates at the end
        update_info = check_for_updates()
        if update_info and update_info['update_available']:
            print(f"\n🔄 Update available: {update_info['current_version']} → {update_info['latest_version']}")
            print("   Run 'pip install --upgrade codesight' to update.")
        return
    
    # Handle initialization if requested
    if args.init:
        initialize_codesight(current_dir, script_dir)
        # Check for updates after initialization
        update_info = check_for_updates()
        if update_info and update_info['update_available']:
            print(f"\n🔄 Update available: {update_info['current_version']} → {update_info['latest_version']}")
            print("   Run 'pip install --upgrade codesight' to update.")
        return
    
    # Look for project-specific config first, then fall back to global
    project_config_path = current_dir / '.codesight-config.json'
    global_config_path = script_dir / '.csconfig.json'
    
    config_path = project_config_path if project_config_path.exists() else global_config_path
    
    # Load or create config
    if args.config:
        create_or_edit_config(config_path, is_project_config=config_path == project_config_path)
        return
    
    config = load_config(config_path)
    
    # Determine if we're in the CodeSight project
    repo_root = find_repo_root(current_dir)
    is_codesight_project = is_in_codesight_project(repo_root)
    
    # Set mode and flags
    prompt_type = 'bugfix' if args.bug is not None else 'improvement'
    dogfood_flag = '--dogfood' if is_codesight_project or config.get('always_dogfood', False) else ''
    
    # If bug description provided, update the bugfix template
    if args.bug is not None and args.bug:
        update_bug_description(script_dir, args.bug)
    
    # Use configured directory if none specified and config has a default
    directory = args.directory
    if directory == '.' and config.get('default_directory'):
        directory = config.get('default_directory')
    
    # Construct command
    collect_script = script_dir / 'collect_code.py'
    cmd = f'python {collect_script} {directory} --prompt {prompt_type} {dogfood_flag}'
    
    # Check for required dependencies before running
    missing_deps = []
    for module in ["tiktoken", "pathspec", "pyperclip", "humanize"]:
        try:
            __import__(module)
        except ImportError:
            missing_deps.append(module)
    
    # If there are missing dependencies, try to install them automatically
    if missing_deps:
        # Check for virtual environment
        venv_dir = current_dir / '.venv'
        in_venv = venv_dir.exists() and 'VIRTUAL_ENV' in os.environ
        
        if in_venv:
            print(f"Virtual environment detected and active.")
            if auto_install_dependencies(missing_deps, in_venv=True):
                print("✅ All dependencies installed successfully.")
            else:
                print("\n⚠️ Failed to install dependencies automatically.")
                print("Please install them manually and try again.")
                sys.exit(1)
        else:
            # Try to auto-install even if not in venv
            if auto_install_dependencies(missing_deps):
                print("✅ All dependencies installed successfully.")
            else:
                if venv_dir.exists():
                    print(f"\nVirtual environment detected at: {venv_dir}")
                    print(f"You may need to activate it first:")
                    print(f"source {venv_dir}/bin/activate")
                print("\nPlease install missing dependencies manually and try again.")
                sys.exit(1)
    
    # Run the command
    print(f"Running: {cmd}")
    os.system(cmd)
    
    # Check for updates after command completes
    update_info = check_for_updates()
    if update_info and update_info['update_available']:
        print(f"\n🔄 Update available: {update_info['current_version']} → {update_info['latest_version']}")
        print("   Run 'pip install --upgrade codesight' to update.")
    
def check_gitignore_for_codesight(project_dir):
    """Check if .gitignore exists and contains .codesight"""
    gitignore_path = project_dir / '.gitignore'
    if not gitignore_path.exists():
        return False
    
    with open(gitignore_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Check for .codesight or .codesight/ in the gitignore
    return '.codesight/' in content or '.codesight' in content

def auto_install_dependencies(missing_deps, in_venv=False):
    """Automatically install missing dependencies using available package managers"""
    if not missing_deps:
        return True
    
    print(f"\nInstalling missing dependencies: {', '.join(missing_deps)}")
    
    # List of package managers to try in order of preference
    package_managers = [
        {"name": "pip", "cmd": "pip install {deps}"},
        {"name": "python -m pip", "cmd": "python -m pip install {deps}"},
        {"name": "uv", "cmd": "uv pip install {deps}"}
    ]
    
    deps_str = " ".join(missing_deps)
    success = False
    
    for pm in package_managers:
        cmd = pm["cmd"].format(deps=deps_str)
        print(f"Trying: {cmd}")
        
        try:
            result = subprocess.run(cmd.split(), 
                                   stdout=subprocess.PIPE, 
                                   stderr=subprocess.PIPE, 
                                   text=True)
            
            if result.returncode == 0:
                print(f"✅ Successfully installed dependencies using {pm['name']}")
                success = True
                break
        except FileNotFoundError:
            print(f"❌ {pm['name']} not found, trying alternative...")
    
    if not success:
        print("\n⚠️ Automatic installation failed. Please install dependencies manually:")
        print("  pip install " + deps_str)
        print("  # or")
        print("  python -m pip install " + deps_str)
        print("  # or")
        print("  uv pip install " + deps_str)
        return False
    
    return True

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
        
        # Use the same encoder as collect_code.py
        encoder = tiktoken.get_encoding("cl100k_base")
        
        # Define exclusion patterns (same as in collect_code.py plus data files)
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
        
        # Compile all patterns
        exclude_patterns = [re.compile(pattern) for pattern in standard_excludes]
        
        # Get list of all files
        project_dir = Path(directory).resolve()
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
            
            # Check exclusion patterns
            should_exclude = False
            for pattern in exclude_patterns:
                if pattern.search(str_path):
                    should_exclude = True
                    skipped_files += 1
                    break
                    
            if should_exclude:
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

if __name__ == "__main__":
    main()