"""
PyLIDC Service

Business logic for PYLIDC dataset integration.
Uses ra_d_ps.adapters.pylidc_adapter.
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
import time

try:
    import pylidc as pl
    PYLIDC_AVAILABLE = True
except ImportError:
    PYLIDC_AVAILABLE = False
    pl = None

from ...adapters.pylidc_adapter import PyLIDCAdapter
from ..models.responses import ParseResponse, DocumentResponse
from datetime import datetime


class PyLIDCService:
    """Service for PYLIDC dataset operations"""

    def __init__(self, db: Optional[Session] = None):
        self.db = db
        if not PYLIDC_AVAILABLE:
            raise ImportError("pylidc library not available. Install with: pip install pylidc")

    def list_scans(self, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """List available PYLIDC scans"""
        try:
            # Query scans from pylidc
            query = pl.query(pl.Scan)
            total = query.count()

            scans = query.offset(offset).limit(limit).all()

            scan_list = []
            for scan in scans:
                scan_list.append({
                    "patient_id": scan.patient_id,
                    "study_instance_uid": scan.study_instance_uid,
                    "series_instance_uid": scan.series_instance_uid,
                    "slice_thickness": scan.slice_thickness,
                    "pixel_spacing": scan.pixel_spacing,
                    "annotation_count": len(scan.annotations)
                })

            return {
                "scans": scan_list,
                "total": total,
                "limit": limit,
                "offset": offset
            }
        except Exception as e:
            return {
                "scans": [],
                "total": 0,
                "error": str(e)
            }

    def get_scan(self, patient_id: str) -> Optional[DocumentResponse]:
        """Get specific PYLIDC scan data"""
        try:
            # Query scan by patient ID
            scans = pl.query(pl.Scan).filter(pl.Scan.patient_id == patient_id).all()

            if not scans:
                return None

            scan = scans[0]  # Get first scan for patient

            # Convert to canonical format
            adapter = PyLIDCAdapter()
            canonical_doc = adapter.scan_to_canonical(scan, include_annotations=True)

            return DocumentResponse(
                document_id=scan.series_instance_uid,
                source_file=f"pylidc://{patient_id}",
                parse_case="LIDC_PYLIDC_Import",
                created_at=datetime.utcnow(),
                content=canonical_doc.dict(),
                metadata={
                    "patient_id": patient_id,
                    "study_instance_uid": scan.study_instance_uid,
                    "slice_count": scan.slice_thickness,
                    "annotation_count": len(scan.annotations)
                }
            )
        except Exception as e:
            return None

    async def import_scan(
        self,
        patient_id: Optional[str],
        extract_keywords: bool,
        detect_parse_case: bool
    ) -> ParseResponse:
        """Import PYLIDC scan to Supabase"""
        start_time = time.time()

        try:
            # Query scan
            if patient_id:
                scans = pl.query(pl.Scan).filter(pl.Scan.patient_id == patient_id).all()
            else:
                scans = pl.query(pl.Scan).limit(1).all()

            if not scans:
                return ParseResponse(
                    status="error",
                    errors=["No scans found"],
                    processing_time_ms=(time.time() - start_time) * 1000
                )

            scan = scans[0]

            # Convert to canonical
            adapter = PyLIDCAdapter()
            canonical_doc = adapter.scan_to_canonical(scan, include_annotations=True)

            # TODO: Insert to database
            document_id = None
            if self.db:
                document_id = scan.series_instance_uid

            # TODO: Extract keywords if requested
            keywords_count = 0
            if extract_keywords:
                keywords_count = 0  # Placeholder

            processing_time = (time.time() - start_time) * 1000

            return ParseResponse(
                status="success",
                document_id=document_id,
                parse_case="LIDC_PYLIDC_Import",
                keywords_extracted=keywords_count,
                processing_time_ms=processing_time
            )
        except Exception as e:
            return ParseResponse(
                status="error",
                errors=[str(e)],
                processing_time_ms=(time.time() - start_time) * 1000
            )

    async def import_batch(
        self,
        limit: Optional[int],
        extract_keywords: bool,
        detect_parse_case: bool
    ) -> Dict[str, Any]:
        """Import multiple PYLIDC scans in batch"""
        start_time = time.time()

        try:
            # Query multiple scans
            query = pl.query(pl.Scan)
            if limit:
                query = query.limit(limit)

            scans = query.all()

            imported_count = 0
            failed_count = 0
            errors = []

            adapter = PyLIDCAdapter()

            for scan in scans:
                try:
                    canonical_doc = adapter.scan_to_canonical(scan, include_annotations=True)

                    # TODO: Insert to database
                    if self.db:
                        pass  # Insert logic here

                    imported_count += 1
                except Exception as e:
                    failed_count += 1
                    errors.append(f"{scan.patient_id}: {str(e)}")

            processing_time = (time.time() - start_time) * 1000

            return {
                "status": "completed",
                "total_scans": len(scans),
                "imported": imported_count,
                "failed": failed_count,
                "processing_time_ms": processing_time,
                "errors": errors if errors else None
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "processing_time_ms": (time.time() - start_time) * 1000
            }

    def get_annotations(self, scan_id: str) -> Dict[str, Any]:
        """Get annotations for a specific scan"""
        try:
            # Query scan
            scans = pl.query(pl.Scan).filter(pl.Scan.series_instance_uid == scan_id).all()

            if not scans:
                return {"annotations": [], "error": "Scan not found"}

            scan = scans[0]
            annotations = scan.annotations

            annotation_list = []
            for ann in annotations:
                annotation_list.append({
                    "annotation_id": ann.id,
                    "radiologist_id": ann._nodule_id,
                    "malignancy": ann.malignancy,
                    "subtlety": ann.subtlety,
                    "calcification": ann.calcification,
                    "sphericity": ann.sphericity,
                    "margin": ann.margin,
                    "lobulation": ann.lobulation,
                    "spiculation": ann.spiculation,
                    "texture": ann.texture,
                    "internal_structure": ann.internal_structure,
                    "contour_count": len(ann.contours)
                })

            return {
                "scan_id": scan_id,
                "patient_id": scan.patient_id,
                "annotations": annotation_list,
                "total": len(annotation_list)
            }
        except Exception as e:
            return {
                "annotations": [],
                "error": str(e)
            }
