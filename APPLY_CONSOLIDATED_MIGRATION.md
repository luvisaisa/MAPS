# Apply Consolidated Migration - 3 Steps

## What I Created

I've consolidated all necessary migrations into **ONE FILE**: `CONSOLIDATED_MIGRATION.sql`

This includes everything from migrations 001, 002, 015, 016 plus indexes, functions, views, and seed data.

## How to Apply (3 Easy Steps)

### Step 1: View the Migration File

```bash
cat CONSOLIDATED_MIGRATION.sql
```

This will display the entire migration. It's about 700 lines but it's all organized with clear sections.

### Step 2: Copy and Paste into Supabase

1. **Open Supabase SQL Editor:**
   - Go to: https://supabase.com/dashboard/project/lfzijlkdmnnrttsatrtc
   - Click: **SQL Editor** (left sidebar)
   - Click: **+ New query**

2. **Copy the file:**
   - Select ALL output from the `cat` command above
   - Copy it (Cmd+C / Ctrl+C)

3. **Paste into SQL Editor:**
   - Paste into the SQL Editor (Cmd+V / Ctrl+V)

4. **Click "Run"**
   - Wait ~30-60 seconds for completion

### Step 3: Verify Success

At the bottom of the SQL output in Supabase, you should see verification results:

```
check_type       | count | expected
-----------------|-------|-------------
Tables Created   | 15+   | 15+ expected
Views Created    | 5+    | 5+ expected
Schema Version   | 16    | 16 expected
```

If you see these results, **SUCCESS!** ✅

## After Migration is Applied

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

## What Gets Created

### Tables (15+):
- documents
- document_content
- profiles
- ingestion_logs
- batch_metadata
- user_queries
- schema_versions
- keywords
- keyword_statistics
- keyword_synonyms
- keyword_sources
- stop_words
- parse_cases
- detection_details
- pending_case_assignment
- case_patterns

### Views (5):
- v_document_summary
- v_document_list
- v_document_detail
- v_ingestion_health
- v_detection_summary

### Functions:
- update_updated_at_column()
- update_searchable_text()
- log_status_change()
- update_parsed_at()

### Seed Data:
- 1 default profile (generic_xml_passthrough)
- 25+ common stop words
- 5 sample medical keywords (nodule, lesion, opacity, etc.)

## Time Estimate

- Copy/paste: 30 seconds
- Execution: 30-60 seconds
- Verification: 10 seconds

**Total: ~2 minutes!** 🎉

## Troubleshooting

### Error: "relation already exists"

If you see errors about tables already existing, uncomment the cleanup section at the top of the file:

```sql
-- Uncomment these lines at the top of CONSOLIDATED_MIGRATION.sql:
DROP SCHEMA IF EXISTS public CASCADE;
CREATE SCHEMA public;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO public;
```

Then run again.

### Error: "syntax error"

Make sure you copied the ENTIRE file. Scroll to the bottom and ensure you got everything including the final comment block.

### Execution takes forever

The migration should complete in under 1 minute. If it's taking longer:
- Check Supabase logs (Dashboard > Database > Logs)
- Try refreshing the page and running again

## After Success

Once verified, proceed to **Phase 2**:
- Complete parse service implementation
- Test document upload and parsing
- Integrate keyword extraction

---

**Ready?** Run `cat CONSOLIDATED_MIGRATION.sql` and copy/paste into Supabase SQL Editor!
