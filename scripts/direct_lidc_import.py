"""
Direct LIDC Import Script - Bypasses numpy issues
Imports LIDC data directly to Supabase without pylidc adapter
"""

import sys
sys.path.insert(0, 'src')

import hashlib
import json
from maps.supabase import supabase

try:
    import pylidc as pl
except ImportError:
    print("❌ pylidc not installed")
    sys.exit(1)

def import_scan_direct(scan):
    """Import scan directly without adapter to avoid numpy issues"""
    
    # Build basic metadata
    metadata = {
        'source': 'LIDC-IDRI',
        'patient_id': scan.patient_id,
        'series_uid': scan.series_instance_uid,
        'study_uid': scan.study_instance_uid,
        'modality': 'CT',
        'slice_thickness': float(scan.slice_thickness),
        'num_annotations': len(scan.annotations),
        'pixel_spacing': str(scan.pixel_spacing),
        'slice_spacing': float(scan.slice_spacing)
    }
    
    # Create content hash
    content_str = json.dumps(metadata, sort_keys=True)
    content_hash = hashlib.sha256(content_str.encode()).hexdigest()
    
    # Insert file
    file_data = {
        'filename': f"{scan.patient_id}.xml",
        'extension': 'xml',
        'file_size_bytes': len(content_str),
        'raw_content_hash': content_hash,
        'processing_status': 'complete',
        'metadata': metadata
    }
    
    print(f"  Inserting file: {file_data['filename']}")
    file_result = supabase.table('file_imports').insert(file_data).execute()
    file_id = file_result.data[0]['file_id']
    print(f"    ✓ File ID: {file_id}")
    
    # Insert annotations as qualitative segments
    for i, ann in enumerate(scan.annotations):
        text_content = f"""Radiologist Annotation {i+1}
Patient: {scan.patient_id}
Characteristics:
  - Subtlety: {ann.subtlety}
  - Internal Structure: {ann.internalStructure}
  - Calcification: {ann.calcification}
  - Sphericity: {ann.sphericity}
  - Margin: {ann.margin}
  - Lobulation: {ann.lobulation}
  - Spiculation: {ann.spiculation}
  - Texture: {ann.texture}
  - Malignancy: {ann.malignancy}
"""
        
        qual_data = {
            'file_id': file_id,
            'text_content': text_content,
            'segment_subtype': 'radiologist_annotation',
            'word_count': len(text_content.split())
        }
        
        supabase.table('qualitative_segments').insert(qual_data).execute()
    
    print(f"    ✓ Inserted {len(scan.annotations)} qualitative segments")
    
    # Insert measurements as quantitative segments
    for i, ann in enumerate(scan.annotations):
        quant_data = {
            'file_id': file_id,
            'data_structure': {
                'annotation_id': i + 1,
                'subtlety': ann.subtlety,
                'internalStructure': ann.internalStructure,
                'calcification': ann.calcification,
                'sphericity': ann.sphericity,
                'margin': ann.margin,
                'lobulation': ann.lobulation,
                'spiculation': ann.spiculation,
                'texture': ann.texture,
                'malignancy': ann.malignancy
            },
            'numeric_density': 1.0,
            'row_count': 1
        }
        
        supabase.table('quantitative_segments').insert(quant_data).execute()
    
    print(f"    ✓ Inserted {len(scan.annotations)} quantitative segments")
    
    return file_id


def main():
    print("="*70)
    print("DIRECT LIDC IMPORT (Bypasses numpy issues)")
    print("="*70)
    
    # Query scans
    print("\n1. Querying high-quality scans...")
    scans = pl.query(pl.Scan).filter(pl.Scan.slice_thickness <= 1.0).limit(5).all()
    scans_with_ann = [s for s in scans if len(s.annotations) > 0]
    
    print(f"   Found {len(scans_with_ann)} scans with annotations:\n")
    for i, scan in enumerate(scans_with_ann, 1):
        print(f"   {i}. {scan.patient_id} - {len(scan.annotations)} annotations, {scan.slice_thickness:.2f}mm slices")
    
    # Import
    print(f"\n2. Importing {len(scans_with_ann)} scans...")
    success = 0
    failed = 0
    
    for scan in scans_with_ann:
        try:
            file_id = import_scan_direct(scan)
            success += 1
        except Exception as e:
            print(f"    ✗ Failed {scan.patient_id}: {e}")
            failed += 1
    
    print(f"\n✅ Import complete: {success} success, {failed} failed")
    
    # Summary
    print("\n3. Checking Supabase...")
    files = supabase.table('file_imports').select('*').execute()
    segments = supabase.table('unified_segments').select('*').execute()
    
    print(f"   Files: {len(files.data)}")
    print(f"   Segments: {len(segments.data)}")
    
    print("\n" + "="*70)
    print("DONE - Data ready for analysis!")
    print("="*70)


if __name__ == '__main__':
    main()
