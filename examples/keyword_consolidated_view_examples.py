#!/usr/bin/env python3
"""
Keyword Consolidated View Examples

This script demonstrates how to use the consolidated keyword view and
the enhanced keyword repository with the new fields (definition, source_refs, etc.)

Prerequisites:
    1. Apply migration 002: bash scripts/apply_keyword_migration.sh
    2. Import keyword data: python scripts/import_keyword_csv.py data/keywords_radiology_standard.csv

Usage:
    python examples/keyword_consolidated_view_examples.py
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

from maps.database.keyword_repository import KeywordRepository


def example_1_get_all_keywords():
    """Example 1: Get all keywords with consolidated view data"""
    print("\n" + "=" * 70)
    print("Example 1: Get All Keywords (Consolidated View)")
    print("=" * 70)

    repo = KeywordRepository(
        database='ra_d_ps_db',
        user='ra_d_ps_user',
        password='changeme'
    )

    # Get first 10 keywords
    keywords = repo.get_all_keywords(limit=10)

    print(f"\nFound {len(keywords)} keywords:\n")

    for kw in keywords:
        print(f"Keyword: {kw.keyword_text}")
        print(f"  ID: {kw.keyword_id}")
        print(f"  Category: {kw.category}")
        print(f"  Normalized: {kw.normalized_form}")

        if kw.definition:
            print(f"  Definition: {kw.definition[:100]}...")

        if kw.source_refs:
            print(f"  References: {kw.source_refs}")

        if kw.vocabulary_source:
            print(f"  Vocabulary: {kw.vocabulary_source}")

        # Statistics (if available)
        if hasattr(kw, 'statistics') and kw.statistics:
            stats = kw.statistics
            print(f"  Frequency: {stats.total_frequency}")
            print(f"  Documents: {stats.document_count}")

        print()

    repo.close()


def example_2_search_keywords():
    """Example 2: Search keywords by text pattern"""
    print("\n" + "=" * 70)
    print("Example 2: Search Keywords")
    print("=" * 70)

    repo = KeywordRepository()

    # Search for keywords containing "lung"
    search_term = "lung"
    results = repo.search_keywords(query=search_term, limit=20)

    print(f"\nSearch results for '{search_term}' ({len(results)} found):\n")

    for kw in results:
        print(f"• {kw.keyword_text} ({kw.category})")
        if kw.definition:
            print(f"  Definition: {kw.definition[:80]}...")
        print()

    repo.close()


def example_3_get_by_category():
    """Example 3: Get keywords by category"""
    print("\n" + "=" * 70)
    print("Example 3: Get Keywords by Category")
    print("=" * 70)

    repo = KeywordRepository()

    # Get imaging biomarker keywords
    category = 'imaging_biomarkers_and_computation'
    keywords = repo.get_keywords_by_category(category)

    print(f"\nKeywords in '{category}' ({len(keywords)} found):\n")

    for kw in keywords:
        print(f"• {kw.keyword_text}")
        if kw.definition:
            print(f"  {kw.definition[:100]}...")
        if kw.source_refs:
            print(f"  References: {kw.source_refs}")
        print()

    repo.close()


def example_4_add_keyword_with_metadata():
    """Example 4: Add a new keyword with full metadata"""
    print("\n" + "=" * 70)
    print("Example 4: Add Keyword with Metadata")
    print("=" * 70)

    repo = KeywordRepository()

    # Add a new keyword with all fields
    keyword_text = "test_keyword_example"

    keyword = repo.add_keyword(
        keyword_text=keyword_text,
        category='testing',
        normalized_form=keyword_text.lower(),
        description='Internal note: This is a test keyword',
        definition='Formal definition: A keyword created for testing purposes',
        source_refs='100;101;102',
        is_standard=True,
        vocabulary_source='test_vocabulary'
    )

    print(f"\nAdded keyword:")
    print(f"  ID: {keyword.keyword_id}")
    print(f"  Text: {keyword.keyword_text}")
    print(f"  Category: {keyword.category}")
    print(f"  Definition: {keyword.definition}")
    print(f"  Source Refs: {keyword.source_refs}")
    print(f"  Is Standard: {bool(keyword.is_standard)}")
    print(f"  Vocabulary: {keyword.vocabulary_source}")

    # Clean up (optional - comment out to keep the test keyword)
    # Note: Direct deletion requires session management
    # For now, we'll leave it in the database
    print("\nNote: Test keyword left in database for demonstration")

    repo.close()


def example_5_get_keyword_with_sources():
    """Example 5: Get keyword with source information"""
    print("\n" + "=" * 70)
    print("Example 5: Get Keyword with Sources")
    print("=" * 70)

    repo = KeywordRepository()

    # Get a specific keyword by text
    keyword_text = "RADS"
    keyword = repo.get_keyword_by_text(keyword_text)

    if keyword:
        print(f"\nKeyword: {keyword.keyword_text}")
        print(f"  ID: {keyword.keyword_id}")
        print(f"  Category: {keyword.category}")
        print(f"  Definition: {keyword.definition}")
        print(f"  Source Refs: {keyword.source_refs}")

        # Get sources for this keyword
        sources = repo.get_sources_for_keyword(keyword.keyword_id)

        print(f"\n  Sources ({len(sources)} found):")
        for source in sources[:5]:  # Show first 5
            print(f"    - {source.source_file} ({source.source_type})")
            print(f"      Frequency: {source.frequency}")
            if source.context:
                print(f"      Context: {source.context[:80]}...")
            print()

        # Get statistics
        stats = repo.get_keyword_statistics(keyword.keyword_id)
        if stats:
            print("  Statistics:")
            print(f"    Total Frequency: {stats.total_frequency}")
            print(f"    Document Count: {stats.document_count}")
            print(f"    IDF Score: {stats.idf_score:.4f}")
            print(f"    Avg TF-IDF: {stats.avg_tf_idf:.4f}")
    else:
        print(f"\nKeyword '{keyword_text}' not found")

    repo.close()


def example_6_get_top_keywords():
    """Example 6: Get top keywords by frequency"""
    print("\n" + "=" * 70)
    print("Example 6: Get Top Keywords by Frequency")
    print("=" * 70)

    repo = KeywordRepository()

    # Get top 20 keywords by frequency
    top_keywords = repo.get_top_keywords(limit=20)

    print(f"\nTop 20 keywords by frequency:\n")

    for idx, (keyword, stats) in enumerate(top_keywords, start=1):
        print(f"{idx}. {keyword.keyword_text}")
        print(f"   Category: {keyword.category}")
        print(f"   Frequency: {stats.total_frequency}")
        print(f"   Documents: {stats.document_count}")
        if keyword.definition:
            print(f"   Definition: {keyword.definition[:80]}...")
        print()

    repo.close()


def example_7_search_with_sql():
    """Example 7: Direct SQL query on consolidated view"""
    print("\n" + "=" * 70)
    print("Example 7: Direct SQL Query (Consolidated View)")
    print("=" * 70)

    repo = KeywordRepository()

    # Execute custom SQL query on the consolidated view
    session = repo._get_session()

    try:
        # Query the consolidated view
        sql = """
        SELECT
            keyword_text,
            category,
            definition,
            source_refs,
            total_frequency,
            document_count,
            synonym_count,
            unique_source_files
        FROM v_keyword_consolidated
        WHERE category = 'standardization_and_reporting'
        ORDER BY keyword_text
        LIMIT 10;
        """

        result = session.execute(sql)
        rows = result.fetchall()

        print(f"\nStandardization & Reporting Keywords ({len(rows)} shown):\n")

        for row in rows:
            print(f"• {row[0]}")  # keyword_text
            print(f"  Category: {row[1]}")
            if row[2]:  # definition
                print(f"  Definition: {row[2][:100]}...")
            if row[3]:  # source_refs
                print(f"  References: {row[3]}")
            if row[4]:  # total_frequency
                print(f"  Frequency: {row[4]}, Documents: {row[5]}")
            print()

    finally:
        session.close()

    repo.close()


def main():
    """Run all examples"""
    print("\n")
    print("=" * 70)
    print(" Keyword Consolidated View Examples")
    print("=" * 70)
    print("\nThis script demonstrates the enhanced keyword repository")
    print("with consolidated view, definition, and source_refs support.")
    print("\nPrerequisites:")
    print("  1. PostgreSQL database running (docker-compose up -d)")
    print("  2. Migration 002 applied (bash scripts/apply_keyword_migration.sh)")
    print("  3. Keyword data imported (python scripts/import_keyword_csv.py data/keywords_radiology_standard.csv)")
    print("\n" + "=" * 70)

    try:
        # Run examples
        example_1_get_all_keywords()
        example_2_search_keywords()
        example_3_get_by_category()
        example_4_add_keyword_with_metadata()
        example_5_get_keyword_with_sources()
        example_6_get_top_keywords()
        example_7_search_with_sql()

        print("\n" + "=" * 70)
        print("✅ All examples completed successfully!")
        print("=" * 70)

    except Exception as e:
        print("\n" + "=" * 70)
        print("❌ Error running examples:")
        print("=" * 70)
        print(f"\n{e}")
        print("\nPlease ensure:")
        print("  1. PostgreSQL is running")
        print("  2. Database credentials are correct")
        print("  3. Migration 002 has been applied")
        print("  4. Keyword data has been imported")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
