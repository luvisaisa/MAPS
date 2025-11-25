# MAPS Migration Status and Action Plan

## Current Situation

### What Happened

1. **Original Migrations:** You have 16 comprehensive migrations (001-016) in `migrations/` directory
2. **Duplicate Migrations:** I created 10 new migrations in `supabase_migrations/` directory without checking for existing ones
3. **Supabase Status:** Only `case_patterns` table exists (partial/incomplete schema)

### Migration Inventory

**migrations/ directory (THESE ARE THE CORRECT ONES):**
- 20 migration files total
- Includes migrations 001-016 plus performance_indexes.sql
- **Issue:** Duplicate numbers (2 files for 002, 2 files for 003)
- **Issue:** Some may be obsolete/alternative approaches

**supabase_migrations/ directory (IGNORE THESE):**
- 10 migration files I created unnecessarily
- Can be archived or deleted

## The Correct Migration Path

### Step 1: Understand What Migration 001 Creates

The core migration `001_initial_schema.sql` creates:
- `documents` - File metadata
- `document_content` - Canonical data storage (JSONB)
- `profiles` - Parsing profiles
- `ingestion_logs` - Audit logs
- `batch_metadata` - Batch processing tracking
- `user_queries` - Search analytics
- `schema_versions` - Migration tracking

This is the foundation everything else builds on.

### Step 2: Handle Duplicate Migration Numbers

**Migration 002 (3 files - need to choose):**
1. `002_add_keyword_enhancements.sql` - Enhances keyword table from 001
2. `002_radiology_supabase.sql` - Adds radiology-specific indexes
3. `002_unified_case_identifier_schema.sql` - **ALTERNATIVE SCHEMA** (likely obsolete)

**RECOMMENDATION:** Apply `002_add_keyword_enhancements.sql` OR `002_radiology_supabase.sql` (or both in sequence), SKIP `002_unified_case_identifier_schema.sql`

**Migration 003 (2 files - need to choose):**
1. `003_analysis_views.sql` - Creates analysis views
2. `003_document_parse_case_links.sql` - Links documents to parse cases

**RECOMMENDATION:** Apply both in sequence (003_document_parse_case_links first, then 003_analysis_views)

### Step 3: Clean Application Order

Here's the recommended order to apply migrations via Supabase SQL Editor:

```
1. DROP existing partial schema:
   DROP TABLE IF EXISTS case_patterns CASCADE;

2. 001_initial_schema.sql
   ✓ Creates: documents, document_content, profiles, ingestion_logs, batch_metadata, user_queries, schema_versions

3. 002_add_keyword_enhancements.sql (OR 002_radiology_supabase.sql)
   ✓ Enhances keyword system / Adds radiology indexes

4. 003_document_parse_case_links.sql
   ✓ Links documents to parse cases

5. 003_analysis_views.sql
   ✓ Creates analysis views

6. 004_enable_public_access.sql
   ✓ RLS policies

7. 005_flatten_radiologist_annotations.sql
   ✓ Radiologist data structures

8. 006_automatic_triggers.sql
   ✓ Automatic keyword extraction triggers

9. 007_case_detection_system.sql
   ✓ Case detection (recreates case_patterns properly)

10. 008_universal_views.sql
    ✓ Universal views for all data sources

11. 009_lidc_specific_views.sql
    ✓ LIDC-IDRI specific views

12. 010_lidc_3d_contour_views.sql
    ✓ 3D contour views

13. 011_export_views.sql
    ✓ Export-ready materialized views

14. 012_public_access_policies.sql
    ✓ Public access policies

15. 013_keyword_semantics.sql
    ✓ Canonical keyword dictionary

16. 014_keyword_navigation_views.sql
    ✓ Keyword navigation views

17. 015_detection_details_table.sql
    ✓ Detection details table

18. 016_documents_enhancements.sql
    ✓ Enhanced document fields

19. performance_indexes.sql
    ✓ Performance optimizations (apply last)
```

## Detailed Instructions

### Option A: Manual Application (Supabase SQL Editor)

**Time Required:** ~1-2 hours

1. **Open Supabase SQL Editor:**
   - URL: https://supabase.com/dashboard/project/lfzijlkdmnnrttsatrtc
   - Navigate to: SQL Editor
   - Click: + New query

2. **First, clean up existing partial schema:**
   ```sql
   DROP TABLE IF EXISTS case_patterns CASCADE;
   ```

3. **Apply each migration in order:**
   - For each file listed above:
     ```bash
     # View the migration
     cat migrations/001_initial_schema.sql

     # Copy output
     # Paste into Supabase SQL Editor
     # Click "Run"
     # Wait for success
     # Move to next file
     ```

4. **After each migration, verify:**
   ```sql
   -- Check schema version
   SELECT MAX(version) FROM schema_versions;

   -- Check tables exist
   SELECT table_name FROM information_schema.tables
   WHERE table_schema = 'public'
   ORDER BY table_name;
   ```

### Option B: Skip Duplicate Migrations (Simpler)

If you want to avoid the duplicate migration issue, here's a simplified path:

**Apply only these files:**
```
001_initial_schema.sql
002_add_keyword_enhancements.sql  (choose this one for 002)
004_enable_public_access.sql
005_flatten_radiologist_annotations.sql
006_automatic_triggers.sql
007_case_detection_system.sql
008_universal_views.sql
013_keyword_semantics.sql
015_detection_details_table.sql
016_documents_enhancements.sql
performance_indexes.sql
```

This gives you the core functionality without dealing with duplicates.

## What to Do with supabase_migrations/

You have two options:

### Option 1: Archive (Recommended)
```bash
mkdir -p archive
mv supabase_migrations archive/supabase_migrations_$(date +%Y%m%d)
```

### Option 2: Delete
```bash
rm -rf supabase_migrations
```

The migrations in `supabase_migrations/` are redundant since your original `migrations/` directory is more complete.

## Verification After Application

After applying migrations, run:

```bash
python3 scripts/verify_supabase_schema.py
```

Expected verification:
```
Schema Version................................ ✓ PASS (version 16+)
Tables........................................ ✓ PASS (20+ tables)
Seed Data..................................... ✓ PASS
Basic Operations.............................. ✓ PASS
```

## Key Tables to Verify

After migrations, these core tables should exist:

```sql
-- Check core tables
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name IN (
    'documents',
    'document_content',
    'profiles',
    'keywords',
    'parse_cases',
    'detection_details',
    'ingestion_logs',
    'batch_metadata',
    'user_queries',
    'schema_versions'
)
ORDER BY table_name;
```

Should return all 10 tables.

## After Migrations Are Complete

Once verified, proceed to Phase 2:

1. **Test backend connection**
2. **Complete parse service** (DB insertion + keyword extraction)
3. **Complete export service**
4. **Build frontend pages**
5. **End-to-end testing**

## Time Estimates

- **Clean approach (all migrations):** 1-2 hours
- **Simplified approach (core only):** 45-60 minutes
- **Verification:** 10 minutes

---

## Summary

**Action Required:** Apply migrations from `migrations/` directory via Supabase SQL Editor

**Recommended Path:** Use the simplified approach (Option B) to avoid duplicate migration complexity

**Next Steps:** After verification, continue to Phase 2 (parse service implementation)

**Files Created for You:**
- `MIGRATION_STATUS_AND_PLAN.md` (this file)
- `scripts/apply_original_migrations.py` (analysis tool)
- `scripts/verify_supabase_schema.py` (verification tool)

---

**Ready?** Start with `001_initial_schema.sql` in the Supabase SQL Editor!
