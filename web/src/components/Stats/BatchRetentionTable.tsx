import type { ProcessingJob } from '../../types/api';

interface BatchRetentionTableProps {
  jobs: ProcessingJob[];
}

export function BatchRetentionTable({ jobs }: BatchRetentionTableProps) {
  const completedJobs = jobs.filter(j => j.status === 'completed' || j.status === 'failed');

  const getRetentionRate = (job: ProcessingJob) => {
    if (job.processed_count === 0) return '0%';
    const retained = job.processed_count - job.error_count;
    return `${((retained / job.file_count) * 100).toFixed(1)}%`;
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      completed: 'bg-green-100 text-green-800',
      failed: 'bg-red-100 text-red-800',
      processing: 'bg-blue-100 text-blue-800',
      pending: 'bg-yellow-100 text-yellow-800',
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Job ID
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Profile
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Files
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Processed
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Errors
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Retention Rate
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Created
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {completedJobs.length === 0 ? (
              <tr>
                <td colSpan={8} className="px-6 py-8 text-center text-gray-500">
                  No completed jobs found
                </td>
              </tr>
            ) : (
              completedJobs.map((job) => (
                <tr key={job.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {job.id.substring(0, 8)}...
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {job.profile_name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 font-medium">
                    {job.file_count}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {job.processed_count}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    {job.error_count > 0 ? (
                      <span className="text-red-600 font-medium">{job.error_count}</span>
                    ) : (
                      <span className="text-gray-500">0</span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <div className="flex items-center">
                      <span className="font-medium text-gray-900">{getRetentionRate(job)}</span>
                      <div className="ml-2 w-24 bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-green-500 h-2 rounded-full"
                          style={{
                            width: getRetentionRate(job),
                          }}
                        />
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(job.status)}`}>
                      {job.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(job.created_at).toLocaleDateString()}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Summary Row */}
      {completedJobs.length > 0 && (
        <div className="bg-gray-50 px-6 py-4 border-t border-gray-200">
          <div className="grid grid-cols-5 gap-4 text-sm">
            <div>
              <span className="text-gray-600">Total Batches:</span>
              <span className="ml-2 font-semibold text-gray-900">{completedJobs.length}</span>
            </div>
            <div>
              <span className="text-gray-600">Total Files:</span>
              <span className="ml-2 font-semibold text-gray-900">
                {completedJobs.reduce((sum, j) => sum + j.file_count, 0)}
              </span>
            </div>
            <div>
              <span className="text-gray-600">Total Processed:</span>
              <span className="ml-2 font-semibold text-gray-900">
                {completedJobs.reduce((sum, j) => sum + j.processed_count, 0)}
              </span>
            </div>
            <div>
              <span className="text-gray-600">Total Errors:</span>
              <span className="ml-2 font-semibold text-red-600">
                {completedJobs.reduce((sum, j) => sum + j.error_count, 0)}
              </span>
            </div>
            <div>
              <span className="text-gray-600">Overall Retention:</span>
              <span className="ml-2 font-semibold text-green-600">
                {(() => {
                  const total = completedJobs.reduce((sum, j) => sum + j.file_count, 0);
                  const errors = completedJobs.reduce((sum, j) => sum + j.error_count, 0);
                  return total > 0 ? `${(((total - errors) / total) * 100).toFixed(1)}%` : '0%';
                })()}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
