"""
Base Structure Detector Interface

Abstract base class for document structure/parse case detection.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
import hashlib


class BaseStructureDetector(ABC):
    """
    Abstract base class for structure/parse case detectors.

    All detectors must implement:
    - can_detect(): Check if this detector handles the file format
    - detect_structure(): Detect document structure and parse case
    - get_structure_signature(): Generate unique signature for caching

    Usage:
        class CSVStructureDetector(BaseStructureDetector):
            def can_detect(self, file_path: str) -> bool:
                return file_path.endswith('.csv')

            def detect_structure(self, file_path: str) -> Dict[str, Any]:
                return {
                    "parse_case": "csv_tabular",
                    "confidence": 0.95,
                    "detected_fields": ["col1", "col2"]
                }
    """

    @abstractmethod
    def can_detect(self, file_path: str) -> bool:
        """
        Check if this detector handles this file format.

        Args:
            file_path: Path to file

        Returns:
            True if this detector can analyze this file, False otherwise
        """
        pass

    @abstractmethod
    def detect_structure(self, file_path: str) -> Dict[str, Any]:
        """
        Detect document structure and parse case.

        Args:
            file_path: Path to file to analyze

        Returns:
            Dictionary with structure information:
            {
                "parse_case": "case_name",
                "confidence": 0.95,  # 0-1 confidence score
                "format_version": "1.0",
                "detected_fields": ["field1", "field2"],
                "metadata": {
                    "field_count": 10,
                    "has_entities": True,
                    ...
                }
            }

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file cannot be analyzed
        """
        pass

    def get_structure_signature(self, file_path: str) -> str:
        """
        Generate unique signature for caching.

        Default implementation uses file path + modification time.
        Override for custom signature logic.

        Args:
            file_path: Path to file

        Returns:
            Unique signature string
        """
        from pathlib import Path

        path = Path(file_path)
        if not path.exists():
            return ""

        mtime = path.stat().st_mtime
        content = f"{file_path}:{mtime}"
        return hashlib.md5(content.encode()).hexdigest()

    def validate_confidence(self, confidence: float) -> float:
        """
        Validate confidence score is in range [0, 1].

        Args:
            confidence: Confidence score

        Returns:
            Clamped confidence value
        """
        return max(0.0, min(1.0, confidence))
