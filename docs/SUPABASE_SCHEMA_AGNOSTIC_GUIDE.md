# Supabase Schema-Agnostic Integration Guide

**Complete guide to schema-agnostic radiology data processing with Supabase**

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Schema-Agnostic Design](#schema-agnostic-design)
3. [Parse Case Tracking](#parse-case-tracking)
4. [Keyword Extraction](#keyword-extraction)
5. [Database Schema](#database-schema)
6. [Setup Guide](#setup-guide)
7. [Usage Examples](#usage-examples)
8. [Query Patterns](#query-patterns)

---

## Architecture Overview

### The Problem

Different radiology systems export XML in different formats:
- LIDC-IDRI has multiple schema versions
- Hospital systems use proprietary formats
- Research datasets have varying structures

**Traditional approach**: Write separate parsers for each format (rigid, hard to maintain)

**Our approach**: Schema-agnostic system that:
1. Detects XML structure automatically (**Parse Case**)
2. Maps to canonical format using profiles
3. Extracts keywords for search
4. Tracks which schema was used

### Data Flow

```

                    SCHEMA-AGNOSTIC PIPELINE                 


XML Source File
    ↓

 1. PARSE CASE           ← Detect XML structure type
    DETECTION              (LIDC v1, v2, custom, etc.)

            ↓

 2. PROFILE-BASED        ← Map fields using detected profile
    PARSING                source_path → target_path

            ↓

 3. CANONICAL SCHEMA     ← Normalized Pydantic model
    (Pydantic)             RadiologyCanonicalDocument

            ↓

 4. KEYWORD              ← Extract medical terms
    EXTRACTION             anatomy, characteristics, etc.

            ↓

 5. SUPABASE             ← Store with metadata
    PostgreSQL             + parse_case_id
                           + keywords

```

---

## Schema-Agnostic Design

### What is a Parse Case?

A **parse case** is a detected XML structure pattern with specific characteristics.

**Example Parse Cases**:
- `LIDC_Single_Session`: One radiologist, one nodule
- `LIDC_Multi_Session_4`: Four radiologists per nodule
- `Custom_Hospital_Format`: Custom XML structure
- `LIDC_v2_Enhanced`: New LIDC format with additional fields

### Parse Case Components

```python
# Database model (from models.py)
class ParseCase(Base):
    id: UUID
    name: str  # "LIDC_Multi_Session_4"
    description: str
    version: str

    # Detection rules (JSONB)
    detection_criteria: dict  # How to detect this format
    field_mappings: list  # How to map fields
    characteristic_fields: list  # Expected fields

    # Structural requirements
    requires_header: bool
    requires_modality: bool
    min_session_count: int
    max_session_count: int

    # Priority for detection
    detection_priority: int  # 0-100, higher = check first
```

### Detection Process

```python
from maps.structure_detector import XMLStructureDetector

detector = XMLStructureDetector()

# Detect parse case from XML file
xml_file = "scan001.xml"
parse_case = detector.detect_structure(xml_file)

print(parse_case.name)  # "LIDC_Multi_Session_4"
print(parse_case.format_type)  # "LIDC"
print(parse_case.characteristic_fields)  # ["subtlety", "malignancy", ...]
```

### Why This Matters

**Without parse case tracking:**
-  Don't know which XML schema was used
-  Can't query "all LIDC v2 format documents"
-  Can't detect when XML format changes
-  Can't track success rates by format

**With parse case tracking:**
-  Know exact schema for each document
-  Query by format type: `WHERE parse_case_id = '...'`
-  Detect schema drift automatically
-  Track parsing success rates per schema
-  Optimize parsing strategies per schema

---

## Parse Case Tracking

### Database Structure

```sql
-- documents table (links to parse_cases)
CREATE TABLE documents (
    id UUID PRIMARY KEY,
    source_file_path TEXT,
    source_system TEXT,  -- "LIDC-IDRI", "Hospital X"
    parse_case_id UUID REFERENCES parse_cases(id),  -- ← Schema identifier
    status TEXT,
    created_at TIMESTAMPTZ
);

-- parse_cases table (defines schemas)
CREATE TABLE parse_cases (
    id UUID PRIMARY KEY,
    name TEXT UNIQUE,  -- "LIDC_Multi_Session_4"
    format_type TEXT,  -- "LIDC", "CXR", "Custom"
    detection_criteria JSONB,  -- Rules for detection
    field_mappings JSONB  -- How to map fields
);

-- parse_case_detection_history (audit trail)
CREATE TABLE parse_case_detection_history (
    id UUID PRIMARY KEY,
    file_path TEXT,
    parse_case_id UUID REFERENCES parse_cases(id),
    parse_case_name TEXT,
    detected_at TIMESTAMPTZ,
    detection_duration_ms INTEGER
);
```

### Enhanced Repository Usage

```python
from maps.database.enhanced_document_repository import EnhancedDocumentRepository

repo = EnhancedDocumentRepository(
    enable_parse_case_tracking=True,  # ← Enable parse case detection
    enable_keyword_extraction=True    # ← Enable keyword extraction
)

# Import with automatic parse case detection
doc, content, parse_case, keyword_count = repo.insert_canonical_document_enhanced(
    canonical_doc,
    source_file="pylidc://LIDC-0001",
    detect_parse_case=True,  # ← Auto-detect parse case
    extract_keywords=True     # ← Auto-extract keywords
)

print(f"Parse case detected: {parse_case}")  # "LIDC_Multi_Session_4"
print(f"Keywords extracted: {keyword_count}")  # 15
```

### Query by Parse Case

```sql
-- Get all documents using LIDC v2 format
SELECT
    d.source_file_name,
    d.ingestion_timestamp,
    pc.name AS parse_case
FROM documents d
JOIN parse_cases pc ON d.parse_case_id = pc.id
WHERE pc.format_type = 'LIDC'
  AND pc.version = '2.0'
ORDER BY d.ingestion_timestamp DESC;

-- Schema distribution
SELECT * FROM document_schema_distribution;

-- Output:
-- parse_case_name      | format_type | document_count
-- ---------------------|-------------|---------------
-- LIDC_Multi_Session_4 | LIDC        | 523
-- LIDC_Multi_Session_3 | LIDC        | 312
-- LIDC_Single_Session  | LIDC        | 183
```

---

## Keyword Extraction

### What are Keywords?

Keywords are **medical terms**, **anatomical references**, and **characteristics** automatically extracted from documents for full-text search.

### Keyword Categories

```python
KEYWORD_CATEGORIES = [
    'anatomy',           # "lung", "lobe", "nodule"
    'characteristic',    # "spiculation", "margin", "texture"
    'diagnosis',         # "malignancy", "benign", "suspicious"
    'modality',          # "CT", "MRI", "X-ray"
    'metadata',          # "patient_id", "study_date"
    'research',          # Dataset-specific terms
    'medical_term'       # General medical terminology
]
```

### Database Structure

```sql
-- keywords table
CREATE TABLE keywords (
    keyword_id SERIAL PRIMARY KEY,
    keyword_text TEXT UNIQUE,  -- "malignancy"
    normalized_form TEXT,       -- "malignancy" (lowercase)
    category TEXT,              -- "characteristic"
    description TEXT
);

-- document_keywords (junction table)
CREATE TABLE document_keywords (
    id UUID PRIMARY KEY,
    document_id UUID REFERENCES documents(id),
    keyword_id INTEGER REFERENCES keywords(keyword_id),
    frequency INTEGER,     -- How many times in document
    tf_idf_score REAL,    -- Relevance score
    extracted_at TIMESTAMPTZ,
    UNIQUE(document_id, keyword_id)
);

-- keyword_sources (legacy table)
CREATE TABLE keyword_sources (
    source_id SERIAL PRIMARY KEY,
    keyword_id INTEGER REFERENCES keywords(keyword_id),
    source_type TEXT,      -- "canonical_document", "xml", "pdf"
    source_file TEXT,      -- Document identifier
    frequency INTEGER,
    tf_idf_score REAL,
    context TEXT          -- Surrounding text snippet
);
```

### Automatic Extraction

```python
# Keywords are automatically extracted during import
doc, content, parse_case, keyword_count = repo.insert_canonical_document_enhanced(
    canonical_doc,
    extract_keywords=True  # ← Automatic extraction
)

# Extracted keywords include:
# - Modality: "CT"
# - Characteristics: "subtlety_3", "malignancy_4", "spiculation_2"
# - Medical terms: "nodule", "lung", "lesion"
# - Anatomy: specific anatomical references
```

### Search by Keywords

```python
# Search documents containing specific keywords
repo = EnhancedDocumentRepository()

# Full-text search
results = repo.search_documents("malignancy", limit=20)

# Results include documents with:
# - "malignancy" in title/description
# - malignancy characteristic values
# - Related medical terms
```

```sql
-- SQL query for keyword-based search
SELECT
    d.id,
    d.source_file_name,
    k.keyword_text,
    dk.frequency,
    dk.tf_idf_score
FROM documents d
JOIN document_keywords dk ON d.id = dk.document_id
JOIN keywords k ON dk.keyword_id = k.keyword_id
WHERE k.category = 'characteristic'
  AND k.keyword_text LIKE '%malignancy%'
ORDER BY dk.tf_idf_score DESC
LIMIT 20;
```

---

## Database Schema

### Core Tables

```
documents
 id (UUID)
 source_file_path (TEXT)
 source_system (TEXT)  ← "LIDC-IDRI", "Hospital X"
 parse_case_id (UUID)  ← Links to parse_cases
 status (TEXT)
 created_at (TIMESTAMPTZ)

document_content
 id (UUID)
 document_id (UUID) → documents.id
 canonical_data (JSONB)  ← Full canonical document
 searchable_text (TEXT)  ← For full-text search
 tags (TEXT[])
 confidence_score (NUMERIC)

parse_cases
 id (UUID)
 name (TEXT)  ← "LIDC_Multi_Session_4"
 format_type (TEXT)  ← "LIDC", "CXR"
 detection_criteria (JSONB)
 field_mappings (JSONB)
 detection_priority (INTEGER)

keywords
 keyword_id (SERIAL)
 keyword_text (TEXT)
 normalized_form (TEXT)
 category (TEXT)

document_keywords
 document_id (UUID) → documents.id
 keyword_id (INTEGER) → keywords.keyword_id
 frequency (INTEGER)
 tf_idf_score (REAL)
```

### Relationships

```
documents → document_content (1:1)
            → parse_cases (N:1)
            → document_keywords (1:N)

document_keywords → keywords (N:1)

parse_cases → parse_case_detection_history (1:N)
              → parse_case_statistics (1:N)
```

---

## Setup Guide

### 1. Apply Migrations

```bash
# Connect to Supabase
psql "postgresql://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres"

# Apply migrations in order
\i migrations/001_initial_schema.sql
\i migrations/002_radiology_supabase.sql
\i migrations/003_document_parse_case_links.sql
```

### 2. Initialize Parse Cases

```python
from maps.database.parse_case_repository import ParseCaseRepository

repo = ParseCaseRepository(connection_string=os.getenv("SUPABASE_DB_URL"))

# Create parse case definitions
repo.create_parse_case(
    name="LIDC_Multi_Session_4",
    description="LIDC format with 4 radiologists per nodule",
    format_type="LIDC",
    detection_criteria={
        "required_fields": ["nodule_id", "radiologists"],
        "min_radiologists": 4,
        "max_radiologists": 4
    },
    field_mappings=[
        {"source": "nodule_id", "target": "nodule_id"},
        {"source": "radiologists", "target": "radiologist_readings"}
    ],
    characteristic_fields=[
        "subtlety", "malignancy", "internalStructure",
        "calcification", "sphericity", "margin",
        "lobulation", "spiculation", "texture"
    ]
)
```

### 3. Configure Environment

```bash
# .env file
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_DB_URL=postgresql://postgres:password@db.project.supabase.co:5432/postgres
```

### 4. Import Data

```bash
# Use enhanced pipeline
python scripts/pylidc_to_supabase.py --limit 10

# Or use enhanced repository directly
python examples/enhanced_supabase_pipeline.py
```

---

## Usage Examples

### Example 1: Import with Full Tracking

```python
from maps.database.enhanced_document_repository import EnhancedDocumentRepository
from maps.adapters.pylidc_adapter import PyLIDCAdapter
import pylidc as pl

# Initialize
repo = EnhancedDocumentRepository(
    enable_parse_case_tracking=True,
    enable_keyword_extraction=True
)
adapter = PyLIDCAdapter()

# Get scan
scan = pl.query(pl.Scan).first()
canonical_doc = adapter.scan_to_canonical(scan)

# Import with full tracking
doc, content, parse_case, keyword_count = repo.insert_canonical_document_enhanced(
    canonical_doc,
    source_file=f"pylidc://{scan.patient_id}",
    detect_parse_case=True,
    extract_keywords=True
)

print(f"Parse case: {parse_case}")          # "LIDC_Multi_Session_4"
print(f"Keywords: {keyword_count}")         # 15
print(f"Document ID: {doc.id}")
```

### Example 2: Query by Schema Type

```python
# Get statistics by parse case
stats = repo.get_document_statistics_enhanced()

print(stats['parse_cases'])
# {
#     'LIDC_Multi_Session_4': 523,
#     'LIDC_Multi_Session_3': 312,
#     'LIDC_Single_Session': 183
# }
```

### Example 3: Search by Keywords

```python
# Search for high-malignancy documents
results = repo.search_documents("malignancy", limit=50)

for doc, content in results:
    # Filter by canonical data
    canonical = content.canonical_data
    if 'nodules' in canonical:
        for nodule in canonical['nodules']:
            avg_malignancy = calculate_avg_malignancy(nodule)
            if avg_malignancy >= 4:
                print(f"High risk: {doc.source_file_name}")
```

---

## Query Patterns

### 1. Get Documents by Parse Case

```sql
SELECT * FROM get_documents_by_parse_case('LIDC_Multi_Session_4', 100);
```

### 2. Schema Distribution

```sql
SELECT * FROM document_schema_distribution;
```

### 3. Parse Case Usage Statistics

```sql
SELECT * FROM parse_case_usage_stats;
```

### 4. Keyword Search

```sql
SELECT
    d.source_file_name,
    k.keyword_text,
    dk.frequency
FROM documents d
JOIN document_keywords dk ON d.id = dk.document_id
JOIN keywords k ON dk.keyword_id = k.keyword_id
WHERE k.keyword_text IN ('malignancy', 'spiculation', 'margin')
ORDER BY dk.tf_idf_score DESC;
```

### 5. Detect Schema Drift

```sql
SELECT * FROM detect_parse_case_drift();
-- Shows documents where detected schema != assigned schema
```

---

## Benefits

### Schema Agnostic
-  No code changes for new XML formats
-  Automatic format detection
-  Profile-based field mapping

### Searchable
-  Automatic keyword extraction
-  Full-text search with PostgreSQL
-  TF-IDF relevance scoring

### Trackable
-  Know which schema was used
-  Detection history audit trail
-  Performance metrics per schema

### Scalable
-  JSONB for flexible data
-  GIN indexes for fast queries
-  Materialized views for analytics
-  Connection pooling

---

## Next Steps

1. **Apply migrations** to add parse_case_id and keyword links
2. **Initialize parse cases** in database
3. **Import data** using enhanced repository
4. **Query and analyze** using SQL views and functions

For more examples, see:
- `examples/enhanced_supabase_pipeline.py`
- `scripts/pylidc_to_supabase.py`
- `tests/test_document_repository.py`
