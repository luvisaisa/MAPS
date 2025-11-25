# Session Continuation Prompt for MAPS Implementation

## Current Status

### ✅ COMPLETED (This Session)
1. **Created 10 Supabase migration files** (`supabase_migrations/` directory)
   - Complete schema with 19 tables, 8 views, 15+ functions
   - Schema-agnostic document processing system
   - Keyword extraction with cross-type validation
   - Case detection with approval queue
   - Full audit trail

2. **Pushed to Git**
   - Commit: `8619213f` - "feat: add complete Supabase schema migrations"
   - Branch: `main`
   - All changes synced to GitHub

### 🔄 CURRENT PHASE: Phase 1 - Supabase Connection & Migration Application

**Status:** Migrations created, not yet applied to Supabase

### 📋 REMAINING WORK (6-Phase Plan)

**Phase 1:** Verify Supabase connection and apply 10 migrations ⏳ IN PROGRESS
- **Next step:** Apply migrations via Supabase SQL Editor
- Files ready in: `supabase_migrations/001_*.sql` through `010_*.sql`
- Instructions in: `supabase_migrations/README.md`

**Phase 2:** Complete parse service backend (DB insertion + keyword extraction) ⏸️ PENDING
- Location: `src/maps/api/services/parse_service.py` lines 94-104
- Need to implement database insertion and keyword extraction integration

**Phase 3:** Complete export service implementation ⏸️ PENDING
- Location: `src/maps/api/services/export_service.py`
- Currently has minimal implementation

**Phase 4:** Create Export page frontend ⏸️ PENDING
- Create: `web/src/pages/Export.tsx`
- UI for filtering, format selection, preview, download

**Phase 5:** Create KeywordDetector page frontend ⏸️ PENDING
- Create: `web/src/pages/KeywordDetector.tsx`
- Upload file → parse → detect keywords → display results

**Phase 6:** End-to-end testing ⏸️ PENDING
- Test complete workflow: upload → parse → detect → extract → export
- Verify all features with real Supabase data

---

## Quick Resume Prompt

Copy and paste this into your new session:

```
Continue MAPS implementation where we left off. Here's the status:

COMPLETED:
- Created 10 Supabase migration files in supabase_migrations/ directory
- Complete schema: 19 tables, 8 views, 15+ functions
- Pushed to git (commit 8619213f on main branch)

CURRENT PHASE: Phase 1 - Apply migrations to Supabase

SUPABASE INFO:
- Project: lfzijlkdmnnrttsatrtc.supabase.co
- Database URL: postgresql://postgres:m3owLove!data@db.lfzijlkdmnnrttsatrtc.supabase.co:5432/postgres
- Connection pooler: postgresql://postgres.lfzijlkdmnnrttsatrtc:m3owLove!data@aws-0-us-west-1.pooler.supabase.com:6543/postgres

NEXT STEPS:
1. Apply the 10 migration files to Supabase (in order: 001 through 010)
2. Verify schema is created correctly
3. Update backend .env with Supabase credentials
4. Test connection from backend
5. Complete Phase 2: Parse service implementation

IMPORTANT FILES:
- Migration files: supabase_migrations/001_*.sql through 010_*.sql
- Instructions: supabase_migrations/README.md
- Summary: supabase_migrations/IMPLEMENTATION_SUMMARY.md

FRONTEND/BACKEND STATUS:
- Frontend: Running on http://localhost:5173 (Vite dev server)
- Backend: Running on http://localhost:8000 (FastAPI)
- Both currently running in background

Let's start by applying the migrations to Supabase using the SQL Editor method.
```

---

## Detailed Context for New Session

### What We Built

**Schema-Agnostic Document Processing System:**
- Any file type (XML, JSON, CSV, PDF) can contain any content type
- Content classified as: quantitative (numeric/tabular), qualitative (text), or mixed
- Flexible JSONB storage for canonical data
- Keywords extracted and linked to segments polymorphically

**Key Features:**
1. **Keyword System** - Standardized vocabulary (RadLex, LOINC, Lung-RADS), synonyms, TF-IDF scoring
2. **Case Detection** - Hybrid detection (filename + keywords), confidence-based auto-assign or manual review
3. **Approval Queue** - Low-confidence detections (<0.8) queued for manual review
4. **Cross-Type Validation** - Keywords in both quantitative + qualitative = high confidence signal
5. **Full Audit Trail** - Comprehensive logs, batch metrics, query analytics

### Migration Files Overview

| File | Purpose | Tables/Views/Functions |
|------|---------|------------------------|
| 001 | Extensions & ENUMs | 8 custom types |
| 002 | Utility functions | 8 trigger functions |
| 003 | Core tables | profiles, documents, document_content, schema_versions |
| 004 | Keyword system | 6 tables (keywords, statistics, synonyms, sources, etc.) |
| 005 | Content segments | 4 tables (quantitative/qualitative/mixed + occurrences) |
| 006 | Case detection | 4 tables (parse_cases, detection_details, approval queue) |
| 007 | Audit & tracking | 4 tables (logs, batch metadata, queries, metrics) |
| 008 | Database views | 8 views for UI query patterns |
| 009 | Stored procedures | 10 functions (detection, search, analytics) |
| 010 | Seed data | Stop words, profiles, parse cases, keywords |

### How to Apply Migrations

**Method 1: Supabase SQL Editor (Recommended)**
1. Open: https://supabase.com/dashboard/project/lfzijlkdmnnrttsatrtc
2. Go to: SQL Editor (left sidebar)
3. Click: "+ New query"
4. Copy/paste: Contents of `001_extensions_and_types.sql`
5. Click: "Run"
6. Wait for success message
7. Repeat for files 002 through 010 **in order**

**Verification After Each Migration:**
- Check bottom of each file for verification queries
- Should see success messages, no errors

**Method 2: Direct psql (if connection works)**
```bash
cd /Users/isa/Desktop/python-projects/MAPS/supabase_migrations
psql "postgresql://postgres:m3owLove!data@db.lfzijlkdmnnrttsatrtc.supabase.co:5432/postgres" -f 001_extensions_and_types.sql
# Repeat for all files
```

### After Migrations Are Applied

**1. Verify Schema**
Run in Supabase SQL Editor:
```sql
SELECT
    (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE') AS tables,
    (SELECT COUNT(*) FROM information_schema.views WHERE table_schema = 'public') AS views,
    (SELECT MAX(version) FROM schema_versions) AS latest_migration;
```
Expected: tables=19, views=8, latest_migration=10

**2. Update Backend .env**
File: `/Users/isa/Desktop/python-projects/MAPS/.env`
```bash
DATABASE_BACKEND=supabase
SUPABASE_URL=https://lfzijlkdmnnrttsatrtc.supabase.co
SUPABASE_KEY=<your_service_role_key_here>
DATABASE_URL=postgresql://postgres:m3owLove!data@db.lfzijlkdmnnrttsatrtc.supabase.co:5432/postgres
```

**3. Test Backend Connection**
```bash
python3 -c "
from src.maps.database.db_config import get_db_config
config = get_db_config()
engine = config.get_engine()
with engine.connect() as conn:
    result = conn.execute('SELECT MAX(version) FROM schema_versions')
    print(f'Schema version: {result.scalar()}')
"
```

**4. Move to Phase 2: Parse Service Implementation**
Edit: `src/maps/api/services/parse_service.py`
- Implement database insertion (lines 94-98)
- Integrate keyword extraction (lines 100-104)
- Use tables: `documents`, `document_content`, `keyword_occurrences`

### Key Implementation Details

**Parse Service (Phase 2):**
```python
# Insert document
document = {
    "source_file_name": filename,
    "file_type": file_type,
    "status": "processing",
    "profile_id": profile_id
}
# INSERT INTO documents ...

# Insert content
content = {
    "document_id": doc_id,
    "canonical_data": parsed_data,  # JSONB
    "searchable_text": extract_text(parsed_data)
}
# INSERT INTO document_content ...

# Extract keywords
keywords = keyword_extractor.extract(text)
for kw in keywords:
    # INSERT INTO keywords ... ON CONFLICT DO NOTHING
    # INSERT INTO keyword_occurrences ...
```

**Export Service (Phase 3):**
```python
# Query from views
if format == "csv":
    df = pd.read_sql("SELECT * FROM v_document_list WHERE ...", conn)
    df.to_csv(output_path)
elif format == "excel":
    df.to_excel(output_path)
elif format == "json":
    data = conn.execute("SELECT * FROM v_document_detail WHERE ...").fetchall()
    json.dump(data, f)
```

### Important Notes

1. **Direct PostgreSQL connection may still fail** with "No route to host" - Use Supabase SQL Editor instead
2. **REST API works** - Confirmed Supabase project is active
3. **Frontend/Backend both running** in background processes
4. **Git is synced** - All changes pushed to main branch

### Files to Reference

- **Migration guide:** `supabase_migrations/README.md`
- **Implementation summary:** `supabase_migrations/IMPLEMENTATION_SUMMARY.md`
- **Schema map:** See full ASCII diagram in previous session
- **Parse service:** `src/maps/api/services/parse_service.py`
- **Export service:** `src/maps/api/services/export_service.py`

### Running Services

**Check if still running:**
```bash
lsof -ti:5173  # Frontend
lsof -ti:8000  # Backend
```

**Restart if needed:**
```bash
cd web && npm run dev  # Frontend
python3 start_api.py   # Backend (from MAPS root)
```

---

## Session Goals

When you continue, aim to:
1. ✅ Apply all 10 migrations to Supabase
2. ✅ Verify schema is created correctly
3. ✅ Test backend connection to Supabase
4. 🎯 Complete parse service implementation (Phase 2)
5. 🎯 Complete export service implementation (Phase 3)
6. 🎯 Build Export page frontend (Phase 4)
7. 🎯 Build KeywordDetector page (Phase 5)
8. 🎯 End-to-end testing (Phase 6)

---

**Last Updated:** Session ended November 25, 2025
**Git Commit:** 8619213f
**Branch:** main
**Next Phase:** Apply migrations to Supabase (Phase 1 completion)
