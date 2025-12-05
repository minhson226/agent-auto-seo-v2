/**
 * Dashboard home page
 */
import { useQuery } from '@tanstack/react-query';
import {
  DocumentTextIcon,
  KeyIcon,
  ChartBarIcon,
  FolderIcon,
} from '@heroicons/react/24/outline';
import { Link } from 'react-router-dom';
import { useWorkspaceStore } from '../store/workspaceStore';
import * as analyticsAPI from '../api/analytics';
import * as contentAPI from '../api/content';
import * as keywordsAPI from '../api/keywords';
import SummaryCards from '../components/analytics/SummaryCards';

export default function Dashboard() {
  const { currentWorkspaceId } = useWorkspaceStore();

  // Fetch summary data
  const summaryQuery = useQuery({
    queryKey: ['analytics-summary', currentWorkspaceId],
    queryFn: () => analyticsAPI.getSummary(currentWorkspaceId!),
    enabled: !!currentWorkspaceId,
  });

  // Fetch articles count
  const articlesQuery = useQuery({
    queryKey: ['articles-count', currentWorkspaceId],
    queryFn: () => contentAPI.getArticles(currentWorkspaceId!, 1, 1),
    enabled: !!currentWorkspaceId,
  });

  // Fetch content plans count
  const plansQuery = useQuery({
    queryKey: ['plans-count', currentWorkspaceId],
    queryFn: () => contentAPI.getContentPlans(currentWorkspaceId!, 1, 1),
    enabled: !!currentWorkspaceId,
  });

  // Fetch keyword lists count
  const keywordsQuery = useQuery({
    queryKey: ['keywords-count', currentWorkspaceId],
    queryFn: () => keywordsAPI.getKeywordLists(currentWorkspaceId!, 1, 1),
    enabled: !!currentWorkspaceId,
  });

  if (!currentWorkspaceId) {
    return (
      <div className="flex h-full flex-col items-center justify-center">
        <h2 className="mb-2 text-xl font-semibold text-gray-900">
          Welcome to Auto-SEO
        </h2>
        <p className="text-gray-500">
          Please select a workspace from the dropdown above to get started.
        </p>
        <Link
          to="/settings"
          className="mt-4 rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
        >
          Create Workspace
        </Link>
      </div>
    );
  }

  const quickLinks = [
    {
      name: 'Articles',
      href: '/articles',
      icon: DocumentTextIcon,
      count: articlesQuery.data?.total || 0,
      color: 'bg-blue-500',
    },
    {
      name: 'Content Plans',
      href: '/content-plans',
      icon: FolderIcon,
      count: plansQuery.data?.total || 0,
      color: 'bg-green-500',
    },
    {
      name: 'Keyword Lists',
      href: '/keywords',
      icon: KeyIcon,
      count: keywordsQuery.data?.total || 0,
      color: 'bg-purple-500',
    },
    {
      name: 'Analytics',
      href: '/analytics',
      icon: ChartBarIcon,
      count: summaryQuery.data?.articles_ranking || 0,
      description: 'articles ranking',
      color: 'bg-orange-500',
    },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-500">
          Welcome back! Here&apos;s an overview of your SEO performance.
        </p>
      </div>

      {/* Summary Cards */}
      {summaryQuery.data && (
        <SummaryCards
          totalImpressions={summaryQuery.data.total_impressions}
          totalClicks={summaryQuery.data.total_clicks}
          avgPosition={summaryQuery.data.avg_position}
          articlesRanking={summaryQuery.data.articles_ranking}
        />
      )}

      {/* Quick Links */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {quickLinks.map((link) => (
          <Link
            key={link.name}
            to={link.href}
            className="group rounded-lg border border-gray-200 bg-white p-6 shadow-sm transition-shadow hover:shadow-md"
          >
            <div className="flex items-center justify-between">
              <div
                className={`rounded-lg p-3 ${link.color} bg-opacity-10`}
              >
                <link.icon className={`h-6 w-6 ${link.color.replace('bg-', 'text-')}`} />
              </div>
              <span className="text-2xl font-bold text-gray-900">
                {link.count}
              </span>
            </div>
            <p className="mt-4 font-medium text-gray-900 group-hover:text-indigo-600">
              {link.name}
            </p>
            {link.description && (
              <p className="text-sm text-gray-500">{link.description}</p>
            )}
          </Link>
        ))}
      </div>

      {/* Top Articles */}
      {summaryQuery.data?.top_articles &&
        summaryQuery.data.top_articles.length > 0 && (
          <div className="rounded-lg border border-gray-200 bg-white p-6">
            <h2 className="mb-4 text-lg font-medium text-gray-900">
              Top Performing Articles
            </h2>
            <div className="divide-y divide-gray-200">
              {summaryQuery.data.top_articles.slice(0, 5).map((article, index) => (
                <div
                  key={article.url}
                  className="flex items-center justify-between py-3"
                >
                  <div className="flex items-center gap-4">
                    <span className="flex h-8 w-8 items-center justify-center rounded-full bg-gray-100 text-sm font-medium text-gray-600">
                      {index + 1}
                    </span>
                    <div>
                      <p className="font-medium text-gray-900 truncate max-w-md">
                        {article.url}
                      </p>
                      <p className="text-sm text-gray-500">
                        Position: {article.position.toFixed(1)}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-medium text-gray-900">
                      {article.clicks.toLocaleString()} clicks
                    </p>
                    <p className="text-sm text-gray-500">
                      {article.impressions.toLocaleString()} impressions
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
    </div>
  );
}
