#!/usr/bin/env python
"""
CodeSight package management utilities.
"""
import json
import subprocess
import sys
import time
import urllib.request
from urllib.error import URLError
from pathlib import Path
import importlib.util

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


def get_latest_version():
    """Get the latest version from GitHub"""
    try:
        url = "https://api.github.com/repos/anthropics/codesight-python/releases/latest"
        request = urllib.request.Request(
            url,
            headers={"Accept": "application/vnd.github.v3+json", "User-Agent": f"CodeSight/{__version__}"}
        )
        
        with urllib.request.urlopen(request, timeout=2) as response:
            if response.getcode() == 200:
                data = json.loads(response.read().decode())
                latest_version = data.get('tag_name', '').lstrip('v')
                return latest_version
    except:
        pass
    
    return "unknown"


def update_codesight():
    """Update CodeSight to the latest version by fetching from GitHub and reinstalling"""
    print("Updating CodeSight to the latest version...")
    
    # Check if we have git access
    try:
        # Check if we can find the global codesight installation
        result = subprocess.run(
            ["pip", "show", "codesight"], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True
        )
        
        if result.returncode == 0:
            # Global installation exists, use pip to update
            print("Found global installation. Updating via pip...")
            update_cmd = ["pip", "install", "--upgrade", "codesight"]
            
            result = subprocess.run(
                update_cmd,
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True
            )
            
            if result.returncode == 0:
                print("✅ CodeSight updated successfully via pip!")
                print(f"Updated to version: {get_latest_version()}")
                return True
            else:
                print("⚠️ Failed to update via pip. Error:")
                print(result.stderr)
        else:
            # Try python -m pip as fallback
            result = subprocess.run(
                ["python", "-m", "pip", "show", "codesight"], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True
            )
            
            if result.returncode == 0:
                print("Found global installation. Updating via python -m pip...")
                update_cmd = ["python", "-m", "pip", "install", "--upgrade", "codesight"]
                
                result = subprocess.run(
                    update_cmd,
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE, 
                    text=True
                )
                
                if result.returncode == 0:
                    print("✅ CodeSight updated successfully via python -m pip!")
                    print(f"Updated to version: {get_latest_version()}")
                    return True
                else:
                    print("⚠️ Failed to update via python -m pip. Error:")
                    print(result.stderr)
    
    except Exception as e:
        print(f"⚠️ Error during update: {e}")
    
    print("\n⚠️ Automatic update failed. Please update manually with:")
    print("  pip install --upgrade codesight")
    print("  # or")
    print("  python -m pip install --upgrade codesight")
    return False


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