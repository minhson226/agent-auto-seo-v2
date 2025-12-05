/**
 * Workspace form component
 */
import { useState } from 'react';
import { XMarkIcon } from '@heroicons/react/24/outline';
import { useWorkspace } from '../../hooks/useWorkspace';

interface WorkspaceFormProps {
  workspaceId?: string;
  onClose: () => void;
  onSuccess: () => void;
}

interface FormData {
  name: string;
  slug: string;
  description: string;
}

// Form component that receives initial data
function WorkspaceFormContent({
  workspaceId,
  initialData,
  onClose,
  onSuccess,
}: WorkspaceFormProps & { initialData: FormData }) {
  const { createWorkspace, updateWorkspace } = useWorkspace();
  const [error, setError] = useState('');
  const [formData, setFormData] = useState(initialData);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
      // Auto-generate slug from name
      ...(name === 'name' && !workspaceId
        ? {
            slug: value
              .toLowerCase()
              .replace(/[^a-z0-9]+/g, '-')
              .replace(/^-|-$/g, ''),
          }
        : {}),
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    try {
      if (workspaceId) {
        await updateWorkspace.mutateAsync({
          workspace_id: workspaceId,
          data: {
            name: formData.name,
            description: formData.description || undefined,
          },
        });
      } else {
        await createWorkspace.mutateAsync({
          name: formData.name,
          slug: formData.slug,
          description: formData.description || undefined,
        });
      }
      onSuccess();
    } catch {
      setError(
        workspaceId
          ? 'Failed to update workspace'
          : 'Failed to create workspace. Slug may already be in use.'
      );
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-lg font-medium text-gray-900">
            {workspaceId ? 'Edit Workspace' : 'New Workspace'}
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
              htmlFor="name"
              className="block text-sm font-medium text-gray-700"
            >
              Name
            </label>
            <input
              type="text"
              id="name"
              name="name"
              required
              value={formData.name}
              onChange={handleChange}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-indigo-500 sm:text-sm"
            />
          </div>

          {!workspaceId && (
            <div>
              <label
                htmlFor="slug"
                className="block text-sm font-medium text-gray-700"
              >
                Slug
              </label>
              <input
                type="text"
                id="slug"
                name="slug"
                required
                value={formData.slug}
                onChange={handleChange}
                pattern="[a-z0-9-]+"
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-indigo-500 sm:text-sm"
              />
              <p className="mt-1 text-xs text-gray-500">
                Only lowercase letters, numbers, and hyphens
              </p>
            </div>
          )}

          <div>
            <label
              htmlFor="description"
              className="block text-sm font-medium text-gray-700"
            >
              Description
            </label>
            <textarea
              id="description"
              name="description"
              rows={3}
              value={formData.description}
              onChange={handleChange}
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
              disabled={createWorkspace.isPending || updateWorkspace.isPending}
              className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
            >
              {createWorkspace.isPending || updateWorkspace.isPending
                ? 'Saving...'
                : workspaceId
                  ? 'Update'
                  : 'Create'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// Wrapper component that fetches workspace data and computes initial values
export default function WorkspaceForm({
  workspaceId,
  onClose,
  onSuccess,
}: WorkspaceFormProps) {
  const { workspaces } = useWorkspace();
  
  const existingWorkspace = workspaces.data?.find((w) => w.id === workspaceId);
  
  // Show loading while fetching
  if (workspaceId && workspaces.isLoading) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
        <div className="flex h-32 w-32 items-center justify-center rounded-lg bg-white">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-600 border-t-transparent"></div>
        </div>
      </div>
    );
  }
  
  // Compute initial data
  const initialData: FormData = existingWorkspace
    ? {
        name: existingWorkspace.name,
        slug: existingWorkspace.slug,
        description: existingWorkspace.description || '',
      }
    : {
        name: '',
        slug: '',
        description: '',
      };

  return (
    <WorkspaceFormContent
      workspaceId={workspaceId}
      initialData={initialData}
      onClose={onClose}
      onSuccess={onSuccess}
    />
  );
}
