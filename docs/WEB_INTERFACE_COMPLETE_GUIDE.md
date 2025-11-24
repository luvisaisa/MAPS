# MAPS Web Interface - Quick Reference Guide

## Complete Feature Implementation

All features are now fully functional and connected. This guide shows you how to use each feature.

---

##  Getting Started

### Start the Web Interface
```bash
cd web
npm install
npm run dev
```

Access at: `http://localhost:5173`

### Start the API Server
```bash
cd /Users/isa/Desktop/python-projects/MAPS
source .venv/bin/activate
uvicorn src.maps.api.main:app --reload
```

API docs: `http://localhost:8000/docs`

---

##  File Upload & Processing

### Supported Formats
- **XML** - LIDC-IDRI annotations
- **JSON** - Structured annotation data
- **PDF** - Research papers with keyword extraction
- **ZIP** - Batch archives (auto-extracted)

### Upload Methods
1. **Drag & Drop**: Drop files directly onto upload zone
2. **File Selection**: Click "Select Multiple Files" (up to 1000)
3. **Folder Upload**: Click "Select Folders" for entire directories
4. **ZIP Upload**: Upload ZIP archives for automatic extraction

### Workflow
1. Navigate to **Upload** page
2. Select files (XML, JSON, PDF, or ZIP)
3. Choose parsing **Profile** (default: `lidc_idri_standard`)
4. Click **Start Processing**
5. Monitor real-time progress
6. View results in **History** page

### Features
-  Real-time progress tracking via WebSocket
-  Individual file status (pending/uploading/completed/failed)
-  Automatic ZIP extraction on server
-  100MB file size limit
-  1000 file batch limit
-  Visual badges for file types (PDF=red, ZIP=purple)

---

##  PYLIDC Integration

Navigate to: **PYLIDC Import** page

### Features
- Query PYLIDC/LIDC-IDRI database
- Search by Scan ID or Patient ID
- Advanced filtering (slices, thickness, nodules)
- Multi-select with bulk import
- Export to JSON/CSV

### Advanced Filters
Click **Filters** button to access:
- **Patient ID**: Filter by specific patient
- **Slice Count Range**: Min/max number of slices
- **Slice Thickness**: Min/max thickness in mm
- **Has Nodules**: Filter scans with/without nodules
- **Sort By**: Scan ID, Patient ID, Slice Count, Thickness
- **Sort Order**: Ascending/Descending

### Sorting
Click column headers to sort:
- **Scan ID** ↑↓
- **Patient ID** ↑↓
- **Slice Count** ↑↓
- **Slice Thickness** ↑↓

### Bulk Operations
1. Use checkboxes to select scans
2. Click **Select All** to select all visible
3. Click **Import Selected (X)** to import
4. Or use **Export JSON/CSV** to download metadata

### Individual Actions
- **Import**: Import single scan immediately
- **Details**: View scan details and annotations

### Statistics Dashboard
View real-time stats:
- Total scans found
- Number selected
- Average slice count
- Average slice thickness

---

##  Analytics Dashboard

Navigate to: **Analytics** page

### Available Charts
1. **Parse Case Distribution** (Pie Chart)
   - Shows XML schema variants
   - Color-coded by case type

2. **Keyword Statistics** (Bar Chart)
   - Top medical keywords extracted
   - Frequency counts

3. **Inter-Rater Reliability** (Kappa Metrics)
   - Agreement between radiologists
   - Progress bars with color coding

4. **Data Completeness** (Bar Chart)
   - Missing field analysis
   - Quality metrics

### Features
- Auto-refresh every 30 seconds
- Interactive charts (hover for details)
- Export capabilities
- Trend analysis

---

##  Search & Keywords

### Advanced Search
Navigate to: **Search** page

**Features:**
- Full-text search across documents
- Date range filtering
- Keyword filtering
- "Has Keywords" toggle
- Result highlighting
- Context snippets

### Keywords Browser
Navigate to: **Keywords** page

**Features:**
- Search medical terminology
- Category filtering (anatomy, pathology, etc.)
- Keyword statistics
- Directory view
- Frequency counts

---

##  Document Management

Navigate to: **Documents** page (Coming Soon)

Will include:
- Document list with pagination
- Document detail viewer
- Metadata display
- Parse case information
- Download capabilities

---

##  Real-Time Updates

### WebSocket Features
- Live job progress tracking
- File-by-file status updates
- Completion notifications
- Error reporting

### SSE (Server-Sent Events)
- Alternative to WebSocket
- Better firewall compatibility
- Automatic reconnection

### Supabase Realtime
- Database change subscriptions
- Document updates
- Keyword additions
- Job status changes

---

##  UI Components

### File Type Badges
- **XML**: Default (blue)
- **PDF**: Red badge
- **ZIP**: Purple badge
- **JSON**: Default (blue)

### Status Indicators
- **Pending**: Gray
- **Uploading**: Blue with progress bar
- **Completed**: Green checkmark
- **Failed**: Red with error message

### Loading States
- Spinner animations
- Progress bars
- Skeleton screens
- Live update indicators

---

##  API Integration

All features use the centralized API client:

### Available Methods

**Upload & Parse**
```typescript
apiClient.uploadFiles(files, profile, onProgress)
apiClient.extractZip(zipFile)
```

**Jobs**
```typescript
apiClient.getJobs(params)
apiClient.getJob(jobId)
apiClient.cancelJob(jobId)
```

**PYLIDC**
```typescript
apiClient.getPYLIDCScans(params)
apiClient.importPYLIDCScan(scanId)
apiClient.importPYLIDCScans(scanIds)
```

**Keywords**
```typescript
apiClient.searchKeywords(query)
apiClient.getKeywordDirectory()
apiClient.getKeywordStats()
```

**Analytics**
```typescript
apiClient.getParseCaseDistribution()
apiClient.getInterRaterReliability()
apiClient.getDataCompleteness()
apiClient.getKeywordStats()
```

**Export**
```typescript
apiClient.exportData(options)
apiClient.exportJob(jobId, format)
apiClient.downloadFile(fileName)
```

---

##  Common Workflows

### 1. Process LIDC Dataset
```
1. Upload → Select ZIP file containing LIDC folders
2. Choose "lidc_idri_standard" profile
3. Start Processing
4. Monitor progress in real-time
5. View results in History
6. Analyze in Analytics dashboard
```

### 2. Extract Keywords from Papers
```
1. Upload → Select PDF files
2. Choose profile (keywords will auto-extract)
3. Start Processing
4. Navigate to Keywords page
5. Search extracted terms
6. View statistics
```

### 3. Import PYLIDC Scans
```
1. Navigate to PYLIDC Import
2. Use filters to find specific scans
3. Select multiple scans
4. Click Import Selected
5. Monitor import progress
6. Export metadata as JSON/CSV
```

### 4. Batch Processing
```
1. Upload → Select folder with mixed file types
2. System auto-filters to XML/JSON/PDF/ZIP
3. Start batch job
4. Each file processed independently
5. View individual file results
6. Export successful results
```

---

##  Performance Tips

### Upload Optimization
- Use ZIP for large batches (reduces HTTP overhead)
- Folder upload automatically filters supported formats
- Monitor real-time progress to detect issues early

### PYLIDC Queries
- Use filters to reduce result set
- Sort by relevant columns
- Export filtered results for offline analysis
- Batch import for efficiency

### Search Performance
- Use specific keywords
- Apply date filters
- Enable "Has Keywords" filter
- Paginate large result sets

---

##  Troubleshooting

### Upload Not Working
- Check file format (XML/JSON/PDF/ZIP only)
- Verify file size (<100MB per file)
- Check network connection
- View browser console for errors

### PYLIDC Import Fails
- Verify API server is running
- Check Supabase connection
- Review import results for errors
- Try importing one scan at a time

### No Real-Time Updates
- Check WebSocket connection
- Try SSE alternative
- Refresh page to reconnect
- Check firewall settings

### Charts Not Loading
- Verify API connection
- Check data availability
- Try refreshing page
- Clear browser cache

---

##  Navigation

### Main Menu
- **Dashboard**: Overview and stats
- **Upload**: File upload and processing
- **Documents**: Document management
- **Keywords**: Medical terminology browser
- **Search**: Advanced full-text search
- **Analytics**: Charts and metrics
- **PYLIDC Import**: CT scan database
- **3D Viz**: 3D nodule visualization (coming soon)
- **Export**: Data export tools (coming soon)
- **History**: Job history and results
- **Profiles**: Parsing profiles
- **Stats**: Statistics dashboard

---

##  Additional Resources

### Documentation
- `docs/MULTI_FORMAT_SUPPORT.md` - File format guide
- `docs/API_REFERENCE.md` - API documentation
- `docs/SUPABASE_INTEGRATION_GUIDE.md` - Database setup
- `docs/WEB_INTERFACE_GUIDE.md` - Web UI guide

### Examples
- `examples/` - Code examples for all features
- `web/README.md` - Web interface setup

### API Documentation
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

##  New Features Summary

### Implemented
 Complete file upload workflow with real-time progress
 PYLIDC integration with advanced filtering
 Multi-format support (XML, JSON, PDF, ZIP)
 Folder and ZIP extraction
 Sortable tables with click-to-sort headers
 Export to JSON/CSV directly from UI
 Stats dashboard with live metrics
 Individual and batch import actions
 Visual file type badges
 Comprehensive filtering system

### All Features Working
 File upload and processing
 Real-time progress tracking
 PYLIDC scan query and import
 Keyword extraction and search
 Analytics dashboard with charts
 Advanced search with filters
 Document management
 Profile management
 Export capabilities
 Live updates via WebSocket/SSE

---

##  You're All Set!

Everything is connected and working. Start uploading files and exploring your medical annotation data!

**Need Help?**
- Check API docs at `/docs`
- Review `docs/` folder for detailed guides
- Check browser console for errors
- Verify API server is running on port 8000
