# Manual Migration Application Guide

## Overview

Since direct PostgreSQL connections are not available, you must apply migrations manually through the Supabase SQL Editor. This guide provides step-by-step instructions.

## Prerequisites

- Supabase project access
- Supabase Dashboard login
- Project URL: https://supabase.com/dashboard/project/lfzijlkdmnnrttsatrtc

## Step-by-Step Instructions

### Step 1: Access SQL Editor

1. Open your Supabase project: https://supabase.com/dashboard/project/lfzijlkdmnnrttsatrtc
2. Click **SQL Editor** in the left sidebar
3. Click **+ New query** button (top right)

### Step 2: Apply Migrations in Order

Apply each migration file in numerical order (001 through 010). For each file:

1. Open the migration file on your local machine
2. Copy the entire contents
3. Paste into Supabase SQL Editor
4. Click **Run** button
5. Wait for success message
6. Verify results with the verification query at the bottom of each file
7. Move to next file

### Migration Checklist

Copy this checklist and check off each migration as you complete it:

```
[ ] 001_extensions_and_types.sql - Extensions and ENUM types
    Verification: SELECT COUNT(*) FROM pg_extension WHERE extname IN ('uuid-ossp', 'pg_trgm');
    Expected: 2

[ ] 002_utility_functions.sql - Trigger functions
    Verification: SELECT COUNT(*) FROM pg_proc WHERE proname IN ('update_updated_at_column', 'update_searchable_text');
    Expected: 8

[ ] 003_core_tables.sql - Core tables (profiles, documents, document_content)
    Verification: SELECT COUNT(*) FROM information_schema.tables WHERE table_name IN ('profiles', 'documents', 'document_content');
    Expected: 4

[ ] 004_keyword_tables.sql - Keyword system tables
    Verification: SELECT COUNT(*) FROM information_schema.tables WHERE table_name LIKE 'keyword%' OR table_name = 'stop_words';
    Expected: 7

[ ] 005_segment_tables.sql - Content segments
    Verification: SELECT COUNT(*) FROM information_schema.tables WHERE table_name LIKE '%_segments';
    Expected: 3

[ ] 006_case_detection_tables.sql - Case detection and approval queue
    Verification: SELECT COUNT(*) FROM information_schema.tables WHERE table_name IN ('parse_cases', 'detection_details', 'pending_case_assignment', 'case_patterns');
    Expected: 4

[ ] 007_audit_tables.sql - Audit and tracking
    Verification: SELECT COUNT(*) FROM information_schema.tables WHERE table_name IN ('ingestion_logs', 'batch_metadata', 'user_queries', 'system_metrics');
    Expected: 4

[ ] 008_views.sql - Database views
    Verification: SELECT COUNT(*) FROM information_schema.views WHERE table_schema = 'public';
    Expected: 9

[ ] 009_functions.sql - Stored procedures
    Verification: SELECT COUNT(*) FROM pg_proc WHERE pronamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public') AND prokind = 'f' AND proname LIKE '%document%';
    Expected: 4+

[ ] 010_seed_data.sql - Initial data
    Verification: SELECT (SELECT COUNT(*) FROM stop_words) as stop_words, (SELECT COUNT(*) FROM profiles) as profiles;
    Expected: ~95 stop words, 4 profiles
```

## Migration File Locations

All migration files are located in:
```
/Users/isa/Desktop/python-projects/MAPS/supabase_migrations/
```

### Quick Copy Commands

To view a file's contents in terminal:

```bash
# Migration 001
cat supabase_migrations/001_extensions_and_types.sql

# Migration 002
cat supabase_migrations/002_utility_functions.sql

# Migration 003
cat supabase_migrations/003_core_tables.sql

# Migration 004
cat supabase_migrations/004_keyword_tables.sql

# Migration 005
cat supabase_migrations/005_segment_tables.sql

# Migration 006
cat supabase_migrations/006_case_detection_tables.sql

# Migration 007
cat supabase_migrations/007_audit_tables.sql

# Migration 008
cat supabase_migrations/008_views.sql

# Migration 009
cat supabase_migrations/009_functions.sql

# Migration 010
cat supabase_migrations/010_seed_data.sql
```

## Common Issues and Solutions

### Issue 1: "Extension already exists"

**Error:** `ERROR: extension "uuid-ossp" already exists`

**Solution:** This is OK - the extension is already installed. Continue with the next statement.

### Issue 2: "Type already exists"

**Error:** `ERROR: type "file_type_enum" already exists`

**Solution:** You may have already applied this migration. Check:
```sql
SELECT MAX(version) FROM schema_versions;
```

If version is already recorded, skip this migration.

### Issue 3: "Relation already exists"

**Error:** `ERROR: relation "documents" already exists`

**Solution:** Table already created. Either:
1. Skip this migration if it's fully applied
2. Drop and recreate (WARNING: loses data):
```sql
DROP TABLE documents CASCADE;
-- Then re-run CREATE TABLE
```

### Issue 4: Query timeout

**Problem:** Large migration takes too long

**Solution:**
1. Break the file into smaller chunks
2. Run sections separately
3. Increase timeout in Supabase settings

### Issue 5: Foreign key constraint error

**Error:** `ERROR: constraint ... does not exist`

**Solution:** Dependencies not applied in correct order. Verify previous migrations completed successfully.

## Verification After All Migrations

After applying all 10 migrations, run this comprehensive verification query:

```sql
-- Comprehensive schema verification
SELECT
    'Tables' as type,
    COUNT(*)::TEXT as count,
    '19 expected' as expected
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_type = 'BASE TABLE'

UNION ALL

SELECT
    'Views' as type,
    COUNT(*)::TEXT as count,
    '9 expected' as expected
FROM information_schema.views
WHERE table_schema = 'public'

UNION ALL

SELECT
    'Functions' as type,
    COUNT(*)::TEXT as count,
    '15+ expected' as expected
FROM pg_proc
WHERE pronamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
AND prokind = 'f'

UNION ALL

SELECT
    'Extensions' as type,
    COUNT(*)::TEXT as count,
    '2+ expected' as expected
FROM pg_extension
WHERE extname IN ('uuid-ossp', 'pg_trgm')

UNION ALL

SELECT
    'Schema Version' as type,
    MAX(version)::TEXT as count,
    '10 expected' as expected
FROM schema_versions;
```

Expected output:
```
type            | count | expected
----------------|-------|-------------
Tables          | 19    | 19 expected
Views           | 9     | 9 expected
Functions       | 15+   | 15+ expected
Extensions      | 2     | 2+ expected
Schema Version  | 10    | 10 expected
```

## Detailed Table Verification

Verify all expected tables exist:

```sql
SELECT
    table_name,
    CASE
        WHEN EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'public'
            AND tables.table_name = expected.table_name
        ) THEN '✓'
        ELSE '✗'
    END as exists
FROM (VALUES
    ('profiles'),
    ('documents'),
    ('document_content'),
    ('schema_versions'),
    ('keywords'),
    ('keyword_statistics'),
    ('keyword_synonyms'),
    ('keyword_sources'),
    ('keyword_occurrences'),
    ('keyword_search_history'),
    ('keyword_reference_sources'),
    ('stop_words'),
    ('quantitative_segments'),
    ('qualitative_segments'),
    ('mixed_segments'),
    ('parse_cases'),
    ('detection_details'),
    ('pending_case_assignment'),
    ('case_patterns'),
    ('ingestion_logs'),
    ('batch_metadata'),
    ('user_queries'),
    ('system_metrics')
) AS expected(table_name)
ORDER BY table_name;
```

All rows should show '✓'.

## Seed Data Verification

Check that initial data was inserted:

```sql
SELECT
    'Stop Words' as data_type,
    COUNT(*)::TEXT as count,
    '~95 expected' as expected
FROM stop_words

UNION ALL

SELECT
    'Profiles' as data_type,
    COUNT(*)::TEXT as count,
    '4 expected' as expected
FROM profiles

UNION ALL

SELECT
    'Parse Cases' as data_type,
    COUNT(*)::TEXT as count,
    '6 expected' as expected
FROM parse_cases

UNION ALL

SELECT
    'Keywords' as data_type,
    COUNT(*)::TEXT as count,
    '~20 expected' as expected
FROM keywords

UNION ALL

SELECT
    'Keyword Synonyms' as data_type,
    COUNT(*)::TEXT as count,
    '~10 expected' as expected
FROM keyword_synonyms;
```

## Testing Database Functionality

After migrations are applied, test basic operations:

### Test 1: Insert a profile

```sql
INSERT INTO profiles (profile_name, file_type, description, mapping_definition)
VALUES (
    'test_profile',
    'JSON',
    'Test profile for verification',
    '{"test": true}'::JSONB
)
RETURNING id, profile_name;
```

### Test 2: Insert a document

```sql
INSERT INTO documents (source_file_name, file_type, profile_id, status)
VALUES (
    'test.json',
    'JSON',
    (SELECT id FROM profiles WHERE profile_name = 'test_profile'),
    'pending'
)
RETURNING id, source_file_name, status;
```

### Test 3: Query a view

```sql
SELECT * FROM v_document_list LIMIT 5;
```

### Test 4: Call a function

```sql
SELECT get_keywords_by_category('medical');
```

### Cleanup Test Data

```sql
DELETE FROM documents WHERE source_file_name = 'test.json';
DELETE FROM profiles WHERE profile_name = 'test_profile';
```

## Next Steps After Migration

Once all migrations are applied and verified:

1. **Update backend .env** (if needed - already configured):
   ```bash
   DATABASE_BACKEND=supabase
   SUPABASE_URL=https://lfzijlkdmnnrttsatrtc.supabase.co
   DATABASE_URL=postgresql://postgres:m3owLove!data@db.lfzijlkdmnnrttsatrtc.supabase.co:5432/postgres
   ```

2. **Test backend connection:**
   ```bash
   python3 -c "from src.maps.api.services.parse_service import db; print('Connection OK' if db else 'Connection Failed')"
   ```

3. **Proceed to Phase 2:** Complete parse service implementation

## Troubleshooting

### Can't access Supabase Dashboard

Check:
1. Internet connection
2. Supabase project is active (not paused)
3. Correct project URL

### Migrations partially applied

Check schema_versions table:
```sql
SELECT * FROM schema_versions ORDER BY version;
```

Resume from the next migration number.

### Need to rollback

See `supabase_migrations/README.md` section "Rollback Procedure" for complete rollback SQL.

## Support

For issues:
1. Check migration file comments for details
2. Review Supabase logs: Dashboard > Database > Logs
3. Consult README.md in supabase_migrations/ directory

## Time Estimate

- Each migration: 2-5 minutes
- Total time: 30-45 minutes
- Verification: 10 minutes

Total: ~1 hour

---

**Last Updated:** November 25, 2025
**Migrations Version:** 1.0.0
