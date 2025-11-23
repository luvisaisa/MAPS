// API Response Types for RA-D-PS

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
