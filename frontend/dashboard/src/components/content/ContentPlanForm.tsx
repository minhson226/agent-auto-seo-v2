/**
 * Content plan form component
 */
import { useState } from 'react';
import { XMarkIcon, PlusIcon } from '@heroicons/react/24/outline';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import * as contentAPI from '../../api/content';

interface ContentPlanFormProps {
  workspaceId: string;
  planId?: string;
  initialData?: {
    title: string;
    target_keywords: string[];
    estimated_word_count: number;
  };
  onClose: () => void;
  onSuccess: () => void;
}

export default function ContentPlanForm({
  workspaceId,
  planId,
  initialData,
  onClose,
  onSuccess,
}: ContentPlanFormProps) {
  const queryClient = useQueryClient();
  const [formData, setFormData] = useState({
    title: initialData?.title || '',
    estimated_word_count: initialData?.estimated_word_count || 1500,
  });
  const [keywords, setKeywords] = useState<string[]>(
    initialData?.target_keywords || []
  );
  const [newKeyword, setNewKeyword] = useState('');
  const [error, setError] = useState('');

  const createPlan = useMutation({
    mutationFn: contentAPI.createContentPlan,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['content-plans'] });
      onSuccess();
    },
  });

  const updatePlan = useMutation({
    mutationFn: ({
      plan_id,
      data,
    }: {
      plan_id: string;
      data: Partial<contentAPI.ContentPlan>;
    }) => contentAPI.updateContentPlan(plan_id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['content-plans'] });
      onSuccess();
    },
  });

  const handleAddKeyword = () => {
    if (newKeyword.trim() && !keywords.includes(newKeyword.trim())) {
      setKeywords([...keywords, newKeyword.trim()]);
      setNewKeyword('');
    }
  };

  const handleRemoveKeyword = (keyword: string) => {
    setKeywords(keywords.filter((k) => k !== keyword));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (keywords.length === 0) {
      setError('Please add at least one target keyword');
      return;
    }

    try {
      if (planId) {
        await updatePlan.mutateAsync({
          plan_id: planId,
          data: {
            title: formData.title,
            target_keywords: keywords,
            estimated_word_count: formData.estimated_word_count,
          },
        });
      } else {
        await createPlan.mutateAsync({
          workspace_id: workspaceId,
          title: formData.title,
          target_keywords: keywords,
          estimated_word_count: formData.estimated_word_count,
        });
      }
    } catch {
      setError('Failed to save content plan');
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="w-full max-w-lg rounded-lg bg-white p-6 shadow-xl">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-lg font-medium text-gray-900">
            {planId ? 'Edit Content Plan' : 'New Content Plan'}
          </h3>
          <button
            onClick={onClose}
            className="rounded-full p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
          >
            <XMarkIcon className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="rounded-md bg-red-50 p-3">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}

          <div>
            <label
              htmlFor="title"
              className="block text-sm font-medium text-gray-700"
            >
              Title
            </label>
            <input
              type="text"
              id="title"
              value={formData.title}
              onChange={(e) =>
                setFormData({ ...formData, title: e.target.value })
              }
              required
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-indigo-500 sm:text-sm"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              Target Keywords
            </label>
            <div className="mt-1 flex gap-2">
              <input
                type="text"
                value={newKeyword}
                onChange={(e) => setNewKeyword(e.target.value)}
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    handleAddKeyword();
                  }
                }}
                placeholder="Add keyword"
                className="flex-1 rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-indigo-500 sm:text-sm"
              />
              <button
                type="button"
                onClick={handleAddKeyword}
                className="rounded-md bg-gray-100 px-3 py-2 text-gray-600 hover:bg-gray-200"
              >
                <PlusIcon className="h-5 w-5" />
              </button>
            </div>
            <div className="mt-2 flex flex-wrap gap-2">
              {keywords.map((keyword) => (
                <span
                  key={keyword}
                  className="inline-flex items-center gap-1 rounded-full bg-indigo-100 px-3 py-1 text-sm text-indigo-800"
                >
                  {keyword}
                  <button
                    type="button"
                    onClick={() => handleRemoveKeyword(keyword)}
                    className="text-indigo-600 hover:text-indigo-800"
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          </div>

          <div>
            <label
              htmlFor="word_count"
              className="block text-sm font-medium text-gray-700"
            >
              Estimated Word Count
            </label>
            <input
              type="number"
              id="word_count"
              min="100"
              max="10000"
              step="100"
              value={formData.estimated_word_count}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  estimated_word_count: parseInt(e.target.value),
                })
              }
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-indigo-500 sm:text-sm"
            />
          </div>

          <div className="flex justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={createPlan.isPending || updatePlan.isPending}
              className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
            >
              {createPlan.isPending || updatePlan.isPending
                ? 'Saving...'
                : planId
                  ? 'Update'
                  : 'Create'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
