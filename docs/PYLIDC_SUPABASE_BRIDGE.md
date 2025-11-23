# PyLIDC → Supabase Integration

Direct integration between pylidc library and Supabase PostgreSQL for querying and importing LIDC-IDRI dataset.

## Quick Start

### 1. Prerequisites

```bash
# Install pylidc
pip install pylidc

# Configure pylidc (points to LIDC-IDRI dataset location)
pylidc conf

# Ensure Supabase credentials are set
export SUPABASE_URL="https://lfzijlkdmnnrttsatrtc.supabase.co"
export SUPABASE_KEY="your-key"
```

### 2. Run Interactive CLI

```bash
python scripts/pylidc_bridge_cli.py
```

**Menu Options:**
1. Query high-quality scans (≤1.0mm slice thickness)
2. Query by patient ID
3. Find malignant nodules (malignancy ≥4)
4. Search by characteristics (spiculation, calcification, etc.)
5. Import scan(s) to Supabase
6. Check what's already imported
7. View Supabase statistics

### 3. Programmatic Usage

```python
from ra_d_ps.pylidc_supabase_bridge import PyLIDCSupabaseBridge

# Initialize bridge
bridge = PyLIDCSupabaseBridge()

# Query pylidc for high-quality scans
scans = bridge.query_scans(
    max_slice_thickness=1.0,  # High quality
    has_annotations=True,
    limit=10
)

# Import to Supabase
for scan in scans:
    if not bridge.is_scan_imported(scan.patient_id):
        result = bridge.import_scan(scan)
        print(f"Imported: {result['patient_id']} with {result['nodule_count']} nodules")
```

## Key Features

### Query PyLIDC Database

```python
# By patient ID
scans = bridge.query_scans(patient_id="LIDC-IDRI-0001")

# By quality (slice thickness)
scans = bridge.query_scans(
    max_slice_thickness=1.0,  # ≤1mm = high quality
    has_annotations=True,
    limit=20
)

# Find malignant nodules
nodules = bridge.query_nodules_by_malignancy(
    min_malignancy=4,  # Highly suspicious
    limit=50
)

# Search by characteristics
results = bridge.search_by_characteristics(
    spiculation=5,      # Highly spiculated
    calcification=6,    # No calcification
    sphericity=1,       # Linear
    limit=30
)
```

### Import to Supabase

```python
# Single scan
result = bridge.import_scan(scan, include_annotations=True)
# Returns: {'document_id': '...', 'patient_id': '...', 'nodule_count': 3}

# Batch import
results = bridge.import_scans_batch(scans)
# Returns: {'total': 10, 'success': 10, 'failed': 0, 'document_ids': [...]}
```

### Check Supabase

```python
# What's already imported?
imported_patients = bridge.get_imported_patients()
# Returns: ['LIDC-IDRI-0001', 'LIDC-IDRI-0002', ...]

# Is specific scan imported?
is_imported = bridge.is_scan_imported("LIDC-IDRI-0001")
# Returns: True/False

# Statistics
stats = bridge.get_supabase_nodule_stats()
# Returns: {'total_nodules': 150, 'documents_with_nodules': 45}
```

## Data Flow

```
PyLIDC Database (SQLite)
    ↓
  query_scans() / query_nodules_by_malignancy()
    ↓
PyLIDC Scan/Annotation Objects
    ↓
  PyLIDCAdapter.scan_to_canonical()
    ↓
RadiologyCanonicalDocument (schema-agnostic)
    ↓
  import_scan()
    ↓
Supabase PostgreSQL (documents + document_content tables)
```

## LIDC-IDRI Characteristic Scales

**Malignancy** (1-5):
- 1: Highly unlikely for cancer
- 2: Moderately unlikely
- 3: Indeterminate
- 4: Moderately suspicious
- 5: Highly suspicious

**Spiculation** (1-5):
- 1: Marked (high spiculation)
- 5: None (smooth)

**Calcification** (1-6):
- 1: Popcorn
- 2: Laminated
- 3: Solid
- 4: Non-central
- 5: Central
- 6: Absent

**Sphericity** (1-5):
- 1: Linear
- 3: Ovoid
- 5: Round

**Margin** (1-5):
- 1: Poorly defined
- 5: Sharp

## Example Workflows

### Workflow 1: Import all high-quality scans

```python
bridge = PyLIDCSupabaseBridge()

# Query high-quality scans not yet imported
scans = bridge.query_scans(max_slice_thickness=1.0, limit=100)

for scan in scans:
    if not bridge.is_scan_imported(scan.patient_id):
        bridge.import_scan(scan)
        print(f"✓ {scan.patient_id}")
```

### Workflow 2: Research malignant nodules

```python
# Find highly malignant nodules
nodules = bridge.query_nodules_by_malignancy(min_malignancy=4, limit=50)

# Get unique scans
scans = list({n['scan'] for n in nodules})

# Import to Supabase for further analysis
bridge.import_scans_batch(scans)

# Now query in Supabase
result = bridge.supabase.rpc('search_nodules_by_malignancy', {
    'min_malignancy': 4
}).execute()
```

### Workflow 3: Build training dataset

```python
# Criteria: High quality + spiculated + malignant
scans = bridge.query_scans(max_slice_thickness=1.0, limit=500)

malignant_spiculated = []
for scan in scans:
    for ann in scan.annotations:
        if ann.malignancy >= 4 and ann.spiculation <= 2:
            malignant_spiculated.append(scan)
            break

# Import to Supabase
bridge.import_scans_batch(malignant_spiculated)
```

## Troubleshooting

**Error: pylidc not installed**
```bash
pip install pylidc
pylidc conf  # Configure dataset path
```

**Error: SUPABASE_URL not set**
```bash
export SUPABASE_URL="https://xxx.supabase.co"
export SUPABASE_KEY="your-key"
# Or add to .env file
```

**Error: Could not find table 'documents'**
- Run migrations first:
  - `migrations/001_initial_schema.sql`
  - `migrations/002_radiology_supabase.sql`

**No scans found**
- Verify pylidc configuration: `pylidc conf`
- Check dataset is downloaded and path is correct
- Test pylidc: `python -c "import pylidc as pl; print(pl.query(pl.Scan).count())"`

## API Reference

See `src/ra_d_ps/pylidc_supabase_bridge.py` for full API documentation.

**Main Methods:**
- `query_scans()` - Query by filters
- `query_nodules_by_malignancy()` - Find malignant nodules
- `search_by_characteristics()` - Search by features
- `import_scan()` - Import single scan
- `import_scans_batch()` - Import multiple
- `get_imported_patients()` - List imported
- `is_scan_imported()` - Check if exists
- `get_supabase_nodule_stats()` - Statistics
