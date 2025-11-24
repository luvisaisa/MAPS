"""
Keyword Extractor Factory

Auto-selects appropriate extractor based on file format.
Implements plugin pattern for custom extractors.
"""

from typing import List, Optional
import logging

from .base import BaseKeywordExtractor

logger = logging.getLogger(__name__)


class KeywordExtractorFactory:
    """
    Factory for automatically selecting the right keyword extractor.

    Usage:
        factory = KeywordExtractorFactory()
        extractor = factory.get_extractor("data.xml")
        keywords = extractor.extract_keywords("data.xml")

    Custom extractors can be registered:
        factory.register_extractor(MyCustomExtractor())
    """

    def __init__(self):
        """Initialize factory with default extractors."""
        self.extractors: List[BaseKeywordExtractor] = []
        self._register_default_extractors()

    def _register_default_extractors(self):
        """Register built-in extractors (XML, PDF)."""
        try:
            from .xml_keyword_extractor import XMLKeywordExtractor
            self.extractors.append(XMLKeywordExtractor())
            logger.info("Registered XMLKeywordExtractor")
        except ImportError as e:
            logger.warning(f"Could not load XMLKeywordExtractor: {e}")

        try:
            from .pdf_keyword_extractor import PDFKeywordExtractor
            self.extractors.append(PDFKeywordExtractor())
            logger.info("Registered PDFKeywordExtractor")
        except ImportError as e:
            logger.warning(f"Could not load PDFKeywordExtractor: {e}")

        # Future extractors will auto-register here:
        # - CSVKeywordExtractor
        # - JSONKeywordExtractor
        # - DICOMKeywordExtractor

    def get_extractor(self, file_path: str) -> Optional[BaseKeywordExtractor]:
        """
        Get the appropriate extractor for the given file.

        Args:
            file_path: Path to file

        Returns:
            BaseKeywordExtractor instance or None if no extractor found
        """
        for extractor in self.extractors:
            if extractor.can_extract(file_path):
                logger.info(f"Selected {extractor.__class__.__name__} for {file_path}")
                return extractor

        logger.warning(f"No extractor found for {file_path}")
        return None

    def register_extractor(self, extractor: BaseKeywordExtractor):
        """
        Register a custom extractor (plugin system).

        Args:
            extractor: Custom BaseKeywordExtractor implementation
        """
        if not isinstance(extractor, BaseKeywordExtractor):
            raise TypeError(f"Extractor must inherit from BaseKeywordExtractor, got {type(extractor)}")

        self.extractors.append(extractor)
        logger.info(f"Registered custom extractor: {extractor.__class__.__name__}")

    def list_extractors(self) -> List[str]:
        """Return list of registered extractor names."""
        return [extractor.__class__.__name__ for extractor in self.extractors]


# Singleton instance
_factory_instance: Optional[KeywordExtractorFactory] = None


def get_keyword_extractor_factory() -> KeywordExtractorFactory:
    """Get singleton factory instance."""
    global _factory_instance
    if _factory_instance is None:
        _factory_instance = KeywordExtractorFactory()
    return _factory_instance
