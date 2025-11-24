"""
Structure Detectors Module

Extensible structure/parse case detection system using abstract base classes.
Supports XML, CSV, JSON, and future formats.
"""

from .base import BaseStructureDetector
from .xml_structure_detector import XMLStructureDetector
from .factory import DetectorFactory, get_detector_factory

__all__ = [
    'BaseStructureDetector',
    'XMLStructureDetector',
    'DetectorFactory',
    'get_detector_factory'
]
