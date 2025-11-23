// API Response Types for MAPS (Medical Annotation Processing System)

export interface APIResponse<T = unknown> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

// Profile Types
export interface ProfileMapping {
  source_path: string;
  target_path: string;
  data_type: string;
  required: boolean;
  default_value?: string;
  transform?: string;
}

export interface ValidationRules {
  required_fields: string[];
  field_constraints?: Record<string, unknown>;
}

export interface Profile {
  profile_name: string;
  file_type: string;
  description: string;
  mappings: ProfileMapping[];
  validation_rules: ValidationRules;
  transformations?: Record<string, unknown>;
}

// Document Types
export interface DocumentMetadata {
  title: string;
  date: string;
  source?: string;
  file_path?: string;
}

export interface CanonicalDocument {
  id?: string;
  metadata: DocumentMetadata;
  content: Record<string, unknown>;
  parse_case?: string;
  created_at?: string;
  updated_at?: string;
}

// Processing Types
export interface ProcessingJob {
  id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled';
  profile_name: string;
  file_count: number;
  processed_count: number;
  error_count: number;
  created_at: string;
  updated_at: string;
  completed_at?: string;
  error_message?: string;
}

export interface ProcessingProgress {
  job_id: string;
  current: number;
  total: number;
  percentage: number;
  current_file?: string;
  status: string;
}

// Upload Types
export interface UploadResponse {
  job_id: string;
  files_uploaded: number;
  message: string;
}

// Export Types
export type ExportFormat = 'excel' | 'json' | 'csv' | 'sqlite';

export interface ExportOptions {
  format: ExportFormat;
  job_id?: string;
  filters?: Record<string, unknown>;
  template?: 'standard' | 'template' | 'multi-folder';
}

export interface ExportResponse {
  download_url: string;
  file_name: string;
  file_size: number;
}

// Statistics Types
export interface DashboardStats {
  total_documents: number;
  total_jobs: number;
  success_rate: number;
  error_rate: number;
  parse_case_distribution: Record<string, number>;
  processing_trends: ProcessingTrend[];
  storage_usage: StorageUsage;
}

export interface ProcessingTrend {
  date: string;
  count: number;
  success: number;
  failed: number;
}

export interface StorageUsage {
  total_size: number;
  document_count: number;
  average_size: number;
}

// Pagination Types
export interface PaginationParams {
  page: number;
  page_size: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// Filter Types
export interface JobFilters {
  status?: ProcessingJob['status'][];
  profile_name?: string;
  date_from?: string;
  date_to?: string;
}

// Error Types
export interface APIError {
  error: string;
  detail?: string;
  path?: string;
  status_code?: number;
}

// Keyword Types
export interface Keyword {
  id: string;
  term: string;
  canonical_term: string;
  category?: string;
  frequency: number;
  confidence?: number;
  source?: string;
  created_at?: string;
}

export interface KeywordSearchResult {
  keyword: Keyword;
  score: number;
  matches: string[];
}

export interface KeywordDirectory {
  categories: Record<string, Keyword[]>;
  total_keywords: number;
  total_categories: number;
}

// Analytics Types
export interface ParseCaseDistribution {
  parse_case: string;
  count: number;
  percentage: number;
}

export interface KeywordStats {
  total_keywords: number;
  unique_terms: number;
  top_keywords: Array<{ term: string; count: number }>;
  categories: Record<string, number>;
}

export interface InterRaterReliability {
  fleiss_kappa?: number;
  cohens_kappa?: number;
  agreement_percentage: number;
  disagreement_details: Record<string, number>;
}

export interface DataCompleteness {
  total_records: number;
  complete_records: number;
  completeness_percentage: number;
  missing_fields: Record<string, number>;
}

// 3D Visualization Types
export interface Nodule3DData {
  nodule_id: string;
  coordinates: Array<{ x: number; y: number; z: number }>;
  contours: Array<Array<{ x: number; y: number }>>;
  slice_indices: number[];
  volume: number;
  diameter: number;
}

export interface VisualizationMetadata {
  scan_id: string;
  patient_id?: string;
  slice_thickness: number;
  pixel_spacing: number[];
  image_position: number[];
}

// PYLIDC Types
export interface PYLIDCScan {
  scan_id: string;
  patient_id: string;
  series_instance_uid: string;
  slice_count: number;
  slice_thickness: number;
  pixel_spacing: number[];
}

export interface PYLIDCAnnotation {
  annotation_id: string;
  nodule_id: string;
  radiologist_id: string;
  subtlety: number;
  internalStructure: number;
  calcification: number;
  sphericity: number;
  margin: number;
  lobulation: number;
  spiculation: number;
  texture: number;
  malignancy: number;
}

// View Types (Supabase)
export interface KeywordConsolidatedView {
  document_id: string;
  keywords: string[];
  categories: string[];
  keyword_count: number;
}

export interface AnnotationView {
  annotation_id: string;
  scan_id: string;
  radiologist_id: string;
  characteristics: Record<string, number>;
  created_at: string;
}

// Search Types
export interface SearchQuery {
  query: string;
  filters?: SearchFilters;
  limit?: number;
  offset?: number;
}

export interface SearchFilters {
  parse_case?: string[];
  date_from?: string;
  date_to?: string;
  keywords?: string[];
  has_keywords?: boolean;
}

export interface SearchResult {
  document_id: string;
  title: string;
  snippet: string;
  score: number;
  highlights: string[];
  metadata: Record<string, unknown>;
}

export interface SearchResponse {
  results: SearchResult[];
  total: number;
  query: string;
  took_ms: number;
}

// Parse Case Types
export interface ParseCase {
  name: string;
  description: string;
  pattern: string;
  priority: number;
  count?: number;
}

// Database Types
export interface DatabaseStats {
  table_name: string;
  row_count: number;
  size_bytes: number;
  last_updated?: string;
}

export interface DatabaseHealth {
  status: 'healthy' | 'degraded' | 'down';
  connection_pool: {
    active: number;
    idle: number;
    max: number;
  };
  response_time_ms: number;
}

// WebSocket Types
export interface WSMessage<T = unknown> {
  type: 'progress' | 'status' | 'error' | 'complete';
  job_id?: string;
  data: T;
  timestamp: string;
}

export interface JobProgressUpdate {
  job_id: string;
  current: number;
  total: number;
  percentage: number;
  current_file?: string;
  status: ProcessingJob['status'];
  message?: string;
}
