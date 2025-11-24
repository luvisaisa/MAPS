# Keyword Consolidated View - Quick Start Guide

## Overview

This update adds a comprehensive keyword management system with:
- Enhanced keyword schema with `definition` and `source_refs` fields
- Consolidated database view (`v_keyword_consolidated`)
- Category-specific views for easy querying
- CSV import script for standardized radiology keywords
- Helper functions for common queries

---

## Quick Setup (3 Steps)

### Step 1: Apply Database Migration

```bash
# Apply migration 002 to add new keyword fields and views
bash scripts/apply_keyword_migration.sh

# Or manually:
psql -h localhost -U ra_d_ps_user -d ra_d_ps_db -f migrations/002_add_keyword_enhancements.sql
```

**What this does:**
- Adds `definition`, `source_refs`, `is_standard`, `vocabulary_source` columns to `keywords` table
- Creates `v_keyword_consolidated` view
- Creates category-specific views (v_keywords_*)
- Adds helper functions for search and retrieval

### Step 2: Import Keyword Data

```bash
# Import the 50 standardized radiology keywords from CSV
python scripts/import_keyword_csv.py data/keywords_radiology_standard.csv \
  --vocabulary-source "radiology_standard" \
  --is-standard

# Or preview first (dry run):
python scripts/import_keyword_csv.py data/keywords_radiology_standard.csv --dry-run
```

**What this does:**
- Imports 50 keywords across 5 categories:
  - Standardization & Reporting (8 keywords)
  - Radiologist Cognition & Diagnostics (11 keywords)
  - Imaging Biomarkers & Computation (11 keywords)
  - Pulmonary Nodules & Databases (14 keywords)
  - NER Performance Metrics (6 keywords)

### Step 3: Verify Setup

```sql
-- Check total keywords
SELECT COUNT(*) FROM keywords;

-- Query consolidated view
SELECT * FROM v_keyword_consolidated LIMIT 10;

-- Get keywords by category
SELECT * FROM v_keywords_standardization_reporting;
```

**Or use Python:**

```python
from maps.database.keyword_repository import KeywordRepository

repo = KeywordRepository()
keywords = repo.get_all_keywords(limit=10)

for kw in keywords:
    print(f"{kw.keyword_text}: {kw.definition}")
```

---

## Files Created

### Database Schema
- **migrations/002_add_keyword_enhancements.sql** - Main migration file
  - Adds new columns to `keywords` table
  - Creates consolidated view and category-specific views
  - Adds helper functions for search

### Data Files
- **data/keywords_radiology_standard.csv** - 50 standardized radiology keywords with definitions and references

### Scripts
- **scripts/apply_keyword_migration.sh** - Shell script to apply migration
- **scripts/import_keyword_csv.py** - Python script to import keywords from CSV

### Documentation
- **docs/KEYWORD_CONSOLIDATED_VIEW.md** - Comprehensive documentation with:
  - Schema details
  - View definitions
  - Usage examples
  - SQL queries
  - Python API examples
  - Troubleshooting

### Examples
- **examples/keyword_consolidated_view_examples.py** - 7 working examples demonstrating:
  - Getting all keywords
  - Searching keywords
  - Filtering by category
  - Adding keywords with metadata
  - Getting sources and statistics
  - Direct SQL queries

### Code Updates
- **src/maps/database/keyword_models.py** - Updated `Keyword` model with new fields
- **src/maps/database/keyword_repository.py** - Updated `add_keyword()` method with new parameters

---

## Database Views

### Main Consolidated View: `v_keyword_consolidated`

Contains all keyword data in a single view:
- Keyword metadata (text, category, definition, references)
- Statistics (frequency, document count, TF-IDF scores)
- Source counts (XML, PDF, papers)
- Synonym counts
- Timestamps

```sql
SELECT * FROM v_keyword_consolidated WHERE category = 'standardization_and_reporting';
```

### Category-Specific Views

- `v_keywords_standardization_reporting` - RADS, RadLex, structured reports
- `v_keywords_radiologist_cognition` - Errors, biases, diagnostic signs
- `v_keywords_imaging_biomarkers` - Radiomics, NLP, computational methods
- `v_keywords_pulmonary_nodules` - Nodules, screening, databases
- `v_keywords_ner_metrics` - Precision, recall, F-measure

```sql
SELECT keyword_text, definition FROM v_keywords_imaging_biomarkers;
```

---

## Helper Functions

### 1. Get Keywords by Category

```sql
SELECT * FROM get_keywords_by_category('imaging_biomarkers_and_computation');
```

### 2. Full-Text Search

```sql
SELECT * FROM search_keywords_full('lung');
```

Returns results ranked by match type (exact, partial, normalized, definition).

---

## Python API Examples

### Example 1: Get All Keywords

```python
from maps.database.keyword_repository import KeywordRepository

repo = KeywordRepository()
keywords = repo.get_all_keywords(limit=20)

for kw in keywords:
    print(f"{kw.keyword_text} ({kw.category})")
    if kw.definition:
        print(f"  {kw.definition[:100]}...")
```

### Example 2: Search Keywords

```python
repo = KeywordRepository()
results = repo.search_keywords(query='radiomics', limit=10)

for kw in results:
    print(f"{kw.keyword_text}: {kw.definition}")
```

### Example 3: Get by Category

```python
repo = KeywordRepository()
keywords = repo.get_keywords_by_category('pulmonary_nodules_and_databases')

for kw in keywords:
    print(f"{kw.keyword_text} - Refs: {kw.source_refs}")
```

### Example 4: Add Keyword with Metadata

```python
repo = KeywordRepository()

keyword = repo.add_keyword(
    keyword_text="my_new_keyword",
    category="custom_category",
    definition="A formal definition of my keyword",
    source_refs="1;2;3",
    is_standard=True,
    vocabulary_source="custom_vocabulary"
)

print(f"Added keyword ID: {keyword.keyword_id}")
```

---

## Sample Queries

### Get Top 20 Keywords by Frequency

```sql
SELECT
    keyword_text,
    category,
    total_frequency,
    document_count
FROM v_keyword_consolidated
WHERE total_frequency > 0
ORDER BY total_frequency DESC
LIMIT 20;
```

### Find Keywords with References

```sql
SELECT
    keyword_text,
    definition,
    source_refs
FROM v_keyword_consolidated
WHERE source_refs IS NOT NULL
ORDER BY category, keyword_text;
```

### Category Statistics

```sql
SELECT
    category,
    COUNT(*) as keyword_count,
    SUM(total_frequency) as total_occurrences
FROM v_keyword_consolidated
GROUP BY category
ORDER BY keyword_count DESC;
```

---

## Running the Examples

```bash
# Run all Python examples
python examples/keyword_consolidated_view_examples.py
```

This demonstrate:
1. Getting all keywords
2. Searching keywords
3. Getting keywords by category
4. Adding keywords with metadata
5. Getting keyword sources
6. Getting top keywords by frequency
7. Direct SQL queries on the view

---

## Troubleshooting

### Problem: View not found

```bash
# Reapply migration
bash scripts/apply_keyword_migration.sh
```

### Problem: No data in view

```bash
# Import keyword data
python scripts/import_keyword_csv.py data/keywords_radiology_standard.csv --is-standard
```

### Problem: Connection error

```bash
# Check if PostgreSQL is running
docker-compose ps

# Start PostgreSQL
docker-compose up -d postgres
```

---

## Next Steps

1. **Explore the data:**
   ```sql
   SELECT * FROM v_keyword_consolidated LIMIT 50;
   ```

2. **Run the examples:**
   ```bash
   python examples/keyword_consolidated_view_examples.py
   ```

3. **Add your own keywords:**
   - Create a CSV file with columns: id, category, keyword, definition, source_refs
   - Import using: `python scripts/import_keyword_csv.py your_file.csv`

4. **Read the full documentation:**
   - `docs/KEYWORD_CONSOLIDATED_VIEW.md`

---

## CSV Format

Your CSV should have these columns:

```csv
id,category,keyword,definition,source_refs
1,standardization_and_reporting,RADS,"Standardized ACR framework...","1;13"
2,imaging_biomarkers_and_computation,radiomics,"Computer-extracted features...","4;11"
```

- **id**: Numeric identifier (reference only, not used as primary key)
- **category**: Keyword category (e.g., `standardization_and_reporting`)
- **keyword**: The keyword/term text
- **definition**: Medical/technical definition
- **source_refs**: Semicolon-separated reference IDs (e.g., "1;13;25")

---

## Summary

 **Migration 002** adds enhanced keyword schema
 **50 radiology keywords** imported from CSV
 **Consolidated view** for easy querying
 **Category-specific views** for focused queries
 **Helper functions** for common operations
 **Python API** with full support for new fields
 **Comprehensive documentation** and examples

---

**For detailed documentation, see:** `docs/KEYWORD_CONSOLIDATED_VIEW.md`

**Last Updated:** November 22, 2025
