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
  study_instance_uid: string;
  series_instance_uid: string;
  slice_count: number;
  slice_thickness: number;
  slice_spacing: number | null;
  pixel_spacing: number[];
  contrast_used: boolean;
  annotation_count: number;
  has_nodules: boolean;
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

// Approval Queue Types
export interface QueueItem {
  id: string;
  filename: string;
  detected_parse_case: string;
  confidence: number;
  file_type: string;
  file_size: number;
  uploaded_at: string;
  status: 'pending' | 'approved' | 'rejected';
  reviewed_by?: string;
  reviewed_at?: string;
  notes?: string;
  detection_details?: Partial<DetectionDetails>;  // Embedded detection details
}

export interface QueueStats {
  total_pending: number;
  total_approved: number;
  total_rejected: number;
  avg_confidence: number;
  low_confidence_count: number;
  medium_confidence_count: number;
  oldest_pending?: string;
}

export interface ApprovalRequest {
  action: 'approve' | 'reject';
  parse_case?: string;
  notes?: string;
  reviewed_by?: string;
}

export interface BatchReviewResult {
  total: number;
  success: number;
  failed: number;
  results: Array<{
    item_id: string;
    status: 'success' | 'error';
    action?: string;
    error?: string;
  }>;
}

// Detection Details Types
export interface AttributeDefinition {
  name: string;
  xpath: string;
  data_type: string;
  required: boolean;
  description: string;
}

export interface DetectedAttribute {
  name: string;
  xpath: string;
  value: string | null;
  found: boolean;
}

export interface MissingAttribute {
  name: string;
  xpath: string;
  required: boolean;
  found: boolean;
}

export interface FieldAnalysis {
  field: string;
  expected: boolean;
  found: boolean;
  confidence: number;
  xpath: string;
  value_sample?: string | null;
  data_type?: string;
  description?: string;
  error?: string;
}

export interface ConfidenceBreakdown {
  base_confidence: number;
  match_percentage?: number;
  total_expected?: number;
  total_detected?: number;
  total_missing?: number;
  final_confidence: number;
  note?: string;
  error?: string;
}

export interface DetectionDetails {
  id: string;
  queue_item_id?: string;
  document_id?: string;
  parse_case: string;
  confidence: number;
  expected_attributes: AttributeDefinition[];
  detected_attributes: DetectedAttribute[];
  missing_attributes: MissingAttribute[];
  match_percentage: number;
  total_expected: number;
  total_detected: number;
  field_analysis: FieldAnalysis[];
  detector_type: string;
  detector_version?: string;
  detection_method?: string;
  confidence_breakdown: ConfidenceBreakdown;
  detected_at: string;
}

export interface ParseCaseSchema {
  parse_case: string;
  total_attributes: number;
  required_attributes: number;
  optional_attributes: number;
  attribute_names: string[];
  required_attribute_names: string[];
  attributes: AttributeDefinition[];
}

// Documents Types
export interface DocumentSummary {
  id: string;
  filename: string;
  document_title?: string;
  parse_case?: string;
  confidence?: number;
  file_type: string;
  file_size_bytes?: number;
  keywords_count: number;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  uploaded_at: string;
  parsed_at?: string;
  document_date?: string;
  uploaded_by?: string;
  content_preview?: string;
}

export interface DocumentDetail {
  id: string;
  filename: string;
  file_path: string;
  document_title?: string;
  file_type: string;
  file_size_bytes?: number;
  parse_case?: string;
  confidence?: number;
  keywords_count: number;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  error_message?: string;
  processing_duration_ms?: number;
  uploaded_at: string;
  parsed_at?: string;
  document_date?: string;
  uploaded_by?: string;
  canonical_data?: Record<string, unknown>;
  tags?: string[];
  detection_details?: DetectionDetails;
}

export interface DocumentsStats {
  total_documents: number;
  by_status: Record<string, number>;
  by_parse_case: Record<string, number>;
  by_file_type: Record<string, number>;
}

export interface DocumentSearchResult {
  document_id: string;
  filename: string;
  parse_case?: string;
  confidence?: number;
  status: string;
  relevance: number;
}
