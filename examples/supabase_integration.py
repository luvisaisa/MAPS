#!/usr/bin/env python3
"""
Supabase Integration Examples

Demonstrates how to use the DocumentRepository with Supabase PostgreSQL
for storing and querying radiology documents from PYLIDC.

Examples covered:
1. Basic document insertion
2. PYLIDC data import
3. Querying documents
4. Full-text search
5. Batch operations
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from maps.database.document_repository import DocumentRepository
from maps.adapters.pylidc_adapter import PyLIDCAdapter


def example_1_basic_insertion():
    """Example 1: Basic document insertion"""
    print("=" * 70)
    print("Example 1: Basic Document Insertion")
    print("=" * 70)

    # Initialize repository (uses SUPABASE_DB_URL from environment)
    repo = DocumentRepository()

    # Create a simple document
    doc = repo.create_document(
        source_file_name="test_scan_001.xml",
        source_file_path="data/test/001.xml",
        file_type="XML",
        uploaded_by="demo_user",
        source_system="LIDC-IDRI"
    )

    print(f"✅ Created document: {doc.id}")
    print(f"   File: {doc.source_file_name}")
    print(f"   Status: {doc.status}")
    print()


def example_2_pylidc_import():
    """Example 2: Import PYLIDC data"""
    print("=" * 70)
    print("Example 2: PYLIDC Data Import")
    print("=" * 70)

    try:
        import pylidc as pl

        # Initialize adapter and repository
        adapter = PyLIDCAdapter()
        repo = DocumentRepository()

        # Query a single scan from PYLIDC
        scan = pl.query(pl.Scan).first()

        if not scan:
            print("⚠️  No PYLIDC scans found. Make sure LIDC-IDRI dataset is downloaded.")
            return

        print(f"📄 Processing scan: {scan.patient_id}")

        # Convert to canonical format
        canonical_doc = adapter.scan_to_canonical(scan, cluster_nodules=True)

        # Insert into Supabase
        doc, content = repo.insert_canonical_document(
            canonical_doc,
            source_file=f"pylidc://{scan.patient_id}",
            uploaded_by="demo_user",
            tags=["LIDC-IDRI", "radiology", "demo"]
        )

        print(f"✅ Imported document: {doc.id}")
        print(f"   Study UID: {canonical_doc.study_instance_uid}")
        print(f"   Nodules: {len(canonical_doc.nodules)}")
        print(f"   Confidence: {content.confidence_score}")
        print()

    except ImportError:
        print("⚠️  pylidc not installed. Install with: pip install pylidc")
    except Exception as e:
        print(f"❌ Error: {e}")


def example_3_querying_documents():
    """Example 3: Query documents"""
    print("=" * 70)
    print("Example 3: Querying Documents")
    print("=" * 70)

    repo = DocumentRepository()

    # Get recent documents
    recent_docs = repo.get_recent_documents(limit=5, status='completed')

    print(f"📋 Recent documents ({len(recent_docs)}):")
    for doc in recent_docs:
        print(f"   • {doc.source_file_name} - {doc.source_system}")

    # Get documents by source system
    lidc_docs = repo.get_documents_by_source_system("LIDC-IDRI")

    print(f"\n📊 LIDC-IDRI documents: {len(lidc_docs)}")

    # Get statistics
    stats = repo.get_statistics()

    print(f"\n📈 Repository Statistics:")
    print(f"   Total documents: {stats['total_documents']}")
    print(f"   By status: {stats['by_status']}")
    print(f"   By system: {stats['by_source_system']}")
    print()


def example_4_full_text_search():
    """Example 4: Full-text search"""
    print("=" * 70)
    print("Example 4: Full-Text Search")
    print("=" * 70)

    repo = DocumentRepository()

    # Search for documents
    search_term = "LIDC"
    results = repo.search_documents(search_term, limit=10)

    print(f"🔍 Search results for '{search_term}': {len(results)} found")

    for doc, content in results[:5]:  # Show first 5
        print(f"   • {doc.source_file_name}")
        print(f"     Tags: {content.tags}")
        print(f"     Searchable: {content.searchable_text[:100]}...")

    print()


def example_5_batch_operations():
    """Example 5: Batch import (simulated)"""
    print("=" * 70)
    print("Example 5: Batch Operations")
    print("=" * 70)

    try:
        import pylidc as pl

        adapter = PyLIDCAdapter()
        repo = DocumentRepository()

        # Query multiple scans
        scans = pl.query(pl.Scan).limit(3).all()

        if not scans:
            print("⚠️  No PYLIDC scans found.")
            return

        print(f"📦 Processing batch of {len(scans)} scans...")

        # Convert all scans
        canonical_docs = []
        source_files = []

        for scan in scans:
            canonical_doc = adapter.scan_to_canonical(scan)
            canonical_docs.append(canonical_doc)
            source_files.append(f"pylidc://{scan.patient_id}")

        # Batch insert
        def progress(current, total):
            print(f"   Progress: {current}/{total}")

        results = repo.batch_insert_canonical_documents(
            canonical_docs=canonical_docs,
            source_files=source_files,
            uploaded_by="batch_demo",
            tags=["LIDC-IDRI", "batch_import"],
            progress_callback=progress
        )

        print(f"✅ Batch import complete: {len(results)}/{len(scans)} succeeded")
        print()

    except ImportError:
        print("⚠️  pylidc not installed.")
    except Exception as e:
        print(f"❌ Error: {e}")


def example_6_advanced_queries():
    """Example 6: Advanced queries using canonical data"""
    print("=" * 70)
    print("Example 6: Advanced Queries (JSONB)")
    print("=" * 70)

    repo = DocumentRepository()

    # This is a placeholder - in production you'd use raw SQL or SQLAlchemy queries
    # to query JSONB fields in canonical_data

    print("💡 Advanced queries can leverage PostgreSQL JSONB operators:")
    print("   • canonical_data->>'study_instance_uid'")
    print("   • canonical_data->'nodules'")
    print("   • canonical_data @> '{\"modality\": \"CT\"}'")
    print()
    print("   See migrations/002_radiology_supabase.sql for helper functions:")
    print("   • get_study_metadata(doc_id)")
    print("   • search_nodules_by_malignancy(min_malignancy, limit)")
    print()


def main():
    """Run all examples"""
    print()
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 20 + "Supabase Integration Examples" + " " * 19 + "║")
    print("╚" + "═" * 68 + "╝")
    print()

    # Check environment
    supabase_url = os.getenv("SUPABASE_DB_URL")
    if not supabase_url:
        print("⚠️  SUPABASE_DB_URL not set in environment!")
        print("   Please set it in your .env file or export it:")
        print("   export SUPABASE_DB_URL='postgresql://postgres:...@db.xxx.supabase.co:5432/postgres'")
        print()
        return

    print(f"✅ Connected to: {supabase_url[:50]}...")
    print()

    # Run examples
    try:
        example_1_basic_insertion()
        example_2_pylidc_import()
        example_3_querying_documents()
        example_4_full_text_search()
        example_5_batch_operations()
        example_6_advanced_queries()

        print("=" * 70)
        print("✅ All examples complete!")
        print("=" * 70)

    except Exception as e:
        print(f"\n❌ Example failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
