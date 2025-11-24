"""
PyLIDC Service

Business logic for PYLIDC dataset integration.
Uses ra_d_ps.adapters.pylidc_adapter.
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
import time
import hashlib
import json
from functools import lru_cache
from datetime import datetime, timedelta

try:
    import pylidc as pl
    PYLIDC_AVAILABLE = True
except ImportError:
    PYLIDC_AVAILABLE = False
    pl = None

from ...adapters.pylidc_adapter import PyLIDCAdapter
from ..models.responses import ParseResponse, DocumentResponse
from ..config import settings

# In-memory cache for PYLIDC metadata
_pylidc_cache: Dict[str, tuple[Any, datetime]] = {}
_scan_metadata_cache: Dict[str, Dict[str, Any]] = {}


class PyLIDCService:
    """Service for PYLIDC dataset operations"""

    def __init__(self, db: Optional[Session] = None):
        self.db = db
        if not PYLIDC_AVAILABLE:
            raise ImportError("pylidc library not available. Install with: pip install pylidc")

    @staticmethod
    def _get_cache_key(prefix: str, **kwargs) -> str:
        """Generate cache key from parameters"""
        params = json.dumps(kwargs, sort_keys=True)
        return f"{prefix}:{hashlib.md5(params.encode()).hexdigest()}"

    @staticmethod
    def _get_cached(key: str) -> Optional[Any]:
        """Get cached value if not expired"""
        if key in _pylidc_cache:
            value, timestamp = _pylidc_cache[key]
            if datetime.utcnow() - timestamp < timedelta(seconds=settings.PYLIDC_CACHE_TTL):
                return value
            # Remove expired entry
            del _pylidc_cache[key]
        return None

    @staticmethod
    def _set_cache(key: str, value: Any):
        """Set cache value with timestamp"""
        _pylidc_cache[key] = (value, datetime.utcnow())

    @staticmethod
    def _get_scan_metadata(scan) -> Dict[str, Any]:
        """Extract and cache scan metadata to avoid repeated DICOM access"""
        scan_id = scan.series_instance_uid
        
        if scan_id in _scan_metadata_cache:
            return _scan_metadata_cache[scan_id]
        
        try:
            slice_count = len(scan.slice_zvals) if scan.slice_zvals else 0
        except:
            slice_count = 0
        
        annotations = scan.annotations
        annotation_count = len(annotations)
        
        metadata = {
            "scan_id": scan_id,
            "patient_id": scan.patient_id,
            "study_instance_uid": scan.study_instance_uid,
            "series_instance_uid": scan_id,
            "slice_thickness": scan.slice_thickness or 0,
            "slice_spacing": scan.slice_spacing,
            "slice_count": slice_count,
            "pixel_spacing": scan.pixel_spacing,
            "contrast_used": scan.contrast_used,
            "annotation_count": annotation_count,
            "has_nodules": annotation_count > 0,
            "annotations": annotations  # Keep reference for characteristic filtering
        }
        
        _scan_metadata_cache[scan_id] = metadata
        return metadata

    def list_scans(
        self,
        page: int = 1,
        page_size: int = 30,
        patient_id: Optional[str] = None,
        min_slices: Optional[int] = None,
        max_slices: Optional[int] = None,
        min_thickness: Optional[float] = None,
        max_thickness: Optional[float] = None,
        min_spacing: Optional[float] = None,
        max_spacing: Optional[float] = None,
        contrast_used: Optional[bool] = None,
        has_nodules: Optional[bool] = None,
        min_annotations: Optional[int] = None,
        max_annotations: Optional[int] = None,
        # annotation characteristic filters
        min_subtlety: Optional[int] = None,
        max_subtlety: Optional[int] = None,
        min_malignancy: Optional[int] = None,
        max_malignancy: Optional[int] = None,
        min_sphericity: Optional[int] = None,
        max_sphericity: Optional[int] = None,
        min_margin: Optional[int] = None,
        max_margin: Optional[int] = None,
        min_lobulation: Optional[int] = None,
        max_lobulation: Optional[int] = None,
        min_spiculation: Optional[int] = None,
        max_spiculation: Optional[int] = None,
        min_texture: Optional[int] = None,
        max_texture: Optional[int] = None,
        calcification: Optional[int] = None,
        min_diameter: Optional[float] = None,
        max_diameter: Optional[float] = None,
        sort_by: str = "patient_id",
        sort_order: str = "asc"
    ) -> Dict[str, Any]:
        """List available PYLIDC scans with filtering"""
        # Check cache first
        cache_key = self._get_cache_key("scans", page=page, page_size=page_size, 
                                       patient_id=patient_id, min_slices=min_slices,
                                       max_slices=max_slices, min_thickness=min_thickness,
                                       max_thickness=max_thickness, sort_by=sort_by, sort_order=sort_order)
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached
        
        try:
            # Build query with filters
            query = pl.query(pl.Scan)
            
            # Apply patient_id filter
            if patient_id:
                query = query.filter(pl.Scan.patient_id.like(f"%{patient_id}%"))
            
            # Apply slice thickness filters
            if min_thickness is not None:
                query = query.filter(pl.Scan.slice_thickness >= min_thickness)
            if max_thickness is not None:
                query = query.filter(pl.Scan.slice_thickness <= max_thickness)
            
            # Get all scans first (pylidc doesn't support direct slice count filtering)
            all_scans = query.all()
            
            # Apply slice count and nodules filters in Python
            # Use cached metadata for faster filtering
            filtered_scans = []
            for scan in all_scans:
                # Get or compute scan metadata
                metadata = self._get_scan_metadata(scan)
                slice_count = metadata["slice_count"]
                annotation_count = metadata["annotation_count"]
                annotations = metadata["annotations"]
                
                # Check slice count filters
                if min_slices is not None and slice_count < min_slices:
                    continue
                if max_slices is not None and slice_count > max_slices:
                    continue
                
                # Check slice spacing filters
                if min_spacing is not None and scan.slice_spacing is not None and scan.slice_spacing < min_spacing:
                    continue
                if max_spacing is not None and scan.slice_spacing is not None and scan.slice_spacing > max_spacing:
                    continue
                
                # Check contrast used filter
                if contrast_used is not None and scan.contrast_used != contrast_used:
                    continue
                
                # Check annotation count filters
                if min_annotations is not None and annotation_count < min_annotations:
                    continue
                if max_annotations is not None and annotation_count > max_annotations:
                    continue
                
                # Check nodules filter
                if has_nodules is not None:
                    if has_nodules and annotation_count == 0:
                        continue
                    if not has_nodules and annotation_count > 0:
                        continue
                
                # Check annotation characteristic filters
                # need at least one annotation to match the criteria
                if any([
                    min_subtlety, max_subtlety, min_malignancy, max_malignancy,
                    min_sphericity, max_sphericity, min_margin, max_margin,
                    min_lobulation, max_lobulation, min_spiculation, max_spiculation,
                    min_texture, max_texture
                ]):
                    if annotation_count == 0:
                        continue  # skip scans with no annotations if characteristic filters are set
                    
                    # check if any annotation matches the characteristic filters
                    has_matching_annotation = False
                    for ann in annotations:
                        # check all characteristic filters
                        if min_subtlety is not None and ann.subtlety < min_subtlety:
                            continue
                        if max_subtlety is not None and ann.subtlety > max_subtlety:
                            continue
                        if calcification is not None and ann.calcification != calcification:
                            continue
                        if min_malignancy is not None and ann.malignancy < min_malignancy:
                            continue
                        if max_malignancy is not None and ann.malignancy > max_malignancy:
                            continue
                        if min_sphericity is not None and ann.sphericity < min_sphericity:
                            continue
                        if max_sphericity is not None and ann.sphericity > max_sphericity:
                            continue
                        if min_margin is not None and ann.margin < min_margin:
                            continue
                        if max_margin is not None and ann.margin > max_margin:
                            continue
                        if min_lobulation is not None and ann.lobulation < min_lobulation:
                            continue
                        if max_lobulation is not None and ann.lobulation > max_lobulation:
                            continue
                        if min_spiculation is not None and ann.spiculation < min_spiculation:
                            continue
                        if max_spiculation is not None and ann.spiculation > max_spiculation:
                            continue
                        if min_texture is not None and ann.texture < min_texture:
                            continue
                        if max_texture is not None and ann.texture > max_texture:
                            continue
                        
                        # check diameter filters (may trigger numpy error, skip if fails)
                        if min_diameter is not None or max_diameter is not None:
                            try:
                                diam = ann.diameter
                                if min_diameter is not None and diam < min_diameter:
                                    continue
                                if max_diameter is not None and diam > max_diameter:
                                    continue
                            except:
                                # skip annotation if diameter calculation fails
                                continue
                        
                        # if we get here, annotation matches all filters
                        has_matching_annotation = True
                        break
                    
                    if not has_matching_annotation:
                        continue
                
                filtered_scans.append((metadata, slice_count, annotation_count))
            
            # Sort using cached metadata
            if sort_by == "patient_id":
                filtered_scans.sort(key=lambda x: x[0]["patient_id"], reverse=(sort_order == "desc"))
            elif sort_by == "slice_thickness":
                filtered_scans.sort(key=lambda x: x[0]["slice_thickness"] or 0, reverse=(sort_order == "desc"))
            elif sort_by == "slice_count":
                filtered_scans.sort(key=lambda x: x[1], reverse=(sort_order == "desc"))
            
            total = len(filtered_scans)
            
            # Paginate
            offset = (page - 1) * page_size
            paginated_scans = filtered_scans[offset:offset + page_size]
            
            # Build response from cached metadata
            scan_list = []
            for metadata, slice_count, annotation_count in paginated_scans:
                scan_list.append({
                    "scan_id": metadata["series_instance_uid"],
                    "patient_id": metadata["patient_id"],
                    "study_instance_uid": metadata["study_instance_uid"],
                    "series_instance_uid": metadata["series_instance_uid"],
                    "slice_thickness": metadata["slice_thickness"],
                    "slice_spacing": metadata["slice_spacing"],
                    "slice_count": slice_count,
                    "pixel_spacing": metadata["pixel_spacing"],
                    "contrast_used": metadata["contrast_used"],
                    "annotation_count": annotation_count,
                    "has_nodules": annotation_count > 0
                })

            result = {
                "items": scan_list,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size
            }
            
            # Cache the result
            self._set_cache(cache_key, result)
            return result
        except Exception as e:
            import traceback
            traceback.print_exc()
            
            error_msg = str(e)
            # Check if it's a configuration error
            if "Could not establish path" in error_msg or "pylidcrc" in error_msg:
                error_msg = ("PYLIDC dataset not configured. Please download the LIDC-IDRI dataset "
                           "and configure ~/.pylidcrc with the path to DICOM files. "
                           "See https://pylidc.github.io for instructions.")
            
            return {
                "items": [],
                "total": 0,
                "page": page,
                "page_size": page_size,
                "total_pages": 0,
                "error": error_msg
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
