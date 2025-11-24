#!/usr/bin/env python3
"""
PyLIDC → Supabase Command-Line Tool
Query LIDC-IDRI dataset and import to Supabase interactively
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from maps.pylidc_supabase_bridge import PyLIDCSupabaseBridge


def main():
    print("=" * 70)
    print("PyLIDC → Supabase Bridge")
    print("=" * 70)
    
    try:
        bridge = PyLIDCSupabaseBridge()
        print("✓ Connected to pylidc and Supabase\n")
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        print("\nSetup required:")
        print("  1. Install pylidc: pip install pylidc")
        print("  2. Configure pylidc: pylidc conf")
        print("  3. Set SUPABASE_URL and SUPABASE_KEY in .env")
        return
    
    while True:
        print("\nActions:")
        print("  1. Query high-quality scans (slice_thickness <= 1.0mm)")
        print("  2. Query by patient ID")
        print("  3. Find malignant nodules (malignancy >= 4)")
        print("  4. Search by characteristics")
        print("  5. Import scan(s) to Supabase")
        print("  6. Check what's already imported")
        print("  7. View Supabase statistics")
        print("  q. Quit")
        
        choice = input("\nEnter choice: ").strip().lower()
        
        if choice == 'q':
            print("Goodbye!")
            break
        
        elif choice == '1':
            limit = int(input("How many scans? (default 10): ") or "10")
            scans = bridge.query_scans(
                max_slice_thickness=1.0,
                has_annotations=True,
                limit=limit
            )
            
            print(f"\nFound {len(scans)} high-quality scans:")
            for i, scan in enumerate(scans, 1):
                imported = "✓" if bridge.is_scan_imported(scan.patient_id) else "○"
                print(f"  {imported} {i}. {scan.patient_id} - "
                      f"{len(scan.annotations)} annotations, "
                      f"{scan.slice_thickness:.2f}mm slices")
            
            if input("\nImport these to Supabase? (y/n): ").lower() == 'y':
                result = bridge.import_scans_batch(scans)
                print(f"\n✓ Imported {result['success']}/{result['total']} scans")
        
        elif choice == '2':
            patient_id = input("Patient ID (e.g., LIDC-IDRI-0001): ").strip()
            scans = bridge.query_scans(patient_id=patient_id)
            
            if scans:
                scan = scans[0]
                print(f"\n{scan.patient_id}:")
                print(f"  Series UID: {scan.series_instance_uid}")
                print(f"  Slice thickness: {scan.slice_thickness:.2f}mm")
                print(f"  Annotations: {len(scan.annotations)}")
                print(f"  Slices: {len(scan.slice_zvals)}")
                
                if input("\nImport to Supabase? (y/n): ").lower() == 'y':
                    result = bridge.import_scan(scan)
                    print(f"✓ Imported: {result['file_id']}")
                    print(f"  Qualitative segments: {result['qualitative_segments']}")
                    print(f"  Quantitative segments: {result['quantitative_segments']}")
            else:
                print(f"✗ No scan found for {patient_id}")
        
        elif choice == '3':
            min_mal = int(input("Minimum malignancy (1-5, default 4): ") or "4")
            limit = int(input("Max results (default 20): ") or "20")
            
            nodules = bridge.query_nodules_by_malignancy(
                min_malignancy=min_mal,
                limit=limit
            )
            
            print(f"\nFound {len(nodules)} nodules:")
            for i, nod in enumerate(nodules[:10], 1):
                print(f"  {i}. {nod['patient_id']} - "
                      f"malignancy={nod['malignancy']}, "
                      f"subtlety={nod['subtlety']}, "
                      f"spiculation={nod['spiculation']}")
            
            if len(nodules) > 10:
                print(f"  ... and {len(nodules) - 10} more")
            
            if input("\nImport all scans with these nodules? (y/n): ").lower() == 'y':
                scans = [n['scan'] for n in nodules]
                result = bridge.import_scans_batch(scans)
                print(f"✓ Imported {result['success']}/{result['total']}")
        
        elif choice == '4':
            print("\nCharacteristic search (press Enter to skip):")
            spic = input("  Spiculation (1-5): ").strip()
            calc = input("  Calcification (1-6): ").strip()
            spher = input("  Sphericity (1-5): ").strip()
            marg = input("  Margin (1-5): ").strip()
            
            kwargs = {}
            if spic: kwargs['spiculation'] = int(spic)
            if calc: kwargs['calcification'] = int(calc)
            if spher: kwargs['sphericity'] = int(spher)
            if marg: kwargs['margin'] = int(marg)
            kwargs['limit'] = 20
            
            results = bridge.search_by_characteristics(**kwargs)
            
            print(f"\nFound {len(results)} matching nodules:")
            for i, r in enumerate(results[:10], 1):
                char = r['characteristics']
                print(f"  {i}. {r['patient_id']}: "
                      f"spic={char['spiculation']}, "
                      f"calc={char['calcification']}, "
                      f"spher={char['sphericity']}, "
                      f"margin={char['margin']}")
        
        elif choice == '5':
            patient_id = input("Patient ID to import: ").strip()
            scans = bridge.query_scans(patient_id=patient_id)
            
            if scans:
                result = bridge.import_scan(scans[0])
                print(f"✓ Imported {result['patient_id']} with {result['nodule_count']} nodules")
            else:
                print(f"✗ Scan not found")
        
        elif choice == '6':
            imported = bridge.get_imported_patients()
            print(f"\n{len(imported)} patients in Supabase:")
            for i, pid in enumerate(sorted(imported)[:20], 1):
                print(f"  {i}. {pid}")
            if len(imported) > 20:
                print(f"  ... and {len(imported) - 20} more")
        
        elif choice == '7':
            stats = bridge.get_supabase_nodule_stats()
            imported = bridge.get_imported_patients()
            
            print("\nSupabase Statistics:")
            print(f"  Imported patients: {len(imported)}")
            print(f"  Total files: {stats['total_files']}")
            print(f"  Total nodules: {stats['total_nodules']}")
            print(f"  Quantitative segments: {stats['quantitative_segments']}")
            print(f"  Qualitative segments: {stats['qualitative_segments']}")


if __name__ == '__main__':
    main()
