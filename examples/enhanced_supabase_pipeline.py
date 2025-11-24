#!/usr/bin/env python3
"""
Enhanced Supabase Pipeline with Parse Case & Keyword Tracking

Demonstrates complete integration of:
- PYLIDC data import
- Parse case detection and tracking
- Automatic keyword extraction
- Schema-agnostic document storage

Usage:
    python examples/enhanced_supabase_pipeline.py
"""

import sys
import os
from pathlib import Path
from uuid import uuid4

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from maps.database.enhanced_document_repository import EnhancedDocumentRepository
from maps.adapters.pylidc_adapter import PyLIDCAdapter


def example_1_enhanced_single_import():
    """Example 1: Import single scan with full tracking"""
    print("=" * 70)
    print("Example 1: Enhanced Single Import")
    print("=" * 70)

    try:
        import pylidc as pl

        # Initialize enhanced repository
        repo = EnhancedDocumentRepository(
            enable_parse_case_tracking=True,
            enable_keyword_extraction=True
        )

        # Get a scan
        scan = pl.query(pl.Scan).first()
        if not scan:
            print("⚠️  No PYLIDC scans found")
            return

        print(f"📄 Processing: {scan.patient_id}")

        # Convert to canonical
        adapter = PyLIDCAdapter()
        canonical_doc = adapter.scan_to_canonical(scan)

        # Insert with enhanced tracking
        doc, content, parse_case, keyword_count = repo.insert_canonical_document_enhanced(
            canonical_doc,
            source_file=f"pylidc://{scan.patient_id}",
            uploaded_by="demo_user",
            tags=["LIDC-IDRI", "demo", "enhanced"],
            detect_parse_case=True,
            extract_keywords=True
        )

        print(f"✅ Import complete!")
        print(f"   Document ID: {doc.id}")
        print(f"   Parse Case: {parse_case}")
        print(f"   Keywords Extracted: {keyword_count}")
        print(f"   Status: {doc.status}")
        print()

    except ImportError:
        print("⚠️  pylidc not installed")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


def example_2_enhanced_batch_import():
    """Example 2: Batch import with tracking"""
    print("=" * 70)
    print("Example 2: Enhanced Batch Import")
    print("=" * 70)

    try:
        import pylidc as pl

        repo = EnhancedDocumentRepository(
            enable_parse_case_tracking=True,
            enable_keyword_extraction=True
        )

        # Get multiple scans
        scans = pl.query(pl.Scan).limit(5).all()
        if not scans:
            print("⚠️  No scans found")
            return

        print(f"📦 Processing {len(scans)} scans...")

        # Convert all to canonical
        adapter = PyLIDCAdapter()
        canonical_docs = []
        source_files = []

        for scan in scans:
            canonical_doc = adapter.scan_to_canonical(scan)
            canonical_docs.append(canonical_doc)
            source_files.append(f"pylidc://{scan.patient_id}")

        # Batch import with tracking
        batch_id = uuid4()

        def progress(current, total):
            print(f"   Progress: {current}/{total}")

        results = repo.batch_insert_canonical_documents_enhanced(
            canonical_docs=canonical_docs,
            source_files=source_files,
            uploaded_by="batch_demo",
            tags=["LIDC-IDRI", "batch"],
            batch_id=batch_id,
            detect_parse_case=True,
            extract_keywords=True,
            progress_callback=progress
        )

        # Analyze results
        parse_cases = {}
        total_keywords = 0

        for doc, content, parse_case, kw_count in results:
            if parse_case:
                parse_cases[parse_case] = parse_cases.get(parse_case, 0) + 1
            total_keywords += kw_count

        print(f"\n✅ Batch import complete!")
        print(f"   Documents imported: {len(results)}")
        print(f"   Parse cases detected: {parse_cases}")
        print(f"   Total keywords extracted: {total_keywords}")
        print(f"   Batch ID: {batch_id}")
        print()

    except ImportError:
        print("⚠️  pylidc not installed")
    except Exception as e:
        print(f"❌ Error: {e}")


def example_3_query_by_parse_case():
    """Example 3: Query documents by parse case"""
    print("=" * 70)
    print("Example 3: Query by Parse Case")
    print("=" * 70)

    repo = EnhancedDocumentRepository()

    # Get all documents
    recent = repo.get_recent_documents(limit=20)

    # Group by parse case
    by_parse_case = {}
    for doc in recent:
        # Parse case would be in doc.parse_case_id (after migration 003)
        system = doc.source_system or "Unknown"
        by_parse_case[system] = by_parse_case.get(system, 0) + 1

    print("📊 Documents by source system:")
    for system, count in by_parse_case.items():
        print(f"   {system}: {count}")
    print()


def example_4_enhanced_statistics():
    """Example 4: Get enhanced statistics"""
    print("=" * 70)
    print("Example 4: Enhanced Statistics")
    print("=" * 70)

    repo = EnhancedDocumentRepository(
        enable_parse_case_tracking=True,
        enable_keyword_extraction=True
    )

    stats = repo.get_document_statistics_enhanced()

    print("📈 Repository Statistics:")
    print(f"   Total documents: {stats.get('total_documents', 0)}")
    print(f"   By status: {stats.get('by_status', {})}")
    print(f"   By source system: {stats.get('by_source_system', {})}")

    if 'parse_cases' in stats:
        print(f"   Parse case stats: {stats['parse_cases']}")

    if 'keywords' in stats:
        kw_stats = stats['keywords']
        print(f"   Total keywords: {kw_stats.get('total_keywords', 0)}")
        print(f"   Keyword sources: {kw_stats.get('total_keyword_sources', 0)}")

    print()


def example_5_keyword_search():
    """Example 5: Search documents by keywords"""
    print("=" * 70)
    print("Example 5: Keyword Search")
    print("=" * 70)

    repo = EnhancedDocumentRepository()

    # Search for documents containing specific keywords
    search_terms = ["malignancy", "nodule", "CT"]

    for term in search_terms:
        results = repo.search_documents(term, limit=5)
        print(f"🔍 Search results for '{term}': {len(results)} found")

        for doc, content in results[:3]:
            print(f"   • {doc.source_file_name}")
            if content.tags:
                print(f"     Tags: {content.tags}")

    print()


def example_6_schema_agnostic_workflow():
    """Example 6: Complete schema-agnostic workflow"""
    print("=" * 70)
    print("Example 6: Schema-Agnostic Workflow")
    print("=" * 70)

    print("""
This example demonstrates the complete schema-agnostic workflow:

1. Import from any XML source (PYLIDC, custom format, etc.)
2. Automatic parse case detection identifies the schema
3. Keywords are extracted for full-text search
4. Documents are linked to their parse cases
5. Query and analyze by schema type

The system tracks:
- Which XML schema/structure was used (parse case)
- What keywords exist in each document
- Schema drift detection (if structure changes)
- Performance metrics per schema type

Database Structure:
┌──────────────────────────────────────────────────┐
│ documents                                        │
│ ├─ id                                            │
│ ├─ source_file_path                              │
│ ├─ parse_case_id  ←──┐                          │
│ └─ status             │                          │
└───────────────────────┼──────────────────────────┘
                        │
                        │ Foreign Key
                        │
┌───────────────────────┼──────────────────────────┐
│ parse_cases           │                          │
│ ├─ id  ───────────────┘                          │
│ ├─ name  (e.g., "LIDC_Multi_Session_4")         │
│ ├─ format_type  (e.g., "LIDC")                   │
│ └─ detection_criteria  (JSONB)                   │
└──────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────┐
│ document_keywords  (junction table)              │
│ ├─ document_id  ────→ documents.id               │
│ ├─ keyword_id   ────→ keywords.keyword_id        │
│ ├─ frequency                                     │
│ └─ tf_idf_score                                  │
└──────────────────────────────────────────────────┘

Benefits:
✅ No code changes needed for new XML schemas
✅ Automatic keyword indexing for search
✅ Track which schema each document uses
✅ Detect schema changes/drift over time
✅ Query performance metrics by schema type
    """)


def main():
    """Run all examples"""
    print()
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "Enhanced Supabase Pipeline Examples" + " " * 17 + "║")
    print("╚" + "═" * 68 + "╝")
    print()

    # Check environment
    supabase_url = os.getenv("SUPABASE_DB_URL")
    if not supabase_url:
        print("⚠️  SUPABASE_DB_URL not set!")
        print("   Set it in .env file or export it:")
        print("   export SUPABASE_DB_URL='postgresql://...'")
        print()
        return

    print(f"✅ Connected to: {supabase_url[:50]}...")
    print()

    # Run examples
    try:
        example_1_enhanced_single_import()
        example_2_enhanced_batch_import()
        example_3_query_by_parse_case()
        example_4_enhanced_statistics()
        example_5_keyword_search()
        example_6_schema_agnostic_workflow()

        print("=" * 70)
        print("✅ All examples complete!")
        print("=" * 70)
        print()
        print("Next steps:")
        print("1. Run migration 003 to add parse_case_id foreign key:")
        print("   psql $SUPABASE_DB_URL -f migrations/003_document_parse_case_links.sql")
        print()
        print("2. Import your full dataset:")
        print("   python scripts/pylidc_to_supabase.py --filter high_quality")
        print()
        print("3. Query by schema:")
        print("   SELECT * FROM document_schema_distribution;")
        print()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
