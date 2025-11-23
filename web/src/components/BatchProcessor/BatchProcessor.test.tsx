import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { BatchProcessor } from './BatchProcessor';

describe('BatchProcessor', () => {
  const mockOnComplete = vi.fn();
  const mockOnProgress = vi.fn();
  const mockUploadFn = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders file list with pending status initially', () => {
    const files = [
      new File(['content'], 'test1.xml', { type: 'text/xml' }),
      new File(['content'], 'test2.xml', { type: 'text/xml' }),
    ];

    render(
      <BatchProcessor
        files={files}
        profileName="default"
        onComplete={mockOnComplete}
        uploadFn={mockUploadFn}
      />
    );

    expect(screen.getByText('test1.xml')).toBeInTheDocument();
    expect(screen.getByText('test2.xml')).toBeInTheDocument();
    expect(screen.getAllByText(/pending/i)).toHaveLength(2);
  });

  it('processes files sequentially', async () => {
    mockUploadFn.mockResolvedValue({ success: true, job_id: '123' });

    const files = [
      new File(['content'], 'test1.xml', { type: 'text/xml' }),
      new File(['content'], 'test2.xml', { type: 'text/xml' }),
    ];

    render(
      <BatchProcessor
        files={files}
        profileName="default"
        onComplete={mockOnComplete}
        uploadFn={mockUploadFn}
      />
    );

    await waitFor(() => {
      expect(mockUploadFn).toHaveBeenCalledTimes(2);
    });

    expect(mockOnComplete).toHaveBeenCalledWith({
      successful: 2,
      failed: 0,
      total: 2,
    });
  });

  it('handles upload failures gracefully', async () => {
    mockUploadFn
      .mockResolvedValueOnce({ success: true, job_id: '123' })
      .mockRejectedValueOnce(new Error('Upload failed'));

    const files = [
      new File(['content'], 'test1.xml', { type: 'text/xml' }),
      new File(['content'], 'test2.xml', { type: 'text/xml' }),
    ];

    render(
      <BatchProcessor
        files={files}
        profileName="default"
        onComplete={mockOnComplete}
        uploadFn={mockUploadFn}
      />
    );

    await waitFor(() => {
      expect(mockOnComplete).toHaveBeenCalled();
    });

    expect(mockOnComplete).toHaveBeenCalledWith({
      successful: 1,
      failed: 1,
      total: 2,
    });
  });

  it('reports progress for each file', async () => {
    mockUploadFn.mockImplementation((files, profile, progressCallback) => {
      progressCallback?.(50);
      return Promise.resolve({ success: true, job_id: '123' });
    });

    const files = [new File(['content'], 'test.xml', { type: 'text/xml' })];

    render(
      <BatchProcessor
        files={files}
        profileName="default"
        onComplete={mockOnComplete}
        uploadFn={mockUploadFn}
        onProgress={mockOnProgress}
      />
    );

    await waitFor(() => {
      expect(mockOnProgress).toHaveBeenCalled();
    });
  });

  it('displays success icon for completed uploads', async () => {
    mockUploadFn.mockResolvedValue({ success: true, job_id: '123' });

    const files = [new File(['content'], 'test.xml', { type: 'text/xml' })];

    render(
      <BatchProcessor
        files={files}
        profileName="default"
        onComplete={mockOnComplete}
        uploadFn={mockUploadFn}
      />
    );

    await waitFor(() => {
      expect(screen.getByText(/success/i)).toBeInTheDocument();
    });
  });

  it('displays error icon for failed uploads', async () => {
    mockUploadFn.mockRejectedValue(new Error('Upload failed'));

    const files = [new File(['content'], 'test.xml', { type: 'text/xml' })];

    render(
      <BatchProcessor
        files={files}
        profileName="default"
        onComplete={mockOnComplete}
        uploadFn={mockUploadFn}
      />
    );

    await waitFor(() => {
      expect(screen.getByText(/failed/i)).toBeInTheDocument();
    });
  });

  it('shows progress percentage during upload', async () => {
    mockUploadFn.mockImplementation((files, profile, progressCallback) => {
      progressCallback?.(75);
      return new Promise(resolve => setTimeout(() => resolve({ success: true, job_id: '123' }), 100));
    });

    const files = [new File(['content'], 'test.xml', { type: 'text/xml' })];

    render(
      <BatchProcessor
        files={files}
        profileName="default"
        onComplete={mockOnComplete}
        uploadFn={mockUploadFn}
      />
    );

    await waitFor(() => {
      expect(screen.getByText(/75%/)).toBeInTheDocument();
    });
  });

  it('handles empty file list', () => {
    render(
      <BatchProcessor
        files={[]}
        profileName="default"
        onComplete={mockOnComplete}
        uploadFn={mockUploadFn}
      />
    );

    expect(screen.getByText(/no files to process/i)).toBeInTheDocument();
  });

  it('passes profile name to upload function', async () => {
    mockUploadFn.mockResolvedValue({ success: true, job_id: '123' });

    const files = [new File(['content'], 'test.xml', { type: 'text/xml' })];
    const profileName = 'custom-profile';

    render(
      <BatchProcessor
        files={files}
        profileName={profileName}
        onComplete={mockOnComplete}
        uploadFn={mockUploadFn}
      />
    );

    await waitFor(() => {
      expect(mockUploadFn).toHaveBeenCalledWith(
        expect.anything(),
        profileName,
        expect.anything()
      );
    });
  });
});
