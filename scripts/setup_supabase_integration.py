#!/usr/bin/env python3
"""
Setup and Verification Script for Supabase Integration

This script helps you:
1. Verify database connection to Supabase
2. Apply migrations
3. Test basic operations
4. Validate the complete pipeline

Usage:
    python scripts/setup_supabase_integration.py --check
    python scripts/setup_supabase_integration.py --migrate
    python scripts/setup_supabase_integration.py --test
    python scripts/setup_supabase_integration.py --full  # All steps
"""

import sys
import os
from pathlib import Path
import argparse

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ra_d_ps.database.document_repository import DocumentRepository
from ra_d_ps.database.enhanced_document_repository import EnhancedDocumentRepository
from ra_d_ps.schemas.canonical import RadiologyCanonicalDocument, DocumentMetadata
from datetime import datetime


def check_environment():
    """Check if environment variables are set correctly"""
    print("=" * 70)
    print("STEP 1: Checking Environment Configuration")
    print("=" * 70)

    required_vars = ['SUPABASE_URL', 'SUPABASE_KEY', 'SUPABASE_DB_URL']
    missing_vars = []

    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Mask the key/password for security
            if 'KEY' in var or 'PASSWORD' in var:
                display_value = value[:10] + "..." if len(value) > 10 else "***"
            else:
                display_value = value[:50] + "..." if len(value) > 50 else value
            print(f"✅ {var}: {display_value}")
        else:
            print(f"❌ {var}: NOT SET")
            missing_vars.append(var)

    if missing_vars:
        print("\n⚠️  Missing environment variables!")
        print("   Please set them in your .env file or export them:")
        print("\n   Example:")
        print("   export SUPABASE_URL='https://xxx.supabase.co'")
        print("   export SUPABASE_KEY='your-anon-key'")
        print("   export SUPABASE_DB_URL='postgresql://postgres:password@db.xxx.supabase.co:5432/postgres'")
        return False

    print("\n✅ All environment variables are set!")
    return True


def test_database_connection():
    """Test connection to Supabase PostgreSQL"""
    print("\n" + "=" * 70)
    print("STEP 2: Testing Database Connection")
    print("=" * 70)

    try:
        repo = DocumentRepository()

        # Try to create tables (will skip if they exist)
        print("📊 Checking database tables...")
        repo.create_tables()

        # Test a simple query
        print("🔍 Testing database query...")
        stats = repo.get_statistics()

        print(f"✅ Connected successfully!")
        print(f"   Total documents: {stats.get('total_documents', 0)}")
        print(f"   By status: {stats.get('by_status', {})}")
        return True

    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("\n💡 Troubleshooting:")
        print("   1. Verify your SUPABASE_DB_URL is correct")
        print("   2. Check that your Supabase project is running")
        print("   3. Ensure your IP is allowed in Supabase dashboard")
        return False


def apply_migrations():
    """Apply database migrations"""
    print("\n" + "=" * 70)
    print("STEP 3: Applying Database Migrations")
    print("=" * 70)

    migrations_dir = Path(__file__).parent.parent / "migrations"
    migration_files = sorted(migrations_dir.glob("*.sql"))

    if not migration_files:
        print("⚠️  No migration files found in migrations/")
        return False

    print(f"📋 Found {len(migration_files)} migration files:")
    for mig in migration_files:
        print(f"   • {mig.name}")

    print("\n💡 To apply migrations, run:")
    print(f"   psql \"$SUPABASE_DB_URL\" -f migrations/001_initial_schema.sql")
    print(f"   psql \"$SUPABASE_DB_URL\" -f migrations/002_radiology_supabase.sql")
    print(f"   psql \"$SUPABASE_DB_URL\" -f migrations/003_document_parse_case_links.sql")

    print("\n   Or use the automated script:")
    print("   make db-migrate  # If using Makefile")

    return True


def test_basic_operations():
    """Test basic CRUD operations"""
    print("\n" + "=" * 70)
    print("STEP 4: Testing Basic Operations")
    print("=" * 70)

    try:
        repo = DocumentRepository()

        # Create test document metadata
        print("📝 Creating test document...")
        metadata = DocumentMetadata(
            document_type="radiology_report",
            title="Setup Verification Test Document",
            date=datetime.utcnow(),
            source_system="SETUP_TEST",
            language="en"
        )

        canonical_doc = RadiologyCanonicalDocument(
            document_metadata=metadata,
            study_instance_uid="1.2.3.4.5.TEST",
            series_instance_uid="1.2.3.4.6.TEST",
            modality="CT",
            nodules=[
                {
                    "nodule_id": "1",
                    "num_radiologists": 1,
                    "radiologists": {
                        "1": {"subtlety": 3, "malignancy": 2}
                    }
                }
            ],
            fields={"test": True}
        )

        # Insert test document
        doc, content = repo.insert_canonical_document(
            canonical_doc,
            source_file="test://setup_verification",
            uploaded_by="setup_script",
            tags=["test", "setup_verification"]
        )

        print(f"✅ Created document: {doc.id}")
        print(f"   Status: {doc.status}")
        print(f"   Tags: {content.tags}")

        # Retrieve document
        print("\n🔍 Retrieving document...")
        retrieved_doc = repo.get_document(doc.id)
        retrieved_content = repo.get_document_content(doc.id)

        if retrieved_doc and retrieved_content:
            print(f"✅ Retrieved successfully!")
            print(f"   File: {retrieved_doc.source_file_name}")
            print(f"   Study UID: {retrieved_content.canonical_data.get('study_instance_uid')}")

        # Clean up test document
        print("\n🗑️  Cleaning up test document...")
        repo.delete_document(doc.id)
        print("✅ Test document deleted")

        return True

    except Exception as e:
        print(f"❌ Basic operations test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_enhanced_operations():
    """Test enhanced operations with parse case and keywords"""
    print("\n" + "=" * 70)
    print("STEP 5: Testing Enhanced Operations (Schema-Agnostic)")
    print("=" * 70)

    try:
        repo = EnhancedDocumentRepository(
            enable_parse_case_tracking=True,
            enable_keyword_extraction=True
        )

        print("📝 Creating test document with enhanced features...")
        metadata = DocumentMetadata(
            document_type="radiology_report",
            title="Enhanced Test Document",
            date=datetime.utcnow(),
            source_system="LIDC-IDRI",
            language="en"
        )

        canonical_doc = RadiologyCanonicalDocument(
            document_metadata=metadata,
            study_instance_uid="1.2.3.4.5.ENHANCED",
            series_instance_uid="1.2.3.4.6.ENHANCED",
            modality="CT",
            nodules=[
                {
                    "nodule_id": "1",
                    "num_radiologists": 4,
                    "radiologists": {
                        "1": {"subtlety": 3, "malignancy": 4, "spiculation": 2},
                        "2": {"subtlety": 4, "malignancy": 5, "spiculation": 3},
                        "3": {"subtlety": 3, "malignancy": 4, "spiculation": 2},
                        "4": {"subtlety": 4, "malignancy": 4, "spiculation": 2}
                    }
                }
            ],
            fields={"test_enhanced": True}
        )

        # Insert with enhanced features
        doc, content, parse_case, keyword_count = repo.insert_canonical_document_enhanced(
            canonical_doc,
            source_file="test://enhanced_verification",
            detect_parse_case=True,
            extract_keywords=True
        )

        print(f"✅ Created enhanced document: {doc.id}")
        print(f"   Parse case detected: {parse_case}")
        print(f"   Keywords extracted: {keyword_count}")

        # Get enhanced statistics
        print("\n📊 Enhanced statistics:")
        stats = repo.get_document_statistics_enhanced()
        print(f"   Total documents: {stats.get('total_documents', 0)}")
        print(f"   Parse cases: {stats.get('parse_cases', {})}")
        print(f"   Top keywords: {list(stats.get('top_keywords', {}).keys())[:5]}")

        # Clean up
        print("\n🗑️  Cleaning up enhanced test document...")
        repo.delete_document(doc.id)
        print("✅ Enhanced test document deleted")

        return True

    except Exception as e:
        print(f"❌ Enhanced operations test failed: {e}")
        print("\n💡 Note: Enhanced operations require parse_cases and keywords tables.")
        print("   Make sure you've applied migration 003:")
        print("   psql \"$SUPABASE_DB_URL\" -f migrations/003_document_parse_case_links.sql")
        import traceback
        traceback.print_exc()
        return False


def test_pylidc_integration():
    """Test PYLIDC integration (if available)"""
    print("\n" + "=" * 70)
    print("STEP 6: Testing PYLIDC Integration (Optional)")
    print("=" * 70)

    try:
        import pylidc as pl
        from ra_d_ps.adapters.pylidc_adapter import PyLIDCAdapter

        print("🔍 Querying PYLIDC database...")
        scan = pl.query(pl.Scan).first()

        if not scan:
            print("⚠️  No PYLIDC scans found in database")
            print("   This is normal if you haven't downloaded the LIDC-IDRI dataset")
            return None

        print(f"✅ Found PYLIDC scan: {scan.patient_id}")

        # Convert to canonical
        print("🔄 Converting to canonical format...")
        adapter = PyLIDCAdapter()
        canonical_doc = adapter.scan_to_canonical(scan)

        print(f"✅ Converted successfully!")
        print(f"   Study UID: {canonical_doc.study_instance_uid}")
        print(f"   Nodules: {len(canonical_doc.nodules)}")

        # Insert to Supabase
        print("💾 Testing insert to Supabase...")
        repo = EnhancedDocumentRepository()
        doc, content, parse_case, keywords = repo.insert_canonical_document_enhanced(
            canonical_doc,
            source_file=f"pylidc://{scan.patient_id}",
            detect_parse_case=True,
            extract_keywords=True
        )

        print(f"✅ Inserted to Supabase!")
        print(f"   Document ID: {doc.id}")
        print(f"   Parse case: {parse_case}")
        print(f"   Keywords: {keywords}")

        # Clean up
        repo.delete_document(doc.id)
        print("✅ Test document cleaned up")

        return True

    except ImportError:
        print("⚠️  PYLIDC not installed")
        print("   To test PYLIDC integration, install with:")
        print("   pip install pylidc")
        return None
    except Exception as e:
        print(f"❌ PYLIDC integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(
        description="Setup and verify Supabase integration for RA-D-PS"
    )
    parser.add_argument(
        '--check', action='store_true',
        help='Check environment and database connection'
    )
    parser.add_argument(
        '--migrate', action='store_true',
        help='Show migration instructions'
    )
    parser.add_argument(
        '--test', action='store_true',
        help='Run basic and enhanced operation tests'
    )
    parser.add_argument(
        '--pylidc', action='store_true',
        help='Test PYLIDC integration'
    )
    parser.add_argument(
        '--full', action='store_true',
        help='Run all steps (check + migrate + test + pylidc)'
    )

    args = parser.parse_args()

    # Default to --full if no args
    if not any(vars(args).values()):
        args.full = True

    print()
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "Supabase Integration Setup" + " " * 26 + "║")
    print("╚" + "═" * 68 + "╝")
    print()

    results = {}

    # Run checks
    if args.check or args.full:
        results['env'] = check_environment()
        if results['env']:
            results['db'] = test_database_connection()
        else:
            print("\n❌ Cannot continue without proper environment configuration")
            return 1

    # Show migration info
    if args.migrate or args.full:
        apply_migrations()

    # Run tests
    if args.test or args.full:
        if results.get('db', True):  # Only if DB connection succeeded
            results['basic'] = test_basic_operations()
            results['enhanced'] = test_enhanced_operations()

    # Test PYLIDC
    if args.pylidc or args.full:
        results['pylidc'] = test_pylidc_integration()

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    for test, result in results.items():
        if result is True:
            print(f"✅ {test.upper()}: PASSED")
        elif result is False:
            print(f"❌ {test.upper()}: FAILED")
        elif result is None:
            print(f"⚠️  {test.upper()}: SKIPPED")

    # Next steps
    print("\n" + "=" * 70)
    print("NEXT STEPS")
    print("=" * 70)

    if all(r in [True, None] for r in results.values()):
        print("✅ Setup complete! You can now:")
        print("   1. Import PYLIDC data:")
        print("      python scripts/pylidc_to_supabase.py --limit 10")
        print()
        print("   2. Use the examples:")
        print("      python examples/supabase_integration.py")
        print("      python examples/enhanced_supabase_pipeline.py")
        print()
        print("   3. Query your data:")
        print("      psql \"$SUPABASE_DB_URL\" -c \"SELECT * FROM documents;\"")
    else:
        print("⚠️  Some tests failed. Please review the errors above.")
        print("   Refer to docs/SUPABASE_SCHEMA_AGNOSTIC_GUIDE.md for help")

    print()
    return 0 if all(r in [True, None] for r in results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
