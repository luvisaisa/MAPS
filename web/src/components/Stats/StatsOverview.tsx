import type { DashboardStats } from '../../types/api';

interface StatsOverviewProps {
  stats?: DashboardStats;
}

export function StatsOverview({ stats }: StatsOverviewProps) {
  const cards = [
    {
      title: 'Total Documents',
      value: stats?.total_documents || 0,
      icon: '📄',
      color: 'bg-blue-50 text-blue-700',
      trend: '+12% from last month',
    },
    {
      title: 'Total Jobs',
      value: stats?.total_jobs || 0,
      icon: '⚙️',
      color: 'bg-green-50 text-green-700',
      trend: '+8% from last month',
    },
    {
      title: 'Success Rate',
      value: `${(stats?.success_rate || 0).toFixed(1)}%`,
      icon: '✓',
      color: 'bg-emerald-50 text-emerald-700',
      trend: stats?.success_rate && stats.success_rate > 95 ? 'Excellent' : 'Good',
    },
    {
      title: 'Error Rate',
      value: `${(stats?.error_rate || 0).toFixed(1)}%`,
      icon: '⚠️',
      color: 'bg-red-50 text-red-700',
      trend: stats?.error_rate && stats.error_rate < 5 ? 'Low' : 'Needs attention',
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {cards.map((card) => (
        <div key={card.title} className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <span className="text-2xl">{card.icon}</span>
            <span className={`text-xs font-medium px-2 py-1 rounded ${card.color}`}>
              {card.trend}
            </span>
          </div>
          <h3 className="text-sm font-medium text-gray-600 mb-1">{card.title}</h3>
          <p className="text-3xl font-bold text-gray-900">{card.value}</p>
        </div>
      ))}
    </div>
  );
}
