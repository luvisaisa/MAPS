import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../../services/api';
import type { ProcessingJob } from '../../types/api';

interface ProgressTrackerProps {
  jobIds: string[];
  autoRefresh?: boolean;
  refreshInterval?: number;
}

export function ProgressTracker({
  jobIds,
  autoRefresh = true,
  refreshInterval = 2000,
}: ProgressTrackerProps) {
  const { data: jobs = [], isLoading } = useQuery({
    queryKey: ['jobs', 'tracker', jobIds],
    queryFn: async () => {
      const jobPromises = jobIds.map(id => apiClient.getJob(id));
      return Promise.all(jobPromises);
    },
    enabled: jobIds.length > 0,
    refetchInterval: autoRefresh ? refreshInterval : false,
  });

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      completed: 'bg-green-100 text-green-800',
      processing: 'bg-blue-100 text-blue-800',
      failed: 'bg-red-100 text-red-800',
      pending: 'bg-yellow-100 text-yellow-800',
      cancelled: 'bg-gray-100 text-gray-800',
    };
    return styles[status] || 'bg-gray-100 text-gray-800';
  };

  const getStatusIcon = (status: string) => {
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
      case 'processing':
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

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="text-gray-500">Loading job status...</div>
      </div>
    );
  }

  if (jobs.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        No jobs to track
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {jobs.map((job: ProcessingJob) => (
        <div key={job.id} className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="flex items-start gap-4">
            {getStatusIcon(job.status)}
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between mb-2">
                <div>
                  <h4 className="text-sm font-medium text-gray-900">
                    Job {job.id.substring(0, 8)}...
                  </h4>
                  <p className="text-xs text-gray-500">Profile: {job.profile_name}</p>
                </div>
                <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusBadge(job.status)}`}>
                  {job.status}
                </span>
              </div>

              {/* Progress Bar for processing jobs */}
              {job.status === 'processing' && job.file_count > 0 && (
                <div className="mt-2">
                  <div className="flex items-center justify-between text-xs text-gray-600 mb-1">
                    <span>Progress</span>
                    <span>
                      {job.processed_count} / {job.file_count} files
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                      style={{
                        width: `${Math.round((job.processed_count / job.file_count) * 100)}%`,
                      }}
                    />
                  </div>
                </div>
              )}

              {/* Error message */}
              {job.error_message && (
                <div className="mt-2 p-2 bg-red-50 rounded text-xs text-red-700">
                  {job.error_message}
                </div>
              )}

              {/* Job metadata */}
              <div className="mt-2 flex items-center gap-4 text-xs text-gray-500">
                <span>Created: {new Date(job.created_at).toLocaleTimeString()}</span>
                {job.completed_at && (
                  <span>Completed: {new Date(job.completed_at).toLocaleTimeString()}</span>
                )}
                {job.error_count > 0 && (
                  <span className="text-red-600">{job.error_count} errors</span>
                )}
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
