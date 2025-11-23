"""
Enhanced Document Repository with Parse Case & Keyword Integration

Extends DocumentRepository to integrate:
- Parse case detection and tracking
- Automatic keyword extraction
- Schema-agnostic case identification

Usage:
    from ra_d_ps.database.enhanced_document_repository import EnhancedDocumentRepository

    repo = EnhancedDocumentRepository()

    # Import with automatic parse case detection and keyword extraction
    doc, content = repo.insert_canonical_document_enhanced(
        canonical_doc,
        source_file="pylidc://LIDC-0001",
        detect_parse_case=True,
        extract_keywords=True
    )
"""

import logging
from typing import Optional, List, Tuple, Dict, Any
from uuid import UUID
from datetime import datetime

from .document_repository import DocumentRepository
from .models import Document, DocumentContent
from ..schemas.canonical import RadiologyCanonicalDocument

# Optional imports for enhanced features
try:
    from .parse_case_repository import ParseCaseRepository
    from .keyword_repository import KeywordRepository
    PARSE_CASE_AVAILABLE = True
except ImportError:
    PARSE_CASE_AVAILABLE = False

try:
    from ..keyword_search_engine import KeywordSearchEngine
    KEYWORD_ENGINE_AVAILABLE = True
except ImportError:
    KEYWORD_ENGINE_AVAILABLE = False

logger = logging.getLogger(__name__)


class EnhancedDocumentRepository(DocumentRepository):
    """
    Enhanced repository with parse case detection and keyword extraction

    Extends DocumentRepository to automatically:
    1. Detect and record which parse case (schema) was used
    2. Extract keywords from canonical documents
    3. Link documents to parse cases for schema tracking
    4. Build keyword indexes for search
    """

    def __init__(
        self,
        connection_string: Optional[str] = None,
        enable_parse_case_tracking: bool = True,
        enable_keyword_extraction: bool = True
    ):
        """
        Initialize enhanced repository

        Args:
            connection_string: Database connection string
            enable_parse_case_tracking: Enable parse case detection/tracking
            enable_keyword_extraction: Enable automatic keyword extraction
        """
        super().__init__(connection_string)

        self.parse_case_tracking_enabled = enable_parse_case_tracking and PARSE_CASE_AVAILABLE
        self.keyword_extraction_enabled = enable_keyword_extraction and KEYWORD_ENGINE_AVAILABLE

        # Initialize sub-repositories
        if self.parse_case_tracking_enabled:
            self.parse_case_repo = ParseCaseRepository(connection_string)
            logger.info("Parse case tracking enabled")
        else:
            self.parse_case_repo = None
            logger.warning("Parse case tracking disabled - module not available")

        if self.keyword_extraction_enabled:
            self.keyword_repo = KeywordRepository(
                database=self.engine.url.database,
                host=self.engine.url.host,
                port=self.engine.url.port,
                user=self.engine.url.username,
                password=self.engine.url.password
            )
            logger.info("Keyword extraction enabled")
        else:
            self.keyword_repo = None
            logger.warning("Keyword extraction disabled - module not available")

    def detect_parse_case_from_canonical(
        self,
        canonical_doc: RadiologyCanonicalDocument
    ) -> Optional[str]:
        """
        Detect which parse case was used based on canonical document structure

        Args:
            canonical_doc: RadiologyCanonicalDocument instance

        Returns:
            Parse case name (e.g., "LIDC_Single_Session", "LIDC_Multi_Session_4")
        """
        if not self.parse_case_tracking_enabled:
            return None

        try:
            # Analyze document structure
            num_nodules = len(canonical_doc.nodules) if canonical_doc.nodules else 0
            num_readings = len(canonical_doc.radiologist_readings) if canonical_doc.radiologist_readings else 0

            # Determine parse case based on structure
            if num_nodules > 0:
                # Check how many radiologists per nodule
                first_nodule = canonical_doc.nodules[0]
                if isinstance(first_nodule, dict):
                    num_radiologists = first_nodule.get('num_radiologists', 0)
                    if num_radiologists == 1:
                        return "LIDC_Single_Session"
                    elif num_radiologists == 2:
                        return "LIDC_Multi_Session_2"
                    elif num_radiologists == 3:
                        return "LIDC_Multi_Session_3"
                    elif num_radiologists == 4:
                        return "LIDC_Multi_Session_4"

            elif num_readings > 0:
                return "LIDC_Individual_Readings"

            # Default
            return "Complete_Attributes"

        except Exception as e:
            logger.error(f"Failed to detect parse case: {e}")
            return None

    def extract_keywords_from_canonical(
        self,
        canonical_doc: RadiologyCanonicalDocument,
        source_file: str
    ) -> List[Dict[str, Any]]:
        """
        Extract keywords from canonical document

        Args:
            canonical_doc: RadiologyCanonicalDocument instance
            source_file: Source file identifier

        Returns:
            List of extracted keywords with metadata
        """
        if not self.keyword_extraction_enabled:
            return []

        try:
            keywords = []

            # Extract from metadata
            if canonical_doc.document_metadata:
                meta = canonical_doc.document_metadata
                if meta.title:
                    keywords.extend(self._extract_medical_terms(meta.title))
                if meta.description:
                    keywords.extend(self._extract_medical_terms(meta.description))

            # Extract from radiology-specific fields
            if hasattr(canonical_doc, 'modality') and canonical_doc.modality:
                keywords.append({
                    'keyword': canonical_doc.modality,
                    'category': 'modality',
                    'source_file': source_file
                })

            # Extract from nodule data
            if canonical_doc.nodules:
                for nodule in canonical_doc.nodules:
                    if isinstance(nodule, dict):
                        # Extract characteristics as keywords
                        for rad_id, rad_data in nodule.get('radiologists', {}).items():
                            if isinstance(rad_data, dict):
                                for char_name, char_value in rad_data.items():
                                    if char_value and char_name not in ['nodule_id', 'radiologist_id']:
                                        keywords.append({
                                            'keyword': f"{char_name}_{char_value}",
                                            'category': 'characteristic',
                                            'source_file': source_file,
                                            'context': f"Nodule characteristic: {char_name}"
                                        })

            return keywords

        except Exception as e:
            logger.error(f"Failed to extract keywords: {e}")
            return []

    def _extract_medical_terms(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract medical terms from text

        Args:
            text: Text to analyze

        Returns:
            List of medical term keywords
        """
        # Simple implementation - can be enhanced with NLP
        medical_terms = []
        common_terms = [
            'nodule', 'lesion', 'opacity', 'malignancy', 'calcification',
            'spiculation', 'margin', 'lobulation', 'texture', 'CT', 'lung'
        ]

        text_lower = text.lower()
        for term in common_terms:
            if term.lower() in text_lower:
                medical_terms.append({
                    'keyword': term,
                    'category': 'medical_term'
                })

        return medical_terms

    def store_keywords(
        self,
        keywords: List[Dict[str, Any]],
        document_id: UUID
    ) -> int:
        """
        Store extracted keywords in database

        Args:
            keywords: List of keyword dictionaries
            document_id: UUID of parent document

        Returns:
            Number of keywords stored
        """
        if not self.keyword_extraction_enabled or not keywords:
            return 0

        try:
            stored_count = 0

            for kw_data in keywords:
                keyword_text = kw_data.get('keyword')
                if not keyword_text:
                    continue

                # Add or get keyword
                keyword = self.keyword_repo.add_keyword(
                    keyword_text=keyword_text,
                    category=kw_data.get('category', 'general'),
                    normalized_form=keyword_text.lower()
                )

                # Add keyword source (link to document)
                self.keyword_repo.add_keyword_source(
                    keyword_id=keyword.keyword_id,
                    source_type='canonical_document',
                    source_file=kw_data.get('source_file', str(document_id)),
                    sector='radiology',
                    context=kw_data.get('context')
                )

                stored_count += 1

            logger.info(f"Stored {stored_count} keywords for document {document_id}")
            return stored_count

        except Exception as e:
            logger.error(f"Failed to store keywords: {e}")
            return 0

    def record_parse_case_detection(
        self,
        file_path: str,
        parse_case_name: str,
        detection_duration_ms: Optional[int] = None
    ):
        """
        Record parse case detection event

        Args:
            file_path: Source file path
            parse_case_name: Name of detected parse case
            detection_duration_ms: Time taken to detect (milliseconds)
        """
        if not self.parse_case_tracking_enabled:
            return

        try:
            # Get parse case ID
            parse_case = self.parse_case_repo.get_parse_case_by_name(parse_case_name)
            if not parse_case:
                logger.warning(f"Parse case '{parse_case_name}' not found in database")
                return

            # Record detection
            self.parse_case_repo.record_detection(
                file_path=file_path,
                parse_case_id=parse_case.id,
                detection_metadata={'automatic': True},
                detection_duration_ms=detection_duration_ms
            )

        except Exception as e:
            logger.error(f"Failed to record parse case detection: {e}")

    def insert_canonical_document_enhanced(
        self,
        canonical_doc: RadiologyCanonicalDocument,
        source_file: str = "pylidc://",
        uploaded_by: Optional[str] = None,
        tags: Optional[List[str]] = None,
        batch_id: Optional[UUID] = None,
        detect_parse_case: bool = True,
        extract_keywords: bool = True
    ) -> Tuple[Document, DocumentContent, Optional[str], int]:
        """
        Insert canonical document with enhanced tracking

        Args:
            canonical_doc: RadiologyCanonicalDocument instance
            source_file: Source file identifier
            uploaded_by: User who uploaded
            tags: Optional tags
            batch_id: Optional batch identifier
            detect_parse_case: Whether to detect and record parse case
            extract_keywords: Whether to extract and store keywords

        Returns:
            Tuple of (Document, DocumentContent, parse_case_name, keyword_count)
        """
        start_time = datetime.now()

        # Detect parse case
        parse_case_name = None
        if detect_parse_case and self.parse_case_tracking_enabled:
            parse_case_name = self.detect_parse_case_from_canonical(canonical_doc)
            logger.info(f"Detected parse case: {parse_case_name}")

        # Insert document (base implementation)
        doc, content = self.insert_canonical_document(
            canonical_doc,
            source_file=source_file,
            uploaded_by=uploaded_by,
            tags=tags,
            batch_id=batch_id
        )

        # Record parse case detection
        if parse_case_name:
            detection_time = int((datetime.now() - start_time).total_seconds() * 1000)
            self.record_parse_case_detection(
                file_path=source_file,
                parse_case_name=parse_case_name,
                detection_duration_ms=detection_time
            )

        # Extract and store keywords
        keyword_count = 0
        if extract_keywords and self.keyword_extraction_enabled:
            keywords = self.extract_keywords_from_canonical(canonical_doc, source_file)
            keyword_count = self.store_keywords(keywords, doc.id)

        logger.info(
            f"Enhanced insert complete: doc_id={doc.id}, "
            f"parse_case={parse_case_name}, keywords={keyword_count}"
        )

        return doc, content, parse_case_name, keyword_count

    def batch_insert_canonical_documents_enhanced(
        self,
        canonical_docs: List[RadiologyCanonicalDocument],
        source_files: List[str],
        uploaded_by: Optional[str] = None,
        tags: Optional[List[str]] = None,
        batch_id: Optional[UUID] = None,
        detect_parse_case: bool = True,
        extract_keywords: bool = True,
        progress_callback=None
    ) -> List[Tuple[Document, DocumentContent, Optional[str], int]]:
        """
        Batch insert with enhanced tracking

        Args:
            canonical_docs: List of RadiologyCanonicalDocument instances
            source_files: List of source file identifiers
            uploaded_by: User who uploaded
            tags: Tags to apply to all documents
            batch_id: Batch identifier
            detect_parse_case: Whether to detect parse cases
            extract_keywords: Whether to extract keywords
            progress_callback: Optional callback(current, total)

        Returns:
            List of (Document, DocumentContent, parse_case_name, keyword_count) tuples
        """
        if len(canonical_docs) != len(source_files):
            raise ValueError("canonical_docs and source_files must have same length")

        results = []
        total = len(canonical_docs)

        for i, (canonical_doc, source_file) in enumerate(zip(canonical_docs, source_files)):
            try:
                result = self.insert_canonical_document_enhanced(
                    canonical_doc,
                    source_file=source_file,
                    uploaded_by=uploaded_by,
                    tags=tags,
                    batch_id=batch_id,
                    detect_parse_case=detect_parse_case,
                    extract_keywords=extract_keywords
                )
                results.append(result)

                if progress_callback:
                    progress_callback(i + 1, total)

            except Exception as e:
                logger.error(f"Failed to insert document {i}/{total}: {e}")
                continue

        # Log batch statistics
        parse_cases = {}
        total_keywords = 0
        for _, _, parse_case, kw_count in results:
            if parse_case:
                parse_cases[parse_case] = parse_cases.get(parse_case, 0) + 1
            total_keywords += kw_count

        logger.info(
            f"Batch insert complete: {len(results)}/{total} documents, "
            f"parse_cases={parse_cases}, total_keywords={total_keywords}"
        )

        return results

    def get_document_statistics_enhanced(self) -> Dict[str, Any]:
        """
        Get enhanced statistics including parse cases and keywords

        Returns:
            Dictionary with comprehensive statistics
        """
        stats = self.get_statistics()  # Base statistics

        # Add parse case statistics
        if self.parse_case_tracking_enabled:
            try:
                parse_case_stats = self.parse_case_repo.get_detection_statistics()
                stats['parse_cases'] = parse_case_stats
            except Exception as e:
                logger.error(f"Failed to get parse case stats: {e}")
                stats['parse_cases'] = {}

        # Add keyword statistics
        if self.keyword_extraction_enabled:
            try:
                with self.keyword_repo._get_session() as session:
                    from .keyword_models import Keyword, KeywordSource
                    total_keywords = session.query(Keyword).count()
                    total_sources = session.query(KeywordSource).count()

                    stats['keywords'] = {
                        'total_keywords': total_keywords,
                        'total_keyword_sources': total_sources
                    }
            except Exception as e:
                logger.error(f"Failed to get keyword stats: {e}")
                stats['keywords'] = {}

        return stats
