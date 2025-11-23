import { useState, useEffect } from 'react';
import { useMutation } from '@tanstack/react-query';
import { apiClient } from '../../services/api';

interface BatchProcessorProps {
  files: File[];
  profileName: string;
  onComplete: (jobIds: string[]) => void;
}

interface UploadProgress {
  fileName: string;
  progress: number;
  status: 'pending' | 'uploading' | 'completed' | 'failed';
  error?: string;
  jobId?: string;
}

export function BatchProcessor({ files, profileName, onComplete }: BatchProcessorProps) {
  const [uploadProgress, setUploadProgress] = useState<UploadProgress[]>([]);
  const [isPaused, setIsPaused] = useState(false);

  const uploadMutation = useMutation({
    mutationFn: async ({ file, profile }: { file: File; profile: string }) => {
      return apiClient.uploadFiles([file], profile, (progress) => {
        if (progress.total) {
          setUploadProgress(prev =>
            prev.map(p =>
              p.fileName === file.name
                ? { ...p, progress: Math.round((progress.loaded / (progress.total || 1)) * 100), status: 'uploading' }
                : p
            )
          );
        }
      });
    },
  });

  useEffect(() => {
    const initialProgress: UploadProgress[] = files.map(file => ({
      fileName: file.name,
      progress: 0,
      status: 'pending',
    }));
    setUploadProgress(initialProgress);

    processFiles();
  }, []);

  const processFiles = async () => {
    const jobs: string[] = [];

    for (const file of files) {
      if (isPaused) break;

      try {
        setUploadProgress(prev =>
          prev.map(p =>
            p.fileName === file.name ? { ...p, status: 'uploading' } : p
          )
        );

        const response = await uploadMutation.mutateAsync({
          file,
          profile: profileName,
        });

        const jobId = response.job_id;
        jobs.push(jobId);

        setUploadProgress(prev =>
          prev.map(p =>
            p.fileName === file.name
              ? { ...p, progress: 100, status: 'completed', jobId }
              : p
          )
        );
      } catch (error) {
        setUploadProgress(prev =>
          prev.map(p =>
            p.fileName === file.name
              ? { ...p, status: 'failed', error: (error as Error).message }
              : p
          )
        );
      }
    }

    onComplete(jobs);
  };

  const getStatusIcon = (status: UploadProgress['status']) => {
    switch (status) {
      case 'completed':
        return (
          <svg className="w-5 h-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
              clipRule="evenodd"
            />
          </svg>
        );
      case 'failed':
        return (
          <svg className="w-5 h-5 text-red-600" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
              clipRule="evenodd"
            />
          </svg>
        );
      case 'uploading':
        return (
          <svg className="w-5 h-5 text-blue-600 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
        );
      default:
        return (
          <svg className="w-5 h-5 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z"
              clipRule="evenodd"
            />
          </svg>
        );
    }
  };

  const completedCount = uploadProgress.filter(p => p.status === 'completed').length;
  const failedCount = uploadProgress.filter(p => p.status === 'failed').length;
  const overallProgress = Math.round((completedCount / files.length) * 100);

  return (
    <div className="space-y-4">
      {/* Overall Progress */}
      <div className="bg-gray-50 rounded-lg p-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-700">
            Overall Progress: {completedCount + failedCount} / {files.length}
          </span>
          <span className="text-sm text-gray-600">{overallProgress}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${overallProgress}%` }}
          />
        </div>
        {failedCount > 0 && (
          <p className="text-sm text-red-600 mt-2">{failedCount} file(s) failed</p>
        )}
      </div>

      {/* Individual File Progress */}
      <div className="space-y-2 max-h-96 overflow-y-auto">
        {uploadProgress.map((item) => (
          <div
            key={item.fileName}
            className="bg-white rounded-lg border border-gray-200 p-3"
          >
            <div className="flex items-center gap-3">
              {getStatusIcon(item.status)}
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">{item.fileName}</p>
                {item.status === 'uploading' && (
                  <div className="mt-1">
                    <div className="w-full bg-gray-200 rounded-full h-1.5">
                      <div
                        className="bg-blue-600 h-1.5 rounded-full transition-all duration-150"
                        style={{ width: `${item.progress}%` }}
                      />
                    </div>
                  </div>
                )}
                {item.error && (
                  <p className="text-xs text-red-600 mt-1">{item.error}</p>
                )}
                {item.jobId && (
                  <p className="text-xs text-gray-500 mt-1">Job ID: {item.jobId.substring(0, 8)}...</p>
                )}
              </div>
              <div className="text-xs text-gray-500 font-medium">
                {item.status === 'uploading' ? `${item.progress}%` : item.status}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Controls */}
      {overallProgress < 100 && (
        <div className="flex justify-end">
          <button
            onClick={() => setIsPaused(!isPaused)}
            className="px-4 py-2 text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            {isPaused ? 'Resume' : 'Pause'}
          </button>
        </div>
      )}
    </div>
  );
}
