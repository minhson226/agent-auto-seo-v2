/**
 * Performance chart component
 */
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { useQuery } from '@tanstack/react-query';
import * as analyticsAPI from '../../api/analytics';

interface PerformanceChartProps {
  articleId?: string;
  days?: number;
}

export default function PerformanceChart({
  articleId,
  days = 30,
}: PerformanceChartProps) {
  // If articleId is provided, fetch article-specific data
  const articlePerformance = useQuery({
    queryKey: ['article-performance', articleId, days],
    queryFn: () => analyticsAPI.getArticlePerformance(articleId!, days),
    enabled: !!articleId,
  });

  // If workspaceId is provided, we would fetch workspace summary
  // For now, we'll use the article data or mock data
  const data = articlePerformance.data?.data || [];

  if (articlePerformance.isLoading) {
    return (
      <div className="flex h-96 items-center justify-center rounded-lg border border-gray-200 bg-white">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-600 border-t-transparent"></div>
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="flex h-96 items-center justify-center rounded-lg border border-gray-200 bg-white">
        <p className="text-gray-500">No performance data available</p>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6">
      <h3 className="mb-4 text-lg font-medium text-gray-900">
        Performance Over Time
      </h3>
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 12 }}
              tickFormatter={(value) =>
                new Date(value).toLocaleDateString('en-US', {
                  month: 'short',
                  day: 'numeric',
                })
              }
            />
            <YAxis
              yAxisId="left"
              tick={{ fontSize: 12 }}
              tickFormatter={(value) =>
                value >= 1000 ? `${(value / 1000).toFixed(0)}K` : value
              }
            />
            <YAxis
              yAxisId="right"
              orientation="right"
              tick={{ fontSize: 12 }}
              domain={[1, 'auto']}
              reversed
            />
            <Tooltip
              contentStyle={{
                backgroundColor: 'white',
                border: '1px solid #e5e7eb',
                borderRadius: '0.375rem',
              }}
              labelFormatter={(label) =>
                new Date(label).toLocaleDateString('en-US', {
                  weekday: 'long',
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric',
                })
              }
            />
            <Legend />
            <Line
              yAxisId="left"
              type="monotone"
              dataKey="impressions"
              stroke="#6366f1"
              strokeWidth={2}
              dot={false}
              name="Impressions"
            />
            <Line
              yAxisId="left"
              type="monotone"
              dataKey="clicks"
              stroke="#10b981"
              strokeWidth={2}
              dot={false}
              name="Clicks"
            />
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="position"
              stroke="#f59e0b"
              strokeWidth={2}
              dot={false}
              name="Position"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
