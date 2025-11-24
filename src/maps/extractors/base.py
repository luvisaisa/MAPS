"""
Base Keyword Extractor Interface

Abstract base class that all keyword extractors must implement.
Enables adding new file formats without modifying existing code.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class ExtractedKeyword:
    """
    Container for an extracted keyword with metadata.

    Attributes:
        text: The keyword text
        category: Category (characteristic, diagnosis, anatomy, metadata, custom)
        context: Surrounding text snippet for display
        source_field: Where the keyword was extracted from
        confidence: Extraction confidence score (0-1)
        frequency: Number of occurrences in document
        position: Optional (start, end) character positions
    """
    text: str
    category: str
    context: str
    source_field: str
    confidence: float = 1.0
    frequency: int = 1
    position: Optional[Tuple[int, int]] = None

    def __repr__(self):
        return f"<ExtractedKeyword(text='{self.text}', category='{self.category}', freq={self.frequency})>"


class BaseKeywordExtractor(ABC):
    """
    Abstract base class for keyword extractors.

    All extractors must implement:
    - can_extract(): Check if this extractor handles the file format
    - extract_keywords(): Extract keywords from file
    - get_supported_categories(): Return list of categories this extractor can identify

    Usage:
        class CSVKeywordExtractor(BaseKeywordExtractor):
            def can_extract(self, file_path: str) -> bool:
                return file_path.endswith('.csv')

            def extract_keywords(self, file_path: str, extraction_config: Dict) -> List[ExtractedKeyword]:
                # Implementation
                pass
    """

    @abstractmethod
    def can_extract(self, file_path: str) -> bool:
        """
        Determine if this extractor can handle the given file.

        Args:
            file_path: Path to file to check

        Returns:
            True if this extractor handles this file format, False otherwise
        """
        pass

    @abstractmethod
    def extract_keywords(self, file_path: str,
                        extraction_config: Optional[Dict] = None) -> List[ExtractedKeyword]:
        """
        Extract keywords from file using format-specific logic.

        Args:
            file_path: Path to file to extract from
            extraction_config: Optional configuration (e.g., fields to extract from,
                             categories to include, etc.)

        Returns:
            List of ExtractedKeyword objects

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is invalid or cannot be parsed
        """
        pass

    @abstractmethod
    def get_supported_categories(self) -> List[str]:
        """
        Return list of keyword categories this extractor can identify.

        Returns:
            List of category names (e.g., ['characteristic', 'diagnosis', 'anatomy'])
        """
        pass

    def validate_file(self, file_path: str) -> Tuple[bool, Optional[str]]:
        """
        Validate that file exists and is readable.

        Args:
            file_path: Path to file

        Returns:
            Tuple of (is_valid, error_message)
        """
        from pathlib import Path

        path = Path(file_path)

        if not path.exists():
            return False, f"File not found: {file_path}"

        if not path.is_file():
            return False, f"Not a file: {file_path}"

        if path.stat().st_size == 0:
            return False, f"File is empty: {file_path}"

        return True, None
