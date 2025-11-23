import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../services/api';
import { StatsOverview, RetentionMetrics, BatchRetentionTable, StorageBreakdown } from '../components/Stats';

export function Stats() {
  const [dateRange, setDateRange] = useState({
    from: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    to: new Date().toISOString().split('T')[0],
  });

  const { data: stats, isLoading, error } = useQuery({
    queryKey: ['stats', dateRange],
    queryFn: () => apiClient.getDashboardStats(),
  });

  const { data: jobsResponse } = useQuery({
    queryKey: ['jobs-retention', dateRange],
    queryFn: () => apiClient.getJobs({ page: 1, page_size: 100 }),
  });

  const jobs = jobsResponse?.items || [];

  if (isLoading) {
    return (
      <div className="p-8">
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-500">Loading statistics...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <h3 className="text-red-800 font-semibold mb-2">Error Loading Statistics</h3>
          <p className="text-red-600">{(error as Error).message}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Processing Statistics & Data Retention</h1>
        
        {/* Date Range Filter */}
        <div className="flex items-center gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">From</label>
            <input
              type="date"
              value={dateRange.from}
              onChange={(e) => setDateRange(prev => ({ ...prev, from: e.target.value }))}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">To</label>
            <input
              type="date"
              value={dateRange.to}
              onChange={(e) => setDateRange(prev => ({ ...prev, to: e.target.value }))}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        </div>
      </div>

      <div className="space-y-8">
        {/* Overall Statistics */}
        <section>
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Overall Statistics</h2>
          <StatsOverview stats={stats} />
        </section>

        {/* Retention Metrics */}
        <section>
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Data Retention Metrics</h2>
          <RetentionMetrics stats={stats} jobs={jobs} />
        </section>

        {/* Storage Breakdown */}
        <section>
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Storage Breakdown</h2>
          <StorageBreakdown stats={stats} />
        </section>

        {/* Per-Batch Retention */}
        <section>
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Retention by Batch/Import</h2>
          <BatchRetentionTable jobs={jobs} />
        </section>
      </div>
    </div>
  );
}
