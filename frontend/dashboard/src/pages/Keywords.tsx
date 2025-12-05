/**
 * Keywords management page
 */
import KeywordUpload from '../components/keywords/KeywordUpload';
import KeywordList from '../components/keywords/KeywordList';
import { useWorkspaceStore } from '../store/workspaceStore';

export default function Keywords() {
  const { currentWorkspaceId } = useWorkspaceStore();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Keywords</h1>
        <p className="text-gray-500">
          Upload and manage your keyword lists for SEO research and content planning.
        </p>
      </div>

      {!currentWorkspaceId ? (
        <div className="rounded-lg border border-gray-200 bg-white p-12 text-center">
          <p className="text-gray-500">
            Please select a workspace to manage keywords.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          <div className="lg:col-span-1">
            <KeywordUpload />
          </div>
          <div className="lg:col-span-2">
            <KeywordList />
          </div>
        </div>
      )}
    </div>
  );
}
