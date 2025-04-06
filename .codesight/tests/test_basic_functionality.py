import os
import tempfile
import shutil
import subprocess
import sys
import pytest

def test_codesight_runs_without_errors():
    """Test that CodeSight can run on a sample directory without errors"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a simple file structure to test with
        os.makedirs(os.path.join(temp_dir, "src"))
        with open(os.path.join(temp_dir, "src", "sample.py"), "w") as f:
            f.write("def hello():\n    return 'Hello, world!'\n")
        
        # Create a simple .gitignore
        with open(os.path.join(temp_dir, ".gitignore"), "w") as f:
            f.write("*.txt\n")
        
        # Get the path to the cs.py script
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cs_script = os.path.join(script_dir, "bin", "cs.py")
        
        # Run the codesight command with -h option to test basic functionality
        result = subprocess.run(
            [sys.executable, cs_script, "-h"],
            cwd=temp_dir,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"CodeSight failed with error: {result.stderr}"
        
        # Test token analysis command
        result = subprocess.run(
            [sys.executable, cs_script, "-t"],
            cwd=temp_dir,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Token analysis failed with error: {result.stderr}"

def test_codesight_runs_on_own_code():
    """Test that CodeSight can run on its own code directory"""
    # Get the root directory of the CodeSight project
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    root_dir = os.path.dirname(script_dir)  # Go up from .codesight to root
    
    # Get the path to the cs.py script
    cs_script = os.path.join(script_dir, "bin", "cs.py")
    
    # Run the codesight token analysis command on its own code
    result = subprocess.run(
        [sys.executable, cs_script, "-t"],
        cwd=root_dir,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"CodeSight failed on its own code with error: {result.stderr}"