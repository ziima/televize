"""
Utilities for tests
"""
import os


def get_path(filepath, path):
    """Returns full path relative to the file."""
    return os.path.join(os.path.dirname(filepath), path)


def get_content(filename):
    """Return file content."""
    with open(filename) as source:
        return source.read()
