"""
Apply original MAPS migrations from migrations/ directory.

This script analyzes the migrations and provides guidance on applying them
in the correct order, handling duplicates and dependencies.
"""

import os
import sys
from pathlib import Path
from typing import List, Tuple, Dict
import re

# Migration directory
MIGRATIONS_DIR = Path(__file__).parent.parent / "migrations"


def parse_migration_filename(filename: str) -> Tuple[int, str, str]:
    """Extract migration number, name, and full filename."""
    match = re.match(r'(\d+)_(.+)\.sql$', filename)
    if match:
        number = int(match.group(1))
        name = match.group(2)
        return (number, name, filename)
    return (999, filename.replace('.sql', ''), filename)


def get_migrations() -> List[Tuple[int, str, Path]]:
    """Get all migration files sorted by number."""
    if not MIGRATIONS_DIR.exists():
        print(f"Error: Migrations directory not found: {MIGRATIONS_DIR}")
        sys.exit(1)

    migrations = []
    for file in MIGRATIONS_DIR.glob("*.sql"):
        number, name, filename = parse_migration_filename(file.name)
        migrations.append((number, name, file))

    # Sort by migration number, then by name
    migrations.sort(key=lambda x: (x[0], x[1]))
    return migrations


def analyze_dependencies(file_path: Path) -> Dict[str, any]:
    """Analyze migration file for dependencies and metadata."""
    content = file_path.read_text()

    # Extract comments at the top
    purpose = ""
    requires = []
    tables_created = []

    for line in content.split('\n')[:50]:  # Check first 50 lines
        if 'Purpose:' in line:
            purpose = line.split('Purpose:')[1].strip()
        if 'Requires:' in line:
            req = line.split('Requires:')[1].strip()
            requires.append(req)
        if 'CREATE TABLE' in line:
            match = re.search(r'CREATE TABLE\s+(?:IF NOT EXISTS\s+)?(\w+)', line)
            if match:
                tables_created.append(match.group(1))

    return {
        'purpose': purpose,
        'requires': requires,
        'tables_created': tables_created
    }


def print_migration_plan():
    """Print detailed migration plan."""
    print("="*80)
    print("MAPS Migration Plan - Using Original Migrations")
    print("="*80)
    print()

    migrations = get_migrations()

    print(f"Found {len(migrations)} migration files:\n")

    # Group by number
    by_number = {}
    for num, name, path in migrations:
        if num not in by_number:
            by_number[num] = []
        by_number[num].append((name, path))

    # Print organized list
    for num in sorted(by_number.keys()):
        files = by_number[num]
        if len(files) > 1:
            print(f"⚠️  Migration {num:03d} - MULTIPLE FILES (needs manual review):")
            for name, path in files:
                info = analyze_dependencies(path)
                print(f"    - {path.name}")
                if info['purpose']:
                    print(f"      Purpose: {info['purpose']}")
                if info['tables_created']:
                    print(f"      Creates: {', '.join(info['tables_created'])}")
            print()
        else:
            name, path = files[0]
            info = analyze_dependencies(path)
            print(f"✓ Migration {num:03d}: {path.name}")
            if info['purpose']:
                print(f"   Purpose: {info['purpose']}")
            if info['tables_created']:
                print(f"   Creates: {', '.join(info['tables_created'][:5])}")
                if len(info['tables_created']) > 5:
                    print(f"            (+ {len(info['tables_created']) - 5} more)")
            print()

    print("="*80)
    print("RECOMMENDATIONS")
    print("="*80)
    print()

    # Check for duplicates
    duplicates = [num for num, files in by_number.items() if len(files) > 1]
    if duplicates:
        print("⚠️  DUPLICATE MIGRATION NUMBERS FOUND")
        print()
        print("The following migration numbers have multiple files:")
        for num in duplicates:
            print(f"  - Migration {num:03d}: {len(by_number[num])} files")
        print()
        print("RECOMMENDATION:")
        print("1. Review each duplicate migration file")
        print("2. Determine which is the primary/current version")
        print("3. Either:")
        print("   a) Rename old versions (e.g., 002_old_radiology_supabase.sql)")
        print("   b) Merge content if both are needed")
        print("   c) Delete obsolete versions")
        print()

    # Check for schema alignment
    print("SCHEMA ALIGNMENT CHECK:")
    print()
    print("Based on src/maps/database/models.py, the following tables are expected:")
    expected_tables = [
        'parse_cases',
        'documents',
        'document_content',
        'profiles',
        'keywords',
        'detection_details',
        'ingestion_logs',
        'batch_metadata'
    ]

    # Find which migrations create these tables
    print()
    for table in expected_tables:
        found_in = []
        for num, files in by_number.items():
            for name, path in files:
                info = analyze_dependencies(path)
                if table in info['tables_created']:
                    found_in.append(f"{num:03d}_{name}")

        if found_in:
            print(f"  ✓ {table}: Created in {', '.join(found_in[:2])}")
        else:
            print(f"  ✗ {table}: NOT FOUND in migrations")

    print()
    print("="*80)
    print("SUGGESTED APPLICATION ORDER")
    print("="*80)
    print()
    print("1. Drop existing partial schema (only case_patterns exists):")
    print("   DROP TABLE IF EXISTS case_patterns CASCADE;")
    print()
    print("2. Apply core migrations:")
    print("   - 001_initial_schema.sql")
    print()
    print("3. Resolve migration 002 duplicates:")
    print("   - Review which 002 file to use")
    print("   - Apply chosen 002 migration")
    print()
    print("4. Continue with remaining migrations 003-016")
    print()
    print("5. Apply performance_indexes.sql last")
    print()
    print("="*80)
    print("NEXT STEPS")
    print("="*80)
    print()
    print("1. Review duplicate migrations manually")
    print("2. Create a single consolidated migration script, or")
    print("3. Apply migrations one by one via Supabase SQL Editor")
    print()
    print("For manual application via Supabase SQL Editor:")
    print("  - Open: https://supabase.com/dashboard/project/lfzijlkdmnnrttsatrtc")
    print("  - Navigate to: SQL Editor")
    print("  - Copy/paste each migration file")
    print("  - Run and verify before moving to next")
    print()


if __name__ == "__main__":
    print_migration_plan()
