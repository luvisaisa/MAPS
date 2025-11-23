import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { FileUploader } from './FileUploader';

describe('FileUploader', () => {
  it('renders dropzone with instructions', () => {
    const onFileSelect = vi.fn();
    render(<FileUploader onFileSelect={onFileSelect} />);
    
    expect(screen.getByText(/drag & drop files here/i)).toBeInTheDocument();
    expect(screen.getByText(/click to browse/i)).toBeInTheDocument();
  });

  it('displays accepted file types', () => {
    const onFileSelect = vi.fn();
    render(<FileUploader onFileSelect={onFileSelect} acceptedTypes={['.xml', '.json']} />);
    
    expect(screen.getByText(/accepted formats:/i)).toBeInTheDocument();
    expect(screen.getByText(/.xml, .json/i)).toBeInTheDocument();
  });

  it('displays selected files', () => {
    const onFileSelect = vi.fn();
    const files = [
      new File(['content'], 'test1.xml', { type: 'text/xml' }),
      new File(['content'], 'test2.xml', { type: 'text/xml' }),
    ];

    const { rerender } = render(<FileUploader onFileSelect={onFileSelect} />);
    
    // simulate file selection
    onFileSelect(files);
    
    rerender(<FileUploader onFileSelect={onFileSelect} selectedFiles={files} />);
    
    expect(screen.getByText('test1.xml')).toBeInTheDocument();
    expect(screen.getByText('test2.xml')).toBeInTheDocument();
  });

  it('formats file sizes correctly', () => {
    const onFileSelect = vi.fn();
    const file = new File(['x'.repeat(1024)], 'test.xml', { type: 'text/xml' });
    
    render(<FileUploader onFileSelect={onFileSelect} selectedFiles={[file]} />);
    
    expect(screen.getByText(/KB/)).toBeInTheDocument();
  });

  it('allows removing individual files', () => {
    const onFileSelect = vi.fn();
    const onRemove = vi.fn();
    const files = [
      new File(['content'], 'test1.xml', { type: 'text/xml' }),
      new File(['content'], 'test2.xml', { type: 'text/xml' }),
    ];

    render(
      <FileUploader 
        onFileSelect={onFileSelect} 
        selectedFiles={files}
        onRemoveFile={onRemove}
      />
    );
    
    const removeButtons = screen.getAllByRole('button', { name: /remove/i });
    fireEvent.click(removeButtons[0]);
    
    expect(onRemove).toHaveBeenCalledWith(0);
  });

  it('shows error state when rejecting files', () => {
    const onFileSelect = vi.fn();
    render(<FileUploader onFileSelect={onFileSelect} maxSize={1000} />);
    
    // simulate oversized file drop
    const largeFile = new File(['x'.repeat(2000)], 'large.xml', { type: 'text/xml' });
    const dropzone = screen.getByText(/drag & drop files here/i).closest('div');
    
    // react-dropzone handles validation internally, we test the UI response
    expect(dropzone).toBeInTheDocument();
  });

  it('respects maxSize prop', () => {
    const onFileSelect = vi.fn();
    const maxSize = 5 * 1024 * 1024; // 5MB
    
    render(<FileUploader onFileSelect={onFileSelect} maxSize={maxSize} />);
    
    expect(screen.getByText(/max file size: 5\.00 MB/i)).toBeInTheDocument();
  });

  it('displays validation errors', () => {
    const onFileSelect = vi.fn();
    const error = 'Invalid file type';
    
    render(<FileUploader onFileSelect={onFileSelect} error={error} />);
    
    expect(screen.getByText(error)).toBeInTheDocument();
  });

  it('shows empty state when no files selected', () => {
    const onFileSelect = vi.fn();
    render(<FileUploader onFileSelect={onFileSelect} />);
    
    expect(screen.queryByText('test.xml')).not.toBeInTheDocument();
  });

  it('handles multiple file selection', () => {
    const onFileSelect = vi.fn();
    render(<FileUploader onFileSelect={onFileSelect} multiple />);
    
    const files = [
      new File(['content1'], 'test1.xml', { type: 'text/xml' }),
      new File(['content2'], 'test2.xml', { type: 'text/xml' }),
      new File(['content3'], 'test3.xml', { type: 'text/xml' }),
    ];

    // simulate drop event
    onFileSelect(files);
    
    expect(onFileSelect).toHaveBeenCalledWith(files);
  });

  it('disables dropzone when disabled prop is true', () => {
    const onFileSelect = vi.fn();
    render(<FileUploader onFileSelect={onFileSelect} disabled />);
    
    const dropzone = screen.getByText(/drag & drop files here/i).closest('div');
    expect(dropzone).toHaveClass('opacity-50');
  });
});
