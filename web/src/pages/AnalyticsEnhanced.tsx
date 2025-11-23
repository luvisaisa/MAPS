/**
 * MAPS - Enhanced Analytics Page
 * 
 * Comprehensive analytics dashboard with parse cases, keywords, inter-rater reliability
 */

import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../services/api';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899', '#14B8A6', '#F97316'];

export default function Analytics() {
  const { data: summary } = useQuery({
    queryKey: ['analytics-summary'],
    queryFn: () => apiClient.getAnalyticsSummary(),
  });

  const { data: parseCases } = useQuery({
    queryKey: ['parse-case-distribution'],
    queryFn: () => apiClient.getParseCaseDistribution(),
  });

  const { data: keywordStats } = useQuery({
    queryKey: ['keyword-stats'],
    queryFn: () => apiClient.getKeywordStats(),
  });

  const { data: interRater } = useQuery({
    queryKey: ['inter-rater'],
    queryFn: () => apiClient.getInterRaterReliability(),
  });

  const { data: completeness } = useQuery({
    queryKey: ['data-completeness'],
    queryFn: () => apiClient.getDataCompleteness(),
  });

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Analytics Dashboard</h1>
        <p className="text-gray-600 mt-2">
          Comprehensive insights into your medical annotation data
        </p>
      </div>

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <StatCard
            title="Total Documents"
            value={summary.total_documents || 0}
            color="blue"
          />
          <StatCard
            title="Total Jobs"
            value={summary.total_jobs || 0}
            color="green"
          />
          <StatCard
            title="Success Rate"
            value={`${((summary.success_rate || 0) * 100).toFixed(1)}%`}
            color="purple"
          />
          <StatCard
            title="Error Rate"
            value={`${((summary.error_rate || 0) * 100).toFixed(1)}%`}
            color="red"
          />
        </div>
      )}

      {/* Parse Case Distribution */}
      {parseCases && parseCases.length > 0 && (
        <div className="bg-white p-6 rounded-lg shadow mb-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Parse Case Distribution
          </h2>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={parseCases}
                dataKey="count"
                nameKey="parse_case"
                cx="50%"
                cy="50%"
                outerRadius={100}
                label={({ parse_case, percentage }) => `${parse_case}: ${percentage.toFixed(1)}%`}
              >
                {parseCases.map((_, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
          <div className="mt-4 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
            {parseCases.map((pc, idx) => (
              <div key={pc.parse_case} className="flex items-center gap-2">
                <div
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: COLORS[idx % COLORS.length] }}
                />
                <span className="text-sm text-gray-700">
                  {pc.parse_case}: {pc.count}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Keyword Statistics */}
        {keywordStats && (
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Keyword Statistics
            </h2>
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div>
                <div className="text-sm text-gray-600">Total Keywords</div>
                <div className="text-2xl font-bold text-blue-600">
                  {keywordStats.total_keywords}
                </div>
              </div>
              <div>
                <div className="text-sm text-gray-600">Unique Terms</div>
                <div className="text-2xl font-bold text-green-600">
                  {keywordStats.unique_terms}
                </div>
              </div>
            </div>
            {keywordStats.top_keywords && keywordStats.top_keywords.length > 0 && (
              <>
                <h3 className="font-medium text-gray-900 mb-2">Top Keywords</h3>
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={keywordStats.top_keywords.slice(0, 10)}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="term" angle={-45} textAnchor="end" height={100} />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="count" fill="#3B82F6" />
                  </BarChart>
                </ResponsiveContainer>
              </>
            )}
          </div>
        )}

        {/* Inter-Rater Reliability */}
        {interRater && (
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Inter-Rater Reliability
            </h2>
            <div className="space-y-4">
              {interRater.fleiss_kappa !== undefined && (
                <MetricBar
                  label="Fleiss' Kappa"
                  value={interRater.fleiss_kappa}
                  color="blue"
                />
              )}
              {interRater.cohens_kappa !== undefined && (
                <MetricBar
                  label="Cohen's Kappa"
                  value={interRater.cohens_kappa}
                  color="green"
                />
              )}
              <MetricBar
                label="Agreement Rate"
                value={interRater.agreement_percentage / 100}
                color="purple"
              />
            </div>
            {interRater.disagreement_details && Object.keys(interRater.disagreement_details).length > 0 && (
              <div className="mt-4">
                <h3 className="font-medium text-gray-900 mb-2">Disagreement Details</h3>
                <div className="space-y-2">
                  {Object.entries(interRater.disagreement_details).map(([key, value]) => (
                    <div key={key} className="flex justify-between text-sm">
                      <span className="text-gray-600">{key}</span>
                      <span className="font-medium text-gray-900">{value}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Data Completeness */}
      {completeness && (
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Data Completeness
          </h2>
          <div className="grid grid-cols-3 gap-4 mb-4">
            <div>
              <div className="text-sm text-gray-600">Total Records</div>
              <div className="text-2xl font-bold text-gray-900">
                {completeness.total_records}
              </div>
            </div>
            <div>
              <div className="text-sm text-gray-600">Complete Records</div>
              <div className="text-2xl font-bold text-green-600">
                {completeness.complete_records}
              </div>
            </div>
            <div>
              <div className="text-sm text-gray-600">Completeness</div>
              <div className="text-2xl font-bold text-blue-600">
                {completeness.completeness_percentage.toFixed(1)}%
              </div>
            </div>
          </div>
          
          {/* Completeness Progress Bar */}
          <div className="mb-4">
            <div className="w-full bg-gray-200 rounded-full h-4">
              <div
                className="bg-blue-600 h-4 rounded-full transition-all"
                style={{ width: `${completeness.completeness_percentage}%` }}
              />
            </div>
          </div>

          {completeness.missing_fields && Object.keys(completeness.missing_fields).length > 0 && (
            <>
              <h3 className="font-medium text-gray-900 mb-2">Missing Fields</h3>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart 
                  data={Object.entries(completeness.missing_fields).map(([field, count]) => ({
                    field,
                    count,
                  }))}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="field" angle={-45} textAnchor="end" height={100} />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="count" fill="#EF4444" />
                </BarChart>
              </ResponsiveContainer>
            </>
          )}
        </div>
      )}
    </div>
  );
}

function StatCard({ title, value, color }: { title: string; value: string | number; color: string }) {
  const colorClasses = {
    blue: 'text-blue-600',
    green: 'text-green-600',
    purple: 'text-purple-600',
    red: 'text-red-600',
  };

  return (
    <div className="bg-white p-4 rounded-lg shadow">
      <div className="text-sm text-gray-600">{title}</div>
      <div className={`text-2xl font-bold ${colorClasses[color as keyof typeof colorClasses]}`}>
        {value}
      </div>
    </div>
  );
}

function MetricBar({ label, value, color }: { label: string; value: number; color: string }) {
  const colorClasses = {
    blue: 'bg-blue-600',
    green: 'bg-green-600',
    purple: 'bg-purple-600',
  };

  return (
    <div>
      <div className="flex justify-between text-sm mb-1">
        <span className="text-gray-700">{label}</span>
        <span className="font-medium text-gray-900">{value.toFixed(3)}</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div
          className={`h-2 rounded-full transition-all ${colorClasses[color as keyof typeof colorClasses]}`}
          style={{ width: `${Math.min(value * 100, 100)}%` }}
        />
      </div>
    </div>
  );
}
