/**
 * Clustering page with drag-drop interface
 */
import DragDropClustering from '../components/clustering/DragDropClustering';
import { useWorkspaceStore } from '../store/workspaceStore';

export default function Clustering() {
  const { currentWorkspaceId } = useWorkspaceStore();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Keyword Clustering</h1>
        <p className="text-gray-500">
          Organize your keywords into topical clusters by dragging them into groups.
        </p>
      </div>

      {!currentWorkspaceId ? (
        <div className="rounded-lg border border-gray-200 bg-white p-12 text-center">
          <p className="text-gray-500">
            Please select a workspace to manage clusters.
          </p>
        </div>
      ) : (
        <DragDropClustering />
      )}
    </div>
  );
}
