#!/usr/bin/env python3
"""
Import Keywords from CSV to Database

This script imports standardized radiology keywords from a CSV file into the
PostgreSQL keywords table. The CSV should have the following columns:
- id: Numeric identifier (not used as primary key, for reference only)
- category: Keyword category
- keyword: The keyword text
- definition: Medical/technical definition
- source_refs: Semicolon-separated reference IDs

Usage:
    python scripts/import_keyword_csv.py <csv_file> [options]

Examples:
    # Import from CSV file
    python scripts/import_keyword_csv.py data/keywords.csv

    # Import with specific database credentials
    python scripts/import_keyword_csv.py data/keywords.csv --user ra_d_ps_user --password changeme

    # Import and mark as standard vocabulary
    python scripts/import_keyword_csv.py data/keywords.csv --vocabulary-source "RadLex"
"""

import os
import sys
import csv
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

from maps.database.keyword_repository import KeywordRepository
from maps.database.keyword_models import Keyword

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_arguments():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description='Import keywords from CSV to PostgreSQL database',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        'csv_file',
        type=str,
        help='Path to CSV file containing keyword data'
    )

    parser.add_argument(
        '--database',
        type=str,
        default='ra_d_ps_db',
        help='Database name (default: ra_d_ps_db)'
    )

    parser.add_argument(
        '--host',
        type=str,
        default='localhost',
        help='Database host (default: localhost)'
    )

    parser.add_argument(
        '--port',
        type=int,
        default=5432,
        help='Database port (default: 5432)'
    )

    parser.add_argument(
        '--user',
        type=str,
        default='ra_d_ps_user',
        help='Database user (default: ra_d_ps_user)'
    )

    parser.add_argument(
        '--password',
        type=str,
        default='changeme',
        help='Database password (default: changeme)'
    )

    parser.add_argument(
        '--vocabulary-source',
        type=str,
        default='radiology_standard',
        help='Vocabulary source name (default: radiology_standard)'
    )

    parser.add_argument(
        '--is-standard',
        action='store_true',
        help='Mark all imported keywords as standard vocabulary terms'
    )

    parser.add_argument(
        '--skip-existing',
        action='store_true',
        help='Skip keywords that already exist in the database'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be imported without actually importing'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    return parser.parse_args()


def validate_csv_file(csv_path: str) -> bool:
    """
    Validate that the CSV file exists and has the required columns.

    Args:
        csv_path: Path to CSV file

    Returns:
        True if valid, False otherwise
    """
    if not os.path.exists(csv_path):
        logger.error(f"CSV file not found: {csv_path}")
        return False

    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames

            required_columns = {'id', 'category', 'keyword', 'definition', 'source_refs'}
            missing_columns = required_columns - set(headers)

            if missing_columns:
                logger.error(f"Missing required columns: {missing_columns}")
                logger.error(f"Found columns: {headers}")
                return False

            logger.info(f"CSV file validated: {csv_path}")
            logger.info(f"Columns: {headers}")
            return True

    except Exception as e:
        logger.error(f"Error validating CSV file: {e}")
        return False


def read_csv_keywords(csv_path: str) -> List[Dict]:
    """
    Read keywords from CSV file.

    Args:
        csv_path: Path to CSV file

    Returns:
        List of keyword dictionaries
    """
    keywords = []

    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row_num, row in enumerate(reader, start=2):  # Start at 2 (1 is header)
                # Validate required fields
                if not row.get('keyword') or not row.get('category'):
                    logger.warning(f"Row {row_num}: Missing keyword or category, skipping")
                    continue

                keyword_data = {
                    'csv_id': row.get('id'),
                    'keyword_text': row['keyword'].strip(),
                    'category': row['category'].strip(),
                    'definition': row.get('definition', '').strip(),
                    'source_refs': row.get('source_refs', '').strip(),
                    'normalized_form': row['keyword'].strip().lower()
                }

                keywords.append(keyword_data)

        logger.info(f"Read {len(keywords)} keywords from CSV")
        return keywords

    except Exception as e:
        logger.error(f"Error reading CSV file: {e}")
        raise


def import_keywords(
    keywords: List[Dict],
    repository: KeywordRepository,
    vocabulary_source: str,
    is_standard: bool,
    skip_existing: bool,
    dry_run: bool
) -> Dict[str, int]:
    """
    Import keywords into the database.

    Args:
        keywords: List of keyword dictionaries
        repository: KeywordRepository instance
        vocabulary_source: Source vocabulary name
        is_standard: Mark as standard vocabulary
        skip_existing: Skip existing keywords
        dry_run: Don't actually import

    Returns:
        Dictionary with import statistics
    """
    stats = {
        'total': len(keywords),
        'imported': 0,
        'skipped': 0,
        'errors': 0
    }

    logger.info(f"Starting import of {stats['total']} keywords...")

    for idx, kw_data in enumerate(keywords, start=1):
        keyword_text = kw_data['keyword_text']

        try:
            # Check if keyword already exists
            if skip_existing:
                existing = repository.get_keyword_by_text(keyword_text)
                if existing:
                    logger.debug(f"[{idx}/{stats['total']}] Skipping existing keyword: {keyword_text}")
                    stats['skipped'] += 1
                    continue

            if dry_run:
                logger.info(f"[DRY RUN] Would import: {keyword_text} ({kw_data['category']})")
                stats['imported'] += 1
                continue

            # Import keyword
            keyword = repository.add_keyword(
                keyword_text=keyword_text,
                category=kw_data['category'],
                normalized_form=kw_data['normalized_form'],
                definition=kw_data['definition'] or None,
                source_refs=kw_data['source_refs'] or None,
                is_standard=is_standard,
                vocabulary_source=vocabulary_source
            )

            logger.debug(f"[{idx}/{stats['total']}] Imported: {keyword_text} (id={keyword.keyword_id})")
            stats['imported'] += 1

            # Log progress every 10 keywords
            if idx % 10 == 0:
                logger.info(f"Progress: {idx}/{stats['total']} keywords processed")

        except Exception as e:
            logger.error(f"[{idx}/{stats['total']}] Error importing '{keyword_text}': {e}")
            stats['errors'] += 1
            continue

    return stats


def print_summary(stats: Dict[str, int], start_time: datetime, dry_run: bool):
    """
    Print import summary.

    Args:
        stats: Import statistics
        start_time: Import start time
        dry_run: Whether this was a dry run
    """
    duration = (datetime.now() - start_time).total_seconds()

    print("\n" + "=" * 70)
    if dry_run:
        print("DRY RUN SUMMARY")
    else:
        print("IMPORT SUMMARY")
    print("=" * 70)
    print(f"Total keywords:     {stats['total']}")
    print(f"Imported:           {stats['imported']}")
    print(f"Skipped:            {stats['skipped']}")
    print(f"Errors:             {stats['errors']}")
    print(f"Duration:           {duration:.2f} seconds")
    print("=" * 70)

    if stats['errors'] > 0:
        print("\n⚠️  WARNING: Some keywords failed to import. Check logs for details.")
    elif dry_run:
        print("\n✅ Dry run completed successfully. Run without --dry-run to import.")
    else:
        print("\n✅ Import completed successfully!")


def main():
    """Main execution function"""
    args = parse_arguments()

    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Validate CSV file
    if not validate_csv_file(args.csv_file):
        sys.exit(1)

    # Read keywords from CSV
    try:
        keywords = read_csv_keywords(args.csv_file)
    except Exception as e:
        logger.error(f"Failed to read CSV file: {e}")
        sys.exit(1)

    if not keywords:
        logger.error("No keywords found in CSV file")
        sys.exit(1)

    # Connect to database
    logger.info(f"Connecting to database: {args.database} at {args.host}:{args.port}")

    try:
        repository = KeywordRepository(
            database=args.database,
            host=args.host,
            port=args.port,
            user=args.user,
            password=args.password
        )
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        sys.exit(1)

    # Import keywords
    start_time = datetime.now()

    try:
        stats = import_keywords(
            keywords=keywords,
            repository=repository,
            vocabulary_source=args.vocabulary_source,
            is_standard=args.is_standard,
            skip_existing=args.skip_existing,
            dry_run=args.dry_run
        )
    except Exception as e:
        logger.error(f"Import failed: {e}")
        sys.exit(1)
    finally:
        repository.close()

    # Print summary
    print_summary(stats, start_time, args.dry_run)


if __name__ == '__main__':
    main()
