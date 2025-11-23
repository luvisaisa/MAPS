"""
Demo: Analysis and Export System with Sample Data

This demonstrates how the system works with imported data.
Run after deploying views and importing LIDC data.
"""

import sys
sys.path.insert(0, 'src')
from ra_d_ps.analysis_exporter import AnalysisExporter
from datetime import datetime

def demo_analysis_system():
    """Comprehensive demo of all analysis features"""
    
    print("="*70)
    print("CASE IDENTIFIER SYSTEM - ANALYSIS & EXPORT DEMO")
    print("="*70)
    
    exporter = AnalysisExporter()
    
    # =========================================================================
    # 1. SUMMARY STATISTICS
    # =========================================================================
    print("\n" + "="*70)
    print("1. SYSTEM STATISTICS")
    print("="*70)
    exporter.print_summary()
    
    # =========================================================================
    # 2. REFRESH EXPORT TABLE
    # =========================================================================
    print("\n" + "="*70)
    print("2. REFRESHING EXPORT TABLE")
    print("="*70)
    try:
        stats = exporter.refresh_export_table()
        print(f"✅ Refreshed {stats['total_rows']} rows")
        print(f"   Duration: {stats['refresh_duration']}")
        print(f"   Timestamp: {stats['refresh_timestamp']}")
    except Exception as e:
        print(f"⚠️  Export table refresh failed: {e}")
        print("   (Run migrations/003_analysis_views.sql first)")
    
    # =========================================================================
    # 3. QUERY MASTER TABLE
    # =========================================================================
    print("\n" + "="*70)
    print("3. QUERYING MASTER ANALYSIS TABLE")
    print("="*70)
    try:
        data = exporter.get_master_table()
        print(f"✅ Found {len(data)} total segments")
        
        if data:
            sample = data[0]
            print(f"\nSample row:")
            print(f"  File: {sample.get('filename')}")
            print(f"  Type: {sample.get('segment_type')}")
            print(f"  Keywords: {sample.get('keyword_count')}")
            print(f"  Preview: {sample.get('content_preview', '')[:80]}...")
    except Exception as e:
        print(f"⚠️  Master table query failed: {e}")
        print("   (Table may not exist yet - deploy SQL first)")
    
    # =========================================================================
    # 4. FILTERED QUERIES
    # =========================================================================
    print("\n" + "="*70)
    print("4. FILTERED QUERIES")
    print("="*70)
    
    # Filter 1: Qualitative content only
    print("\n4a. Qualitative segments:")
    try:
        qual_data = exporter.filter_by_criteria(segment_types=['qualitative'])
        print(f"   Found {len(qual_data)} qualitative segments")
    except Exception as e:
        print(f"   ⚠️  Query failed: {str(e)[:80]}")
    
    # Filter 2: High keyword density
    print("\n4b. Segments with ≥5 keywords:")
    try:
        keyword_rich = exporter.filter_by_criteria(min_keyword_count=5)
        print(f"   Found {len(keyword_rich)} keyword-rich segments")
    except Exception as e:
        print(f"   ⚠️  Query failed: {str(e)[:80]}")
    
    # Filter 3: XML files only
    print("\n4c. XML files:")
    try:
        xml_data = exporter.filter_by_criteria(file_types=['xml'])
        print(f"   Found {len(xml_data)} XML segments")
    except Exception as e:
        print(f"   ⚠️  Query failed: {str(e)[:80]}")
    
    # Filter 4: Case patterns
    print("\n4d. Segments with case patterns:")
    try:
        pattern_data = exporter.filter_by_criteria(has_case_patterns=True)
        print(f"   Found {len(pattern_data)} segments with patterns")
    except Exception as e:
        print(f"   ⚠️  Query failed: {str(e)[:80]}")
    
    # =========================================================================
    # 5. EXPORTS
    # =========================================================================
    print("\n" + "="*70)
    print("5. DATA EXPORTS")
    print("="*70)
    
    # Export all data
    print("\n5a. Exporting all data to CSV:")
    try:
        csv_path = exporter.export_to_csv('./exports/demo_all_data.csv')
        if csv_path:
            print(f"   ✅ Exported to {csv_path}")
    except Exception as e:
        print(f"   ⚠️  Export failed: {e}")
    
    # Export to JSON
    print("\n5b. Exporting all data to JSON:")
    try:
        json_path = exporter.export_to_json('./exports/demo_all_data.json')
        if json_path:
            print(f"   ✅ Exported to {json_path}")
    except Exception as e:
        print(f"   ⚠️  Export failed: {e}")
    
    # Export by file type
    print("\n5c. Exporting by file type:")
    try:
        exporter.export_by_file_type('xml', output_dir='./exports/demo')
    except Exception as e:
        print(f"   ⚠️  Export failed: {str(e)[:80]}")
    
    # Export high-relevance keywords
    print("\n5d. Exporting high-relevance keywords:")
    try:
        exporter.export_high_relevance_keywords(
            min_relevance=5.0, 
            output_dir='./exports/demo'
        )
    except Exception as e:
        print(f"   ⚠️  Export failed: {str(e)[:80]}")
    
    # =========================================================================
    # 6. KEYWORD ANALYSIS
    # =========================================================================
    print("\n" + "="*70)
    print("6. KEYWORD ANALYSIS")
    print("="*70)
    
    try:
        # Get top keywords
        keywords = exporter.supabase.table('extracted_keywords')\
            .select('*')\
            .order('relevance_score', desc=True)\
            .limit(10)\
            .execute()
        
        if keywords.data:
            print(f"\nTop 10 keywords by relevance:")
            for i, kw in enumerate(keywords.data, 1):
                print(f"   {i}. {kw['term']}: {kw['relevance_score']:.2f} "
                      f"(docs: {kw['document_frequency']}, total: {kw['total_frequency']})")
    except Exception as e:
        print(f"⚠️  Keyword query failed: {e}")
    
    # =========================================================================
    # 7. CROSS-TYPE KEYWORDS
    # =========================================================================
    print("\n" + "="*70)
    print("7. CROSS-TYPE KEYWORDS (High Signal)")
    print("="*70)
    
    try:
        cross_keywords = exporter.supabase.table('cross_type_keywords')\
            .select('*')\
            .limit(10)\
            .execute()
        
        if cross_keywords.data:
            print(f"\nKeywords appearing in BOTH quantitative and qualitative content:")
            for i, kw in enumerate(cross_keywords.data, 1):
                print(f"   {i}. {kw['term']}: "
                      f"quant={kw['quantitative_occurrences']}, "
                      f"qual={kw['qualitative_occurrences']}, "
                      f"files={kw['file_count']}")
        else:
            print("   (No cross-type keywords yet - import data and extract keywords)")
    except Exception as e:
        print(f"⚠️  Cross-type query failed: {str(e)[:80]}")
    
    # =========================================================================
    # 8. CASE PATTERNS
    # =========================================================================
    print("\n" + "="*70)
    print("8. CASE PATTERNS")
    print("="*70)
    
    try:
        patterns = exporter.supabase.table('case_patterns')\
            .select('*')\
            .order('confidence_score', desc=True)\
            .limit(5)\
            .execute()
        
        if patterns.data:
            print(f"\nTop case patterns by confidence:")
            for i, pattern in enumerate(patterns.data, 1):
                validated = "✓ Cross-validated" if pattern['cross_type_validated'] else ""
                print(f"   {i}. Pattern {pattern['case_id'][:8]}: "
                      f"confidence={pattern['confidence_score']:.2f}, "
                      f"keywords={pattern['keyword_count']}, "
                      f"segments={pattern['segment_count']} {validated}")
        else:
            print("   (No patterns detected yet - run pattern detection)")
    except Exception as e:
        print(f"⚠️  Pattern query failed: {str(e)[:80]}")
    
    # =========================================================================
    # SUMMARY
    # =========================================================================
    print("\n" + "="*70)
    print("DEMO COMPLETE")
    print("="*70)
    print("\n✅ All analysis features demonstrated!")
    print("\nNext steps:")
    print("1. Deploy views: Run migrations/003_analysis_views.sql")
    print("2. Import data: python3 scripts/pylidc_bridge_cli.py")
    print("3. Extract keywords: (coming soon)")
    print("4. Detect patterns: (coming soon)")
    print("5. Run this demo again with real data!")
    print("\n" + "="*70 + "\n")


if __name__ == '__main__':
    demo_analysis_system()
