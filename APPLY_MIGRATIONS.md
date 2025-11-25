# Apply MAPS Migrations to Supabase

## Current Status

- **Original migrations:** 16 files in `migrations/` directory (001-016) ✓
- **Duplicate migrations:** 10 files in `supabase_migrations/` directory (ignore these)
- **Supabase status:** Only `case_patterns` table exists (partial/incomplete)

## Decision: Use Original Migrations

We'll use the existing migrations in `migrations/` directory (001-016) which are:
- More comprehensive and complete
- Specific to MAPS requirements
- Already tested and verified

## Migration List (migrations/ directory)

Apply these in order:

```
001_initial_schema.sql              - Core tables (documents, document_content, profiles)
002_add_keyword_enhancements.sql    - Keyword system enhancements
002_unified_case_identifier_schema.sql - (Note: Also numbered 002 - check ordering)
003_analysis_views.sql              - Analysis views
003_document_parse_case_links.sql   - Parse case relationships
004_enable_public_access.sql        - RLS policies
005_flatten_radiologist_annotations.sql - Radiologist data
006_automatic_triggers.sql          - Automatic triggers
007_case_detection_system.sql       - Case detection (includes case_patterns)
008_universal_views.sql             - Universal views
009_lidc_specific_views.sql         - LIDC-IDRI views
010_lidc_3d_contour_views.sql       - 3D contour views
011_export_views.sql                - Export views
012_public_access_policies.sql      - Access policies
013_keyword_semantics.sql           - Keyword semantics
014_keyword_navigation_views.sql    - Keyword navigation
015_detection_details_table.sql     - Detection details
016_documents_enhancements.sql      - Document enhancements
performance_indexes.sql             - Performance indexes (apply last)
```

## Issue: Multiple 002 and 003 Files

There are multiple files with the same migration number:
- `002_add_keyword_enhancements.sql`
- `002_radiology_supabase.sql`
- `002_unified_case_identifier_schema.sql`
- `003_analysis_views.sql`
- `003_document_parse_case_links.sql`

This needs to be resolved. Let me check which ones should be applied.

## Recommended Approach

### Option 1: Clean Start (Recommended)

1. **Drop the case_patterns table:**
   ```sql
   DROP TABLE IF EXISTS case_patterns CASCADE;
   ```

2. **Apply migrations via Supabase SQL Editor in order:**
   - Start with 001
   - For duplicate numbers (002, 003), examine content and apply in logical dependency order
   - Continue through 016
   - Apply performance_indexes.sql last

### Option 2: Skip to Next Migration

Since only case_patterns exists:
1. Check which migration created it (007_case_detection_system.sql)
2. Apply migrations 001-006 to catch up
3. Verify 007 is fully applied
4. Continue with 008-016

## Detailed Application Instructions

### Step 1: Review Migration Dependencies

Before applying, check for:
- Duplicate migration numbers (002, 003)
- Dependencies between migrations
- Which migration created case_patterns table

### Step 2: Create Migration Order

Let me check the content of duplicate migrations to determine correct order:
