#!/usr/bin/env python3
"""
Database Migration Runner for MAPS

Automatically applies SQL migrations in order and tracks applied migrations.
Supports both local PostgreSQL and Supabase.

Usage:
    python scripts/apply_migrations.py                    # Apply all pending migrations
    python scripts/apply_migrations.py --list             # List migration status
    python scripts/apply_migrations.py --target 005       # Apply up to specific migration
    python scripts/apply_migrations.py --rollback 003     # Rollback to specific migration (if supported)
    python scripts/apply_migrations.py --force            # Force reapply all migrations
    python scripts/apply_migrations.py --dry-run          # Show what would be applied without executing
"""

import sys
import os
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import argparse
import logging
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Try to import psycopg2 for PostgreSQL connection
try:
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MigrationRunner:
    """Handles database migration execution and tracking"""

    def __init__(self, db_url: Optional[str] = None, dry_run: bool = False):
        """
        Initialize migration runner

        Args:
            db_url: Database connection URL (uses env vars if not provided)
            dry_run: If True, show what would be done without executing
        """
        self.dry_run = dry_run
        self.migrations_dir = project_root / "migrations"
        self.db_url = db_url or self._get_db_url()
        self.conn = None

        if not HAS_PSYCOPG2:
            logger.error("psycopg2 not installed. Install with: pip install psycopg2-binary")
            sys.exit(1)

    def _get_db_url(self) -> str:
        """Get database URL from environment variables"""
        # Try Supabase first
        supabase_url = os.getenv('SUPABASE_DB_URL')
        if supabase_url:
            logger.info("Using Supabase database")
            return supabase_url

        # Fall back to local PostgreSQL
        host = os.getenv('DB_HOST', 'localhost')
        port = os.getenv('DB_PORT', '5432')
        database = os.getenv('DB_NAME', 'ra_d_ps_db')
        user = os.getenv('DB_USER', 'ra_d_ps_user')
        password = os.getenv('DB_PASSWORD', 'changeme')

        logger.info(f"Using local PostgreSQL: {host}:{port}/{database}")
        return f"postgresql://{user}:{password}@{host}:{port}/{database}"

    def connect(self):
        """Establish database connection"""
        if self.dry_run:
            logger.info("[DRY RUN] Would connect to database")
            return

        try:
            self.conn = psycopg2.connect(self.db_url)
            logger.info("✅ Connected to database")
        except Exception as e:
            logger.error(f"❌ Failed to connect to database: {e}")
            sys.exit(1)

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")

    def create_migrations_table(self):
        """Create schema_migrations table if it doesn't exist"""
        if self.dry_run:
            logger.info("[DRY RUN] Would create schema_migrations table")
            return

        create_table_sql = """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            id SERIAL PRIMARY KEY,
            version VARCHAR(255) NOT NULL UNIQUE,
            filename VARCHAR(500) NOT NULL,
            applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            execution_time_ms INTEGER,
            checksum VARCHAR(64),
            status VARCHAR(50) DEFAULT 'success' CHECK (status IN ('success', 'failed', 'rolled_back'))
        );

        CREATE INDEX IF NOT EXISTS idx_migrations_version ON schema_migrations(version);
        CREATE INDEX IF NOT EXISTS idx_migrations_status ON schema_migrations(status);
        """

        try:
            cursor = self.conn.cursor()
            cursor.execute(create_table_sql)
            self.conn.commit()
            cursor.close()
            logger.info("✅ schema_migrations table ready")
        except Exception as e:
            logger.error(f"❌ Failed to create migrations table: {e}")
            raise

    def get_applied_migrations(self) -> List[str]:
        """Get list of already applied migration versions"""
        if self.dry_run:
            return []

        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT version FROM schema_migrations
                WHERE status = 'success'
                ORDER BY version
            """)
            applied = [row[0] for row in cursor.fetchall()]
            cursor.close()
            return applied
        except Exception as e:
            logger.warning(f"Could not fetch applied migrations: {e}")
            return []

    def get_migration_files(self) -> List[Tuple[str, Path]]:
        """
        Get all migration files sorted by version

        Returns:
            List of (version, filepath) tuples sorted by version
        """
        if not self.migrations_dir.exists():
            logger.error(f"Migrations directory not found: {self.migrations_dir}")
            return []

        migration_files = []
        version_pattern = re.compile(r'^(\d+)_.*\.sql$')

        for sql_file in self.migrations_dir.glob("*.sql"):
            match = version_pattern.match(sql_file.name)
            if match:
                version = match.group(1)
                migration_files.append((version, sql_file))

        # Sort by version number (numeric)
        migration_files.sort(key=lambda x: int(x[0]))

        return migration_files

    def parse_migration_metadata(self, filepath: Path) -> Dict[str, str]:
        """
        Parse metadata from migration file comments

        Returns dict with: description, requires, target
        """
        metadata = {
            'description': '',
            'requires': '',
            'target': ''
        }

        try:
            with open(filepath, 'r') as f:
                # Read first 20 lines for metadata
                for i, line in enumerate(f):
                    if i > 20:
                        break

                    line = line.strip()
                    if 'Purpose:' in line:
                        metadata['description'] = line.split('Purpose:', 1)[1].strip()
                    elif 'Requires:' in line:
                        metadata['requires'] = line.split('Requires:', 1)[1].strip()
                    elif 'Target:' in line:
                        metadata['target'] = line.split('Target:', 1)[1].strip()

        except Exception as e:
            logger.warning(f"Could not parse metadata from {filepath.name}: {e}")

        return metadata

    def calculate_checksum(self, filepath: Path) -> str:
        """Calculate SHA256 checksum of migration file"""
        import hashlib
        sha256 = hashlib.sha256()
        with open(filepath, 'rb') as f:
            sha256.update(f.read())
        return sha256.hexdigest()

    def apply_migration(self, version: str, filepath: Path) -> bool:
        """
        Apply a single migration file

        Args:
            version: Migration version number
            filepath: Path to SQL file

        Returns:
            True if successful, False otherwise
        """
        logger.info(f"📋 Applying migration {version}: {filepath.name}")

        if self.dry_run:
            logger.info(f"[DRY RUN] Would apply: {filepath.name}")
            metadata = self.parse_migration_metadata(filepath)
            if metadata['description']:
                logger.info(f"   Description: {metadata['description']}")
            if metadata['requires']:
                logger.info(f"   Requires: {metadata['requires']}")
            return True

        # Read migration SQL
        try:
            with open(filepath, 'r') as f:
                sql = f.read()
        except Exception as e:
            logger.error(f"❌ Failed to read {filepath.name}: {e}")
            return False

        # Calculate checksum
        checksum = self.calculate_checksum(filepath)

        # Execute migration
        start_time = datetime.now()
        try:
            cursor = self.conn.cursor()

            # Execute the migration SQL
            cursor.execute(sql)

            # Record migration
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
            cursor.execute("""
                INSERT INTO schema_migrations (version, filename, execution_time_ms, checksum, status)
                VALUES (%s, %s, %s, %s, 'success')
                ON CONFLICT (version) DO UPDATE
                SET applied_at = CURRENT_TIMESTAMP,
                    execution_time_ms = EXCLUDED.execution_time_ms,
                    checksum = EXCLUDED.checksum,
                    status = 'success'
            """, (version, filepath.name, execution_time, checksum))

            self.conn.commit()
            cursor.close()

            logger.info(f"✅ Applied {filepath.name} in {execution_time}ms")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to apply {filepath.name}: {e}")
            self.conn.rollback()

            # Record failure
            try:
                cursor = self.conn.cursor()
                cursor.execute("""
                    INSERT INTO schema_migrations (version, filename, status)
                    VALUES (%s, %s, 'failed')
                    ON CONFLICT (version) DO UPDATE SET status = 'failed'
                """, (version, filepath.name))
                self.conn.commit()
                cursor.close()
            except:
                pass

            return False

    def list_migrations(self):
        """List all migrations and their status"""
        print("\n" + "=" * 80)
        print("MIGRATION STATUS")
        print("=" * 80)

        migration_files = self.get_migration_files()
        if not migration_files:
            print("No migration files found")
            return

        applied = set(self.get_applied_migrations()) if not self.dry_run else set()

        print(f"\n{'Version':<8} {'Status':<12} {'File':<40} {'Description':<30}")
        print("-" * 80)

        for version, filepath in migration_files:
            status = "✅ Applied" if version in applied else "⏳ Pending"
            metadata = self.parse_migration_metadata(filepath)
            description = metadata.get('description', '')[:28]

            print(f"{version:<8} {status:<12} {filepath.name:<40} {description:<30}")

        print(f"\nTotal: {len(migration_files)} migrations ({len(applied)} applied, "
              f"{len(migration_files) - len(applied)} pending)")

    def run_migrations(self, target_version: Optional[str] = None, force: bool = False):
        """
        Run all pending migrations

        Args:
            target_version: Apply migrations up to this version (inclusive)
            force: If True, reapply already applied migrations
        """
        print("\n" + "=" * 80)
        print("APPLYING DATABASE MIGRATIONS")
        print("=" * 80)

        if self.dry_run:
            print("\n⚠️  DRY RUN MODE - No changes will be made\n")

        # Get migrations
        migration_files = self.get_migration_files()
        if not migration_files:
            logger.error("No migration files found")
            return False

        logger.info(f"Found {len(migration_files)} migration files")

        # Connect and setup
        if not self.dry_run:
            self.connect()
            self.create_migrations_table()

        applied = set(self.get_applied_migrations())
        logger.info(f"Already applied: {len(applied)} migrations")

        # Filter migrations
        pending_migrations = []
        for version, filepath in migration_files:
            # Check target version
            if target_version and int(version) > int(target_version):
                break

            # Skip if already applied (unless force)
            if version in applied and not force:
                logger.info(f"⏭️  Skipping {filepath.name} (already applied)")
                continue

            pending_migrations.append((version, filepath))

        if not pending_migrations:
            print("\n✅ No pending migrations to apply")
            return True

        logger.info(f"\nWill apply {len(pending_migrations)} migrations:")
        for version, filepath in pending_migrations:
            metadata = self.parse_migration_metadata(filepath)
            desc = metadata.get('description', 'No description')
            logger.info(f"  {version}: {filepath.name} - {desc}")

        if not self.dry_run:
            confirm = input("\nProceed with migration? (yes/no): ")
            if confirm.lower() != 'yes':
                logger.info("Migration cancelled")
                return False

        # Apply migrations
        print()
        success_count = 0
        for version, filepath in pending_migrations:
            if self.apply_migration(version, filepath):
                success_count += 1
            else:
                logger.error("❌ Migration failed, stopping execution")
                break

        # Summary
        print("\n" + "=" * 80)
        print("MIGRATION SUMMARY")
        print("=" * 80)
        print(f"Total migrations: {len(pending_migrations)}")
        print(f"Successful: {success_count}")
        print(f"Failed: {len(pending_migrations) - success_count}")

        if success_count == len(pending_migrations):
            print("\n✅ All migrations applied successfully!")
            return True
        else:
            print("\n❌ Some migrations failed")
            return False


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(
        description="MAPS Database Migration Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/apply_migrations.py                # Apply all pending migrations
  python scripts/apply_migrations.py --list         # List migration status
  python scripts/apply_migrations.py --target 005   # Apply up to migration 005
  python scripts/apply_migrations.py --dry-run      # Show what would be applied
  python scripts/apply_migrations.py --force        # Reapply all migrations
        """
    )

    parser.add_argument(
        '--list', '-l',
        action='store_true',
        help='List all migrations and their status'
    )
    parser.add_argument(
        '--target', '-t',
        type=str,
        help='Apply migrations up to this version (e.g., 005)'
    )
    parser.add_argument(
        '--force', '-f',
        action='store_true',
        help='Force reapply already applied migrations'
    )
    parser.add_argument(
        '--dry-run', '-d',
        action='store_true',
        help='Show what would be done without executing'
    )
    parser.add_argument(
        '--db-url',
        type=str,
        help='Database URL (overrides environment variables)'
    )

    args = parser.parse_args()

    # Create runner
    runner = MigrationRunner(db_url=args.db_url, dry_run=args.dry_run)

    try:
        if args.list:
            if not args.dry_run:
                runner.connect()
                runner.create_migrations_table()
            runner.list_migrations()
        else:
            success = runner.run_migrations(
                target_version=args.target,
                force=args.force
            )
            sys.exit(0 if success else 1)
    finally:
        runner.close()


if __name__ == "__main__":
    main()
