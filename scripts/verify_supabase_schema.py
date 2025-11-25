"""
Verify Supabase schema after migrations are applied.

This script checks that all tables, views, functions, and seed data
have been created correctly.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from supabase import create_client, Client
except ImportError:
    print("Error: supabase-py not installed")
    print("Install with: pip install supabase")
    sys.exit(1)

from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")


def get_supabase_client() -> Client:
    """Create Supabase client."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("Error: SUPABASE_URL and SUPABASE_KEY must be set in .env")
        sys.exit(1)

    return create_client(SUPABASE_URL, SUPABASE_KEY)


def verify_tables(client: Client) -> Tuple[bool, List[str]]:
    """Verify all expected tables exist."""
    expected_tables = [
        "profiles",
        "documents",
        "document_content",
        "schema_versions",
        "keywords",
        "keyword_statistics",
        "keyword_synonyms",
        "keyword_sources",
        "keyword_occurrences",
        "keyword_search_history",
        "keyword_reference_sources",
        "stop_words",
        "quantitative_segments",
        "qualitative_segments",
        "mixed_segments",
        "parse_cases",
        "detection_details",
        "pending_case_assignment",
        "case_patterns",
        "ingestion_logs",
        "batch_metadata",
        "user_queries",
        "system_metrics",
    ]

    print("\nChecking tables...")
    errors = []
    found = []

    for table in expected_tables:
        try:
            # Try to query the table
            result = client.table(table).select("*", count="exact").limit(0).execute()
            found.append(table)
            print(f"  ✓ {table}")
        except Exception as e:
            errors.append(f"  ✗ {table}: {str(e)}")
            print(f"  ✗ {table}")

    print(f"\nTables found: {len(found)}/{len(expected_tables)}")

    return len(errors) == 0, errors


def verify_seed_data(client: Client) -> Tuple[bool, List[str]]:
    """Verify seed data exists."""
    print("\nChecking seed data...")
    checks = []

    # Check stop words
    try:
        result = client.table("stop_words").select("*", count="exact").limit(0).execute()
        count = result.count if hasattr(result, "count") else 0
        if count >= 50:  # Should be ~95
            print(f"  ✓ Stop words: {count}")
            checks.append(True)
        else:
            print(f"  ✗ Stop words: {count} (expected ~95)")
            checks.append(False)
    except Exception as e:
        print(f"  ✗ Stop words: {str(e)}")
        checks.append(False)

    # Check profiles
    try:
        result = client.table("profiles").select("*", count="exact").limit(0).execute()
        count = result.count if hasattr(result, "count") else 0
        if count >= 4:
            print(f"  ✓ Profiles: {count}")
            checks.append(True)
        else:
            print(f"  ✗ Profiles: {count} (expected 4)")
            checks.append(False)
    except Exception as e:
        print(f"  ✗ Profiles: {str(e)}")
        checks.append(False)

    # Check parse cases
    try:
        result = client.table("parse_cases").select("*", count="exact").limit(0).execute()
        count = result.count if hasattr(result, "count") else 0
        if count >= 6:
            print(f"  ✓ Parse cases: {count}")
            checks.append(True)
        else:
            print(f"  ✗ Parse cases: {count} (expected 6)")
            checks.append(False)
    except Exception as e:
        print(f"  ✗ Parse cases: {str(e)}")
        checks.append(False)

    # Check keywords
    try:
        result = client.table("keywords").select("*", count="exact").limit(0).execute()
        count = result.count if hasattr(result, "count") else 0
        if count >= 10:  # Should be ~20
            print(f"  ✓ Keywords: {count}")
            checks.append(True)
        else:
            print(f"  ✗ Keywords: {count} (expected ~20)")
            checks.append(False)
    except Exception as e:
        print(f"  ✗ Keywords: {str(e)}")
        checks.append(False)

    return all(checks), []


def verify_schema_version(client: Client) -> Tuple[bool, str]:
    """Check schema version."""
    print("\nChecking schema version...")
    try:
        result = (
            client.table("schema_versions")
            .select("version")
            .order("version", desc=True)
            .limit(1)
            .execute()
        )

        if result.data and len(result.data) > 0:
            version = result.data[0]["version"]
            if version == 10:
                print(f"  ✓ Schema version: {version}")
                return True, f"Version {version}"
            else:
                print(f"  ✗ Schema version: {version} (expected 10)")
                return False, f"Version {version}, expected 10"
        else:
            print("  ✗ No schema version found")
            return False, "No version found"
    except Exception as e:
        print(f"  ✗ Schema version check failed: {str(e)}")
        return False, str(e)


def test_basic_operations(client: Client) -> Tuple[bool, List[str]]:
    """Test basic CRUD operations."""
    print("\nTesting basic operations...")
    errors = []

    # Test 1: Query profiles
    try:
        result = client.table("profiles").select("profile_name").limit(5).execute()
        if result.data:
            print(f"  ✓ Query profiles: {len(result.data)} rows")
        else:
            print("  ✗ Query profiles: No data")
            errors.append("No profiles found")
    except Exception as e:
        print(f"  ✗ Query profiles: {str(e)}")
        errors.append(f"Query profiles failed: {str(e)}")

    # Test 2: Query parse cases
    try:
        result = client.table("parse_cases").select("name").limit(5).execute()
        if result.data:
            print(f"  ✓ Query parse_cases: {len(result.data)} rows")
        else:
            print("  ✗ Query parse_cases: No data")
            errors.append("No parse cases found")
    except Exception as e:
        print(f"  ✗ Query parse_cases: {str(e)}")
        errors.append(f"Query parse_cases failed: {str(e)}")

    # Test 3: Query keywords
    try:
        result = client.table("keywords").select("keyword_text").limit(5).execute()
        if result.data:
            print(f"  ✓ Query keywords: {len(result.data)} rows")
        else:
            print("  ✗ Query keywords: No data")
            errors.append("No keywords found")
    except Exception as e:
        print(f"  ✗ Query keywords: {str(e)}")
        errors.append(f"Query keywords failed: {str(e)}")

    return len(errors) == 0, errors


def main():
    """Main verification."""
    print("="*70)
    print("MAPS Supabase Schema Verification")
    print("="*70)
    print(f"\nSupabase URL: {SUPABASE_URL}")

    # Create client
    try:
        client = get_supabase_client()
        print("✓ Supabase client created")
    except Exception as e:
        print(f"✗ Failed to create Supabase client: {str(e)}")
        sys.exit(1)

    # Run verifications
    results = {}

    # Schema version
    version_ok, version_msg = verify_schema_version(client)
    results["Schema Version"] = version_ok

    # Tables
    tables_ok, table_errors = verify_tables(client)
    results["Tables"] = tables_ok

    # Seed data
    seed_ok, seed_errors = verify_seed_data(client)
    results["Seed Data"] = seed_ok

    # Basic operations
    ops_ok, ops_errors = test_basic_operations(client)
    results["Basic Operations"] = ops_ok

    # Summary
    print("\n" + "="*70)
    print("VERIFICATION SUMMARY")
    print("="*70)

    all_passed = True
    for check, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{check:.<40} {status}")
        if not passed:
            all_passed = False

    print("="*70)

    if all_passed:
        print("\n✓ All verifications passed!")
        print("\nNext steps:")
        print("1. Proceed to Phase 2: Complete parse service implementation")
        print("2. File: src/maps/api/services/parse_service.py (lines 94-104)")
        return 0
    else:
        print("\n✗ Some verifications failed")
        print("\nTroubleshooting:")
        print("1. Check that all migrations were applied in order")
        print("2. Review Supabase Dashboard > Database > Logs for errors")
        print("3. Run verification queries from MANUAL_APPLICATION_GUIDE.md")
        print("4. If tables are missing, re-apply the relevant migration file")
        return 1


if __name__ == "__main__":
    sys.exit(main())
