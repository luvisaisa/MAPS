# Database Migration Guide

## Overview

This guide explains how to manage database migrations for the MAPS system using the automated migration runner.

## Migration Script

Location: `scripts/apply_migrations.py`

The migration script provides automated, tracked database schema migrations with the following features:

- Automatic migration tracking via `schema_migrations` table
- Support for both local PostgreSQL and Supabase
- Dry-run mode to preview changes
- Selective migration application (target specific versions)
- Force re-application of migrations
- Migration status listing
- Checksum validation
- Execution time tracking

## Usage

### Apply All Pending Migrations

```bash
python scripts/apply_migrations.py
```

Or using Make:

```bash
make db-migrate
```

This will:
1. Connect to the database
2. Create `schema_migrations` tracking table if needed
3. Check which migrations have been applied
4. Apply all pending migrations in order
5. Record migration status and execution time

### List Migration Status

```bash
python scripts/apply_migrations.py --list
```

Or using Make:

```bash
make db-migrate-list
```

Shows all migrations with their status (Applied/Pending) and descriptions.

### Dry Run (Preview Without Executing)

```bash
python scripts/apply_migrations.py --dry-run
```

Shows what migrations would be applied without actually executing them.

### Apply Migrations Up to Specific Version

```bash
python scripts/apply_migrations.py --target 005
```

Applies migrations 001 through 005 only.

### Force Reapply Migrations

```bash
python scripts/apply_migrations.py --force
```

Reapplies all migrations, even those already applied. Use with caution.

### Custom Database URL

```bash
python scripts/apply_migrations.py --db-url "postgresql://user:pass@host:5432/dbname"
```

Override environment variables with a custom database URL.

## Migration Files

### Location

All migration files are stored in: `/migrations/`

### Naming Convention

Migration files follow the pattern: `NNN_description.sql`

- `NNN`: Three-digit version number (e.g., 001, 002, 003)
- `description`: Brief description of the migration
- Extension: `.sql` (PostgreSQL SQL file)

### Current Migrations

As of this writing, the repository contains 17 migration files:

```
001_initial_schema.sql
002_add_keyword_enhancements.sql
002_unified_case_identifier_schema.sql
002_radiology_supabase.sql
003_analysis_views.sql
003_document_parse_case_links.sql
004_enable_public_access.sql
005_flatten_radiologist_annotations.sql
006_automatic_triggers.sql
007_case_detection_system.sql
008_universal_views.sql
009_lidc_specific_views.sql
010_lidc_3d_contour_views.sql
011_export_views.sql
012_public_access_policies.sql
013_keyword_semantics.sql
014_keyword_navigation_views.sql
```

### Known Issues

**Duplicate Version Numbers**: Multiple migrations have the same version prefix:

- Three `002_*.sql` files
- Two `003_*.sql` files

This creates ambiguity in migration order and tracking. These should be renumbered to unique versions.

### Recommended Renumbering

To resolve version conflicts, consider renumbering as follows:

```
001_initial_schema.sql                     → 001 (keep)
002_add_keyword_enhancements.sql           → 002 (keep)
002_unified_case_identifier_schema.sql     → 003 (rename)
002_radiology_supabase.sql                 → 004 (rename)
003_analysis_views.sql                     → 005 (rename)
003_document_parse_case_links.sql          → 006 (rename)
004_enable_public_access.sql               → 007 (rename)
005_flatten_radiologist_annotations.sql    → 008 (rename)
006_automatic_triggers.sql                 → 009 (rename)
007_case_detection_system.sql              → 010 (rename)
008_universal_views.sql                    → 011 (rename)
009_lidc_specific_views.sql                → 012 (rename)
010_lidc_3d_contour_views.sql              → 013 (rename)
011_export_views.sql                       → 014 (rename)
012_public_access_policies.sql             → 015 (rename)
013_keyword_semantics.sql                  → 016 (rename)
014_keyword_navigation_views.sql           → 017 (rename)
```

## Migration File Format

### Required Metadata

Migration files should include metadata comments at the top:

```sql
-- =====================================================================
-- Migration: Brief description
-- Version: NNN
-- Date: YYYY-MM-DD
-- =====================================================================
-- Purpose: Detailed description of what this migration does
-- Requires: List of prerequisite migrations (e.g., 001_initial_schema.sql)
-- Target: Deployment target (e.g., Local PostgreSQL, Supabase)
-- =====================================================================

-- SQL statements here
```

### Best Practices

1. **Idempotent Operations**: Use `IF NOT EXISTS` and `IF EXISTS` clauses
2. **Transactions**: Wrap in `BEGIN`/`COMMIT` if appropriate
3. **Rollback Support**: Include rollback instructions in comments
4. **Testing**: Test migrations on a copy of production data
5. **Documentation**: Clearly document what the migration does and why

### Example Migration

```sql
-- =====================================================================
-- Migration: Add user preferences table
-- Version: 018
-- Date: 2025-11-23
-- =====================================================================
-- Purpose: Store user-specific UI preferences and settings
-- Requires: 001_initial_schema.sql
-- Target: All environments
-- =====================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS user_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255) NOT NULL,
    preference_key VARCHAR(100) NOT NULL,
    preference_value JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, preference_key)
);

CREATE INDEX idx_user_prefs_user ON user_preferences(user_id);

COMMIT;

-- Rollback:
-- DROP TABLE IF EXISTS user_preferences;
```

## Database Configuration

### Environment Variables

The migration script uses the following environment variables:

**Supabase** (checked first):
```bash
SUPABASE_DB_URL=postgresql://postgres:[password]@db.[project].supabase.co:5432/postgres
```

**Local PostgreSQL** (fallback):
```bash
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ra_d_ps_db
DB_USER=ra_d_ps_user
DB_PASSWORD=changeme
```

### Setting Environment Variables

Create a `.env` file in the project root:

```bash
# .env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ra_d_ps_db
DB_USER=ra_d_ps_user
DB_PASSWORD=changeme
```

The script will automatically load from `.env` if `python-dotenv` is installed.

## Migration Tracking

### schema_migrations Table

The script automatically creates and maintains a `schema_migrations` table:

```sql
CREATE TABLE schema_migrations (
    id SERIAL PRIMARY KEY,
    version VARCHAR(255) NOT NULL UNIQUE,
    filename VARCHAR(500) NOT NULL,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    execution_time_ms INTEGER,
    checksum VARCHAR(64),
    status VARCHAR(50) DEFAULT 'success' CHECK (status IN ('success', 'failed', 'rolled_back'))
);
```

### Checking Applied Migrations

Query the database directly:

```sql
SELECT version, filename, applied_at, execution_time_ms, status
FROM schema_migrations
ORDER BY version;
```

Or use the migration script:

```bash
python scripts/apply_migrations.py --list
```

## Troubleshooting

### Connection Errors

**Error**: `psycopg2.OperationalError: could not connect to server`

**Solutions**:
1. Verify PostgreSQL is running: `docker-compose ps postgres`
2. Check environment variables: `echo $DB_HOST`
3. Test connection: `psql -h localhost -U ra_d_ps_user -d ra_d_ps_db`
4. Ensure database exists: `createdb -U postgres ra_d_ps_db`

### Migration Failures

**Error**: Migration SQL fails to execute

**Solutions**:
1. Check migration file for syntax errors
2. Verify prerequisites are met (check `Requires:` comment)
3. Review error message for specific issue
4. Test migration on development database first
5. Check database permissions

### Version Conflicts

**Error**: Multiple migrations with same version number

**Solution**: Renumber migration files to ensure unique versions (see Recommended Renumbering above)

### Forced Migration

If you need to reapply a specific migration:

```bash
# Mark migration as pending
psql -h localhost -U ra_d_ps_user -d ra_d_ps_db -c \
  "DELETE FROM schema_migrations WHERE version = '005';"

# Reapply
python scripts/apply_migrations.py --target 005
```

Or force reapply all:

```bash
python scripts/apply_migrations.py --force
```

## Integration with Makefile

The migration script is integrated into the Makefile for convenience:

```makefile
# Apply all pending migrations
make db-migrate

# List migration status
make db-migrate-list

# Reset database (drops all data and reapplies migrations)
make db-reset
```

## Creating New Migrations

### Manual Creation

1. Determine next version number:
```bash
ls migrations/*.sql | sort | tail -1
```

2. Create new migration file:
```bash
touch migrations/018_add_feature.sql
```

3. Add SQL content with metadata comments

4. Test migration:
```bash
python scripts/apply_migrations.py --dry-run
```

5. Apply migration:
```bash
python scripts/apply_migrations.py
```

### Future: Migration Generator

Consider creating a migration generator script:

```bash
python scripts/create_migration.py "add user preferences table"
# Creates: migrations/018_add_user_preferences_table.sql
```

## Best Practices

1. **Version Control**: Commit migration files to git
2. **Testing**: Test migrations on development database first
3. **Backups**: Backup production database before applying migrations
4. **Atomic**: Keep migrations focused on a single change
5. **Reversible**: Document rollback steps in comments
6. **Idempotent**: Use `IF EXISTS` clauses to allow re-running
7. **Sequential**: Apply migrations in order
8. **Documentation**: Update this guide when adding major migrations

## References

- PostgreSQL Documentation: https://www.postgresql.org/docs/
- Supabase Migrations: https://supabase.com/docs/guides/database/migrations
- SQLAlchemy Alembic: https://alembic.sqlalchemy.org/ (alternative migration tool)
