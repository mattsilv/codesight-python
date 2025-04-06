# CodeSight-Python package initialization

try:
    from ._version import __version__
except ImportError:
    # For development and testing purposes
    import os
    version_path = os.path.join(os.path.dirname(__file__), "_version.py")
    with open(version_path) as f:
        version_content = f.read()
    exec(version_content)  # This defines __version__ in this scope

__all__ = ["__version__"]