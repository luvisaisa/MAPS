# Database Setup Instructions

## Step 1: Open Supabase SQL Editor

1. Go to: https://supabase.com/dashboard/project/lfzijlkdmnnrttsatrtc/sql
2. Click "New query"

## Step 2: Run the Migration

Copy the entire contents of:
```
/migrations/002_unified_case_identifier_schema.sql
```

Paste into the SQL editor and click "Run" or press Cmd+Enter.

## Step 3: Verify Installation

After running the migration, you should see:

**Tables created (8):**
- `file_imports` - All imported files
- `quantitative_segments` - Numeric/tabular content
- `qualitative_segments` - Text/prose content  
- `mixed_segments` - Hybrid content
- `keywords` - Extracted terms
- `keyword_occurrences` - Keyword locations
- `case_patterns` - Detected patterns
- `stop_words` - Filter list

**Views created (3):**
- `unified_segments` - All segments joined
- `cross_type_keywords` - Keywords in multiple types
- `keyword_numeric_associations` - Keywords near numbers

**Functions created (4):**
- `find_cross_type_keywords()`
- `find_files_with_keywords()`
- `get_keyword_contexts()`
- `full_text_search()`

## Step 4: Test Connection

Run this in the case_identifier directory:

```bash
cd src/case_identifier
npm install dotenv
node -r dotenv/config -e "
const { validateConnection } = require('./dist/supabase-client.js');
validateConnection().then(ok => console.log(ok ? '✓ Connected!' : '✗ Failed'));
"
```

## Troubleshooting

**Error: Extension not available**
- Go to Database → Extensions in Supabase dashboard
- Enable: uuid-ossp, pg_trgm, btree_gin

**Error: Permission denied**
- Make sure you're using the service_role key for migrations
- Or run migrations in the SQL Editor (uses service role automatically)

**Error: Table already exists**
- The migration is idempotent - drop existing tables first:
```sql
DROP TABLE IF EXISTS keyword_occurrences CASCADE;
DROP TABLE IF EXISTS keywords CASCADE;
DROP TABLE IF EXISTS case_patterns CASCADE;
DROP TABLE IF EXISTS mixed_segments CASCADE;
DROP TABLE IF EXISTS qualitative_segments CASCADE;
DROP TABLE IF EXISTS quantitative_segments CASCADE;
DROP TABLE IF EXISTS stop_words CASCADE;
DROP TABLE IF EXISTS file_imports CASCADE;
DROP TYPE IF EXISTS segment_type_enum CASCADE;
DROP TYPE IF EXISTS processing_status_enum CASCADE;
DROP TYPE IF EXISTS stop_word_category_enum CASCADE;
```

Then run the migration again.
