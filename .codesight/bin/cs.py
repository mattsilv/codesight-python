#!/usr/bin/env python
"""
CodeSight CLI - Quick shortcut for running CodeSight
"""
import argparse
import json
import os
import sys
from pathlib import Path
import subprocess

def main():
    # Define CLI arguments
    parser = argparse.ArgumentParser(description='CodeSight - Code analysis tool')
    parser.add_argument('directory', nargs='?', default='.', 
                        help='Directory to analyze (default: current directory)')
    parser.add_argument('-b', '--bug', nargs='?', const='', 
                        help='Run in bug mode with optional description')
    parser.add_argument('-c', '--config', action='store_true',
                        help='Create or edit config file')
    parser.add_argument('--no-venv', action='store_true',
                        help='Skip virtual environment activation')
    
    args = parser.parse_args()
    
    # Paths
    script_dir = Path(__file__).parent.parent
    config_path = script_dir / '.csconfig.json'
    
    # Load or create config
    if args.config:
        create_or_edit_config(config_path)
        return
    
    config = load_config(config_path)
    
    # Determine if we're in the CodeSight project
    current_dir = Path.cwd()
    repo_root = find_repo_root(current_dir)
    is_codesight_project = is_in_codesight_project(repo_root)
    
    # Set mode and flags
    prompt_type = 'bugfix' if args.bug is not None else 'improvement'
    dogfood_flag = '--dogfood' if is_codesight_project or config.get('always_dogfood', False) else ''
    
    # If bug description provided, update the bugfix template
    if args.bug is not None and args.bug:
        update_bug_description(script_dir, args.bug)
    
    # Construct command
    collect_script = script_dir / 'collect_code.py'
    cmd = f'python {collect_script} {args.directory} --prompt {prompt_type} {dogfood_flag}'
    
    # Run the command
    print(f"Running: {cmd}")
    os.system(cmd)

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

def create_or_edit_config(config_path):
    """Create or edit the config file"""
    config = load_config(config_path)
    
    print("CodeSight Configuration:")
    print("========================")
    
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