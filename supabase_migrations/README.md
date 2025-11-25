# MAPS Supabase Schema Migrations

Complete database schema for MAPS (Medical/Multiformat Agnostic Processing System) designed for Supabase PostgreSQL.

## Overview

This migration suite implements a comprehensive schema-agnostic document processing system with:
- Unified file ingestion (XML, JSON, CSV, PDF, DOCX, etc.)
- Content-based segment classification (quantitative, qualitative, mixed)
- Keyword extraction with cross-type validation
- Confidence-based case detection with approval queue
- Full audit trail with performance metrics

## Migration Files

| File | Description | Dependencies |
|------|-------------|--------------|
| `001_extensions_and_types.sql` | PostgreSQL extensions and custom ENUM types | None |
| `002_utility_functions.sql` | Reusable trigger functions and utilities | 001 |
| `003_core_tables.sql` | Core tables (profiles, documents, document_content) | 002 |
| `004_keyword_tables.sql` | Keyword system tables | 003 |
| `005_segment_tables.sql` | Content segments (quan/qual/mixed) + keyword occurrences | 003, 004 |
| `006_case_detection_tables.sql` | Parse cases, detection details, approval queue | 003, 004 |
| `007_audit_tables.sql` | Ingestion logs, batch metadata, user queries | 003 |
| `008_views.sql` | Database views for common UI query patterns | All tables |
| `009_functions.sql` | Stored procedures for detection and search | All tables |
| `010_seed_data.sql` | Initial data (stop words, profiles, parse cases) | All tables |

## Prerequisites

- Supabase project (Free tier or higher)
- PostgreSQL 15+ (Supabase default)
- Database access via Supabase SQL Editor or direct connection

## Application Methods

### Method 1: Supabase SQL Editor (Recommended)

1. Open your Supabase project
2. Navigate to **SQL Editor** in the left sidebar
3. Create a new query
4. Copy and paste the contents of each migration file **in order**
5. Click **Run** for each migration
6. Verify success with the verification queries at the bottom of each file

**Pros:**
- Works on all Supabase tiers (including Free)
- No additional tools required
- Built-in error reporting

**Cons:**
- Manual process for each file
- No automatic rollback on error

### Method 2: Direct PostgreSQL Connection

If you have direct PostgreSQL access (connection pooler):

```bash
# Get your connection string from Supabase Dashboard > Settings > Database
# Connection pooler format:
# postgresql://postgres.PROJECT_REF:[PASSWORD]@aws-0-us-west-1.pooler.supabase.com:6543/postgres

# Apply migrations
psql "YOUR_CONNECTION_STRING" -f 001_extensions_and_types.sql
psql "YOUR_CONNECTION_STRING" -f 002_utility_functions.sql
psql "YOUR_CONNECTION_STRING" -f 003_core_tables.sql
# ... continue for all files
```

**Pros:**
- Can automate with scripts
- Transaction control

**Cons:**
- Requires direct database access (may not work on Free tier with network restrictions)
- Connection pooler doesn't support all PostgreSQL commands

### Method 3: Batch Application Script

Create a shell script to apply all migrations:

```bash
#!/bin/bash
# apply_migrations.sh

SUPABASE_URL="YOUR_CONNECTION_STRING"

for i in {001..010}; do
    FILE="${i}_*.sql"
    echo "Applying $FILE..."
    psql "$SUPABASE_URL" -f $FILE
    if [ $? -ne 0 ]; then
        echo "Error applying $FILE"
        exit 1
    fi
done

echo "All migrations applied successfully!"
```

Run with:
```bash
chmod +x apply_migrations.sh
./apply_migrations.sh
```

## Verification

After applying all migrations, run these verification queries in Supabase SQL Editor:

```sql
-- Check schema version
SELECT * FROM schema_versions ORDER BY version DESC;

-- Should show versions 1-10

-- Count tables created
SELECT COUNT(*) AS table_count
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_type = 'BASE TABLE';

-- Should return ~19 tables

-- Count views created
SELECT COUNT(*) AS view_count
FROM information_schema.views
WHERE table_schema = 'public';

-- Should return ~8 views

-- Count functions created
SELECT COUNT(*) AS function_count
FROM pg_proc
WHERE pronamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
AND prokind = 'f';

-- Should return ~15+ functions

-- Check seed data
SELECT
    (SELECT COUNT(*) FROM stop_words) AS stop_words_count,
    (SELECT COUNT(*) FROM profiles) AS profiles_count,
    (SELECT COUNT(*) FROM parse_cases) AS parse_cases_count,
    (SELECT COUNT(*) FROM keywords) AS keywords_count,
    (SELECT COUNT(*) FROM keyword_synonyms) AS synonyms_count;

-- Should show: ~95 stop words, 4 profiles, 6 parse cases, 20 keywords, 10 synonyms
```

## Post-Migration Configuration

### 1. Enable Realtime (Optional)

For live updates to the approval queue:

```sql
-- Enable realtime for pending_case_assignment table
ALTER PUBLICATION supabase_realtime ADD TABLE pending_case_assignment;
```

In Supabase Dashboard: **Database > Replication > Enable Realtime for tables**

### 2. Configure RLS (Row Level Security)

For multi-user scenarios, add RLS policies. Example:

```sql
-- Enable RLS on documents table
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;

-- Policy: Users can view their own documents
CREATE POLICY "Users can view own documents" ON documents
    FOR SELECT
    USING (auth.uid()::TEXT = uploaded_by);

-- Policy: Authenticated users can insert documents
CREATE POLICY "Authenticated users can insert documents" ON documents
    FOR INSERT
    WITH CHECK (auth.uid()::TEXT = uploaded_by);
```

**Note:** Adjust policies based on your authentication model.

### 3. Create Storage Bucket (Optional)

For storing uploaded files:

In Supabase Dashboard: **Storage > Create a new bucket**
- Bucket name: `maps-documents`
- Public access: FALSE
- File size limit: Configure as needed

### 4. Set Up Database Backups

In Supabase Dashboard: **Database > Backups**
- Daily backups (included in paid plans)
- Configure retention period

## Integration with MAPS Backend

Update your MAPS backend `.env` file:

```bash
# Supabase Configuration
DATABASE_BACKEND=supabase
SUPABASE_URL=https://YOUR_PROJECT_REF.supabase.co
SUPABASE_KEY=YOUR_ANON_KEY_OR_SERVICE_ROLE_KEY
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@db.YOUR_PROJECT_REF.supabase.co:5432/postgres

# For connection pooler (recommended for serverless)
# DATABASE_URL=postgresql://postgres.YOUR_PROJECT_REF:YOUR_PASSWORD@aws-0-region.pooler.supabase.com:6543/postgres
```

Get these values from: **Supabase Dashboard > Settings > Database**

## Common Issues and Solutions

### Issue 1: "extension does not exist"
**Error:** `ERROR: extension "uuid-ossp" does not exist`

**Solution:**
```sql
-- Run as superuser (Supabase Dashboard SQL Editor has correct permissions)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

If using direct connection, ensure you're using the postgres user.

### Issue 2: "type already exists"
**Error:** `ERROR: type "file_type_enum" already exists`

**Solution:** You've already applied the migration. Either:
1. Skip this migration
2. Drop and recreate:
```sql
DROP TYPE IF EXISTS file_type_enum CASCADE;
-- Then run the CREATE TYPE statement again
```

### Issue 3: Function already exists
**Error:** `ERROR: function ... already exists`

**Solution:**
```sql
-- Use CREATE OR REPLACE
CREATE OR REPLACE FUNCTION function_name() ...
```

All functions in these migrations use `CREATE OR REPLACE` for idempotency.

### Issue 4: Slow query performance
**Problem:** Views or searches are slow

**Solution:**
1. Check indexes:
```sql
SELECT schemaname, tablename, indexname
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;
```

2. Analyze tables:
```sql
ANALYZE documents;
ANALYZE document_content;
ANALYZE keyword_occurrences;
```

3. Enable query timing:
```sql
EXPLAIN ANALYZE SELECT * FROM v_document_list LIMIT 10;
```

### Issue 5: JSONB query optimization
**Problem:** Queries on JSONB fields are slow

**Solution:** Ensure GIN indexes are created:
```sql
-- Check GIN indexes
SELECT indexname, indexdef
FROM pg_indexes
WHERE indexdef LIKE '%gin%'
AND schemaname = 'public';

-- Create missing GIN index (example)
CREATE INDEX idx_document_content_canonical_data
ON document_content USING gin(canonical_data);
```

## Maintenance

### Regular Tasks

**Weekly:**
```sql
-- Update keyword statistics
SELECT update_keyword_statistics(keyword_id)
FROM keywords;

-- Vacuum and analyze
VACUUM ANALYZE documents;
VACUUM ANALYZE document_content;
VACUUM ANALYZE keyword_occurrences;
```

**Monthly:**
```sql
-- Check for orphaned records
SELECT COUNT(*) FROM ingestion_logs
WHERE document_id NOT IN (SELECT id FROM documents);

-- Archive old logs (optional)
DELETE FROM ingestion_logs
WHERE timestamp < NOW() - INTERVAL '90 days'
AND log_level IN ('DEBUG', 'INFO');
```

### Monitoring Queries

```sql
-- Database size
SELECT pg_size_pretty(pg_database_size(current_database())) AS db_size;

-- Largest tables
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
LIMIT 10;

-- Index usage
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan AS index_scans,
    idx_tup_read AS tuples_read,
    idx_tup_fetch AS tuples_fetched
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan ASC;
```

## Rollback Procedure

If you need to rollback migrations:

```sql
-- WARNING: This will delete all data

-- Drop all views
DROP VIEW IF EXISTS v_document_list CASCADE;
DROP VIEW IF EXISTS v_document_detail CASCADE;
DROP VIEW IF EXISTS v_documents_by_parse_case CASCADE;
DROP VIEW IF EXISTS v_detection_summary CASCADE;
DROP VIEW IF EXISTS v_keyword_consolidated CASCADE;
DROP VIEW IF EXISTS v_cross_type_keywords CASCADE;
DROP VIEW IF EXISTS v_ingestion_health CASCADE;
DROP VIEW IF EXISTS v_pending_queue_summary CASCADE;
DROP VIEW IF EXISTS v_batch_processing_status CASCADE;

-- Drop all tables (order matters due to foreign keys)
DROP TABLE IF EXISTS ingestion_logs CASCADE;
DROP TABLE IF EXISTS user_queries CASCADE;
DROP TABLE IF EXISTS system_metrics CASCADE;
DROP TABLE IF EXISTS batch_metadata CASCADE;
DROP TABLE IF EXISTS case_patterns CASCADE;
DROP TABLE IF EXISTS pending_case_assignment CASCADE;
DROP TABLE IF EXISTS detection_details CASCADE;
DROP TABLE IF EXISTS keyword_occurrences CASCADE;
DROP TABLE IF EXISTS keyword_search_history CASCADE;
DROP TABLE IF EXISTS keyword_reference_sources CASCADE;
DROP TABLE IF EXISTS keyword_sources CASCADE;
DROP TABLE IF EXISTS keyword_synonyms CASCADE;
DROP TABLE IF EXISTS keyword_statistics CASCADE;
DROP TABLE IF EXISTS keywords CASCADE;
DROP TABLE IF EXISTS stop_words CASCADE;
DROP TABLE IF EXISTS mixed_segments CASCADE;
DROP TABLE IF EXISTS qualitative_segments CASCADE;
DROP TABLE IF EXISTS quantitative_segments CASCADE;
DROP TABLE IF EXISTS parse_cases CASCADE;
DROP TABLE IF EXISTS document_content CASCADE;
DROP TABLE IF EXISTS documents CASCADE;
DROP TABLE IF EXISTS profiles CASCADE;
DROP TABLE IF EXISTS schema_versions CASCADE;

-- Drop functions
DROP FUNCTION IF EXISTS update_updated_at_column CASCADE;
DROP FUNCTION IF EXISTS update_parsed_at CASCADE;
DROP FUNCTION IF EXISTS log_status_change CASCADE;
DROP FUNCTION IF EXISTS update_searchable_text CASCADE;
DROP FUNCTION IF EXISTS generate_content_hash CASCADE;
DROP FUNCTION IF EXISTS extract_numeric_from_jsonb CASCADE;
DROP FUNCTION IF EXISTS calculate_similarity CASCADE;
DROP FUNCTION IF EXISTS is_valid_uuid CASCADE;
DROP FUNCTION IF EXISTS search_documents CASCADE;
DROP FUNCTION IF EXISTS get_keywords_by_category CASCADE;
DROP FUNCTION IF EXISTS search_keywords_full CASCADE;
DROP FUNCTION IF EXISTS calculate_case_confidence CASCADE;
DROP FUNCTION IF EXISTS detect_case_from_file CASCADE;
DROP FUNCTION IF EXISTS process_case_assignment CASCADE;
DROP FUNCTION IF EXISTS assign_case_manually CASCADE;
DROP FUNCTION IF EXISTS get_cross_type_keywords CASCADE;
DROP FUNCTION IF EXISTS update_keyword_statistics CASCADE;
DROP FUNCTION IF EXISTS get_document_keywords CASCADE;
DROP FUNCTION IF EXISTS get_ingestion_health CASCADE;
DROP FUNCTION IF EXISTS get_batch_summary CASCADE;

-- Drop types
DROP TYPE IF EXISTS file_type_enum CASCADE;
DROP TYPE IF EXISTS document_status_enum CASCADE;
DROP TYPE IF EXISTS log_level_enum CASCADE;
DROP TYPE IF EXISTS review_status_enum CASCADE;
DROP TYPE IF EXISTS segment_type_enum CASCADE;
DROP TYPE IF EXISTS detection_method_enum CASCADE;
DROP TYPE IF EXISTS qualitative_segment_subtype_enum CASCADE;
DROP TYPE IF EXISTS batch_status_enum CASCADE;

-- Drop extensions (optional - may be used by other schemas)
-- DROP EXTENSION IF EXISTS "uuid-ossp";
-- DROP EXTENSION IF EXISTS pg_trgm;
```

## Support

For issues or questions:
1. Check migration file comments for specific table/function documentation
2. Review verification queries at the end of each migration file
3. Consult Supabase documentation: https://supabase.com/docs/guides/database
4. Check PostgreSQL logs in Supabase Dashboard: **Database > Logs**

## License

MIT License - Same as MAPS project

## Version History

- **v1.0.0** (November 25, 2025) - Initial complete schema with 10 migrations
  - Core document processing
  - Schema-agnostic content segments
  - Keyword system with cross-type validation
  - Case detection with approval queue
  - Comprehensive audit trail

---

**Last Updated:** November 25, 2025
**Compatibility:** Supabase (PostgreSQL 15+), MAPS v1.0.0
