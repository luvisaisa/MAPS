"""
Keyword Extractors Module

Extensible keyword extraction system using abstract base classes and factory pattern.
Supports XML, PDF, and future formats (CSV, JSON, DICOM, etc.)
"""

from .base import BaseKeywordExtractor, ExtractedKeyword
from .xml_keyword_extractor import XMLKeywordExtractor
from .pdf_keyword_extractor import PDFKeywordExtractor
from .factory import KeywordExtractorFactory, get_keyword_extractor_factory

__all__ = [
    'BaseKeywordExtractor',
    'ExtractedKeyword',
    'XMLKeywordExtractor',
    'PDFKeywordExtractor',
    'KeywordExtractorFactory',
    'get_keyword_extractor_factory'
]
