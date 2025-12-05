/**
 * Settings page
 */
import { useState } from 'react';
import WorkspaceList from '../components/workspace/WorkspaceList';
import { useSites } from '../hooks/useWorkspace';
import { useWorkspaceStore } from '../store/workspaceStore';
import { PlusIcon, TrashIcon } from '@heroicons/react/24/outline';

export default function Settings() {
  const { currentWorkspaceId } = useWorkspaceStore();
  const { sites, createSite, deleteSite } = useSites(
    currentWorkspaceId || undefined
  );
  const [showSiteForm, setShowSiteForm] = useState(false);
  const [siteFormData, setSiteFormData] = useState({
    name: '',
    domain: '',
    description: '',
  });
  const [siteError, setSiteError] = useState('');

  const handleCreateSite = async (e: React.FormEvent) => {
    e.preventDefault();
    setSiteError('');

    if (!currentWorkspaceId) {
      setSiteError('Please select a workspace first');
      return;
    }

    try {
      await createSite.mutateAsync({
        workspace_id: currentWorkspaceId,
        data: siteFormData,
      });
      setShowSiteForm(false);
      setSiteFormData({ name: '', domain: '', description: '' });
    } catch {
      setSiteError('Failed to create site');
    }
  };

  const handleDeleteSite = async (id: string) => {
    if (window.confirm('Are you sure you want to delete this site?')) {
      await deleteSite.mutateAsync(id);
    }
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-500">
          Manage your workspaces, sites, and preferences.
        </p>
      </div>

      {/* Workspaces Section */}
      <section>
        <h2 className="mb-4 text-lg font-semibold text-gray-900">Workspaces</h2>
        <WorkspaceList />
      </section>

      {/* Sites Section */}
      <section>
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">Sites</h2>
          {currentWorkspaceId && (
            <button
              onClick={() => setShowSiteForm(true)}
              className="flex items-center gap-2 rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
            >
              <PlusIcon className="h-5 w-5" />
              Add Site
            </button>
          )}
        </div>

        {!currentWorkspaceId ? (
          <div className="rounded-lg border border-gray-200 bg-white p-6 text-center">
            <p className="text-gray-500">
              Select a workspace to manage sites.
            </p>
          </div>
        ) : (
          <>
            {showSiteForm && (
              <div className="mb-4 rounded-lg border border-gray-200 bg-white p-6">
                <h3 className="mb-4 text-lg font-medium text-gray-900">
                  Add New Site
                </h3>
                <form onSubmit={handleCreateSite} className="space-y-4">
                  {siteError && (
                    <div className="rounded-md bg-red-50 p-3">
                      <p className="text-sm text-red-700">{siteError}</p>
                    </div>
                  )}

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">
                        Site Name
                      </label>
                      <input
                        type="text"
                        value={siteFormData.name}
                        onChange={(e) =>
                          setSiteFormData({
                            ...siteFormData,
                            name: e.target.value,
                          })
                        }
                        required
                        className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-indigo-500 sm:text-sm"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">
                        Domain
                      </label>
                      <input
                        type="text"
                        value={siteFormData.domain}
                        onChange={(e) =>
                          setSiteFormData({
                            ...siteFormData,
                            domain: e.target.value,
                          })
                        }
                        required
                        placeholder="example.com"
                        className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-indigo-500 sm:text-sm"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700">
                      Description (optional)
                    </label>
                    <textarea
                      value={siteFormData.description}
                      onChange={(e) =>
                        setSiteFormData({
                          ...siteFormData,
                          description: e.target.value,
                        })
                      }
                      rows={2}
                      className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-indigo-500 sm:text-sm"
                    />
                  </div>

                  <div className="flex justify-end gap-3">
                    <button
                      type="button"
                      onClick={() => {
                        setShowSiteForm(false);
                        setSiteFormData({ name: '', domain: '', description: '' });
                      }}
                      className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={createSite.isPending}
                      className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
                    >
                      {createSite.isPending ? 'Adding...' : 'Add Site'}
                    </button>
                  </div>
                </form>
              </div>
            )}

            {sites.isLoading ? (
              <div className="flex items-center justify-center py-12">
                <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-600 border-t-transparent"></div>
              </div>
            ) : sites.data && sites.data.length > 0 ? (
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {sites.data.map((site) => (
                  <div
                    key={site.id}
                    className="rounded-lg border border-gray-200 bg-white p-6"
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <h3 className="font-medium text-gray-900">
                          {site.name}
                        </h3>
                        <p className="text-sm text-indigo-600">{site.domain}</p>
                        {site.description && (
                          <p className="mt-2 text-sm text-gray-500">
                            {site.description}
                          </p>
                        )}
                      </div>
                      <div className="flex gap-1">
                        <button
                          onClick={() => handleDeleteSite(site.id)}
                          className="rounded p-1 text-gray-400 hover:bg-red-100 hover:text-red-600"
                        >
                          <TrashIcon className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="rounded-lg border-2 border-dashed border-gray-300 p-12 text-center">
                <p className="text-gray-500">No sites yet</p>
                <button
                  onClick={() => setShowSiteForm(true)}
                  className="mt-2 text-indigo-600 hover:text-indigo-500"
                >
                  Add your first site
                </button>
              </div>
            )}
          </>
        )}
      </section>
    </div>
  );
}
