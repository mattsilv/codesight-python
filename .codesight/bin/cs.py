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

# Version information
__version__ = "0.1.2"  # Following semantic versioning

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
    
    # Check if local venv has all required dependencies
    venv_dir = current_dir / '.venv'
    if venv_dir.exists():
        # We have a venv, let's make sure it has the required packages
        try:
            # Check for the humanize package which seems to be causing issues
            import_check = ['python', '-c', 'import humanize, tiktoken, pathspec']
            subprocess.run(import_check, cwd=current_dir, env=os.environ,
                          capture_output=True, text=True, check=True)
            print("Virtual environment already configured with required dependencies.")
        except subprocess.CalledProcessError:
            # Missing dependencies, install them
            print("Installing required dependencies in the virtual environment...")
            install_cmd = ['/bin/bash', '-c', f'source {venv_dir}/bin/activate && pip install tiktoken openai pytest typer more-itertools humanize pathspec']
            subprocess.run(install_cmd, cwd=current_dir, env=os.environ, shell=True)
    
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

if __name__ == "__main__":
    main()