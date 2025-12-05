/**
 * Publishing page
 */
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  PaperAirplaneIcon,
  ClockIcon,
  TrashIcon,
  ArrowTopRightOnSquareIcon,
} from '@heroicons/react/24/outline';
import * as publishingAPI from '../api/publishing';
import * as contentAPI from '../api/content';
import { useSites } from '../hooks/useWorkspace';
import { useWorkspaceStore } from '../store/workspaceStore';

function getStatusBadgeColor(status: string) {
  switch (status) {
    case 'published':
      return 'bg-green-100 text-green-800';
    case 'scheduled':
      return 'bg-blue-100 text-blue-800';
    case 'failed':
      return 'bg-red-100 text-red-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
}

export default function Publishing() {
  const { currentWorkspaceId } = useWorkspaceStore();
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [showPublishForm, setShowPublishForm] = useState(false);
  const [selectedArticle, setSelectedArticle] = useState('');
  const [selectedSite, setSelectedSite] = useState('');
  const [scheduleDate, setScheduleDate] = useState('');

  const { sites } = useSites(currentWorkspaceId || undefined);

  const publishedQuery = useQuery({
    queryKey: ['published-articles', currentWorkspaceId, page],
    queryFn: () =>
      publishingAPI.getPublishedArticles(currentWorkspaceId!, page),
    enabled: !!currentWorkspaceId,
  });

  const articlesQuery = useQuery({
    queryKey: ['articles-for-publish', currentWorkspaceId],
    queryFn: () => contentAPI.getArticles(currentWorkspaceId!, 1, 100),
    enabled: !!currentWorkspaceId && showPublishForm,
  });

  const publishMutation = useMutation({
    mutationFn: publishingAPI.publishArticle,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['published-articles'] });
      setShowPublishForm(false);
      setSelectedArticle('');
      setSelectedSite('');
    },
  });

  const unpublishMutation = useMutation({
    mutationFn: publishingAPI.unpublishArticle,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['published-articles'] });
    },
  });

  const handlePublish = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedArticle || !selectedSite) return;

    await publishMutation.mutateAsync({
      article_id: selectedArticle,
      site_id: selectedSite,
      publish_date: scheduleDate || undefined,
      schedule: !!scheduleDate,
    });
  };

  if (!currentWorkspaceId) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Publishing</h1>
          <p className="text-gray-500">
            Publish your articles to your connected sites.
          </p>
        </div>
        <div className="rounded-lg border border-gray-200 bg-white p-12 text-center">
          <p className="text-gray-500">
            Please select a workspace to manage publishing.
          </p>
        </div>
      </div>
    );
  }

  const data = publishedQuery.data;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Publishing</h1>
          <p className="text-gray-500">
            Publish your articles to your connected sites.
          </p>
        </div>
        <button
          onClick={() => setShowPublishForm(true)}
          className="flex items-center gap-2 rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
        >
          <PaperAirplaneIcon className="h-5 w-5" />
          Publish Article
        </button>
      </div>

      {/* Publish Form Modal */}
      {showPublishForm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
            <h3 className="mb-4 text-lg font-medium text-gray-900">
              Publish Article
            </h3>
            <form onSubmit={handlePublish} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Select Article
                </label>
                <select
                  value={selectedArticle}
                  onChange={(e) => setSelectedArticle(e.target.value)}
                  required
                  className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-indigo-500 sm:text-sm"
                >
                  <option value="">Choose an article...</option>
                  {articlesQuery.data?.data?.map((article) => (
                    <option key={article.id} value={article.id}>
                      {article.title}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Select Site
                </label>
                <select
                  value={selectedSite}
                  onChange={(e) => setSelectedSite(e.target.value)}
                  required
                  className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-indigo-500 sm:text-sm"
                >
                  <option value="">Choose a site...</option>
                  {sites.data?.map((site) => (
                    <option key={site.id} value={site.id}>
                      {site.name} ({site.domain})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Schedule (optional)
                </label>
                <input
                  type="datetime-local"
                  value={scheduleDate}
                  onChange={(e) => setScheduleDate(e.target.value)}
                  className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-indigo-500 sm:text-sm"
                />
                <p className="mt-1 text-xs text-gray-500">
                  Leave empty to publish immediately
                </p>
              </div>

              <div className="flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setShowPublishForm(false)}
                  className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={publishMutation.isPending}
                  className="flex items-center gap-2 rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
                >
                  {scheduleDate ? (
                    <>
                      <ClockIcon className="h-4 w-4" />
                      Schedule
                    </>
                  ) : (
                    <>
                      <PaperAirplaneIcon className="h-4 w-4" />
                      Publish Now
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Published Articles List */}
      <div className="rounded-lg border border-gray-200 bg-white">
        <div className="border-b border-gray-200 px-6 py-4">
          <h3 className="text-lg font-medium text-gray-900">
            Published Articles
          </h3>
        </div>

        {publishedQuery.isLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-600 border-t-transparent"></div>
          </div>
        ) : data?.data && data.data.length > 0 ? (
          <>
            <div className="divide-y divide-gray-200">
              {data.data.map((item) => (
                <div
                  key={item.id}
                  className="flex items-center justify-between px-6 py-4"
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span
                        className={`rounded-full px-2 py-0.5 text-xs font-medium ${getStatusBadgeColor(
                          item.status
                        )}`}
                      >
                        {item.status}
                      </span>
                      {item.published_url && (
                        <a
                          href={item.published_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-1 text-sm text-indigo-600 hover:text-indigo-500"
                        >
                          View <ArrowTopRightOnSquareIcon className="h-4 w-4" />
                        </a>
                      )}
                    </div>
                    <p className="mt-1 text-sm text-gray-500">
                      Article ID: {item.article_id}
                    </p>
                    <p className="text-xs text-gray-400">
                      {item.published_at
                        ? `Published: ${new Date(
                            item.published_at
                          ).toLocaleString()}`
                        : item.scheduled_at
                          ? `Scheduled: ${new Date(
                              item.scheduled_at
                            ).toLocaleString()}`
                          : `Created: ${new Date(
                              item.created_at
                            ).toLocaleString()}`}
                    </p>
                  </div>
                  <button
                    onClick={() => {
                      if (
                        window.confirm('Remove this published article?')
                      ) {
                        unpublishMutation.mutate(item.id);
                      }
                    }}
                    disabled={unpublishMutation.isPending}
                    className="rounded p-2 text-gray-400 hover:bg-red-100 hover:text-red-600"
                    title="Unpublish"
                  >
                    <TrashIcon className="h-5 w-5" />
                  </button>
                </div>
              ))}
            </div>

            {/* Pagination */}
            {data.total > data.page_size && (
              <div className="border-t border-gray-200 px-6 py-4">
                <div className="flex items-center justify-between">
                  <p className="text-sm text-gray-700">
                    Showing {(page - 1) * data.page_size + 1} to{' '}
                    {Math.min(page * data.page_size, data.total)} of{' '}
                    {data.total} results
                  </p>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setPage((p) => Math.max(1, p - 1))}
                      disabled={page === 1}
                      className="rounded-md border border-gray-300 px-3 py-1 text-sm disabled:opacity-50"
                    >
                      Previous
                    </button>
                    <button
                      onClick={() => setPage((p) => p + 1)}
                      disabled={page * data.page_size >= data.total}
                      className="rounded-md border border-gray-300 px-3 py-1 text-sm disabled:opacity-50"
                    >
                      Next
                    </button>
                  </div>
                </div>
              </div>
            )}
          </>
        ) : (
          <div className="px-6 py-12 text-center">
            <p className="text-gray-500">No published articles yet</p>
            <button
              onClick={() => setShowPublishForm(true)}
              className="mt-2 text-indigo-600 hover:text-indigo-500"
            >
              Publish your first article
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
