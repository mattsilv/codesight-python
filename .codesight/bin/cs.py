#!/usr/bin/env python
"""
CodeSight CLI - Quick shortcut for running CodeSight
"""
import argparse
import os
import sys
from pathlib import Path
import importlib.util

# Import version from _version.py
script_dir = Path(__file__).parent.parent
spec = importlib.util.spec_from_file_location("_version", script_dir / "_version.py")
version_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(version_module)
__version__ = version_module.__version__

# Import from our other modules
# Use absolute imports for direct execution (tests, etc.)
try:
    # For package installation context
    from .cs_package import check_for_updates, update_codesight, auto_install_dependencies
    from .cs_project import (
        initialize_codesight, load_config, create_or_edit_config,
        find_repo_root, is_in_codesight_project, update_bug_description,
        analyze_token_usage
    )
except ImportError:
    # For direct script execution or tests
    import sys
    import os
    bin_dir = os.path.dirname(os.path.abspath(__file__))
    if bin_dir not in sys.path:
        sys.path.append(bin_dir)
    
    from cs_package import check_for_updates, update_codesight, auto_install_dependencies
    from cs_project import (
        initialize_codesight, load_config, create_or_edit_config,
        find_repo_root, is_in_codesight_project, update_bug_description,
        analyze_token_usage
    )


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
    parser.add_argument('-u', '--update', action='store_true',
                        help='Update CodeSight to the latest version')
    parser.add_argument('--no-venv', action='store_true',
                        help='Skip virtual environment activation')
    parser.add_argument('-v', '--version', action='store_true',
                        help='Show version information')
    
    args = parser.parse_args()
    
    # Show version if requested
    if args.version:
        print(f"CodeSight version {__version__}")
        sys.exit(0)
        
    # Handle update if requested
    if args.update:
        update_codesight()
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
                
        # Get custom exclusions from config if they exist
        custom_exclusions = []
        if config.get('exclusions'):
            custom_exclusions = [pattern.strip() for pattern in config.get('exclusions', '').split(',') if pattern.strip()]
        
        # Run token analysis with custom exclusions
        results = analyze_token_usage(directory, custom_exclusions=custom_exclusions)
        
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
        
        # Show custom exclusions if any were used
        if custom_exclusions:
            print("\nCustom exclusions applied:")
            for pattern in custom_exclusions:
                print(f"- {pattern}")
                
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
    is_codesight_proj = is_in_codesight_project(repo_root)
    
    # Set mode and flags
    prompt_type = 'bugfix' if args.bug is not None else 'improvement'
    dogfood_flag = '--dogfood' if is_codesight_proj or config.get('always_dogfood', False) else ''
    
    # If bug description provided, update the bugfix template
    if args.bug is not None and args.bug:
        update_bug_description(script_dir, args.bug)
    
    # Use configured directory if none specified and config has a default
    directory = args.directory
    if directory == '.' and config.get('default_directory'):
        directory = config.get('default_directory')
    
    # Construct command
    collect_script = script_dir / 'collect_code.py'
    
    # Add custom exclusions from config if they exist
    exclusions = config.get('exclusions', '').strip()
    exclusion_args = ''
    if exclusions:
        # Convert comma-separated exclusions to space-separated args for --exclude
        exclusion_list = [pattern.strip() for pattern in exclusions.split(',')]
        exclusion_args = '--exclude ' + ' '.join([f'"{pattern}"' for pattern in exclusion_list if pattern])
    
    # Build the full command
    cmd = f'python {collect_script} {directory} --prompt {prompt_type} {dogfood_flag} {exclusion_args}'
    
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


if __name__ == "__main__":
    main()