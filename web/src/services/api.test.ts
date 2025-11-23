import { describe, it, expect, vi, beforeEach } from 'vitest';
import axios from 'axios';
import { APIClient } from './api';

vi.mock('axios');
const mockedAxios = vi.mocked(axios, true);

describe('APIClient', () => {
  let client: APIClient;

  beforeEach(() => {
    client = new APIClient('http://localhost:8000');
    vi.clearAllMocks();
  });

  describe('uploadFiles', () => {
    it('uploads files with profile name', async () => {
      const mockResponse = { data: { job_id: '123', status: 'processing' } };
      mockedAxios.post.mockResolvedValue(mockResponse);

      const files = [new File(['content'], 'test.xml', { type: 'text/xml' })];
      const result = await client.uploadFiles(files, 'default');

      expect(mockedAxios.post).toHaveBeenCalledWith(
        expect.stringContaining('/upload'),
        expect.any(FormData),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Content-Type': 'multipart/form-data',
          }),
        })
      );
      expect(result).toEqual(mockResponse.data);
    });

    it('calls progress callback during upload', async () => {
      const mockProgressCallback = vi.fn();
      mockedAxios.post.mockImplementation((url, data, config) => {
        config?.onUploadProgress?.({ loaded: 50, total: 100 } as any);
        return Promise.resolve({ data: { job_id: '123' } });
      });

      const files = [new File(['content'], 'test.xml', { type: 'text/xml' })];
      await client.uploadFiles(files, 'default', mockProgressCallback);

      expect(mockProgressCallback).toHaveBeenCalledWith(50);
    });

    it('handles upload errors', async () => {
      mockedAxios.post.mockRejectedValue(new Error('Network error'));

      const files = [new File(['content'], 'test.xml', { type: 'text/xml' })];
      
      await expect(client.uploadFiles(files, 'default')).rejects.toThrow('Network error');
    });
  });

  describe('getJobs', () => {
    it('fetches jobs with pagination', async () => {
      const mockResponse = {
        data: {
          items: [{ id: '1', status: 'completed' }],
          total: 1,
          page: 1,
          page_size: 10,
        },
      };
      mockedAxios.get.mockResolvedValue(mockResponse);

      const result = await client.getJobs({ page: 1, page_size: 10 });

      expect(mockedAxios.get).toHaveBeenCalledWith(
        expect.stringContaining('/jobs'),
        expect.objectContaining({
          params: { page: 1, page_size: 10 },
        })
      );
      expect(result).toEqual(mockResponse.data);
    });

    it('applies filters when provided', async () => {
      mockedAxios.get.mockResolvedValue({ data: { items: [], total: 0 } });

      await client.getJobs({ 
        page: 1, 
        page_size: 10,
        status: 'completed',
        profile_name: 'default',
      });

      expect(mockedAxios.get).toHaveBeenCalledWith(
        expect.anything(),
        expect.objectContaining({
          params: expect.objectContaining({
            status: 'completed',
            profile_name: 'default',
          }),
        })
      );
    });
  });

  describe('getJob', () => {
    it('fetches single job by id', async () => {
      const mockJob = { id: '123', status: 'completed' };
      mockedAxios.get.mockResolvedValue({ data: mockJob });

      const result = await client.getJob('123');

      expect(mockedAxios.get).toHaveBeenCalledWith(expect.stringContaining('/jobs/123'));
      expect(result).toEqual(mockJob);
    });
  });

  describe('getProfiles', () => {
    it('fetches all profiles', async () => {
      const mockProfiles = [
        { profile_name: 'default', description: 'Default profile' },
        { profile_name: 'custom', description: 'Custom profile' },
      ];
      mockedAxios.get.mockResolvedValue({ data: mockProfiles });

      const result = await client.getProfiles();

      expect(mockedAxios.get).toHaveBeenCalledWith(expect.stringContaining('/profiles'));
      expect(result).toEqual(mockProfiles);
    });
  });

  describe('getProfile', () => {
    it('fetches single profile by name', async () => {
      const mockProfile = { profile_name: 'default', description: 'Default profile' };
      mockedAxios.get.mockResolvedValue({ data: mockProfile });

      const result = await client.getProfile('default');

      expect(mockedAxios.get).toHaveBeenCalledWith(
        expect.stringContaining('/profiles/default')
      );
      expect(result).toEqual(mockProfile);
    });
  });

  describe('deleteProfile', () => {
    it('deletes profile by name', async () => {
      mockedAxios.delete.mockResolvedValue({ data: { success: true } });

      await client.deleteProfile('custom');

      expect(mockedAxios.delete).toHaveBeenCalledWith(
        expect.stringContaining('/profiles/custom')
      );
    });
  });

  describe('getDashboardStats', () => {
    it('fetches dashboard statistics', async () => {
      const mockStats = {
        total_documents: 100,
        total_jobs: 50,
        success_rate: 95.5,
        error_rate: 4.5,
      };
      mockedAxios.get.mockResolvedValue({ data: mockStats });

      const result = await client.getDashboardStats();

      expect(mockedAxios.get).toHaveBeenCalledWith(expect.stringContaining('/stats/dashboard'));
      expect(result).toEqual(mockStats);
    });
  });

  describe('exportJob', () => {
    it('exports job with specified format', async () => {
      const mockBlob = new Blob(['data'], { type: 'application/vnd.ms-excel' });
      mockedAxios.get.mockResolvedValue({ 
        data: mockBlob,
        headers: { 'content-type': 'application/vnd.ms-excel' },
      });

      const result = await client.exportJob('123', 'excel');

      expect(mockedAxios.get).toHaveBeenCalledWith(
        expect.stringContaining('/jobs/123/export'),
        expect.objectContaining({
          params: { format: 'excel' },
          responseType: 'blob',
        })
      );
      expect(result).toBeInstanceOf(Blob);
    });

    it('supports sqlite export format', async () => {
      const mockBlob = new Blob(['data'], { type: 'application/x-sqlite3' });
      mockedAxios.get.mockResolvedValue({ data: mockBlob });

      await client.exportJob('123', 'sqlite');

      expect(mockedAxios.get).toHaveBeenCalledWith(
        expect.anything(),
        expect.objectContaining({
          params: { format: 'sqlite' },
        })
      );
    });
  });

  describe('error handling', () => {
    it('throws error with message from API response', async () => {
      mockedAxios.get.mockRejectedValue({
        response: {
          data: { detail: 'Profile not found' },
        },
      });

      await expect(client.getProfile('nonexistent')).rejects.toThrow();
    });

    it('handles network errors', async () => {
      mockedAxios.get.mockRejectedValue(new Error('Network Error'));

      await expect(client.getJobs({ page: 1, page_size: 10 })).rejects.toThrow('Network Error');
    });
  });

  describe('request interceptors', () => {
    it('adds base url to requests', async () => {
      mockedAxios.get.mockResolvedValue({ data: [] });

      await client.getProfiles();

      expect(mockedAxios.get).toHaveBeenCalledWith(
        expect.stringContaining('http://localhost:8000')
      );
    });
  });
});
