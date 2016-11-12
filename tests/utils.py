"""
Utilities for tests
"""
import os
from io import BytesIO

from requests import Response


def get_path(filepath, path):
    """
    Returns full path relative to the file.
    """
    return os.path.join(os.path.dirname(filepath), path)


def make_response(content):
    """
    Returns `requests.Response` object with defined `content`.
    """
    response = Response()
    response.raw = BytesIO(content)
    return response
