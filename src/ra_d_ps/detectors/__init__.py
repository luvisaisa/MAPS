"""
Structure Detectors Module

Extensible structure/parse case detection system using abstract base classes.
Supports XML, CSV, JSON, and future formats.
"""

from .base import BaseStructureDetector

__all__ = ['BaseStructureDetector']
