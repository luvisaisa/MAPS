"""
Parse Case Service

Business logic for parse case detection and management.
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import xml.etree.ElementTree as ET

from ...parser import detect_parse_case, get_expected_attributes_for_case
from ..models.responses import ParseCaseInfo, ParseCaseStatsResponse, DetectResponse, StructureAnalysis


class ParseCaseService:
    """Service for parse case operations"""

    def __init__(self, db: Optional[Session] = None):
        self.db = db

    def get_all_parse_cases(self) -> List[ParseCaseInfo]:
        """Get all recognized parse cases"""
        parse_cases = [
            ParseCaseInfo(
                name="Complete_Attributes",
                description="Full radiologist data with all attributes",
                fields=["confidence", "subtlety", "obscuration", "reason"],
                required_fields=["nodule_id", "radiologist_id"],
                example_count=None
            ),
            ParseCaseInfo(
                name="LIDC_Multi_Session_4",
                description="LIDC format with 4 radiologist readings",
                fields=["malignancy", "subtlety", "calcification", "sphericity", "margin",
                       "lobulation", "spiculation", "texture", "internal_structure"],
                required_fields=["study_instance_uid"],
                example_count=None
            ),
            ParseCaseInfo(
                name="LIDC_Multi_Session_3",
                description="LIDC format with 3 radiologist readings",
                fields=["malignancy", "subtlety", "calcification", "sphericity", "margin",
                       "lobulation", "spiculation", "texture", "internal_structure"],
                required_fields=["study_instance_uid"],
                example_count=None
            ),
            ParseCaseInfo(
                name="Core_Attributes_Only",
                description="Essential attributes without reason",
                fields=["confidence", "subtlety", "obscuration"],
                required_fields=["nodule_id"],
                example_count=None
            )
        ]
        return parse_cases

    def get_parse_case(self, name: str) -> Optional[ParseCaseInfo]:
        """Get specific parse case by name"""
        all_cases = self.get_all_parse_cases()
        for case in all_cases:
            if case.name == name:
                return case
        return None

    def detect_from_content(
        self,
        content: bytes,
        filename: str,
        analyze_structure: bool = True
    ) -> DetectResponse:
        """Detect parse case from file content"""
        try:
            # Parse XML
            root = ET.fromstring(content)

            # Detect parse case using existing function
            parse_case = detect_parse_case(root)

            # Structure analysis
            structure = None
            if analyze_structure:
                session_count = len(root.findall(".//readingSession"))
                unblinded = len(root.findall(".//unblindedReadNodule")) > 0
                structure = StructureAnalysis(
                    root_element=root.tag,
                    session_count=session_count,
                    has_unblinded_reads=unblinded,
                    element_count=len(list(root.iter())),
                    depth=self._get_tree_depth(root)
                )

            # Get expected fields
            expected_attrs = get_expected_attributes_for_case(parse_case)

            return DetectResponse(
                detected_parse_case=parse_case,
                confidence=1.0 if parse_case != "Unknown" else 0.0,
                file_type="XML",
                structure_analysis=structure,
                possible_fields=expected_attrs
            )
        except Exception as e:
            raise ValueError(f"Parse case detection failed: {e}")

    def get_statistics(self) -> ParseCaseStatsResponse:
        """Get parse case statistics from database"""
        if not self.db:
            raise ValueError("Database session required")

        # Query database for statistics
        query = """
        SELECT
            COUNT(*) as total_documents,
            parse_case,
            COUNT(*) as count
        FROM documents
        GROUP BY parse_case
        """

        result = self.db.execute(query)
        rows = result.fetchall()

        total = sum(row[2] for row in rows)
        distribution = {row[1]: row[2] for row in rows}

        return ParseCaseStatsResponse(
            total_documents=total,
            parse_case_distribution=distribution,
            last_updated=datetime.utcnow()
        )

    def _get_tree_depth(self, element, depth=0) -> int:
        """Get XML tree depth"""
        if len(element) == 0:
            return depth
        return max(self._get_tree_depth(child, depth + 1) for child in element)
