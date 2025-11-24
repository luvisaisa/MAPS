# MAPS Quick Reference - New Features

Quick guide to using the newly integrated features in MAPS.

---

##  Real-time Job Progress

### Using WebSocket in React

```typescript
import { useJobProgress } from '@/hooks/useJobProgress';

function UploadWithProgress() {
  const [jobId, setJobId] = useState<string>();
  
  const { progress, isConnected } = useJobProgress({
    jobId: jobId!,
    enabled: !!jobId,
    useWebSocket: true, // or false for SSE
    onComplete: (job) => {
      console.log('Processing complete!', job);
    },
  });

  return (
    <div>
      {isConnected && <Badge>🟢 Live</Badge>}
      {progress && (
        <>
          <Progress value={progress.percentage} />
          <p>{progress.current} / {progress.total} files</p>
          <p>Status: {progress.status}</p>
        </>
      )}
    </div>
  );
}
```

### Using Server-Sent Events (Alternative)

```typescript
const { progress, isConnected } = useJobProgress({
  jobId,
  useWebSocket: false, // Use SSE instead
  enabled: true,
});
```

---

##  Supabase Realtime

### Listen to Document Changes

```typescript
import { useDocumentsRealtime } from '@/hooks/useSupabaseRealtime';

function DocumentList() {
  const [documents, setDocuments] = useState([]);
  const { data, isConnected } = useDocumentsRealtime();

  useEffect(() => {
    if (data?.eventType === 'INSERT') {
      setDocuments(prev => [...prev, data.new]);
    } else if (data?.eventType === 'UPDATE') {
      setDocuments(prev => 
        prev.map(doc => doc.id === data.new.id ? data.new : doc)
      );
    } else if (data?.eventType === 'DELETE') {
      setDocuments(prev => 
        prev.filter(doc => doc.id !== data.old.id)
      );
    }
  }, [data]);

  return (
    <div>
      {isConnected && <span>🟢 Synced</span>}
      {documents.map(doc => <DocumentCard key={doc.id} {...doc} />)}
    </div>
  );
}
```

### Listen to Jobs

```typescript
import { useJobsRealtime } from '@/hooks/useSupabaseRealtime';

const { data: jobUpdate, isConnected } = useJobsRealtime();
```

### Custom Table Subscription

```typescript
import { useSupabaseRealtime } from '@/hooks/useSupabaseRealtime';

const { data, isConnected } = useSupabaseRealtime({
  table: 'keywords',
  event: 'INSERT', // or 'UPDATE', 'DELETE', '*'
  filter: 'category=eq.anatomy', // optional SQL filter
});
```

---

##  Keywords API

### Search Keywords

```typescript
import { apiClient } from '@/services/api';

// Search by term
const results = await apiClient.searchKeywords('nodule', 100);

// Get keyword directory
const directory = await apiClient.getKeywordDirectory();
console.log(directory.total_keywords);
console.log(directory.categories);

// Get keywords by category
const keywords = await apiClient.getKeywords({
  category: 'anatomy',
  limit: 50,
  offset: 0,
});

// Normalize keyword
const normalized = await apiClient.normalizeKeyword('nOdUlE');
```

---

##  Analytics API

### Comprehensive Analytics

```typescript
import { apiClient } from '@/services/api';

// Dashboard summary
const summary = await apiClient.getAnalyticsSummary();

// Parse case distribution
const parseCases = await apiClient.getParseCaseDistribution();
// Returns: [{ parse_case: "CASE_A", count: 50, percentage: 25.5 }, ...]

// Keyword statistics
const keywordStats = await apiClient.getKeywordStats();
console.log(keywordStats.total_keywords);
console.log(keywordStats.top_keywords);

// Inter-rater reliability
const interRater = await apiClient.getInterRaterReliability();
console.log(`Fleiss' Kappa: ${interRater.fleiss_kappa}`);
console.log(`Agreement: ${interRater.agreement_percentage}%`);

// Data completeness
const completeness = await apiClient.getDataCompleteness();
console.log(`Complete: ${completeness.completeness_percentage}%`);
```

---

##  Advanced Search

### Full-text Search

```typescript
import { apiClient } from '@/services/api';

const results = await apiClient.advancedSearch('lung nodule', {
  date_from: '2024-01-01',
  date_to: '2024-12-31',
  keywords: ['nodule', 'lesion'],
  has_keywords: true,
});

console.log(`Found ${results.total} results in ${results.took_ms}ms`);
results.results.forEach(result => {
  console.log(result.title);
  console.log(result.snippet);
  console.log(result.highlights);
});

// Search by keywords only
const keywordResults = await apiClient.searchByKeywords(['nodule', 'opacity']);
```

---

##  Parse Cases

### Manage Parse Cases

```typescript
import { apiClient } from '@/services/api';

// List all parse cases
const parseCases = await apiClient.getParseCases();

// Get specific parse case
const parseCase = await apiClient.getParseCase('CASE_A_STANDARD');

// Create new parse case
await apiClient.createParseCase({
  name: 'CUSTOM_CASE',
  description: 'Custom parsing pattern',
  pattern: 'xml_root_pattern',
  priority: 10,
});
```

---

##  PYLIDC Integration

### Import PYLIDC Data

```typescript
import { apiClient } from '@/services/api';

// List PYLIDC scans
const scans = await apiClient.getPYLIDCScans({
  page: 1,
  page_size: 20,
});

// Get scan details
const scan = await apiClient.getPYLIDCScan('LIDC-IDRI-0001');

// Import scan to Supabase
await apiClient.importPYLIDCScan('LIDC-IDRI-0001');

// Get annotations
const annotations = await apiClient.getPYLIDCAnnotations('LIDC-IDRI-0001');
```

---

##  3D Visualization

### Get Nodule Data

```typescript
import { apiClient } from '@/services/api';

// Get nodule 3D data
const noduleData = await apiClient.get3DNoduleData('nodule-123');
console.log(noduleData.coordinates);
console.log(noduleData.contours);
console.log(noduleData.volume);

// Get visualization metadata
const metadata = await apiClient.get3DVisualizationMetadata('scan-456');

// Generate volume rendering
await apiClient.generateVolumeRendering('scan-456', {
  colormap: 'hot',
  opacity: 0.8,
});
```

---

##  Supabase Views

### Access Materialized Views

```typescript
import { apiClient } from '@/services/api';

// Keyword consolidated view
const keywordView = await apiClient.getKeywordConsolidatedView({
  page: 1,
  page_size: 50,
});

keywordView.items.forEach(item => {
  console.log(`Document ${item.document_id}: ${item.keyword_count} keywords`);
  console.log(item.keywords);
  console.log(item.categories);
});

// Annotation view
const annotationView = await apiClient.getAnnotationView({
  page: 1,
  page_size: 100,
});

// View metadata
const metadata = await apiClient.getViewMetadata('keywords_consolidated');
```

---

##  Database Operations

### Health and Stats

```typescript
import { apiClient } from '@/services/api';

// Database health check
const health = await apiClient.getDatabaseHealth();
console.log(health.status); // 'healthy', 'degraded', 'down'
console.log(health.connection_pool);
console.log(health.response_time_ms);

// Database statistics
const stats = await apiClient.getDatabaseStats();
stats.forEach(table => {
  console.log(`${table.table_name}: ${table.row_count} rows, ${table.size_bytes} bytes`);
});

// Vacuum database (optimize)
await apiClient.vacuumDatabase();

// Reset database (DANGER!)
await apiClient.resetDatabase(true); // requires confirmation
```

---

##  Export

### Export Data

```typescript
import { apiClient } from '@/services/api';

// Export all data
const exportResult = await apiClient.exportData({
  format: 'excel', // or 'json', 'csv', 'sqlite'
  template: 'standard',
});

// Download export
const blob = await apiClient.downloadFile(exportResult.file_name);
const url = URL.createObjectURL(blob);
window.open(url);

// Export specific job
const jobExport = await apiClient.exportJob('job-123', {
  format: 'json',
});
```

---

##  Complete Example: Upload with Real-time Progress

```typescript
import { useState } from 'react';
import { apiClient } from '@/services/api';
import { useJobProgress } from '@/hooks/useJobProgress';
import { useDocumentsRealtime } from '@/hooks/useSupabaseRealtime';

function CompleteUploadExample() {
  const [jobId, setJobId] = useState<string>();
  const [files, setFiles] = useState<File[]>([]);

  // Real-time job progress
  const { progress, isConnected: jobConnected } = useJobProgress({
    jobId: jobId!,
    enabled: !!jobId,
    useWebSocket: true,
    onComplete: (job) => {
      alert(`Processing complete! ${job.processed_count} files processed.`);
    },
  });

  // Real-time document updates
  const { data: docUpdate, isConnected: dbConnected } = useDocumentsRealtime();

  useEffect(() => {
    if (docUpdate?.eventType === 'INSERT') {
      console.log('New document created:', docUpdate.new);
    }
  }, [docUpdate]);

  const handleUpload = async () => {
    try {
      const result = await apiClient.uploadFiles(files, 'lidc_idri_standard');
      setJobId(result.job_id);
    } catch (error) {
      console.error('Upload failed:', error);
    }
  };

  return (
    <div>
      <input 
        type="file" 
        multiple 
        onChange={(e) => setFiles(Array.from(e.target.files || []))}
      />
      <button onClick={handleUpload}>Upload</button>

      <div>
        Job Updates: {jobConnected ? '🟢' : ''}
        Database: {dbConnected ? '🟢' : ''}
      </div>

      {progress && (
        <div>
          <progress value={progress.percentage} max={100} />
          <p>{progress.current} / {progress.total}</p>
          <p>Status: {progress.status}</p>
        </div>
      )}
    </div>
  );
}
```

---

##  API Client Reference

All API methods are available through `apiClient`:

```typescript
import { apiClient } from '@/services/api';

// Health
await apiClient.healthCheck();

// Profiles
await apiClient.getProfiles();
await apiClient.createProfile(profile);

// Jobs
await apiClient.getJobs({ page: 1, page_size: 20 });
await apiClient.cancelJob(jobId);

// Documents
await apiClient.getDocuments({ page: 1, page_size: 50 });
await apiClient.getDocument(docId);

// Keywords
await apiClient.searchKeywords(query);
await apiClient.getKeywordDirectory();

// Analytics
await apiClient.getAnalyticsSummary();
await apiClient.getParseCaseDistribution();
await apiClient.getInterRaterReliability();

// Search
await apiClient.advancedSearch(query, filters);

// Export
await apiClient.exportData(options);
await apiClient.downloadFile(filename);

// And 40+ more methods...
```

---

##  Additional Resources

- **API Documentation**: http://localhost:8000/docs
- **Complete Integration Guide**: `/COMPLETE_INTEGRATION.md`
- **Web Interface Guide**: `/docs/WEB_INTERFACE_GUIDE.md`
- **Supabase Setup**: `/docs/QUICKSTART_SUPABASE.md`

---

**Happy coding with MAPS! **
