"""
API routes package for the 003 Worker Refactor.

This package contains all the API route definitions for the upload pipeline
and related functionality.
"""

from .upload import router as upload_router

__all__ = ["upload_router"]
