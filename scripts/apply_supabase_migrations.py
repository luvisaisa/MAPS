"""
Apply Supabase migrations using the Supabase Python client.

This script reads migration files from supabase_migrations/ directory
and applies them to Supabase using the REST API via the Python client.
"""

import os
import sys
from pathlib import Path
from typing import List, Tuple
import time

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from supabase import create_client, Client
except ImportError:
    print("Error: supabase-py not installed")
    print("Install with: pip install supabase")
    sys.exit(1)

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
MIGRATIONS_DIR = Path(__file__).parent.parent / "supabase_migrations"


def get_supabase_client() -> Client:
    """Create Supabase client."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("Error: SUPABASE_URL and SUPABASE_KEY must be set in .env")
        sys.exit(1)

    return create_client(SUPABASE_URL, SUPABASE_KEY)


def get_migration_files() -> List[Path]:
    """Get sorted list of migration files."""
    if not MIGRATIONS_DIR.exists():
        print(f"Error: Migrations directory not found: {MIGRATIONS_DIR}")
        sys.exit(1)

    files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    files = [f for f in files if f.stem.split("_")[0].isdigit()]
    return files


def check_applied_migrations(client: Client) -> List[int]:
    """Check which migrations have already been applied."""
    try:
        result = client.table("schema_versions").select("version").execute()
        return [row["version"] for row in result.data]
    except Exception as e:
        # Table might not exist yet
        return []


def apply_migration(client: Client, file_path: Path) -> Tuple[bool, str]:
    """
    Apply a single migration file.

    Note: This uses the Supabase REST API which has limitations.
    For best results, use the Supabase SQL Editor directly.
    """
    print(f"\n{'='*70}")
    print(f"Applying: {file_path.name}")
    print(f"{'='*70}")

    try:
        # Read SQL file
        sql_content = file_path.read_text()

        # Split into statements (basic split on semicolons)
        # This is a simplified approach - complex SQL might need better parsing
        statements = [s.strip() for s in sql_content.split(";") if s.strip()]

        print(f"Found {len(statements)} SQL statements")

        # Note: Supabase REST API doesn't support arbitrary SQL execution
        # This is a limitation - we need to use the SQL Editor or direct psql
        print("\nWARNING: Supabase REST API cannot execute arbitrary SQL")
        print("You must use one of these methods:")
        print("1. Supabase Dashboard SQL Editor (recommended)")
        print("2. Direct psql connection (requires network access)")
        print("3. Supabase CLI (if installed)")

        return False, "REST API limitations - use SQL Editor"

    except Exception as e:
        error_msg = f"Error: {str(e)}"
        print(error_msg)
        return False, error_msg


def main():
    """Main execution."""
    print("MAPS Supabase Migration Tool")
    print("="*70)

    # Check Supabase connection
    print(f"\nSupabase URL: {SUPABASE_URL}")
    client = get_supabase_client()

    # Get migration files
    migration_files = get_migration_files()
    print(f"\nFound {len(migration_files)} migration files:")
    for f in migration_files:
        print(f"  - {f.name}")

    # Check which migrations are applied
    print("\nChecking applied migrations...")
    applied = check_applied_migrations(client)
    if applied:
        print(f"Already applied: {applied}")
    else:
        print("No migrations applied yet (or schema_versions table doesn't exist)")

    print("\n" + "="*70)
    print("IMPORTANT: Supabase REST API Limitations")
    print("="*70)
    print("\nThe Supabase Python client cannot execute DDL statements (CREATE TABLE, etc.)")
    print("You must apply migrations using one of these methods:")
    print("\n1. RECOMMENDED: Supabase Dashboard SQL Editor")
    print("   a. Open: https://supabase.com/dashboard/project/lfzijlkdmnnrttsatrtc")
    print("   b. Navigate to: SQL Editor")
    print("   c. Click: + New query")
    print("   d. Copy/paste each migration file in order (001 through 010)")
    print("   e. Click: Run")
    print("   f. Verify success before moving to next file")

    print("\n2. Direct psql (if network access available):")
    print("   cd supabase_migrations")
    print("   psql \"<YOUR_CONNECTION_STRING>\" -f 001_extensions_and_types.sql")
    print("   # Repeat for all files")

    print("\n3. Supabase CLI (if installed):")
    print("   supabase db push")
    print("   # Requires supabase CLI setup")

    print("\n" + "="*70)
    print("Quick Copy Commands for SQL Editor:")
    print("="*70)

    for i, file_path in enumerate(migration_files, 1):
        print(f"\n[{i}/10] {file_path.name}")
        print(f"File path: {file_path}")
        print(f"Command to view: cat {file_path}")


if __name__ == "__main__":
    main()
