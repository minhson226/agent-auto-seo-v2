/**
 * Article list component
 */
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  PlusIcon,
  PencilIcon,
  TrashIcon,
  EyeIcon,
  SparklesIcon,
} from '@heroicons/react/24/outline';
import * as contentAPI from '../../api/content';
import { useWorkspaceStore } from '../../store/workspaceStore';

function getStatusBadgeColor(status: string) {
  switch (status) {
    case 'published':
      return 'bg-green-100 text-green-800';
    case 'draft':
      return 'bg-yellow-100 text-yellow-800';
    case 'archived':
      return 'bg-gray-100 text-gray-800';
    default:
      return 'bg-blue-100 text-blue-800';
  }
}

interface ArticleListProps {
  onCreateNew: () => void;
  onEdit: (articleId: string) => void;
  onView: (articleId: string) => void;
}

export default function ArticleList({
  onCreateNew,
  onEdit,
  onView,
}: ArticleListProps) {
  const { currentWorkspaceId } = useWorkspaceStore();
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState<string | undefined>();

  const articlesQuery = useQuery({
    queryKey: ['articles', currentWorkspaceId, page, statusFilter],
    queryFn: () =>
      contentAPI.getArticles(currentWorkspaceId!, page, 20, statusFilter),
    enabled: !!currentWorkspaceId,
  });

  const deleteMutation = useMutation({
    mutationFn: contentAPI.deleteArticle,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['articles'] });
    },
  });

  const handleDelete = async (id: string) => {
    if (window.confirm('Are you sure you want to delete this article?')) {
      await deleteMutation.mutateAsync(id);
    }
  };

  if (!currentWorkspaceId) {
    return (
      <div className="rounded-lg border border-gray-200 bg-white p-6 text-center">
        <p className="text-gray-500">Please select a workspace first</p>
      </div>
    );
  }

  if (articlesQuery.isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-600 border-t-transparent"></div>
      </div>
    );
  }

  const data = articlesQuery.data;

  return (
    <div className="rounded-lg border border-gray-200 bg-white">
      <div className="border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-medium text-gray-900">Articles</h3>
          <div className="flex items-center gap-4">
            <select
              value={statusFilter || ''}
              onChange={(e) => setStatusFilter(e.target.value || undefined)}
              className="rounded-md border border-gray-300 px-3 py-1.5 text-sm"
            >
              <option value="">All Status</option>
              <option value="draft">Draft</option>
              <option value="published">Published</option>
              <option value="archived">Archived</option>
            </select>
            <button
              onClick={onCreateNew}
              className="flex items-center gap-2 rounded-md bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-700"
            >
              <PlusIcon className="h-4 w-4" />
              New Article
            </button>
          </div>
        </div>
      </div>

      {data?.data && data.data.length > 0 ? (
        <>
          <div className="divide-y divide-gray-200">
            {data.data.map((article) => (
              <div
                key={article.id}
                className="flex items-center justify-between px-6 py-4"
              >
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <h4 className="font-medium text-gray-900">
                      {article.title}
                    </h4>
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs font-medium ${getStatusBadgeColor(
                        article.status
                      )}`}
                    >
                      {article.status}
                    </span>
                    {article.ai_model_used && (
                      <span className="flex items-center gap-1 text-xs text-purple-600">
                        <SparklesIcon className="h-3 w-3" />
                        AI Generated
                      </span>
                    )}
                  </div>
                  <div className="mt-1 flex items-center gap-4 text-xs text-gray-500">
                    <span>{article.word_count || 0} words</span>
                    {article.cost_usd && (
                      <span>${article.cost_usd.toFixed(4)}</span>
                    )}
                    <span>
                      {article.image_count} image
                      {article.image_count !== 1 ? 's' : ''}
                    </span>
                    <span>
                      Updated:{' '}
                      {new Date(article.updated_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => onView(article.id)}
                    className="rounded p-2 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
                    title="View article"
                  >
                    <EyeIcon className="h-5 w-5" />
                  </button>
                  <button
                    onClick={() => onEdit(article.id)}
                    className="rounded p-2 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
                    title="Edit article"
                  >
                    <PencilIcon className="h-5 w-5" />
                  </button>
                  <button
                    onClick={() => handleDelete(article.id)}
                    disabled={deleteMutation.isPending}
                    className="rounded p-2 text-gray-400 hover:bg-red-100 hover:text-red-600"
                    title="Delete article"
                  >
                    <TrashIcon className="h-5 w-5" />
                  </button>
                </div>
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
          <p className="text-gray-500">No articles yet</p>
          <button
            onClick={onCreateNew}
            className="mt-2 text-indigo-600 hover:text-indigo-500"
          >
            Create your first article
          </button>
        </div>
      )}
    </div>
  );
}
