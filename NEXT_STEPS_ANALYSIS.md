# 🚀 Next Steps - Deploy Analysis System

## Current Status
✅ Database schema deployed (002_unified_case_identifier_schema.sql)  
✅ Python exporter created (analysis_exporter.py)  
✅ Documentation written (ANALYSIS_AND_EXPORT_GUIDE.md)  
⚠️ **Analysis views NOT YET deployed** (need to run 003_analysis_views.sql)  
⚠️ **No data imported yet** (need to run pylidc bridge)  

## What You Need to Do

### Step 1: Deploy Analysis Views (REQUIRED)
**Open Supabase SQL Editor**:
```
https://supabase.com/dashboard/project/lfzijlkdmnnrttsatrtc/sql/new
```

**Copy and paste entire file**:
```
migrations/003_analysis_views.sql
```

**Click "Run"**

This will create:
- ✅ `master_analysis_table` view
- ✅ `export_ready_table` materialized view
- ✅ `filter_analysis_table()` function
- ✅ `refresh_export_table()` function

**Verification**:
```python
python3 -c "
import sys
sys.path.insert(0, 'src')
from ra_d_ps.analysis_exporter import AnalysisExporter
exporter = AnalysisExporter()
data = exporter.get_master_table()
print(f'✅ Views deployed! Found {len(data)} rows')
"
```

---

### Step 2: Import LIDC Data
```bash
python3 scripts/pylidc_bridge_cli.py
```

**Choose from menu**:
- Option 1: Import high-quality scans (slice thickness ≤1.0mm)
- Option 3: Import malignant nodules (malignancy ≥4)
- Option 5: Import specific patient scan

**This will populate**:
- `file_imports` table (XML files)
- `qualitative_segments` table (radiologist annotations)
- `quantitative_segments` table (nodule measurements)

---

### Step 3: Verify Import
```python
python3 -c "
import sys
sys.path.insert(0, 'src')
from ra_d_ps.analysis_exporter import AnalysisExporter
exporter = AnalysisExporter()
exporter.print_summary()
"
```

**Expected output**:
```
📁 FILES: 5 (or more)
   xml: 5

📊 PROCESSING STATUS:
   complete: 5

📄 SEGMENTS: 10 (or more)
   qualitative: 5
   quantitative: 5
```

---

### Step 4: Refresh Export Table
```python
python3 -c "
import sys
sys.path.insert(0, 'src')
from ra_d_ps.analysis_exporter import AnalysisExporter
exporter = AnalysisExporter()
stats = exporter.refresh_export_table()
print(f'Refreshed {stats[\"total_rows\"]} rows in {stats[\"refresh_duration\"]}')
"
```

---

### Step 5: Export Data
```python
python3 -c "
import sys
sys.path.insert(0, 'src')
from ra_d_ps.analysis_exporter import AnalysisExporter

exporter = AnalysisExporter()

# Export all data
exporter.export_to_csv('./exports/all_data.csv')
exporter.export_to_json('./exports/all_data.json')

# Export by type
exporter.export_by_file_type('xml')

print('✅ Exports complete! Check ./exports directory')
"
```

---

### Step 6: Run Full Demo
```bash
python3 scripts/demo_analysis_system.py
```

**Expected output**: Full statistics, queries, and exports working

---

## Quick Commands

### Deploy Everything
```bash
# 1. Deploy SQL (manual - copy/paste in Supabase)
#    migrations/003_analysis_views.sql

# 2. Import data
python3 scripts/pylidc_bridge_cli.py

# 3. Export
python3 -c "
import sys
sys.path.insert(0, 'src')
from ra_d_ps.analysis_exporter import AnalysisExporter
exporter = AnalysisExporter()
exporter.refresh_export_table()
exporter.export_to_csv('./exports/lidc_data.csv')
exporter.print_summary()
"
```

---

## Troubleshooting

### "Could not find table master_analysis_table"
**Problem**: Views not deployed  
**Solution**: Run `migrations/003_analysis_views.sql` in Supabase SQL Editor

### "No data to export"
**Problem**: No data imported yet  
**Solution**: Run `python3 scripts/pylidc_bridge_cli.py`

### "0 files, 0 segments"
**Problem**: PyLIDC import failed or no scans found  
**Solution**: Check LIDC database configuration in `.env`

---

## File Reference

### SQL Migrations
- `migrations/002_unified_case_identifier_schema.sql` - ✅ Already deployed
- `migrations/003_analysis_views.sql` - ⚠️ **DEPLOY THIS NEXT**

### Python Utilities
- `src/ra_d_ps/analysis_exporter.py` - Export utility (ready)
- `src/ra_d_ps/pylidc_supabase_bridge.py` - LIDC bridge (ready)
- `scripts/pylidc_bridge_cli.py` - Interactive import CLI (ready)
- `scripts/demo_analysis_system.py` - Demo script (ready)

### Documentation
- `docs/ANALYSIS_AND_EXPORT_GUIDE.md` - Complete usage guide
- `ANALYSIS_EXPORT_SYSTEM_COMPLETE.md` - Implementation summary
- `docs/PYLIDC_SUPABASE_BRIDGE.md` - PyLIDC integration guide

---

## What You'll Be Able to Do

After completing all steps, you can:

✅ **View all data in single table** with filters  
✅ **Export to CSV** for Excel/R/Python analysis  
✅ **Export to JSON** for programmatic use  
✅ **Filter by**:
   - File type (XML, PDF, etc.)
   - Segment type (quantitative, qualitative, mixed)
   - Keyword count (≥5, ≥10, etc.)
   - Date range (last week, month, etc.)
   - Case patterns (with/without)
   - Keyword search ("malignancy", "spiculation", etc.)
✅ **Get statistics** (file counts, segment counts, keyword stats)  
✅ **Find high-value content** (cross-validated patterns, high-relevance keywords)  
✅ **Track radiologist annotations** (qualitative segments)  
✅ **Track measurements** (quantitative segments)  

---

## Summary

**Priority 1**: Deploy `migrations/003_analysis_views.sql` in Supabase  
**Priority 2**: Import LIDC data via `pylidc_bridge_cli.py`  
**Priority 3**: Export and analyze data  

**Total time**: ~15 minutes

🎯 **You're one SQL deployment away from a complete analysis system!**
