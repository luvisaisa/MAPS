# Quick Start: Apply MAPS Migrations

## TL;DR

You have 16 original migrations that need to be applied to Supabase. I created duplicate migrations by mistake - ignore those.

## What You Need to Do

### 1. Open Supabase SQL Editor

https://supabase.com/dashboard/project/lfzijlkdmnnrttsatrtc → SQL Editor → + New query

### 2. Clean Up Partial Schema

Run this first:
```sql
DROP TABLE IF EXISTS case_patterns CASCADE;
```

### 3. Apply Migrations in Order

**Simplified Path (Recommended - avoids duplicates):**

```bash
# Apply these files from migrations/ directory in this order:

cat migrations/001_initial_schema.sql
# Copy → Paste into SQL Editor → Run → Verify success

cat migrations/002_add_keyword_enhancements.sql
# Copy → Paste → Run

cat migrations/004_enable_public_access.sql
# Copy → Paste → Run

cat migrations/005_flatten_radiologist_annotations.sql
# Copy → Paste → Run

cat migrations/006_automatic_triggers.sql
# Copy → Paste → Run

cat migrations/007_case_detection_system.sql
# Copy → Paste → Run

cat migrations/008_universal_views.sql
# Copy → Paste → Run

cat migrations/013_keyword_semantics.sql
# Copy → Paste → Run

cat migrations/015_detection_details_table.sql
# Copy → Paste → Run

cat migrations/016_documents_enhancements.sql
# Copy → Paste → Run

cat migrations/performance_indexes.sql
# Copy → Paste → Run
```

### 4. Verify

After all migrations:
```bash
python3 scripts/verify_supabase_schema.py
```

Should show all ✓ PASS.

## Alternative: Full Path with All Migrations

See `MIGRATION_STATUS_AND_PLAN.md` for complete details including handling duplicate migration files.

## Time Estimate

- Simplified path: ~45 minutes
- Full path: ~1-2 hours
- Verification: ~5 minutes

## After Verification

Continue to Phase 2: Parse service implementation (`src/maps/api/services/parse_service.py`)

---

**Questions?** See `MIGRATION_STATUS_AND_PLAN.md` for full details.
