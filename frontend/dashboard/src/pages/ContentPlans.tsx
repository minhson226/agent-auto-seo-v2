/**
 * Content plans page
 */
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  PlusIcon,
  PencilIcon,
  TrashIcon,
  SparklesIcon,
} from '@heroicons/react/24/outline';
import * as contentAPI from '../api/content';
import { useWorkspaceStore } from '../store/workspaceStore';
import ContentPlanForm from '../components/content/ContentPlanForm';

function getStatusBadgeColor(status: string) {
  switch (status) {
    case 'completed':
      return 'bg-green-100 text-green-800';
    case 'in_progress':
      return 'bg-yellow-100 text-yellow-800';
    case 'draft':
      return 'bg-gray-100 text-gray-800';
    default:
      return 'bg-blue-100 text-blue-800';
  }
}

export default function ContentPlans() {
  const { currentWorkspaceId } = useWorkspaceStore();
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [editingPlanId, setEditingPlanId] = useState<string | null>(null);
  const [page, setPage] = useState(1);

  const plansQuery = useQuery({
    queryKey: ['content-plans', currentWorkspaceId, page],
    queryFn: () => contentAPI.getContentPlans(currentWorkspaceId!, page, 20),
    enabled: !!currentWorkspaceId,
  });

  const deleteMutation = useMutation({
    mutationFn: contentAPI.deleteContentPlan,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['content-plans'] });
    },
  });

  const generateMutation = useMutation({
    mutationFn: contentAPI.generateArticle,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['articles'] });
    },
  });

  const handleDelete = async (id: string) => {
    if (
      window.confirm('Are you sure you want to delete this content plan?')
    ) {
      await deleteMutation.mutateAsync(id);
    }
  };

  const handleGenerate = async (planId: string) => {
    if (
      window.confirm(
        'Generate an article from this content plan using AI? This will use API credits.'
      )
    ) {
      try {
        await generateMutation.mutateAsync(planId);
        alert('Article generated successfully! Check the Articles page.');
      } catch {
        alert('Failed to generate article. Please try again.');
      }
    }
  };

  if (!currentWorkspaceId) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Content Plans</h1>
          <p className="text-gray-500">
            Create content plans to guide your article generation.
          </p>
        </div>
        <div className="rounded-lg border border-gray-200 bg-white p-12 text-center">
          <p className="text-gray-500">
            Please select a workspace to manage content plans.
          </p>
        </div>
      </div>
    );
  }

  const data = plansQuery.data;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Content Plans</h1>
          <p className="text-gray-500">
            Create content plans to guide your article generation.
          </p>
        </div>
        <button
          onClick={() => setShowForm(true)}
          className="flex items-center gap-2 rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
        >
          <PlusIcon className="h-5 w-5" />
          New Plan
        </button>
      </div>

      {showForm && (
        <ContentPlanForm
          workspaceId={currentWorkspaceId}
          onClose={() => setShowForm(false)}
          onSuccess={() => setShowForm(false)}
        />
      )}

      {editingPlanId && (
        <ContentPlanForm
          workspaceId={currentWorkspaceId}
          planId={editingPlanId}
          initialData={(() => {
            const plan = data?.data?.find((p) => p.id === editingPlanId);
            return plan
              ? {
                  title: plan.title,
                  target_keywords: plan.target_keywords,
                  estimated_word_count: plan.estimated_word_count,
                }
              : undefined;
          })()}
          onClose={() => setEditingPlanId(null)}
          onSuccess={() => setEditingPlanId(null)}
        />
      )}

      <div className="rounded-lg border border-gray-200 bg-white">
        {plansQuery.isLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-600 border-t-transparent"></div>
          </div>
        ) : data?.data && data.data.length > 0 ? (
          <>
            <div className="divide-y divide-gray-200">
              {data.data.map((plan) => (
                <div
                  key={plan.id}
                  className="flex items-center justify-between px-6 py-4"
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <h4 className="font-medium text-gray-900">
                        {plan.title}
                      </h4>
                      <span
                        className={`rounded-full px-2 py-0.5 text-xs font-medium ${getStatusBadgeColor(
                          plan.status
                        )}`}
                      >
                        {plan.status}
                      </span>
                    </div>
                    <div className="mt-1 flex flex-wrap gap-1">
                      {plan.target_keywords.slice(0, 5).map((kw) => (
                        <span
                          key={kw}
                          className="rounded bg-gray-100 px-2 py-0.5 text-xs text-gray-600"
                        >
                          {kw}
                        </span>
                      ))}
                      {plan.target_keywords.length > 5 && (
                        <span className="text-xs text-gray-400">
                          +{plan.target_keywords.length - 5} more
                        </span>
                      )}
                    </div>
                    <p className="mt-1 text-xs text-gray-500">
                      ~{plan.estimated_word_count} words • Created{' '}
                      {new Date(plan.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleGenerate(plan.id)}
                      disabled={generateMutation.isPending}
                      className="flex items-center gap-1 rounded bg-purple-100 px-3 py-1.5 text-sm font-medium text-purple-700 hover:bg-purple-200 disabled:opacity-50"
                      title="Generate article with AI"
                    >
                      <SparklesIcon className="h-4 w-4" />
                      Generate
                    </button>
                    <button
                      onClick={() => setEditingPlanId(plan.id)}
                      className="rounded p-2 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
                      title="Edit plan"
                    >
                      <PencilIcon className="h-5 w-5" />
                    </button>
                    <button
                      onClick={() => handleDelete(plan.id)}
                      disabled={deleteMutation.isPending}
                      className="rounded p-2 text-gray-400 hover:bg-red-100 hover:text-red-600"
                      title="Delete plan"
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
            <p className="text-gray-500">No content plans yet</p>
            <button
              onClick={() => setShowForm(true)}
              className="mt-2 text-indigo-600 hover:text-indigo-500"
            >
              Create your first content plan
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
