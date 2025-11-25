# Supabase Migration Quick Start

## Current Status

- ✓ 10 migration files created in `supabase_migrations/`
- ✓ Helper scripts created
- ✓ Verification tools ready
- ⏳ **NEXT:** Apply migrations to Supabase

## Quick Steps to Apply Migrations

### Option 1: Supabase SQL Editor (Recommended)

**Time estimate: ~30-45 minutes**

1. **Open Supabase SQL Editor:**
   - Go to: https://supabase.com/dashboard/project/lfzijlkdmnnrttsatrtc
   - Click: **SQL Editor** (left sidebar)

2. **Apply each migration file (001 through 010):**

   For each file:
   ```bash
   # In terminal, view the file:
   cat supabase_migrations/001_extensions_and_types.sql

   # Copy the entire output
   # Paste into Supabase SQL Editor
   # Click "Run"
   # Wait for success message
   # Move to next file
   ```

3. **Files to apply in order:**
   - `001_extensions_and_types.sql` - Extensions and ENUMs
   - `002_utility_functions.sql` - Trigger functions
   - `003_core_tables.sql` - Core tables
   - `004_keyword_tables.sql` - Keyword system
   - `005_segment_tables.sql` - Content segments
   - `006_case_detection_tables.sql` - Case detection
   - `007_audit_tables.sql` - Audit tables
   - `008_views.sql` - Database views
   - `009_functions.sql` - Stored procedures
   - `010_seed_data.sql` - Initial data

4. **Verify after all migrations:**
   ```bash
   python3 scripts/verify_supabase_schema.py
   ```

### Option 2: Automated Script (if you have Supabase CLI)

```bash
# Install Supabase CLI
npm install -g supabase

# Login
supabase login

# Link project
supabase link --project-ref lfzijlkdmnnrttsatrtc

# Apply migrations
for file in supabase_migrations/*.sql; do
    supabase db execute -f "$file"
done
```

## Detailed Guides

- **Manual Application:** See `supabase_migrations/MANUAL_APPLICATION_GUIDE.md`
- **Migration Details:** See `supabase_migrations/README.md`
- **Implementation Summary:** See `supabase_migrations/IMPLEMENTATION_SUMMARY.md`

## Verification After Application

Run the verification script:

```bash
python3 scripts/verify_supabase_schema.py
```

Expected output:
```
Schema Version................................ ✓ PASS
Tables........................................ ✓ PASS
Seed Data..................................... ✓ PASS
Basic Operations.............................. ✓ PASS

✓ All verifications passed!
```

## Quick Verification Queries

Run these in Supabase SQL Editor to check status:

```sql
-- Check schema version (should be 10)
SELECT MAX(version) FROM schema_versions;

-- Count tables (should be ~23)
SELECT COUNT(*) FROM information_schema.tables
WHERE table_schema = 'public' AND table_type = 'BASE TABLE';

-- Count views (should be ~9)
SELECT COUNT(*) FROM information_schema.views
WHERE table_schema = 'public';

-- Check seed data
SELECT
    (SELECT COUNT(*) FROM stop_words) as stop_words,
    (SELECT COUNT(*) FROM profiles) as profiles,
    (SELECT COUNT(*) FROM parse_cases) as parse_cases,
    (SELECT COUNT(*) FROM keywords) as keywords;

-- Should show: ~95 stop words, 4 profiles, 6 parse cases, ~20 keywords
```

## After Migrations Are Applied

1. **Verify schema:**
   ```bash
   python3 scripts/verify_supabase_schema.py
   ```

2. **Test backend connection:**
   ```bash
   python3 -c "
   from src.maps.database.db_config import get_db_config
   config = get_db_config()
   print('✓ Database configured' if config else '✗ Config failed')
   "
   ```

3. **Proceed to Phase 2:** Complete parse service implementation
   - File: `src/maps/api/services/parse_service.py`
   - Lines: 94-104 (database insertion + keyword extraction)

## Troubleshooting

### Migrations fail with "already exists" errors

Check which migrations are applied:
```sql
SELECT * FROM schema_versions ORDER BY version;
```

Resume from the next version number.

### Can't connect to Supabase

Check:
1. Project is active (not paused)
2. Credentials in `.env` are correct
3. Internet connection is working

Try accessing: https://supabase.com/dashboard/project/lfzijlkdmnnrttsatrtc

### Verification script fails

Ensure migrations were applied in correct order. Check Supabase logs:
- Dashboard > Database > Logs

## Next Steps After Verification

Once schema is verified:

1. ✓ Complete - Phase 1: Apply migrations
2. → Next - Phase 2: Complete parse service (database insertion + keyword extraction)
3. → Next - Phase 3: Complete export service
4. → Next - Phase 4: Build Export frontend page
5. → Next - Phase 5: Build KeywordDetector page
6. → Next - Phase 6: End-to-end testing

## Support Files

All migration files and documentation:
```
supabase_migrations/
├── 001_extensions_and_types.sql
├── 002_utility_functions.sql
├── 003_core_tables.sql
├── 004_keyword_tables.sql
├── 005_segment_tables.sql
├── 006_case_detection_tables.sql
├── 007_audit_tables.sql
├── 008_views.sql
├── 009_functions.sql
├── 010_seed_data.sql
├── README.md                        # Comprehensive guide
├── MANUAL_APPLICATION_GUIDE.md      # Step-by-step manual process
└── IMPLEMENTATION_SUMMARY.md        # Architecture overview

scripts/
├── apply_supabase_migrations.py     # Helper script (lists files)
└── verify_supabase_schema.py        # Verification script
```

## Environment Configuration

Your `.env` is already configured:
```bash
DATABASE_BACKEND=supabase
SUPABASE_URL=https://lfzijlkdmnnrttsatrtc.supabase.co
SUPABASE_KEY=<your_anon_key>
DATABASE_URL=postgresql://postgres:m3owLove!data@db.lfzijlkdmnnrttsatrtc.supabase.co:5432/postgres
```

## Time Estimates

- Applying migrations: 30-45 minutes (manual)
- Verification: 5 minutes
- Testing: 10 minutes
- **Total: ~1 hour**

---

**Ready to start?** Open the Supabase SQL Editor and begin with `001_extensions_and_types.sql`

**Need help?** See `MANUAL_APPLICATION_GUIDE.md` for detailed step-by-step instructions
