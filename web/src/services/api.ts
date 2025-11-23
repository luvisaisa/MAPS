import axios, { AxiosInstance, AxiosError } from 'axios';
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
  async uploadFiles(files: File[], profileName: string, onProgress?: (progress: number) => void): Promise<UploadResponse> {
    const formData = new FormData();
    files.forEach((file) => formData.append('files', file));
    formData.append('profile', profileName);

    const response = await this.client.post<UploadResponse>('/api/v1/parse/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total && onProgress) {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(percentCompleted);
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
}

export const apiClient = new APIClient();
export default apiClient;
