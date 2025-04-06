#!/usr/bin/env python3
"""
Pre-commit hook for CodeSight that tests basic functionality.
This ensures that changes don't break the tool itself.
"""

import os
import subprocess
import sys

def main():
    """Run the tests to ensure CodeSight works properly"""
    print("Running CodeSight pre-commit tests...")
    
    # Get the root directory of the CodeSight project
    script_dir = os.path.dirname(os.path.abspath(__file__))
    codesight_dir = os.path.dirname(script_dir)  # Go up from tests to .codesight
    root_dir = os.path.dirname(codesight_dir)  # Go up from .codesight to root
    
    # Run the tests
    result = subprocess.run(
        [sys.executable, "-m", "pytest", script_dir, "-xvs"],
        cwd=root_dir,
        text=True,
    )
    
    if result.returncode != 0:
        print("❌ CodeSight tests failed. Please fix the issues before committing.")
        sys.exit(1)
    
    print("✅ CodeSight tests passed!")
    sys.exit(0)

if __name__ == "__main__":
    main()