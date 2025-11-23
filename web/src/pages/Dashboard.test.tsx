import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderWithProviders, screen, waitFor } from '../test/test-utils';
import { Dashboard } from './Dashboard';
import { apiClient } from '../services/api';

vi.mock('../../services/api');

describe('Dashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading state initially', () => {
    vi.mocked(apiClient.getDashboardStats).mockImplementation(
      () => new Promise(() => {}) // never resolves
    );
    vi.mocked(apiClient.getProfiles).mockImplementation(
      () => new Promise(() => {})
    );

    renderWithProviders(<Dashboard />);
    
    expect(screen.getByText(/loading dashboard/i)).toBeInTheDocument();
  });

  it('displays dashboard stats when loaded', async () => {
    const mockStats = {
      total_documents: 150,
      total_jobs: 25,
      success_rate: 92.5,
      error_rate: 7.5,
      parse_case_distribution: {
        'LIDC_v2': 80,
        'Complete_Attributes': 70,
      },
      processing_trends: [
        { date: '2025-11-20', count: 10, success: 9, failed: 1 },
        { date: '2025-11-21', count: 15, success: 14, failed: 1 },
      ],
      storage_usage: {
        total_size: 500000000,
        document_count: 150,
        average_size: 3333333,
      },
    };

    vi.mocked(apiClient.getDashboardStats).mockResolvedValue(mockStats);
    vi.mocked(apiClient.getProfiles).mockResolvedValue([
      { profile_name: 'profile1', file_type: 'xml', description: '', mappings: [], validation_rules: { required_fields: [] } },
      { profile_name: 'profile2', file_type: 'json', description: '', mappings: [], validation_rules: { required_fields: [] } },
    ]);

    renderWithProviders(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText('150')).toBeInTheDocument(); // total documents
      expect(screen.getByText('25')).toBeInTheDocument(); // total jobs
    });

    expect(screen.getByText(/92.5%/i)).toBeInTheDocument(); // success rate
  });

  it('displays parse case distribution chart', async () => {
    const mockStats = {
      total_documents: 100,
      total_jobs: 20,
      success_rate: 95,
      error_rate: 5,
      parse_case_distribution: {
        'LIDC_v2': 60,
        'Complete_Attributes': 40,
      },
      processing_trends: [],
      storage_usage: { total_size: 0, document_count: 0, average_size: 0 },
    };

    vi.mocked(apiClient.getDashboardStats).mockResolvedValue(mockStats);
    vi.mocked(apiClient.getProfiles).mockResolvedValue([]);

    renderWithProviders(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText(/parse case distribution/i)).toBeInTheDocument();
    });
  });

  it('displays processing trends chart', async () => {
    const mockStats = {
      total_documents: 100,
      total_jobs: 20,
      success_rate: 95,
      error_rate: 5,
      parse_case_distribution: {},
      processing_trends: [
        { date: '2025-11-20', count: 10, success: 9, failed: 1 },
        { date: '2025-11-21', count: 15, success: 14, failed: 1 },
        { date: '2025-11-22', count: 12, success: 11, failed: 1 },
      ],
      storage_usage: { total_size: 0, document_count: 0, average_size: 0 },
    };

    vi.mocked(apiClient.getDashboardStats).mockResolvedValue(mockStats);
    vi.mocked(apiClient.getProfiles).mockResolvedValue([]);

    renderWithProviders(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText(/processing trends/i)).toBeInTheDocument();
    });
  });

  it('shows quick action buttons', async () => {
    vi.mocked(apiClient.getDashboardStats).mockResolvedValue({
      total_documents: 0,
      total_jobs: 0,
      success_rate: 0,
      error_rate: 0,
      parse_case_distribution: {},
      processing_trends: [],
      storage_usage: { total_size: 0, document_count: 0, average_size: 0 },
    });
    vi.mocked(apiClient.getProfiles).mockResolvedValue([]);

    renderWithProviders(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText(/upload files/i)).toBeInTheDocument();
      expect(screen.getByText(/view history/i)).toBeInTheDocument();
    });
  });

  it('handles API errors gracefully', async () => {
    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {});
    
    vi.mocked(apiClient.getDashboardStats).mockRejectedValue(
      new Error('API Error')
    );
    vi.mocked(apiClient.getProfiles).mockRejectedValue(
      new Error('API Error')
    );

    renderWithProviders(<Dashboard />);

    await waitFor(() => {
      // component should handle error without crashing
      expect(screen.queryByText(/loading dashboard/i)).not.toBeInTheDocument();
    });

    consoleError.mockRestore();
  });

  it('refreshes data every 30 seconds', async () => {
    vi.useFakeTimers();

    vi.mocked(apiClient.getDashboardStats).mockResolvedValue({
      total_documents: 100,
      total_jobs: 20,
      success_rate: 95,
      error_rate: 5,
      parse_case_distribution: {},
      processing_trends: [],
      storage_usage: { total_size: 0, document_count: 0, average_size: 0 },
    });
    vi.mocked(apiClient.getProfiles).mockResolvedValue([]);

    renderWithProviders(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText('100')).toBeInTheDocument();
    });

    expect(apiClient.getDashboardStats).toHaveBeenCalledTimes(1);

    // advance time by 30 seconds
    vi.advanceTimersByTime(30000);

    await waitFor(() => {
      expect(apiClient.getDashboardStats).toHaveBeenCalledTimes(2);
    });

    vi.useRealTimers();
  });
});
