# Supabase Integration Guide

**MAPS Radiology Data Processing System**
**Version:** 1.0.0
**Last Updated:** November 23, 2025

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Environment Setup](#environment-setup)
4. [Database Migration](#database-migration)
5. [Basic Usage](#basic-usage)
6. [Advanced Operations](#advanced-operations)
7. [PYLIDC Integration](#pylidc-integration)
8. [API Reference](#api-reference)
9. [Troubleshooting](#troubleshooting)

---

## Overview

The MAPS system integrates with Supabase to provide:

- Cloud-hosted PostgreSQL database
- Real-time data synchronization
- Built-in authentication and authorization
- Row-level security (RLS) policies
- REST API access to data
- Full-text search capabilities
- JSONB storage for flexible schema-agnostic data

### Architecture

```
MAPS Application
 Python Client (supabase-py) → Supabase REST API
 SQLAlchemy ORM → PostgreSQL (direct connection)
 DocumentRepository → Database operations

Supabase Platform
 PostgreSQL Database
    documents table (metadata)
    document_content table (JSONB canonical data)
    parse_cases table (structure classification)
    keywords table (extracted keywords)
 Authentication (optional)
 Storage (optional)
 Edge Functions (optional)
```

---

## Prerequisites

### Required Software

- Python 3.8+
- pip package manager
- PostgreSQL client tools (optional, for manual queries)

### Required Python Packages

```bash
pip install supabase
pip install python-dotenv
pip install sqlalchemy
pip install psycopg2-binary
```

### Supabase Project

1. Create account at https://supabase.com
2. Create new project
3. Note the following credentials from project settings:
   - Project URL
   - Anon/Public API key
   - Service Role key (for admin operations)
   - Database password

---

## Environment Setup

### Step 1: Configure Environment Variables

Create or edit `.env` file in project root:

```bash
# Supabase REST API credentials
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=your-anon-public-key-here
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here

# Supabase PostgreSQL connection
SUPABASE_DB_URL=postgresql://postgres:your-password@db.xxxxx.supabase.co:5432/postgres

# Database backend selection (optional)
DATABASE_BACKEND=supabase
```

### Step 2: Verify Connection

```bash
python scripts/setup_supabase_integration.py --check
```

Expected output:
```
 SUPABASE_URL: https://xxxxx.supabase.co
 SUPABASE_KEY: eyJhbGciO...
 SUPABASE_DB_URL: postgresql://postgres:***...
```

---

## Database Migration

### Apply Schema Migrations

#### Option 1: Using psql Command Line

```bash
# Apply initial schema
psql "$SUPABASE_DB_URL" -f migrations/001_initial_schema.sql

# Apply radiology-specific extensions
psql "$SUPABASE_DB_URL" -f migrations/002_radiology_supabase.sql

# Apply parse case and keyword tracking
psql "$SUPABASE_DB_URL" -f migrations/003_document_parse_case_links.sql
```

#### Option 2: Using Supabase Dashboard

1. Navigate to SQL Editor in Supabase dashboard
2. Copy content from each migration file
3. Execute migrations in order (001, 002, 003)

#### Option 3: Using Makefile

```bash
make db-migrate
```

### Verify Migration Success

```bash
psql "$SUPABASE_DB_URL" -c "\dt"
```

Expected tables:
- documents
- document_content
- profiles
- ingestion_logs
- keywords
- parse_cases
- document_parse_case_links

---

## Basic Usage

### Initialize Repository

```python
from maps.database.document_repository import DocumentRepository

# Initialize (uses SUPABASE_DB_URL from environment)
repo = DocumentRepository()
```

### Create Document

```python
# Create document metadata
doc = repo.create_document(
    source_file_name="scan_001.xml",
    source_file_path="/data/scans/001.xml",
    file_type="XML",
    uploaded_by="user@example.com",
    source_system="LIDC-IDRI"
)

print(f"Created document ID: {doc.id}")
```

### Insert Canonical Document

```python
from maps.schemas.canonical import RadiologyCanonicalDocument, DocumentMetadata
from datetime import datetime

# Create canonical document
metadata = DocumentMetadata(
    document_type="radiology_report",
    title="CT Scan Report",
    date=datetime.utcnow(),
    source_system="LIDC-IDRI",
    language="en"
)

canonical_doc = RadiologyCanonicalDocument(
    document_metadata=metadata,
    study_instance_uid="1.2.840.113654.2.55.12345",
    series_instance_uid="1.2.840.113654.2.55.12346",
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
    ],
    fields={"additional_data": "value"}
)

# Insert to Supabase
doc, content = repo.insert_canonical_document(
    canonical_doc,
    source_file="data/scans/001.xml",
    uploaded_by="user@example.com",
    tags=["LIDC-IDRI", "lung", "CT"]
)
```

### Query Documents

```python
# Get recent documents
recent = repo.get_recent_documents(limit=10, status='completed')

# Get by source system
lidc_docs = repo.get_documents_by_source_system("LIDC-IDRI")

# Search documents
results = repo.search_documents("lung nodule", limit=20)

# Get statistics
stats = repo.get_statistics()
print(f"Total documents: {stats['total_documents']}")
print(f"By status: {stats['by_status']}")
```

### Update and Delete

```python
# Update document status
repo.update_document_status(
    document_id=doc.id,
    status='completed',
    processing_duration_ms=1250
)

# Delete document (cascades to content)
repo.delete_document(doc.id)
```

---

## Advanced Operations

### Enhanced Repository with Parse Case Tracking

```python
from maps.database.enhanced_document_repository import EnhancedDocumentRepository

# Initialize with enhanced features
repo = EnhancedDocumentRepository(
    enable_parse_case_tracking=True,
    enable_keyword_extraction=True
)

# Insert with automatic parse case detection and keyword extraction
doc, content, parse_case, keyword_count = repo.insert_canonical_document_enhanced(
    canonical_doc,
    source_file="data/scans/001.xml",
    detect_parse_case=True,
    extract_keywords=True
)

print(f"Parse case: {parse_case}")
print(f"Keywords extracted: {keyword_count}")
```

### Batch Import

```python
# Prepare multiple canonical documents
canonical_docs = [doc1, doc2, doc3]
source_files = ["file1.xml", "file2.xml", "file3.xml"]

# Batch insert with progress tracking
def progress_callback(current, total):
    print(f"Processing {current}/{total}")

results = repo.batch_insert_canonical_documents(
    canonical_docs=canonical_docs,
    source_files=source_files,
    uploaded_by="batch_user",
    tags=["batch_import"],
    progress_callback=progress_callback
)

print(f"Imported {len(results)} documents")
```

### Direct SQL Queries

```python
from sqlalchemy import text

# Execute custom query
with repo.Session() as session:
    result = session.execute(
        text("""
            SELECT
                canonical_data->>'study_instance_uid' as study_uid,
                COUNT(*) as nodule_count
            FROM document_content
            WHERE canonical_data->'nodules' IS NOT NULL
            GROUP BY study_uid
            LIMIT 10
        """)
    )

    for row in result:
        print(f"Study {row.study_uid}: {row.nodule_count} nodules")
```

### Using Materialized Views

```python
# Query the pre-computed radiology summary view
with repo.Session() as session:
    result = session.execute(
        text("""
            SELECT * FROM radiology_document_summary
            WHERE nodule_count > 0
            ORDER BY ingestion_timestamp DESC
            LIMIT 10
        """)
    )

    for row in result:
        print(f"{row.source_file_name}: {row.nodule_count} nodules")

# Refresh the materialized view
with repo.Session() as session:
    session.execute(text("SELECT refresh_radiology_summary()"))
    session.commit()
```

### Search Nodules by Malignancy

```python
# Use the built-in PostgreSQL function
with repo.Session() as session:
    result = session.execute(
        text("""
            SELECT * FROM search_nodules_by_malignancy(
                min_malignancy := 4,
                limit_count := 50
            )
        """)
    )

    for row in result:
        print(f"Document: {row.document_id}")
        print(f"Study UID: {row.study_uid}")
        print(f"Nodule ID: {row.nodule_id}")
        print(f"Avg Malignancy: {row.avg_malignancy}")
```

---

## PYLIDC Integration

### Import LIDC-IDRI Dataset

```python
import pylidc as pl
from maps.adapters.pylidc_adapter import PyLIDCAdapter

# Initialize adapter and repository
adapter = PyLIDCAdapter()
repo = EnhancedDocumentRepository()

# Query PYLIDC scans
scans = pl.query(pl.Scan).limit(10).all()

# Convert and import each scan
for scan in scans:
    # Convert to canonical format
    canonical_doc = adapter.scan_to_canonical(scan, cluster_nodules=True)

    # Insert to Supabase
    doc, content, parse_case, keywords = repo.insert_canonical_document_enhanced(
        canonical_doc,
        source_file=f"pylidc://{scan.patient_id}",
        detect_parse_case=True,
        extract_keywords=True
    )

    print(f"Imported {scan.patient_id}: {len(canonical_doc.nodules)} nodules")
```

### Batch PYLIDC Import

```bash
# Use the batch import script
python scripts/pylidc_to_supabase.py --limit 100 --batch-size 10

# With progress tracking
python scripts/pylidc_to_supabase.py --limit 100 --verbose
```

---

## API Reference

### Supabase Client Functions

#### get_supabase_client()

Returns Supabase REST API client for database, authentication, and storage operations.

```python
from maps.supabase import get_supabase_client

client = get_supabase_client()

# Query using Supabase REST API
response = client.table('documents').select('*').limit(10).execute()
documents = response.data
```

#### get_supabase_service_client()

Returns Supabase client with service role privileges (bypasses RLS).

```python
from maps.supabase import get_supabase_service_client

# Use for administrative operations only
admin_client = get_supabase_service_client()
```

#### is_supabase_available()

Checks if Supabase credentials are configured.

```python
from maps.supabase import is_supabase_available

if is_supabase_available():
    print("Supabase is configured")
else:
    print("Supabase credentials not found")
```

### DocumentRepository Methods

#### create_document()

Creates document metadata entry.

```python
doc = repo.create_document(
    source_file_name: str,
    source_file_path: str,
    file_type: str,
    uploaded_by: str = None,
    source_system: str = None,
    batch_id: str = None
)
```

#### insert_canonical_document()

Inserts canonical document with content.

```python
doc, content = repo.insert_canonical_document(
    canonical_doc: RadiologyCanonicalDocument,
    source_file: str,
    uploaded_by: str = None,
    tags: List[str] = None,
    confidence_score: float = None
)
```

#### get_document()

Retrieves document by ID.

```python
doc = repo.get_document(document_id: UUID)
```

#### search_documents()

Full-text search across documents.

```python
results = repo.search_documents(
    query: str,
    limit: int = 100,
    source_system: str = None
)
```

#### get_statistics()

Returns repository statistics.

```python
stats = repo.get_statistics()
# Returns:
# {
#     'total_documents': int,
#     'by_status': Dict[str, int],
#     'by_source_system': Dict[str, int],
#     'by_file_type': Dict[str, int]
# }
```

---

## Troubleshooting

### Connection Issues

**Problem**: `psycopg2.OperationalError: could not connect to server`

**Solution**:
1. Verify SUPABASE_DB_URL is correct
2. Check Supabase project status in dashboard
3. Ensure IP address is allowed in Supabase Network Restrictions
4. Confirm database password is correct

### Authentication Errors

**Problem**: `RuntimeError: SUPABASE_URL and SUPABASE_KEY must be set`

**Solution**:
1. Check .env file exists in project root
2. Verify environment variables are loaded:
   ```python
   import os
   print(os.getenv('SUPABASE_URL'))
   ```
3. Reload environment or restart application

### Migration Failures

**Problem**: Migration fails with "relation already exists"

**Solution**:
Migrations are idempotent. Errors about existing tables/functions can be ignored if they use `IF NOT EXISTS` or `IF EXISTS` clauses.

### RLS Policy Conflicts

**Problem**: Operations fail with "new row violates row-level security policy"

**Solution**:
1. Use service role client for administrative operations:
   ```python
   from maps.supabase import get_supabase_service_client
   admin_client = get_supabase_service_client()
   ```
2. Or disable RLS for development:
   ```sql
   ALTER TABLE documents DISABLE ROW LEVEL SECURITY;
   ALTER TABLE document_content DISABLE ROW LEVEL SECURITY;
   ```

### Performance Issues

**Problem**: Slow queries on large datasets

**Solution**:
1. Refresh materialized views:
   ```sql
   SELECT refresh_radiology_summary();
   ```
2. Add custom indexes:
   ```sql
   CREATE INDEX idx_custom ON document_content
   USING GIN ((canonical_data -> 'your_field'));
   ```
3. Use connection pooling for high-traffic applications

### Import Errors

**Problem**: `ImportError: No module named 'supabase'`

**Solution**:
```bash
pip install supabase python-dotenv sqlalchemy psycopg2-binary
```

---

## Example Workflows

### Complete Import Pipeline

```python
from maps.database.enhanced_document_repository import EnhancedDocumentRepository
from maps.adapters.pylidc_adapter import PyLIDCAdapter
import pylidc as pl

# 1. Initialize components
adapter = PyLIDCAdapter()
repo = EnhancedDocumentRepository(
    enable_parse_case_tracking=True,
    enable_keyword_extraction=True
)

# 2. Query PYLIDC dataset
scans = pl.query(pl.Scan).filter(
    pl.Scan.slice_thickness <= 2.5
).limit(50).all()

print(f"Found {len(scans)} scans")

# 3. Batch convert and import
canonical_docs = []
source_files = []

for scan in scans:
    canonical_doc = adapter.scan_to_canonical(scan, cluster_nodules=True)
    canonical_docs.append(canonical_doc)
    source_files.append(f"pylidc://{scan.patient_id}")

# 4. Batch insert to Supabase
results = repo.batch_insert_canonical_documents(
    canonical_docs=canonical_docs,
    source_files=source_files,
    uploaded_by="pipeline_user",
    tags=["LIDC-IDRI", "batch_import", "thin_slice"],
    progress_callback=lambda i, total: print(f"Progress: {i}/{total}")
)

print(f"Imported {len(results)} documents to Supabase")

# 5. Query imported data
stats = repo.get_statistics()
print(f"Total documents in database: {stats['total_documents']}")
```

### Real-time Query Dashboard

```python
from maps.database.document_repository import DocumentRepository
from sqlalchemy import text

repo = DocumentRepository()

# Get summary statistics
with repo.Session() as session:
    # Document counts by status
    status_counts = session.execute(
        text("SELECT status, COUNT(*) as count FROM documents GROUP BY status")
    ).fetchall()

    # Top keywords
    top_keywords = session.execute(
        text("""
            SELECT keyword, COUNT(*) as frequency
            FROM keywords
            GROUP BY keyword
            ORDER BY frequency DESC
            LIMIT 10
        """)
    ).fetchall()

    # Recent high-malignancy nodules
    high_malignancy = session.execute(
        text("""
            SELECT * FROM search_nodules_by_malignancy(4, 20)
        """)
    ).fetchall()

print("Dashboard Statistics:")
print(f"Documents by status: {dict(status_counts)}")
print(f"Top keywords: {[k.keyword for k in top_keywords]}")
print(f"High malignancy nodules: {len(high_malignancy)}")
```

---

## Additional Resources

### Documentation
- Supabase Documentation: https://supabase.com/docs
- PostgreSQL JSONB: https://www.postgresql.org/docs/current/datatype-json.html
- SQLAlchemy ORM: https://docs.sqlalchemy.org/

### Example Scripts
- `examples/supabase_integration.py` - Basic usage examples
- `examples/enhanced_supabase_pipeline.py` - Advanced pipeline
- `scripts/pylidc_to_supabase.py` - Batch PYLIDC import
- `scripts/setup_supabase_integration.py` - Setup verification

### Migration Files
- `migrations/001_initial_schema.sql` - Base schema
- `migrations/002_radiology_supabase.sql` - Radiology extensions
- `migrations/003_document_parse_case_links.sql` - Parse case tracking

---

**Last Updated:** November 23, 2025
**Version:** 1.0.0
**Maintainer:** MAPS Development Team
