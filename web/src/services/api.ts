import axios, { type AxiosInstance, type AxiosError } from 'axios';
import type {
  APIResponse,
  Profile,
  ProcessingJob,
  UploadResponse,
  ExportResponse,
  ExportOptions,
  DashboardStats,
  PaginatedResponse,
  PaginationParams,
  JobFilters,
  CanonicalDocument,
  Keyword,
  KeywordSearchResult,
  KeywordDirectory,
  KeywordStats,
  ParseCaseDistribution,
  InterRaterReliability,
  DataCompleteness,
  Nodule3DData,
  VisualizationMetadata,
  PYLIDCScan,
  PYLIDCAnnotation,
  KeywordConsolidatedView,
  AnnotationView,
  SearchQuery,
  SearchResponse,
  SearchFilters,
  ParseCase,
  DatabaseStats,
  DatabaseHealth,
  WSMessage,
  JobProgressUpdate,
} from '../types/api';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class APIClient {
  private client: AxiosInstance;

  constructor(baseURL: string = API_BASE_URL) {
    this.client = axios.create({
      baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        console.error('API Error:', error.response?.data || error.message);
        return Promise.reject(error);
      }
    );
  }

  // Health Check
  async healthCheck() {
    const response = await this.client.get('/health');
    return response.data;
  }

  // Profile Management
  async getProfiles(): Promise<Profile[]> {
    const response = await this.client.get<Profile[]>('/api/v1/profiles');
    return response.data;
  }

  async getProfile(name: string): Promise<Profile> {
    const response = await this.client.get<Profile>(`/api/v1/profiles/${name}`);
    return response.data;
  }

  async createProfile(profile: Profile): Promise<APIResponse<Profile>> {
    const response = await this.client.post<APIResponse<Profile>>('/api/v1/profiles', profile);
    return response.data;
  }

  async updateProfile(name: string, profile: Profile): Promise<APIResponse<Profile>> {
    const response = await this.client.put<APIResponse<Profile>>(`/api/v1/profiles/${name}`, profile);
    return response.data;
  }

  async deleteProfile(name: string): Promise<APIResponse> {
    const response = await this.client.delete<APIResponse>(`/api/v1/profiles/${name}`);
    return response.data;
  }

  // File Upload & Processing
  async uploadFiles(
    files: File[], 
    profileName: string, 
    onProgress?: (progress: { loaded: number; total?: number }) => void
  ): Promise<UploadResponse> {
    const formData = new FormData();
    files.forEach((file) => formData.append('files', file));
    formData.append('profile', profileName);

    const response = await this.client.post<UploadResponse>('/api/v1/parse/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress) {
          onProgress({ loaded: progressEvent.loaded, total: progressEvent.total });
        }
      },
    });

    return response.data;
  }

  // Job Management
  async getJobs(params?: PaginationParams & JobFilters): Promise<PaginatedResponse<ProcessingJob>> {
    const response = await this.client.get<PaginatedResponse<ProcessingJob>>('/api/v1/batch/jobs', {
      params,
    });
    return response.data;
  }

  async getJob(jobId: string): Promise<ProcessingJob> {
    const response = await this.client.get<ProcessingJob>(`/api/v1/batch/jobs/${jobId}`);
    return response.data;
  }

  async deleteJob(jobId: string): Promise<APIResponse> {
    const response = await this.client.delete<APIResponse>(`/api/v1/batch/jobs/${jobId}`);
    return response.data;
  }

  async cancelJob(jobId: string): Promise<APIResponse> {
    const response = await this.client.post<APIResponse>(`/api/v1/batch/jobs/${jobId}/cancel`);
    return response.data;
  }

  // Documents
  async getDocuments(params?: PaginationParams): Promise<PaginatedResponse<CanonicalDocument>> {
    const response = await this.client.get<PaginatedResponse<CanonicalDocument>>('/api/v1/documents', {
      params,
    });
    return response.data;
  }

  async getDocument(documentId: string): Promise<CanonicalDocument> {
    const response = await this.client.get<CanonicalDocument>(`/api/v1/documents/${documentId}`);
    return response.data;
  }

  // Export & Download
  async exportData(options: ExportOptions): Promise<ExportResponse> {
    const response = await this.client.post<ExportResponse>('/api/v1/export', options);
    return response.data;
  }

  async exportJob(jobId: string, options: { format: ExportOptions['format'] }): Promise<ExportResponse> {
    const response = await this.client.get<ExportResponse>(`/api/v1/export/job/${jobId}`, {
      params: { format: options.format },
    });
    return response.data;
  }

  async downloadFile(fileName: string): Promise<Blob> {
    const response = await this.client.get(`/api/v1/export/download/${fileName}`, {
      responseType: 'blob',
    });
    return response.data;
  }

  // Statistics & Analytics
  async getDashboardStats(): Promise<DashboardStats> {
    const response = await this.client.get<DashboardStats>('/api/v1/analytics/dashboard');
    return response.data;
  }

  async getProcessingTrends(dateFrom?: string, dateTo?: string) {
    const response = await this.client.get('/api/v1/analytics/trends', {
      params: { date_from: dateFrom, date_to: dateTo },
    });
    return response.data;
  }

  async getAnalyticsSummary() {
    const response = await this.client.get('/api/v1/analytics/summary');
    return response.data;
  }

  async getParseCaseDistribution(): Promise<ParseCaseDistribution[]> {
    const response = await this.client.get<ParseCaseDistribution[]>('/api/v1/analytics/parse-cases');
    return response.data;
  }

  async getKeywordStats(): Promise<KeywordStats> {
    const response = await this.client.get<KeywordStats>('/api/v1/analytics/keywords');
    return response.data;
  }

  async getInterRaterReliability(): Promise<InterRaterReliability> {
    const response = await this.client.get<InterRaterReliability>('/api/v1/analytics/inter-rater');
    return response.data;
  }

  async getDataCompleteness(): Promise<DataCompleteness> {
    const response = await this.client.get<DataCompleteness>('/api/v1/analytics/completeness');
    return response.data;
  }

  // Keywords
  async getKeywords(params?: { limit?: number; offset?: number; category?: string }): Promise<Keyword[]> {
    const response = await this.client.get<Keyword[]>('/api/v1/keywords', { params });
    return response.data;
  }

  async getKeyword(keywordId: string): Promise<Keyword> {
    const response = await this.client.get<Keyword>(`/api/v1/keywords/${keywordId}`);
    return response.data;
  }

  async searchKeywords(query: string, limit: number = 100): Promise<KeywordSearchResult[]> {
    const response = await this.client.get<KeywordSearchResult[]>('/api/v1/keywords/search', {
      params: { query, limit },
    });
    return response.data;
  }

  async getKeywordDirectory(): Promise<KeywordDirectory> {
    const response = await this.client.get<KeywordDirectory>('/api/v1/keywords/directory');
    return response.data;
  }

  async normalizeKeyword(term: string) {
    const response = await this.client.post('/api/v1/keywords/normalize', { term });
    return response.data;
  }

  // 3D Visualization
  async get3DNoduleData(noduleId: string): Promise<Nodule3DData> {
    const response = await this.client.get<Nodule3DData>(`/api/v1/3d/nodule/${noduleId}`);
    return response.data;
  }

  async get3DVisualizationMetadata(scanId: string): Promise<VisualizationMetadata> {
    const response = await this.client.get<VisualizationMetadata>(`/api/v1/3d/scan/${scanId}/metadata`);
    return response.data;
  }

  async generateVolumeRendering(scanId: string, options?: Record<string, unknown>) {
    const response = await this.client.post(`/api/v1/3d/scan/${scanId}/render`, options);
    return response.data;
  }

  // PYLIDC Integration
  async getPYLIDCScans(params?: PaginationParams): Promise<PaginatedResponse<PYLIDCScan>> {
    const response = await this.client.get<PaginatedResponse<PYLIDCScan>>('/api/v1/pylidc/scans', { params });
    return response.data;
  }

  async getPYLIDCScan(scanId: string): Promise<PYLIDCScan> {
    const response = await this.client.get<PYLIDCScan>(`/api/v1/pylidc/scans/${scanId}`);
    return response.data;
  }

  async importPYLIDCScan(scanId: string) {
    const response = await this.client.post(`/api/v1/pylidc/import/${scanId}`);
    return response.data;
  }

  async getPYLIDCAnnotations(scanId: string): Promise<PYLIDCAnnotation[]> {
    const response = await this.client.get<PYLIDCAnnotation[]>(`/api/v1/pylidc/scans/${scanId}/annotations`);
    return response.data;
  }

  // Views (Supabase)
  async getKeywordConsolidatedView(params?: PaginationParams): Promise<PaginatedResponse<KeywordConsolidatedView>> {
    const response = await this.client.get<PaginatedResponse<KeywordConsolidatedView>>('/api/v1/views/keywords-consolidated', { params });
    return response.data;
  }

  async getAnnotationView(params?: PaginationParams): Promise<PaginatedResponse<AnnotationView>> {
    const response = await this.client.get<PaginatedResponse<AnnotationView>>('/api/v1/views/annotations', { params });
    return response.data;
  }

  async getViewMetadata(viewName: string) {
    const response = await this.client.get(`/api/v1/views/${viewName}/metadata`);
    return response.data;
  }

  // Search
  async search(searchQuery: SearchQuery): Promise<SearchResponse> {
    const response = await this.client.post<SearchResponse>('/api/v1/search', searchQuery);
    return response.data;
  }

  async advancedSearch(query: string, filters?: SearchFilters): Promise<SearchResponse> {
    const response = await this.client.post<SearchResponse>('/api/v1/search/advanced', { query, filters });
    return response.data;
  }

  async searchByKeywords(keywords: string[]): Promise<SearchResponse> {
    const response = await this.client.post<SearchResponse>('/api/v1/search/keywords', { keywords });
    return response.data;
  }

  // Parse Cases
  async getParseCases(): Promise<ParseCase[]> {
    const response = await this.client.get<ParseCase[]>('/api/v1/parse-cases');
    return response.data;
  }

  async getParseCase(name: string): Promise<ParseCase> {
    const response = await this.client.get<ParseCase>(`/api/v1/parse-cases/${name}`);
    return response.data;
  }

  async createParseCase(parseCase: ParseCase): Promise<APIResponse<ParseCase>> {
    const response = await this.client.post<APIResponse<ParseCase>>('/api/v1/parse-cases', parseCase);
    return response.data;
  }

  // Database Operations
  async getDatabaseStats(): Promise<DatabaseStats[]> {
    const response = await this.client.get<DatabaseStats[]>('/api/v1/db/stats');
    return response.data;
  }

  async getDatabaseHealth(): Promise<DatabaseHealth> {
    const response = await this.client.get<DatabaseHealth>('/api/v1/db/health');
    return response.data;
  }

  async vacuumDatabase() {
    const response = await this.client.post('/api/v1/db/vacuum');
    return response.data;
  }

  async resetDatabase(confirm: boolean = false) {
    if (!confirm) {
      throw new Error('Database reset requires explicit confirmation');
    }
    const response = await this.client.post('/api/v1/db/reset', { confirm });
    return response.data;
  }

  // WebSocket Connection (for real-time updates)
  connectWebSocket(jobId: string, onMessage: (message: WSMessage) => void): WebSocket {
    const wsUrl = this.client.defaults.baseURL?.replace('http', 'ws') || 'ws://localhost:8000';
    const ws = new WebSocket(`${wsUrl}/api/v1/batch/jobs/${jobId}/ws`);
    
    ws.onmessage = (event) => {
      const message = JSON.parse(event.data) as WSMessage;
      onMessage(message);
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
    
    return ws;
  }

  // Server-Sent Events (alternative to WebSocket)
  subscribeToJobProgress(jobId: string, onProgress: (update: JobProgressUpdate) => void): EventSource {
    const sseUrl = `${this.client.defaults.baseURL}/api/v1/batch/jobs/${jobId}/progress`;
    const eventSource = new EventSource(sseUrl);
    
    eventSource.onmessage = (event) => {
      const update = JSON.parse(event.data) as JobProgressUpdate;
      onProgress(update);
    };
    
    eventSource.onerror = (error) => {
      console.error('SSE error:', error);
      eventSource.close();
    };
    
    return eventSource;
  }
}

export const apiClient = new APIClient();
export default apiClient;
