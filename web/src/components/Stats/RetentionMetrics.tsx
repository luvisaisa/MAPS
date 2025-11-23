import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import type { DashboardStats, ProcessingJob } from '../../types/api';

interface RetentionMetricsProps {
  stats?: DashboardStats;
  jobs: ProcessingJob[];
}

export function RetentionMetrics({ stats, jobs }: RetentionMetricsProps) {
  // calculate retention metrics from jobs
  const retentionData = calculateRetentionMetrics(jobs);
  
  // trend data from stats
  const trendData = stats?.processing_trends?.map(trend => ({
    date: new Date(trend.date).toLocaleDateString(),
    retained: trend.success,
    failed: trend.failed,
    total: trend.count,
  })) || [];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Retention Summary Cards */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Retention Summary</h3>
        <div className="space-y-4">
          <div className="flex items-center justify-between p-4 bg-blue-50 rounded-lg">
            <div>
              <p className="text-sm text-gray-600">Total Data Retained</p>
              <p className="text-2xl font-bold text-blue-700">{retentionData.totalRetained}</p>
            </div>
            <div className="text-4xl">💾</div>
          </div>
          
          <div className="flex items-center justify-between p-4 bg-green-50 rounded-lg">
            <div>
              <p className="text-sm text-gray-600">Retention Rate</p>
              <p className="text-2xl font-bold text-green-700">{retentionData.retentionRate}%</p>
            </div>
            <div className="text-4xl">📊</div>
          </div>
          
          <div className="flex items-center justify-between p-4 bg-purple-50 rounded-lg">
            <div>
              <p className="text-sm text-gray-600">Average Batch Size</p>
              <p className="text-2xl font-bold text-purple-700">{retentionData.avgBatchSize}</p>
            </div>
            <div className="text-4xl">📦</div>
          </div>
          
          <div className="flex items-center justify-between p-4 bg-amber-50 rounded-lg">
            <div>
              <p className="text-sm text-gray-600">Data Loss Rate</p>
              <p className="text-2xl font-bold text-amber-700">{retentionData.lossRate}%</p>
            </div>
            <div className="text-4xl">⚠️</div>
          </div>
        </div>
      </div>

      {/* Retention Trend Chart */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Retention Trend (Last 30 Days)</h3>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={trendData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" tick={{ fontSize: 12 }} />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line 
              type="monotone" 
              dataKey="retained" 
              stroke="#10b981" 
              strokeWidth={2}
              name="Successfully Retained"
            />
            <Line 
              type="monotone" 
              dataKey="failed" 
              stroke="#ef4444" 
              strokeWidth={2}
              name="Failed/Lost"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Processing Efficiency */}
      <div className="bg-white rounded-lg shadow p-6 lg:col-span-2">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Processing Efficiency by Day</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={trendData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" tick={{ fontSize: 12 }} />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="retained" fill="#3b82f6" name="Successful" />
            <Bar dataKey="failed" fill="#ef4444" name="Failed" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function calculateRetentionMetrics(jobs: ProcessingJob[]) {
  const completedJobs = jobs.filter(j => j.status === 'completed');
  const totalProcessed = completedJobs.reduce((sum, j) => sum + j.processed_count, 0);
  const totalErrors = completedJobs.reduce((sum, j) => sum + j.error_count, 0);
  const totalRetained = totalProcessed - totalErrors;
  
  return {
    totalRetained,
    retentionRate: totalProcessed > 0 ? ((totalRetained / totalProcessed) * 100).toFixed(1) : '0',
    avgBatchSize: completedJobs.length > 0 ? Math.round(totalProcessed / completedJobs.length) : 0,
    lossRate: totalProcessed > 0 ? ((totalErrors / totalProcessed) * 100).toFixed(1) : '0',
  };
}
