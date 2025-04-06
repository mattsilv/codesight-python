import os
import tempfile
import subprocess
import sys
import platform
import shutil
import pytest

@pytest.mark.skipif(
    not shutil.which("python3") or not shutil.which("pip"),
    reason="Python3 or pip not available on system"
)
def test_codesight_in_fresh_virtual_environment():
    """Test that CodeSight can be installed and run in a fresh virtual environment"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Get the root directory of the CodeSight project
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        root_dir = os.path.dirname(script_dir)  # Go up from .codesight to root
        
        # Create a virtual environment
        venv_dir = os.path.join(temp_dir, "venv")
        venv_command = [sys.executable, "-m", "venv", venv_dir]
        result = subprocess.run(
            venv_command,
            cwd=temp_dir,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Failed to create virtual environment: {result.stderr}"
        
        # Determine python executable and pip in virtual environment
        if platform.system() == "Windows":
            python_path = os.path.join(venv_dir, "Scripts", "python.exe")
            pip_path = os.path.join(venv_dir, "Scripts", "pip.exe")
        else:
            python_path = os.path.join(venv_dir, "bin", "python")
            pip_path = os.path.join(venv_dir, "bin", "pip")
        
        # Upgrade pip
        result = subprocess.run(
            [python_path, "-m", "pip", "install", "--upgrade", "pip"],
            cwd=temp_dir,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Failed to upgrade pip: {result.stderr}"
        
        # Install dependencies
        result = subprocess.run(
            [pip_path, "install", "pytest", "pathspec", "tiktoken", "pyperclip", "humanize"],
            cwd=temp_dir,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Failed to install dependencies: {result.stderr}"
        
        # Create a simple project to test with
        test_project_dir = os.path.join(temp_dir, "test_project")
        os.makedirs(os.path.join(test_project_dir, "src"))
        with open(os.path.join(test_project_dir, "src", "test.py"), "w") as f:
            f.write("print('Hello, world!')\n")
        
        with open(os.path.join(test_project_dir, ".gitignore"), "w") as f:
            f.write("*.log\n")
        
        # Copy the CodeSight code to a temporary location
        temp_codesight_dir = os.path.join(temp_dir, ".codesight")
        shutil.copytree(script_dir, temp_codesight_dir)
        
        # Run the CodeSight token analysis command
        cs_script = os.path.join(temp_codesight_dir, "bin", "cs.py")
        result = subprocess.run(
            [python_path, cs_script, "-t"],
            cwd=test_project_dir,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"CodeSight failed in a fresh environment: {result.stderr}"