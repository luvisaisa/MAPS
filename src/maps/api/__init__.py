"""
MAPS REST API

FastAPI-based REST API for radiology data processing system.
Provides endpoints for parsing, querying, and exporting radiology data.
"""

from .main import app

__all__ = ['app']
