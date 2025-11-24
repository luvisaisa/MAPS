"""
Keyword Extractors Module

Extensible keyword extraction system using abstract base classes and factory pattern.
Supports XML, PDF, and future formats (CSV, JSON, DICOM, etc.)
"""

from .base import BaseKeywordExtractor, ExtractedKeyword

__all__ = ['BaseKeywordExtractor', 'ExtractedKeyword']
