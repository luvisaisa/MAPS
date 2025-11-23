import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import type { DashboardStats } from '../../types/api';

interface StorageBreakdownProps {
  stats?: DashboardStats;
}

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

export function StorageBreakdown({ stats }: StorageBreakdownProps) {
  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`;
  };

  // parse case distribution data for pie chart
  const parseCaseData = stats?.parse_case_distribution 
    ? Object.entries(stats.parse_case_distribution).map(([name, value]) => ({
        name: name.replace(/_/g, ' ').toUpperCase(),
        value,
      }))
    : [];

  const storageStats = stats?.storage_usage || {
    total_size: 0,
    document_count: 0,
    average_size: 0,
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Storage Statistics */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Storage Statistics</h3>
        <div className="space-y-4">
          <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
            <div>
              <p className="text-sm text-gray-600">Total Storage Used</p>
              <p className="text-2xl font-bold text-gray-900">{formatBytes(storageStats.total_size)}</p>
            </div>
            <div className="text-4xl">💽</div>
          </div>

          <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
            <div>
              <p className="text-sm text-gray-600">Total Documents</p>
              <p className="text-2xl font-bold text-gray-900">{storageStats.document_count}</p>
            </div>
            <div className="text-4xl">📄</div>
          </div>

          <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
            <div>
              <p className="text-sm text-gray-600">Average Document Size</p>
              <p className="text-2xl font-bold text-gray-900">{formatBytes(storageStats.average_size)}</p>
            </div>
            <div className="text-4xl">📊</div>
          </div>

          <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
            <div>
              <p className="text-sm text-gray-600">Storage Efficiency</p>
              <p className="text-2xl font-bold text-green-600">Optimized</p>
            </div>
            <div className="text-4xl">✓</div>
          </div>
        </div>
      </div>

      {/* Parse Case Distribution */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Data Distribution by Parse Case</h3>
        {parseCaseData.length > 0 ? (
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={parseCaseData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name}: ${((percent || 0) * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {parseCaseData.map((_entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        ) : (
          <div className="flex items-center justify-center h-64 text-gray-500">
            No parse case data available
          </div>
        )}

        {/* Legend Details */}
        {parseCaseData.length > 0 && (
          <div className="mt-6 space-y-2">
            {parseCaseData.map((entry, index) => (
              <div key={entry.name} className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div
                    className="w-4 h-4 rounded"
                    style={{ backgroundColor: COLORS[index % COLORS.length] }}
                  />
                  <span className="text-sm text-gray-700">{entry.name}</span>
                </div>
                <span className="text-sm font-medium text-gray-900">{entry.value} documents</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
