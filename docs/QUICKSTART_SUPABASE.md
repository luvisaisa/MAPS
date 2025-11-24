# Supabase Integration Quick Start Guide

**Complete setup guide for importing PYLIDC data into Supabase PostgreSQL**

---

##  Prerequisites

- Python 3.8+
- Supabase account (free tier works)
- PYLIDC dataset downloaded (optional for testing)

---

##  Quick Start (5 Minutes)

### Step 1: Create Supabase Project

1. Go to [https://supabase.com](https://supabase.com)
2. Create a new project
3. Wait for database to initialize (~2 minutes)
4. Get your connection details:
   - **Project URL**: `https://xxx.supabase.co`
   - **Anon Key**: Settings → API → Project API keys → anon/public
   - **Database URL**: Settings → Database → Connection string → URI

### Step 2: Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your Supabase credentials
nano .env  # or use any text editor
```

Add these lines to `.env`:

```bash
# Supabase Configuration
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_KEY=your-anon-key-here
SUPABASE_DB_URL=postgresql://postgres:your-password@db.project-ref.supabase.co:5432/postgres
```

** Important**: Replace `your-password` with your actual database password from Supabase dashboard.

### Step 3: Install Dependencies

```bash
# Install required packages
pip install -r requirements.txt

# Install package in editable mode
pip install -e .

# (Optional) Install PYLIDC for dataset access
pip install pylidc
```

### Step 4: Apply Database Migrations

```bash
# Option 1: Using psql directly
psql "$SUPABASE_DB_URL" -f migrations/001_initial_schema.sql
psql "$SUPABASE_DB_URL" -f migrations/002_radiology_supabase.sql
psql "$SUPABASE_DB_URL" -f migrations/003_document_parse_case_links.sql

# Option 2: Using our setup script
python scripts/setup_supabase_integration.py --migrate
```

**What this does:**
- Creates `documents` and `document_content` tables
- Creates `parse_cases` and `keywords` tables
- Adds GIN indexes for fast JSONB queries
- Creates helper functions for querying
- Sets up materialized views for analytics

### Step 5: Verify Setup

```bash
# Run verification script
python scripts/setup_supabase_integration.py --full
```

**Expected output:**
```
 Environment: ALL SET
 Database: CONNECTED
 Basic Operations: PASSED
 Enhanced Operations: PASSED
  PYLIDC: SKIPPED (optional)
```

### Step 6: Import Your First Document

```bash
# Option A: Import from PYLIDC (if installed)
python scripts/pylidc_to_supabase.py --limit 5

# Option B: Use the example script
python examples/supabase_integration.py
```

---

##  Usage Examples

### Example 1: Basic Document Import

```python
from maps.database.document_repository import DocumentRepository
from maps.schemas.canonical import RadiologyCanonicalDocument, DocumentMetadata
from datetime import datetime

# Initialize repository (uses SUPABASE_DB_URL from environment)
repo = DocumentRepository()

# Create canonical document
metadata = DocumentMetadata(
    document_type="radiology_report",
    title="My First Radiology Report",
    date=datetime.utcnow(),
    source_system="LIDC-IDRI",
    language="en"
)

canonical_doc = RadiologyCanonicalDocument(
    document_metadata=metadata,
    study_instance_uid="1.2.3.4.5",
    series_instance_uid="1.2.3.4.6",
    modality="CT",
    nodules=[
        {
            "nodule_id": "1",
            "num_radiologists": 4,
            "radiologists": {
                "1": {"subtlety": 3, "malignancy": 4},
                "2": {"subtlety": 4, "malignancy": 5},
                "3": {"subtlety": 3, "malignancy": 4},
                "4": {"subtlety": 4, "malignancy": 4}
            }
        }
    ]
)

# Insert to Supabase
doc, content = repo.insert_canonical_document(
    canonical_doc,
    source_file="test://my_first_doc",
    tags=["example", "test"]
)

print(f" Inserted document: {doc.id}")
print(f"   Status: {doc.status}")
print(f"   Tags: {content.tags}")
```

### Example 2: Import from PYLIDC with Parse Case Detection

```python
from maps.database.enhanced_document_repository import EnhancedDocumentRepository
from maps.adapters.pylidc_adapter import PyLIDCAdapter
import pylidc as pl

# Initialize enhanced repository (with parse case and keyword tracking)
repo = EnhancedDocumentRepository(
    enable_parse_case_tracking=True,
    enable_keyword_extraction=True
)

# Get PYLIDC scan
adapter = PyLIDCAdapter()
scan = pl.query(pl.Scan).first()

# Convert to canonical
canonical_doc = adapter.scan_to_canonical(scan)

# Import with full tracking
doc, content, parse_case, keywords = repo.insert_canonical_document_enhanced(
    canonical_doc,
    source_file=f"pylidc://{scan.patient_id}",
    detect_parse_case=True,
    extract_keywords=True
)

print(f" Imported: {scan.patient_id}")
print(f"   Parse case: {parse_case}")
print(f"   Keywords: {keywords}")
```

### Example 3: Query Documents

```python
from maps.database.document_repository import DocumentRepository

repo = DocumentRepository()

# Get recent documents
recent = repo.get_recent_documents(limit=10)
for doc in recent:
    print(f"• {doc.source_file_name} - {doc.source_system}")

# Search documents
results = repo.search_documents("malignancy", limit=20)
for doc, content in results:
    print(f"• {doc.source_file_name}")
    print(f"  Tags: {content.tags}")

# Get statistics
stats = repo.get_statistics()
print(f"Total documents: {stats['total_documents']}")
print(f"By status: {stats['by_status']}")
```

### Example 4: Batch Import

```python
from maps.database.enhanced_document_repository import EnhancedDocumentRepository
from maps.adapters.pylidc_adapter import PyLIDCAdapter
import pylidc as pl

repo = EnhancedDocumentRepository()
adapter = PyLIDCAdapter()

# Get multiple scans
scans = pl.query(pl.Scan).limit(10).all()

# Convert to canonical
canonical_docs = [adapter.scan_to_canonical(scan) for scan in scans]
source_files = [f"pylidc://{scan.patient_id}" for scan in scans]

# Batch import
def progress(current, total):
    print(f"Progress: {current}/{total}")

results = repo.batch_insert_canonical_documents(
    canonical_docs=canonical_docs,
    source_files=source_files,
    tags=["LIDC-IDRI", "batch_import"],
    progress_callback=progress
)

print(f" Imported {len(results)}/{len(scans)} documents")
```

---

##  Querying Data

### Using Python

```python
from maps.database.enhanced_document_repository import EnhancedDocumentRepository

repo = EnhancedDocumentRepository()

# Get statistics with parse case breakdown
stats = repo.get_document_statistics_enhanced()
print(f"Total: {stats['total_documents']}")
print(f"Parse cases: {stats['parse_cases']}")
print(f"Top keywords: {stats['top_keywords']}")

# Search by keyword
results = repo.search_documents("spiculation", limit=50)
for doc, content in results:
    canonical = content.canonical_data
    print(f"• {doc.source_file_name}")
    print(f"  Nodules: {len(canonical.get('nodules', []))}")
```

### Using SQL

```sql
-- View all documents
SELECT id, source_file_name, source_system, status
FROM documents
ORDER BY ingestion_timestamp DESC
LIMIT 10;

-- Get document with canonical data
SELECT
    d.source_file_name,
    d.source_system,
    dc.canonical_data->>'study_instance_uid' AS study_uid,
    jsonb_array_length(dc.canonical_data->'nodules') AS nodule_count
FROM documents d
JOIN document_content dc ON d.id = dc.document_id;

-- Search by modality
SELECT
    d.source_file_name,
    dc.canonical_data->>'modality' AS modality
FROM documents d
JOIN document_content dc ON d.id = dc.document_id
WHERE dc.canonical_data->>'modality' = 'CT';

-- Schema distribution
SELECT * FROM document_schema_distribution;

-- Top keywords
SELECT k.keyword_text, COUNT(*) AS usage_count
FROM keywords k
JOIN document_keywords dk ON k.keyword_id = dk.keyword_id
GROUP BY k.keyword_text
ORDER BY usage_count DESC
LIMIT 20;
```

### Using Supabase Dashboard

1. Go to your Supabase project
2. Click "Table Editor" in sidebar
3. Select `documents` or `document_content` table
4. Use filters and search to explore data

---

##  Available Tables

### `documents`
- **Purpose**: Document metadata and status tracking
- **Key Fields**: `id`, `source_file_name`, `source_system`, `status`, `parse_case_id`

### `document_content`
- **Purpose**: Canonical document data (JSONB)
- **Key Fields**: `document_id`, `canonical_data`, `searchable_text`, `tags`

### `parse_cases`
- **Purpose**: XML schema definitions
- **Key Fields**: `name`, `format_type`, `detection_criteria`, `field_mappings`

### `keywords`
- **Purpose**: Extracted medical terms
- **Key Fields**: `keyword_text`, `normalized_form`, `category`

### `document_keywords`
- **Purpose**: Document-keyword relationships
- **Key Fields**: `document_id`, `keyword_id`, `frequency`, `tf_idf_score`

---

##  Utilities

### Check Database Status

```bash
# Using setup script
python scripts/setup_supabase_integration.py --check

# Using psql
psql "$SUPABASE_DB_URL" -c "\dt"  # List tables
psql "$SUPABASE_DB_URL" -c "SELECT COUNT(*) FROM documents;"
```

### Import PYLIDC Data

```bash
# Import 10 scans
python scripts/pylidc_to_supabase.py --limit 10

# Import specific patient
python scripts/pylidc_to_supabase.py --patient LIDC-IDRI-0001

# Import high-quality scans only
python scripts/pylidc_to_supabase.py --filter high_quality --limit 50
```

### View Logs

```bash
# Check import logs
tail -f logs/maps.log

# Query ingestion logs from database
psql "$SUPABASE_DB_URL" -c "SELECT * FROM ingestion_logs ORDER BY start_time DESC LIMIT 10;"
```

---

##  Troubleshooting

### Connection Issues

**Problem**: `psycopg2.OperationalError: could not connect to server`

**Solutions:**
1. Check your `SUPABASE_DB_URL` is correct
2. Verify your Supabase project is active
3. Check if your IP is allowed:
   - Go to Supabase Dashboard → Settings → Database
   - Add your IP to "Connection pooling" allowlist

### Import Errors

**Problem**: `ParsingError` or `ValidationError` during import

**Solutions:**
1. Check PYLIDC dataset is properly installed
2. Verify scan data is complete
3. Use `--skip-errors` flag for batch imports

### Migration Issues

**Problem**: Migrations fail or table already exists

**Solutions:**
```bash
# Check applied migrations
psql "$SUPABASE_DB_URL" -c "SELECT * FROM schema_migrations;"

# Reset database ( DELETES ALL DATA)
psql "$SUPABASE_DB_URL" -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

# Re-apply migrations
psql "$SUPABASE_DB_URL" -f migrations/001_initial_schema.sql
```

---

##  Next Steps

1. **Import your dataset**: Use `scripts/pylidc_to_supabase.py` to import PYLIDC data
2. **Explore examples**: Check `examples/` directory for more usage patterns
3. **Read full guide**: See `docs/SUPABASE_SCHEMA_AGNOSTIC_GUIDE.md` for architecture details
4. **Query your data**: Use SQL or Python to analyze imported documents
5. **Customize**: Modify profiles to support your specific XML formats

---

##  Related Documentation

- **Complete Guide**: [SUPABASE_SCHEMA_AGNOSTIC_GUIDE.md](SUPABASE_SCHEMA_AGNOSTIC_GUIDE.md)
- **Implementation Details**: [IMPLEMENTATION_GUIDE_SCHEMA_AGNOSTIC.md](IMPLEMENTATION_GUIDE_SCHEMA_AGNOSTIC.md)
- **API Reference**: [API_REFERENCE.md](API_REFERENCE.md)
- **Developer Guide**: [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)

---

##  Quick Validation Checklist

- [ ] Supabase project created
- [ ] Environment variables set in `.env`
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Package installed (`pip install -e .`)
- [ ] Migrations applied (3 SQL files)
- [ ] Verification script passed (`python scripts/setup_supabase_integration.py --full`)
- [ ] First document imported successfully
- [ ] Can query data from Supabase dashboard

---

**Need Help?**
- Check `docs/SUPABASE_SCHEMA_AGNOSTIC_GUIDE.md` for detailed documentation
- Review examples in `examples/supabase_integration.py`
- Run verification: `python scripts/setup_supabase_integration.py --check`

---

*Last Updated: November 2025*
