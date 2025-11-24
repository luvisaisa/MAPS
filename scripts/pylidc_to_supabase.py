#!/usr/bin/env python3
"""
PYLIDC to Supabase ETL Pipeline

Complete ETL pipeline for importing LIDC-IDRI dataset into Supabase PostgreSQL.

Usage:
    # Import first 10 scans
    python scripts/pylidc_to_supabase.py --limit 10

    # Import all high-quality scans (slice thickness <= 1mm)
    python scripts/pylidc_to_supabase.py --filter "high_quality" --limit 100

    # Import specific patient
    python scripts/pylidc_to_supabase.py --patient "LIDC-IDRI-0001"

    # Dry run (no database writes)
    python scripts/pylidc_to_supabase.py --dry-run --limit 5

Requirements:
    - SUPABASE_DB_URL environment variable set
    - pylidc installed and configured
    - LIDC-IDRI dataset downloaded
"""

import os
import sys
import argparse
import logging
from datetime import datetime
from typing import Optional, List
from uuid import uuid4
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    import pylidc as pl
    PYLIDC_AVAILABLE = True
except ImportError:
    PYLIDC_AVAILABLE = False
    print("⚠️  pylidc not installed. Install with: pip install pylidc")
    sys.exit(1)

from maps.adapters.pylidc_adapter import PyLIDCAdapter
from maps.database.document_repository import DocumentRepository
from maps.database.db_config import db_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PylidcToSupabasePipeline:
    """ETL Pipeline for PYLIDC → Supabase"""

    def __init__(self, connection_string: Optional[str] = None, dry_run: bool = False):
        """
        Initialize pipeline

        Args:
            connection_string: Supabase database URL
            dry_run: If True, don't write to database
        """
        self.dry_run = dry_run
        self.adapter = PyLIDCAdapter()
        self.batch_id = uuid4()

        if not dry_run:
            if connection_string is None:
                connection_string = os.getenv("SUPABASE_DB_URL")
                if not connection_string:
                    raise ValueError(
                        "SUPABASE_DB_URL environment variable not set. "
                        "Set it to: postgresql://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres"
                    )

            self.repository = DocumentRepository(connection_string=connection_string)
            logger.info("✅ Connected to Supabase")
        else:
            logger.info("🔍 DRY RUN MODE - No database writes")

    def query_scans(
        self,
        filter_type: Optional[str] = None,
        patient_id: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List:
        """
        Query PYLIDC database

        Args:
            filter_type: Predefined filter ('high_quality', 'with_nodules', 'all')
            patient_id: Specific patient ID
            limit: Maximum scans to process

        Returns:
            List of pylidc.Scan objects
        """
        logger.info("🔍 Querying PYLIDC database...")

        query = pl.query(pl.Scan)

        # Apply filters
        if patient_id:
            query = query.filter(pl.Scan.patient_id == patient_id)
            logger.info(f"   Filter: patient_id = {patient_id}")

        elif filter_type == 'high_quality':
            query = query.filter(pl.Scan.slice_thickness <= 1.0)
            logger.info("   Filter: slice_thickness <= 1.0mm (high quality)")

        elif filter_type == 'with_nodules':
            # Only scans that have annotations
            query = query.filter(pl.Scan.annotations.any())
            logger.info("   Filter: scans with nodules")

        elif filter_type == 'all' or filter_type is None:
            logger.info("   Filter: all scans")

        if limit:
            query = query.limit(limit)
            logger.info(f"   Limit: {limit} scans")

        scans = query.all()
        logger.info(f"✅ Found {len(scans)} scans")

        return scans

    def convert_scans(self, scans: List, cluster_nodules: bool = True) -> List:
        """
        Convert PYLIDC scans to canonical documents

        Args:
            scans: List of pylidc.Scan objects
            cluster_nodules: Whether to cluster annotations into nodules

        Returns:
            List of RadiologyCanonicalDocument objects
        """
        logger.info(f"🔄 Converting {len(scans)} scans to canonical format...")

        canonical_docs = []
        for i, scan in enumerate(scans, 1):
            try:
                canonical_doc = self.adapter.scan_to_canonical(
                    scan,
                    cluster_nodules=cluster_nodules
                )
                canonical_docs.append(canonical_doc)

                if i % 10 == 0 or i == len(scans):
                    logger.info(f"   Converted: {i}/{len(scans)}")

            except Exception as e:
                logger.error(f"❌ Failed to convert scan {scan.patient_id}: {e}")
                continue

        logger.info(f"✅ Converted {len(canonical_docs)}/{len(scans)} scans")
        return canonical_docs

    def import_to_supabase(
        self,
        canonical_docs: List,
        scans: List,
        uploaded_by: Optional[str] = None
    ) -> int:
        """
        Import canonical documents to Supabase

        Args:
            canonical_docs: List of RadiologyCanonicalDocument objects
            scans: Corresponding list of pylidc.Scan objects (for patient IDs)
            uploaded_by: User identifier

        Returns:
            Number of documents successfully imported
        """
        if self.dry_run:
            logger.info(f"🔍 DRY RUN: Would import {len(canonical_docs)} documents")
            return len(canonical_docs)

        logger.info(f"📤 Importing {len(canonical_docs)} documents to Supabase...")

        # Build source file identifiers
        source_files = [f"pylidc://{scan.patient_id}" for scan in scans]

        # Batch insert with progress tracking
        def progress_callback(current, total):
            if current % 10 == 0 or current == total:
                logger.info(f"   Imported: {current}/{total}")

        results = self.repository.batch_insert_canonical_documents(
            canonical_docs=canonical_docs,
            source_files=source_files,
            uploaded_by=uploaded_by or "pylidc_pipeline",
            tags=["LIDC-IDRI", "radiology", "lung_nodules"],
            batch_id=self.batch_id,
            progress_callback=progress_callback
        )

        logger.info(f"✅ Successfully imported {len(results)}/{len(canonical_docs)} documents")
        return len(results)

    def run(
        self,
        filter_type: Optional[str] = None,
        patient_id: Optional[str] = None,
        limit: Optional[int] = None,
        cluster_nodules: bool = True,
        uploaded_by: Optional[str] = None
    ) -> dict:
        """
        Run complete ETL pipeline

        Args:
            filter_type: Predefined filter ('high_quality', 'with_nodules', 'all')
            patient_id: Specific patient ID
            limit: Maximum scans to process
            cluster_nodules: Whether to cluster annotations
            uploaded_by: User identifier

        Returns:
            Dictionary with pipeline statistics
        """
        start_time = datetime.now()

        logger.info("=" * 70)
        logger.info("🚀 PYLIDC → Supabase ETL Pipeline")
        logger.info("=" * 70)
        logger.info(f"Batch ID: {self.batch_id}")
        logger.info(f"Start time: {start_time}")
        logger.info("")

        try:
            # Step 1: Query PYLIDC
            scans = self.query_scans(
                filter_type=filter_type,
                patient_id=patient_id,
                limit=limit
            )

            if not scans:
                logger.warning("⚠️  No scans found matching criteria")
                return {'success': False, 'message': 'No scans found'}

            # Step 2: Convert to canonical format
            canonical_docs = self.convert_scans(scans, cluster_nodules=cluster_nodules)

            if not canonical_docs:
                logger.warning("⚠️  No documents converted successfully")
                return {'success': False, 'message': 'Conversion failed'}

            # Step 3: Import to Supabase
            imported_count = self.import_to_supabase(
                canonical_docs,
                scans,
                uploaded_by=uploaded_by
            )

            # Calculate statistics
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            stats = {
                'success': True,
                'batch_id': str(self.batch_id),
                'scans_found': len(scans),
                'scans_converted': len(canonical_docs),
                'documents_imported': imported_count,
                'duration_seconds': duration,
                'avg_time_per_scan': duration / len(scans) if scans else 0
            }

            logger.info("")
            logger.info("=" * 70)
            logger.info("✅ PIPELINE COMPLETE")
            logger.info("=" * 70)
            logger.info(f"Scans found: {stats['scans_found']}")
            logger.info(f"Scans converted: {stats['scans_converted']}")
            logger.info(f"Documents imported: {stats['documents_imported']}")
            logger.info(f"Duration: {duration:.2f} seconds")
            logger.info(f"Avg time per scan: {stats['avg_time_per_scan']:.2f} seconds")
            logger.info(f"Batch ID: {self.batch_id}")
            logger.info("=" * 70)

            return stats

        except Exception as e:
            logger.error(f"❌ Pipeline failed: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Import LIDC-IDRI dataset into Supabase PostgreSQL",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Import first 10 scans
  python scripts/pylidc_to_supabase.py --limit 10

  # Import high-quality scans
  python scripts/pylidc_to_supabase.py --filter high_quality --limit 100

  # Import specific patient
  python scripts/pylidc_to_supabase.py --patient LIDC-IDRI-0001

  # Dry run (no database writes)
  python scripts/pylidc_to_supabase.py --dry-run --limit 5
        """
    )

    parser.add_argument(
        '--filter',
        choices=['high_quality', 'with_nodules', 'all'],
        default='all',
        help='Predefined filter for scans'
    )

    parser.add_argument(
        '--patient',
        type=str,
        help='Specific patient ID to import'
    )

    parser.add_argument(
        '--limit',
        type=int,
        help='Maximum number of scans to process'
    )

    parser.add_argument(
        '--no-clustering',
        action='store_true',
        help='Disable nodule clustering (keep individual annotations)'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run without writing to database'
    )

    parser.add_argument(
        '--connection-string',
        type=str,
        help='Supabase database URL (overrides SUPABASE_DB_URL env var)'
    )

    parser.add_argument(
        '--uploaded-by',
        type=str,
        default='pylidc_pipeline',
        help='User identifier for audit trail'
    )

    args = parser.parse_args()

    # Initialize pipeline
    pipeline = PylidcToSupabasePipeline(
        connection_string=args.connection_string,
        dry_run=args.dry_run
    )

    # Run pipeline
    stats = pipeline.run(
        filter_type=args.filter if not args.patient else None,
        patient_id=args.patient,
        limit=args.limit,
        cluster_nodules=not args.no_clustering,
        uploaded_by=args.uploaded_by
    )

    # Exit with appropriate code
    sys.exit(0 if stats.get('success') else 1)


if __name__ == "__main__":
    main()
