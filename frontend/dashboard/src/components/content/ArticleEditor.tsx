/**
 * Article editor component
 */
import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { XMarkIcon, PhotoIcon, TrashIcon } from '@heroicons/react/24/outline';
import * as contentAPI from '../../api/content';

interface ArticleEditorProps {
  workspaceId: string;
  articleId?: string;
  onClose: () => void;
  onSuccess: () => void;
}

// Helper component to handle form state
function ArticleEditorForm({
  workspaceId,
  articleId,
  initialData,
  onClose,
  onSuccess,
}: ArticleEditorProps & {
  initialData: { title: string; content: string; status: string };
}) {
  const queryClient = useQueryClient();
  const [error, setError] = useState('');
  const [formData, setFormData] = useState(initialData);

  // Fetch article for images
  const articleQuery = useQuery({
    queryKey: ['article', articleId],
    queryFn: () => contentAPI.getArticle(articleId!),
    enabled: !!articleId,
  });

  const createArticle = useMutation({
    mutationFn: contentAPI.createArticle,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['articles'] });
      onSuccess();
    },
  });

  const updateArticle = useMutation({
    mutationFn: ({
      article_id,
      data,
    }: {
      article_id: string;
      data: { title?: string; content?: string; status?: string };
    }) => contentAPI.updateArticle(article_id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['articles'] });
      queryClient.invalidateQueries({ queryKey: ['article', articleId] });
      onSuccess();
    },
  });

  const uploadImage = useMutation({
    mutationFn: ({ article_id, file }: { article_id: string; file: File }) =>
      contentAPI.uploadArticleImage(article_id, file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['article', articleId] });
    },
  });

  const deleteImage = useMutation({
    mutationFn: ({
      article_id,
      image_id,
    }: {
      article_id: string;
      image_id: string;
    }) => contentAPI.deleteArticleImage(article_id, image_id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['article', articleId] });
    },
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    try {
      if (articleId) {
        await updateArticle.mutateAsync({
          article_id: articleId,
          data: formData,
        });
      } else {
        await createArticle.mutateAsync({
          workspace_id: workspaceId,
          title: formData.title,
          content: formData.content,
        });
      }
    } catch {
      setError('Failed to save article');
    }
  };

  const handleImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !articleId) return;

    try {
      await uploadImage.mutateAsync({ article_id: articleId, file });
    } catch {
      setError('Failed to upload image');
    }
  };

  if (articleId && articleQuery.isLoading) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
        <div className="flex h-64 w-64 items-center justify-center rounded-lg bg-white">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-600 border-t-transparent"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="flex h-[90vh] w-full max-w-4xl flex-col rounded-lg bg-white shadow-xl">
        <div className="flex items-center justify-between border-b border-gray-200 px-6 py-4">
          <h3 className="text-lg font-medium text-gray-900">
            {articleId ? 'Edit Article' : 'New Article'}
          </h3>
          <button
            onClick={onClose}
            className="rounded-full p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
          >
            <XMarkIcon className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-1 flex-col overflow-hidden">
          <div className="flex-1 overflow-y-auto p-6">
            {error && (
              <div className="mb-4 rounded-md bg-red-50 p-3">
                <p className="text-sm text-red-700">{error}</p>
              </div>
            )}

            <div className="mb-4">
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

            {articleId && (
              <div className="mb-4">
                <label
                  htmlFor="status"
                  className="block text-sm font-medium text-gray-700"
                >
                  Status
                </label>
                <select
                  id="status"
                  value={formData.status}
                  onChange={(e) =>
                    setFormData({ ...formData, status: e.target.value })
                  }
                  className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-indigo-500 sm:text-sm"
                >
                  <option value="draft">Draft</option>
                  <option value="published">Published</option>
                  <option value="archived">Archived</option>
                </select>
              </div>
            )}

            <div className="mb-4">
              <label
                htmlFor="content"
                className="block text-sm font-medium text-gray-700"
              >
                Content
              </label>
              <textarea
                id="content"
                value={formData.content}
                onChange={(e) =>
                  setFormData({ ...formData, content: e.target.value })
                }
                rows={20}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 font-mono text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-indigo-500"
              />
              <p className="mt-1 text-xs text-gray-500">
                {formData.content.split(/\s+/).filter(Boolean).length} words
              </p>
            </div>

            {/* Images section */}
            {articleId && (
              <div className="mb-4">
                <div className="mb-2 flex items-center justify-between">
                  <label className="block text-sm font-medium text-gray-700">
                    Images
                  </label>
                  <label className="flex cursor-pointer items-center gap-1 text-sm text-indigo-600 hover:text-indigo-500">
                    <PhotoIcon className="h-4 w-4" />
                    Upload Image
                    <input
                      type="file"
                      accept="image/*"
                      onChange={handleImageUpload}
                      className="sr-only"
                    />
                  </label>
                </div>
                <div className="grid grid-cols-4 gap-2">
                  {articleQuery.data?.images?.map((image) => (
                    <div
                      key={image.id}
                      className="group relative rounded border border-gray-200"
                    >
                      <div className="aspect-square overflow-hidden rounded">
                        <img
                          src={image.storage_path}
                          alt={image.original_filename}
                          className="h-full w-full object-cover"
                        />
                      </div>
                      <button
                        type="button"
                        onClick={() =>
                          deleteImage.mutate({
                            article_id: articleId,
                            image_id: image.id,
                          })
                        }
                        className="absolute right-1 top-1 hidden rounded bg-red-500 p-1 text-white group-hover:block"
                      >
                        <TrashIcon className="h-4 w-4" />
                      </button>
                      <p className="truncate p-1 text-xs text-gray-500">
                        {image.original_filename}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="flex justify-end gap-3 border-t border-gray-200 px-6 py-4">
            <button
              type="button"
              onClick={onClose}
              className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={createArticle.isPending || updateArticle.isPending}
              className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
            >
              {createArticle.isPending || updateArticle.isPending
                ? 'Saving...'
                : articleId
                  ? 'Update'
                  : 'Create'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// Wrapper component that fetches initial data
export default function ArticleEditor({
  workspaceId,
  articleId,
  onClose,
  onSuccess,
}: ArticleEditorProps) {
  // Fetch article if editing
  const articleQuery = useQuery({
    queryKey: ['article', articleId],
    queryFn: () => contentAPI.getArticle(articleId!),
    enabled: !!articleId,
  });

  // Show loading state while fetching
  if (articleId && articleQuery.isLoading) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
        <div className="flex h-64 w-64 items-center justify-center rounded-lg bg-white">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-600 border-t-transparent"></div>
        </div>
      </div>
    );
  }

  // Compute initial data from query
  const initialData = articleQuery.data
    ? {
        title: articleQuery.data.title,
        content: articleQuery.data.content,
        status: articleQuery.data.status,
      }
    : {
        title: '',
        content: '',
        status: 'draft',
      };

  return (
    <ArticleEditorForm
      workspaceId={workspaceId}
      articleId={articleId}
      initialData={initialData}
      onClose={onClose}
      onSuccess={onSuccess}
    />
  );
}
