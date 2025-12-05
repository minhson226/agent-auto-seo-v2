/**
 * Keyword list component
 */
import { useState } from 'react';
import { TrashIcon, EyeIcon, ArrowPathIcon } from '@heroicons/react/24/outline';
import { useKeywords } from '../../hooks/useKeywords';
import { useWorkspaceStore } from '../../store/workspaceStore';

function getStatusBadgeColor(status: string) {
  switch (status) {
    case 'completed':
      return 'bg-green-100 text-green-800';
    case 'processing':
      return 'bg-yellow-100 text-yellow-800';
    case 'failed':
      return 'bg-red-100 text-red-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
}

export default function KeywordList() {
  const { currentWorkspaceId } = useWorkspaceStore();
  const [page, setPage] = useState(1);
  const { keywordLists, deleteKeywordList } = useKeywords(
    currentWorkspaceId || undefined,
    page
  );

  const handleDelete = async (id: string) => {
    if (window.confirm('Are you sure you want to delete this keyword list?')) {
      await deleteKeywordList.mutateAsync(id);
    }
  };

  if (!currentWorkspaceId) {
    return (
      <div className="rounded-lg border border-gray-200 bg-white p-6 text-center">
        <p className="text-gray-500">Please select a workspace first</p>
      </div>
    );
  }

  if (keywordLists.isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-600 border-t-transparent"></div>
      </div>
    );
  }

  if (keywordLists.isError) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-center">
        <p className="text-red-700">Failed to load keyword lists</p>
        <button
          onClick={() => keywordLists.refetch()}
          className="mt-2 text-sm text-red-600 hover:text-red-500"
        >
          Retry
        </button>
      </div>
    );
  }

  const data = keywordLists.data;

  return (
    <div className="rounded-lg border border-gray-200 bg-white">
      <div className="border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-medium text-gray-900">Keyword Lists</h3>
          <button
            onClick={() => keywordLists.refetch()}
            className="rounded p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
          >
            <ArrowPathIcon className={`h-5 w-5 ${keywordLists.isFetching ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {data?.data && data.data.length > 0 ? (
        <>
          <div className="divide-y divide-gray-200">
            {data.data.map((list) => (
              <div
                key={list.id}
                className="flex items-center justify-between px-6 py-4"
              >
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <h4 className="font-medium text-gray-900">{list.name}</h4>
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs font-medium ${getStatusBadgeColor(
                        list.status
                      )}`}
                    >
                      {list.status}
                    </span>
                  </div>
                  {list.description && (
                    <p className="mt-1 text-sm text-gray-500">
                      {list.description}
                    </p>
                  )}
                  <div className="mt-1 flex items-center gap-4 text-xs text-gray-500">
                    <span>{list.total_keywords} keywords</span>
                    <span>Source: {list.source}</span>
                    <span>
                      Created:{' '}
                      {new Date(list.created_at).toLocaleDateString()}
                    </span>
                  </div>
                  {list.error_message && (
                    <p className="mt-1 text-sm text-red-600">
                      {list.error_message}
                    </p>
                  )}
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => {
                      // Navigate to keyword list details
                      window.location.href = `/keywords/${list.id}`;
                    }}
                    className="rounded p-2 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
                    title="View keywords"
                  >
                    <EyeIcon className="h-5 w-5" />
                  </button>
                  <button
                    onClick={() => handleDelete(list.id)}
                    disabled={deleteKeywordList.isPending}
                    className="rounded p-2 text-gray-400 hover:bg-red-100 hover:text-red-600"
                    title="Delete list"
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
          <p className="text-gray-500">No keyword lists yet</p>
          <p className="mt-1 text-sm text-gray-400">
            Upload a CSV or TXT file to get started
          </p>
        </div>
      )}
    </div>
  );
}
