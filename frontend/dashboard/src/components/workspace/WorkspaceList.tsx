/**
 * Workspace list component
 */
import { useState } from 'react';
import {
  PlusIcon,
  PencilIcon,
  TrashIcon,
} from '@heroicons/react/24/outline';
import { useWorkspace } from '../../hooks/useWorkspace';
import WorkspaceForm from './WorkspaceForm';

export default function WorkspaceList() {
  const { workspaces, deleteWorkspace, setCurrentWorkspace, currentWorkspaceId } =
    useWorkspace();
  const [showForm, setShowForm] = useState(false);
  const [editingWorkspace, setEditingWorkspace] = useState<string | null>(null);

  const handleDelete = async (id: string) => {
    if (window.confirm('Are you sure you want to delete this workspace?')) {
      await deleteWorkspace.mutateAsync(id);
      if (currentWorkspaceId === id) {
        setCurrentWorkspace(null);
      }
    }
  };

  if (workspaces.isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-600 border-t-transparent"></div>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">Workspaces</h2>
        <button
          onClick={() => setShowForm(true)}
          className="flex items-center gap-2 rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
        >
          <PlusIcon className="h-5 w-5" />
          New Workspace
        </button>
      </div>

      {showForm && (
        <WorkspaceForm
          onClose={() => setShowForm(false)}
          onSuccess={() => setShowForm(false)}
        />
      )}

      {editingWorkspace && (
        <WorkspaceForm
          workspaceId={editingWorkspace}
          onClose={() => setEditingWorkspace(null)}
          onSuccess={() => setEditingWorkspace(null)}
        />
      )}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {workspaces.data?.map((workspace) => (
          <div
            key={workspace.id}
            className={`relative rounded-lg border bg-white p-6 shadow-sm ${
              workspace.id === currentWorkspaceId
                ? 'border-indigo-500 ring-2 ring-indigo-500'
                : 'border-gray-200 hover:border-gray-300'
            }`}
          >
            <div className="flex items-start justify-between">
              <div
                className="flex-1 cursor-pointer"
                onClick={() => setCurrentWorkspace(workspace.id)}
              >
                <h3 className="font-medium text-gray-900">{workspace.name}</h3>
                <p className="mt-1 text-sm text-gray-500">
                  {workspace.slug}
                </p>
                {workspace.description && (
                  <p className="mt-2 text-sm text-gray-600">
                    {workspace.description}
                  </p>
                )}
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setEditingWorkspace(workspace.id)}
                  className="rounded p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
                >
                  <PencilIcon className="h-4 w-4" />
                </button>
                <button
                  onClick={() => handleDelete(workspace.id)}
                  className="rounded p-1 text-gray-400 hover:bg-red-100 hover:text-red-600"
                >
                  <TrashIcon className="h-4 w-4" />
                </button>
              </div>
            </div>
            {workspace.id === currentWorkspaceId && (
              <span className="absolute bottom-4 right-4 text-xs font-medium text-indigo-600">
                Active
              </span>
            )}
          </div>
        ))}
      </div>

      {workspaces.data?.length === 0 && (
        <div className="rounded-lg border-2 border-dashed border-gray-300 p-12 text-center">
          <p className="text-gray-500">No workspaces yet</p>
          <button
            onClick={() => setShowForm(true)}
            className="mt-4 text-indigo-600 hover:text-indigo-500"
          >
            Create your first workspace
          </button>
        </div>
      )}
    </div>
  );
}
