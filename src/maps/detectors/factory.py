"""
Structure Detector Factory

Auto-selects appropriate detector based on file format.
"""

from typing import List, Optional
import logging

from .base import BaseStructureDetector

logger = logging.getLogger(__name__)


class DetectorFactory:
    """
    Factory for automatically selecting the right structure detector.

    Usage:
        factory = DetectorFactory()
        detector = factory.get_detector("data.xml")
        structure = detector.detect_structure("data.xml")
    """

    def __init__(self):
        """Initialize factory with default detectors."""
        self.detectors: List[BaseStructureDetector] = []
        self._register_default_detectors()

    def _register_default_detectors(self):
        """Register built-in detectors (XML, etc.)."""
        try:
            from .xml_structure_detector import XMLStructureDetector
            self.detectors.append(XMLStructureDetector())
            logger.info("Registered XMLStructureDetector")
        except ImportError as e:
            logger.warning(f"Could not load XMLStructureDetector: {e}")

        # Future detectors will auto-register here:
        # - CSVStructureDetector
        # - JSONStructureDetector
        # - DICOMStructureDetector

    def get_detector(self, file_path: str) -> Optional[BaseStructureDetector]:
        """
        Get the appropriate detector for the given file.

        Args:
            file_path: Path to file

        Returns:
            BaseStructureDetector instance or None if no detector found
        """
        for detector in self.detectors:
            if detector.can_detect(file_path):
                logger.info(f"Selected {detector.__class__.__name__} for {file_path}")
                return detector

        logger.warning(f"No detector found for {file_path}")
        return None

    def register_detector(self, detector: BaseStructureDetector):
        """
        Register a custom detector (plugin system).

        Args:
            detector: Custom BaseStructureDetector implementation
        """
        if not isinstance(detector, BaseStructureDetector):
            raise TypeError(f"Detector must inherit from BaseStructureDetector, got {type(detector)}")

        self.detectors.append(detector)
        logger.info(f"Registered custom detector: {detector.__class__.__name__}")

    def list_detectors(self) -> List[str]:
        """Return list of registered detector names."""
        return [detector.__class__.__name__ for detector in self.detectors]


# Singleton instance
_factory_instance: Optional[DetectorFactory] = None


def get_detector_factory() -> DetectorFactory:
    """Get singleton factory instance."""
    global _factory_instance
    if _factory_instance is None:
        _factory_instance = DetectorFactory()
    return _factory_instance
