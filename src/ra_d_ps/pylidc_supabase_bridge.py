"""
PyLIDC to Supabase Query Bridge
Direct integration for querying LIDC-IDRI and importing to Supabase
"""

import os
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

try:
    import pylidc as pl
    PYLIDC_AVAILABLE = True
except ImportError:
    PYLIDC_AVAILABLE = False
    pl = None

from ra_d_ps.supabase import supabase
from ra_d_ps.adapters.pylidc_adapter import PyLIDCAdapter

logger = logging.getLogger(__name__)


class PyLIDCSupabaseBridge:
    """
    Bridge for querying pylidc and importing to Supabase
    Provides unified interface for LIDC-IDRI data access and storage
    """
    
    def __init__(self):
        """Initialize bridge with pylidc and Supabase connections"""
        if not PYLIDC_AVAILABLE:
            raise ImportError(
                "pylidc not installed. Install with: pip install pylidc\n"
                "Then configure: pylidc conf"
            )
        
        self.adapter = PyLIDCAdapter()
        self.supabase = supabase
    
    # =========================================================================
    # QUERY METHODS - Query pylidc database
    # =========================================================================
    
    def query_scans(
        self,
        patient_id: Optional[str] = None,
        min_slice_thickness: Optional[float] = None,
        max_slice_thickness: Optional[float] = None,
        has_annotations: bool = False,
        limit: Optional[int] = None
    ) -> List:
        """
        Query LIDC scans with filters
        
        Args:
            patient_id: Specific patient ID (e.g., "LIDC-IDRI-0001")
            min_slice_thickness: Minimum slice thickness in mm
            max_slice_thickness: Maximum slice thickness in mm (1.0 = high quality)
            has_annotations: Only return scans with annotations
            limit: Maximum number of results
            
        Returns:
            List of pylidc Scan objects
            
        Example:
            # Get high-quality scans with annotations
            scans = bridge.query_scans(max_slice_thickness=1.0, has_annotations=True, limit=10)
        """
        query = pl.query(pl.Scan)
        
        if patient_id:
            query = query.filter(pl.Scan.patient_id == patient_id)
        
        if min_slice_thickness:
            query = query.filter(pl.Scan.slice_thickness >= min_slice_thickness)
        
        if max_slice_thickness:
            query = query.filter(pl.Scan.slice_thickness <= max_slice_thickness)
        
        if limit:
            query = query.limit(limit)
        
        scans = query.all()
        
        if has_annotations:
            scans = [s for s in scans if len(s.annotations) > 0]
        
        logger.info(f"Found {len(scans)} scans matching criteria")
        return scans
    
    def query_nodules_by_malignancy(
        self,
        min_malignancy: int = 3,
        max_malignancy: int = 5,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Query nodules by malignancy rating
        
        Args:
            min_malignancy: Minimum malignancy (1-5 scale)
            max_malignancy: Maximum malignancy (1-5 scale)
            limit: Maximum number of nodules
            
        Returns:
            List of dicts with scan and annotation info
            
        Example:
            # Find highly malignant nodules
            nodules = bridge.query_nodules_by_malignancy(min_malignancy=4, limit=20)
        """
        anns = pl.query(pl.Annotation).filter(
            pl.Annotation.malignancy >= min_malignancy,
            pl.Annotation.malignancy <= max_malignancy
        )
        
        if limit:
            anns = anns.limit(limit)
        
        results = []
        for ann in anns:
            results.append({
                'scan': ann.scan,
                'annotation': ann,
                'patient_id': ann.scan.patient_id,
                'malignancy': ann.malignancy,
                'subtlety': ann.subtlety,
                'spiculation': ann.spiculation,
                'calcification': ann.calcification,
                'sphericity': ann.sphericity,
                'margin': ann.margin,
                'lobulation': ann.lobulation,
                'texture': ann.texture
            })
        
        logger.info(f"Found {len(results)} nodules with malignancy {min_malignancy}-{max_malignancy}")
        return results
    
    def search_by_characteristics(
        self,
        spiculation: Optional[int] = None,
        calcification: Optional[int] = None,
        sphericity: Optional[int] = None,
        margin: Optional[int] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Search nodules by specific characteristics
        
        Args:
            spiculation: 1-5 scale
            calcification: 1-6 scale
            sphericity: 1-5 scale
            margin: 1-5 scale
            limit: Maximum results
            
        Returns:
            List of matching nodules with scan info
        """
        query = pl.query(pl.Annotation)
        
        if spiculation is not None:
            query = query.filter(pl.Annotation.spiculation == spiculation)
        if calcification is not None:
            query = query.filter(pl.Annotation.calcification == calcification)
        if sphericity is not None:
            query = query.filter(pl.Annotation.sphericity == sphericity)
        if margin is not None:
            query = query.filter(pl.Annotation.margin == margin)
        
        if limit:
            query = query.limit(limit)
        
        results = []
        for ann in query.all():
            results.append({
                'scan': ann.scan,
                'annotation': ann,
                'patient_id': ann.scan.patient_id,
                'characteristics': {
                    'spiculation': ann.spiculation,
                    'calcification': ann.calcification,
                    'sphericity': ann.sphericity,
                    'margin': ann.margin,
                    'lobulation': ann.lobulation,
                    'malignancy': ann.malignancy
                }
            })
        
        return results
    
    # =========================================================================
    # IMPORT METHODS - Add pylidc data to Supabase
    # =========================================================================
    
    def import_scan(
        self,
        scan,  # pylidc.Scan
        include_annotations: bool = True,
        cluster_nodules: bool = False  # Set to False by default to avoid numpy issues
    ) -> Dict[str, Any]:
        """
        Import a single pylidc scan to Supabase using unified case identifier schema
        
        Args:
            scan: pylidc.Scan object
            include_annotations: Include nodule annotations
            cluster_nodules: Group annotations by nodule
            
        Returns:
            Dict with file_id and status
            
        Example:
            scan = pl.query(pl.Scan).first()
            result = bridge.import_scan(scan)
            print(f"Imported: {result['file_id']}")
        """
        import hashlib
        import json
        
        # Convert to canonical format
        canonical = self.adapter.scan_to_canonical(
            scan,
            include_annotations=include_annotations,
            cluster_nodules=cluster_nodules
        )
        
        # Create content hash for deduplication
        content_str = json.dumps(canonical.model_dump(mode='json'), sort_keys=True)
        content_hash = hashlib.sha256(content_str.encode()).hexdigest()
        
        # Insert into file_imports table (NEW SCHEMA)
        file_data = {
            'filename': f"{scan.patient_id}.xml",
            'extension': 'xml',
            'file_size_bytes': len(content_str),
            'raw_content_hash': content_hash,
            'processing_status': 'complete',
            'metadata': {
                'source': 'LIDC-IDRI',
                'patient_id': scan.patient_id,
                'series_uid': scan.series_instance_uid,
                'study_uid': scan.study_instance_uid,
                'modality': 'CT',
                'slice_thickness': float(scan.slice_thickness),
                'num_annotations': len(scan.annotations),
                'num_nodules': len(canonical.nodules) if hasattr(canonical, 'nodules') else 0
            }
        }
        
        try:
            file_result = self.supabase.table('file_imports').insert(file_data).execute()
            file_id = file_result.data[0]['file_id']
        except Exception as e:
            # If duplicate hash, update existing
            if 'unique_content_hash' in str(e):
                logger.info(f"Scan {scan.patient_id} already imported, updating...")
                existing = self.supabase.table('file_imports').select('file_id').eq(
                    'raw_content_hash', content_hash
                ).execute()
                file_id = existing.data[0]['file_id']
            else:
                raise
        
        # Extract qualitative segments (nodule descriptions, radiologist readings)
        qualitative_segments = []
        if include_annotations:
            for nodule in canonical.nodules:
                for rad_id, rad_data in nodule.get('radiologists', {}).items():
                    segment = {
                        'file_id': file_id,
                        'text_content': json.dumps(rad_data),
                        'segment_subtype': 'radiologist_annotation',
                        'word_count': len(json.dumps(rad_data).split()),
                        'position_in_file': {
                            'nodule_id': nodule.get('nodule_id'),
                            'radiologist': rad_id
                        }
                    }
                    qualitative_segments.append(segment)
        
        if qualitative_segments:
            self.supabase.table('qualitative_segments').insert(qualitative_segments).execute()
        
        # Extract quantitative segments (measurements, characteristics)
        quantitative_segments = []
        if include_annotations:
            for nodule in canonical.nodules:
                measurements = []
                for rad_id, rad_data in nodule.get('radiologists', {}).items():
                    measurements.append({
                        'radiologist': rad_id,
                        'malignancy': rad_data.get('malignancy'),
                        'subtlety': rad_data.get('subtlety'),
                        'spiculation': rad_data.get('spiculation'),
                        'calcification': rad_data.get('calcification'),
                        'sphericity': rad_data.get('sphericity'),
                        'margin': rad_data.get('margin'),
                        'lobulation': rad_data.get('lobulation'),
                        'texture': rad_data.get('texture')
                    })
                
                segment = {
                    'file_id': file_id,
                    'data_structure': {
                        'nodule_id': nodule.get('nodule_id'),
                        'measurements': measurements
                    },
                    'column_mappings': {
                        'malignancy': 'integer',
                        'subtlety': 'integer',
                        'spiculation': 'integer',
                        'calcification': 'integer',
                        'sphericity': 'integer',
                        'margin': 'integer',
                        'lobulation': 'integer',
                        'texture': 'integer'
                    },
                    'row_count': len(measurements),
                    'numeric_density': 1.0,
                    'position_in_file': {'nodule_index': nodule.get('nodule_id')}
                }
                quantitative_segments.append(segment)
        
        if quantitative_segments:
            self.supabase.table('quantitative_segments').insert(quantitative_segments).execute()
        
        logger.info(f"✓ Imported scan {scan.patient_id} → {file_id}")
        
        return {
            'file_id': file_id,
            'patient_id': scan.patient_id,
            'series_uid': scan.series_instance_uid,
            'nodule_count': len(canonical.nodules) if hasattr(canonical, 'nodules') else 0,
            'qualitative_segments': len(qualitative_segments),
            'quantitative_segments': len(quantitative_segments),
            'status': 'success'
        }
    
    def import_scans_batch(
        self,
        scans: List,
        include_annotations: bool = True
    ) -> Dict[str, Any]:
        """
        Import multiple scans to Supabase
        
        Args:
            scans: List of pylidc.Scan objects
            include_annotations: Include nodule data
            
        Returns:
            Summary with success/failure counts
        """
        results = {
            'total': len(scans),
            'success': 0,
            'failed': 0,
            'document_ids': []
        }
        
        for scan in scans:
            try:
                result = self.import_scan(
                    scan, 
                    include_annotations=include_annotations,
                    cluster_nodules=False  # Avoid numpy compatibility issues
                )
                results['success'] += 1
                results['document_ids'].append(result['document_id'])
            except Exception as e:
                logger.error(f"Failed to import {scan.patient_id}: {e}")
                results['failed'] += 1
        
        return results
    
    # =========================================================================
    # QUERY SUPABASE - Check what's already imported
    # =========================================================================
    
    def get_imported_patients(self) -> List[str]:
        """
        Get list of patient IDs already in Supabase
        
        Returns:
            List of patient ID strings
        """
        result = self.supabase.table('file_imports').select('metadata').execute()
        
        patient_ids = [
            r['metadata'].get('patient_id')
            for r in result.data
            if r.get('metadata') and r['metadata'].get('source') == 'LIDC-IDRI'
        ]
        
        return [pid for pid in patient_ids if pid]
    
    def is_scan_imported(self, patient_id: str) -> bool:
        """
        Check if a specific scan is already imported
        
        Args:
            patient_id: Patient ID (e.g., "LIDC-IDRI-0001")
            
        Returns:
            True if already imported
        """
        result = self.supabase.table('file_imports').select('file_id').eq(
            'filename', f'{patient_id}.xml'
        ).limit(1).execute()
        
        return len(result.data) > 0
    
    def get_supabase_nodule_stats(self) -> Dict[str, int]:
        """
        Get statistics on imported nodules
        
        Returns:
            Dict with counts and statistics
        """
        # Count files from LIDC-IDRI
        files = self.supabase.table('file_imports').select('file_id,metadata').execute()
        lidc_files = [f for f in files.data if f.get('metadata', {}).get('source') == 'LIDC-IDRI']
        
        # Count quantitative segments (nodule measurements)
        quant_result = self.supabase.table('quantitative_segments').select('segment_id').execute()
        
        # Count qualitative segments (annotations)
        qual_result = self.supabase.table('qualitative_segments').select('segment_id').execute()
        
        return {
            'total_files': len(lidc_files),
            'total_nodules': sum(f['metadata'].get('num_nodules', 0) for f in lidc_files),
            'quantitative_segments': len(quant_result.data),
            'qualitative_segments': len(qual_result.data)
        }


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == '__main__':
    # Initialize bridge
    bridge = PyLIDCSupabaseBridge()
    
    # Example 1: Query high-quality scans and import
    print("Example 1: Import high-quality scans")
    scans = bridge.query_scans(max_slice_thickness=1.0, has_annotations=True, limit=5)
    
    for scan in scans:
        if not bridge.is_scan_imported(scan.patient_id):
            result = bridge.import_scan(scan)
            print(f"  ✓ {result['patient_id']}: {result['nodule_count']} nodules")
        else:
            print(f"  ⊙ {scan.patient_id}: already imported")
    
    # Example 2: Find malignant nodules
    print("\nExample 2: Query malignant nodules")
    nodules = bridge.query_nodules_by_malignancy(min_malignancy=4, limit=10)
    print(f"Found {len(nodules)} highly malignant nodules")
    
    # Example 3: Check Supabase stats
    print("\nExample 3: Supabase statistics")
    imported = bridge.get_imported_patients()
    print(f"Imported patients: {len(imported)}")
    stats = bridge.get_supabase_nodule_stats()
    print(f"Total nodules in Supabase: {stats['total_nodules']}")
