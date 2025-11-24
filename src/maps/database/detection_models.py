"""
Detection Details SQLAlchemy Models
ORM models for parse case detection analysis storage
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import uuid4

from sqlalchemy import (
    Column, String, Integer, DateTime, Text, ForeignKey, CheckConstraint, Index, Numeric
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .models import Base, JSONBCompat, UUIDCompat


class DetectionDetails(Base):
    """
    Store detailed parse case detection analysis

    Tracks expected attributes, detected attributes, and match metrics
    for each file's structure detection process.
    """
    __tablename__ = 'detection_details'

    # Primary key
    id = Column(UUIDCompat, primary_key=True, default=uuid4)

    # References
    queue_item_id = Column(String(50), index=True, nullable=True)  # Reference to approval queue
    document_id = Column(UUIDCompat, ForeignKey('documents.id', ondelete='CASCADE'), index=True, nullable=True)

    # Detection results
    parse_case = Column(String(255), nullable=False, index=True)
    confidence = Column(
        Numeric(5, 4),
        nullable=False,
        index=True,
        doc="Confidence score from 0.0000 to 1.0000"
    )

    # Attribute analysis (stored as JSONB for flexibility)
    expected_attributes = Column(
        JSONBCompat,
        nullable=False,
        default=[],
        doc="JSON array of attributes expected for this parse case"
    )
    detected_attributes = Column(
        JSONBCompat,
        nullable=False,
        default=[],
        doc="JSON array of attributes found in the source document"
    )
    missing_attributes = Column(
        JSONBCompat,
        nullable=False,
        default=[],
        doc="JSON array of expected attributes not found"
    )

    # Match metrics
    match_percentage = Column(
        Numeric(5, 2),
        nullable=False,
        doc="Percentage of expected attributes found (0.00-100.00)"
    )
    total_expected = Column(Integer, nullable=False, default=0)
    total_detected = Column(Integer, nullable=False, default=0)

    # Field-by-field analysis
    field_analysis = Column(
        JSONBCompat,
        default=[],
        doc="JSON array with detailed field-level analysis"
    )

    # Detection metadata
    detector_type = Column(String(100), default='XMLStructureDetector')
    detector_version = Column(String(50), default='1.0.0')
    detection_method = Column(
        String(255),
        doc="e.g., 'keyword_matching', 'structure_analysis'"
    )

    # Confidence breakdown
    confidence_breakdown = Column(
        JSONBCompat,
        default={},
        doc="JSON object with detailed confidence scoring factors"
    )

    # Timestamps
    detected_at = Column(DateTime(timezone=True), default=func.now(), index=True)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    # Constraints
    __table_args__ = (
        CheckConstraint(
            'confidence >= 0 AND confidence <= 1',
            name='check_confidence_range'
        ),
        CheckConstraint(
            'match_percentage >= 0 AND match_percentage <= 100',
            name='check_match_percentage_range'
        ),
        Index('idx_detection_confidence', 'confidence'),
        Index('idx_detection_match_percentage', 'match_percentage'),
        Index('idx_detection_detected_at', 'detected_at'),
    )

    # Relationships
    document = relationship(
        "Document",
        foreign_keys=[document_id],
        backref="detection_details"
    )

    def __repr__(self):
        return (
            f"<DetectionDetails(id={self.id}, parse_case={self.parse_case}, "
            f"confidence={self.confidence}, match={self.match_percentage}%)>"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            'id': str(self.id),
            'queue_item_id': self.queue_item_id,
            'document_id': str(self.document_id) if self.document_id else None,
            'parse_case': self.parse_case,
            'confidence': float(self.confidence),
            'expected_attributes': self.expected_attributes,
            'detected_attributes': self.detected_attributes,
            'missing_attributes': self.missing_attributes,
            'match_percentage': float(self.match_percentage),
            'total_expected': self.total_expected,
            'total_detected': self.total_detected,
            'field_analysis': self.field_analysis,
            'detector_type': self.detector_type,
            'detector_version': self.detector_version,
            'detection_method': self.detection_method,
            'confidence_breakdown': self.confidence_breakdown,
            'detected_at': self.detected_at.isoformat() if self.detected_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_detection_result(
        cls,
        detection_result: Dict[str, Any],
        queue_item_id: Optional[str] = None,
        document_id: Optional[str] = None
    ) -> 'DetectionDetails':
        """
        Create DetectionDetails from detector output

        Args:
            detection_result: Dictionary from detector.detect_structure()
            queue_item_id: Optional queue item reference
            document_id: Optional document reference

        Returns:
            DetectionDetails instance
        """
        expected = detection_result.get('expected_attributes', [])
        detected = detection_result.get('detected_attributes', [])

        total_expected = len(expected)
        total_detected = len([attr for attr in detected if attr.get('found', False)])
        match_percentage = (total_detected / total_expected * 100) if total_expected > 0 else 0.0

        # Calculate missing attributes
        detected_names = {attr.get('name') for attr in detected if attr.get('found')}
        missing = [attr for attr in expected if attr.get('name') not in detected_names]

        return cls(
            queue_item_id=queue_item_id,
            document_id=document_id,
            parse_case=detection_result.get('parse_case'),
            confidence=detection_result.get('confidence', 0.0),
            expected_attributes=expected,
            detected_attributes=detected,
            missing_attributes=missing,
            match_percentage=match_percentage,
            total_expected=total_expected,
            total_detected=total_detected,
            field_analysis=detection_result.get('field_analysis', []),
            detector_type=detection_result.get('metadata', {}).get('detector', 'XMLStructureDetector'),
            detection_method=detection_result.get('metadata', {}).get('method'),
            confidence_breakdown=detection_result.get('confidence_breakdown', {})
        )


class DetectionSummary:
    """
    View model for detection summary queries
    Not a database table, used for API responses
    """

    def __init__(self, detection: DetectionDetails, document_info: Optional[Dict] = None):
        self.id = str(detection.id)
        self.queue_item_id = detection.queue_item_id
        self.document_id = str(detection.document_id) if detection.document_id else None
        self.parse_case = detection.parse_case
        self.confidence = float(detection.confidence)
        self.match_percentage = float(detection.match_percentage)
        self.total_expected = detection.total_expected
        self.total_detected = detection.total_detected
        self.total_missing = detection.total_expected - detection.total_detected
        self.detector_type = detection.detector_type
        self.detected_at = detection.detected_at.isoformat() if detection.detected_at else None

        # Extract attribute names for easy display
        self.expected_attr_names = [attr.get('name') for attr in detection.expected_attributes]
        self.detected_attr_names = [attr.get('name') for attr in detection.detected_attributes if attr.get('found')]
        self.missing_attr_names = [attr.get('name') for attr in detection.missing_attributes]

        # Optional document info
        if document_info:
            self.document_filename = document_info.get('filename')
            self.document_status = document_info.get('status')
            self.file_type = document_info.get('file_type')

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        result = {
            'id': self.id,
            'queue_item_id': self.queue_item_id,
            'document_id': self.document_id,
            'parse_case': self.parse_case,
            'confidence': self.confidence,
            'match_percentage': self.match_percentage,
            'total_expected': self.total_expected,
            'total_detected': self.total_detected,
            'total_missing': self.total_missing,
            'detector_type': self.detector_type,
            'detected_at': self.detected_at,
            'expected_attr_names': self.expected_attr_names,
            'detected_attr_names': self.detected_attr_names,
            'missing_attr_names': self.missing_attr_names,
        }

        # Add document info if available
        if hasattr(self, 'document_filename'):
            result['document_filename'] = self.document_filename
            result['document_status'] = self.document_status
            result['file_type'] = self.file_type

        return result
