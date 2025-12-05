/**
 * Analytics page
 */
import { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import * as analyticsAPI from '../api/analytics';
import { useWorkspaceStore } from '../store/workspaceStore';
import SummaryCards from '../components/analytics/SummaryCards';
import PerformanceChart from '../components/analytics/PerformanceChart';

function getDefaultDateRange() {
  const now = new Date();
  const thirtyDaysAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
  return {
    from: thirtyDaysAgo.toISOString().split('T')[0],
    to: now.toISOString().split('T')[0],
  };
}

export default function Analytics() {
  const { currentWorkspaceId } = useWorkspaceStore();
  const defaultDateRange = useMemo(() => getDefaultDateRange(), []);
  const [dateRange, setDateRange] = useState(defaultDateRange);
  const [selectedArticle, setSelectedArticle] = useState<string | null>(null);

  const summaryQuery = useQuery({
    queryKey: ['analytics-summary', currentWorkspaceId, dateRange],
    queryFn: () =>
      analyticsAPI.getSummary(
        currentWorkspaceId!,
        dateRange.from,
        dateRange.to
      ),
    enabled: !!currentWorkspaceId,
  });

  if (!currentWorkspaceId) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Analytics</h1>
          <p className="text-gray-500">
            Track your SEO performance and rankings.
          </p>
        </div>
        <div className="rounded-lg border border-gray-200 bg-white p-12 text-center">
          <p className="text-gray-500">
            Please select a workspace to view analytics.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Analytics</h1>
          <p className="text-gray-500">
            Track your SEO performance and rankings.
          </p>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <label className="text-sm text-gray-600">From:</label>
            <input
              type="date"
              value={dateRange.from}
              onChange={(e) =>
                setDateRange({ ...dateRange, from: e.target.value })
              }
              className="rounded-md border border-gray-300 px-3 py-1.5 text-sm"
            />
          </div>
          <div className="flex items-center gap-2">
            <label className="text-sm text-gray-600">To:</label>
            <input
              type="date"
              value={dateRange.to}
              onChange={(e) =>
                setDateRange({ ...dateRange, to: e.target.value })
              }
              className="rounded-md border border-gray-300 px-3 py-1.5 text-sm"
            />
          </div>
        </div>
      </div>

      {/* Summary Cards */}
      {summaryQuery.isLoading ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <div
              key={i}
              className="h-32 animate-pulse rounded-lg border border-gray-200 bg-gray-100"
            />
          ))}
        </div>
      ) : summaryQuery.data ? (
        <SummaryCards
          totalImpressions={summaryQuery.data.total_impressions}
          totalClicks={summaryQuery.data.total_clicks}
          avgPosition={summaryQuery.data.avg_position}
          articlesRanking={summaryQuery.data.articles_ranking}
        />
      ) : (
        <div className="rounded-lg border border-gray-200 bg-white p-6 text-center">
          <p className="text-gray-500">No analytics data available</p>
        </div>
      )}

      {/* Performance Chart */}
      {selectedArticle ? (
        <div>
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-medium text-gray-900">
              Article Performance
            </h2>
            <button
              onClick={() => setSelectedArticle(null)}
              className="text-sm text-indigo-600 hover:text-indigo-500"
            >
              View All
            </button>
          </div>
          <PerformanceChart articleId={selectedArticle} days={30} />
        </div>
      ) : null}

      {/* Top Performing Articles */}
      {summaryQuery.data?.top_articles &&
        summaryQuery.data.top_articles.length > 0 && (
          <div className="rounded-lg border border-gray-200 bg-white">
            <div className="border-b border-gray-200 px-6 py-4">
              <h2 className="text-lg font-medium text-gray-900">
                Top Performing Articles
              </h2>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                      URL
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">
                      Impressions
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">
                      Clicks
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">
                      CTR
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">
                      Position
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 bg-white">
                  {summaryQuery.data.top_articles.map((article) => (
                    <tr
                      key={article.url}
                      className="cursor-pointer hover:bg-gray-50"
                      onClick={() => {
                        // Extract article ID from URL if possible
                        // For demo, just show the URL
                      }}
                    >
                      <td className="max-w-xs truncate px-6 py-4 text-sm text-gray-900">
                        {article.url}
                      </td>
                      <td className="px-6 py-4 text-right text-sm text-gray-900">
                        {article.impressions.toLocaleString()}
                      </td>
                      <td className="px-6 py-4 text-right text-sm text-gray-900">
                        {article.clicks.toLocaleString()}
                      </td>
                      <td className="px-6 py-4 text-right text-sm text-gray-900">
                        {article.impressions > 0
                          ? (
                              (article.clicks / article.impressions) *
                              100
                            ).toFixed(2)
                          : '0.00'}
                        %
                      </td>
                      <td className="px-6 py-4 text-right text-sm text-gray-900">
                        {article.position.toFixed(1)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
    </div>
  );
}
