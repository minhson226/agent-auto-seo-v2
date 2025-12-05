/**
 * Drag-drop clustering interface
 */
import { useState, useEffect, useRef } from 'react';
import { DndProvider, useDrag } from 'react-dnd';
import { HTML5Backend } from 'react-dnd-html5-backend';
import { PlusIcon } from '@heroicons/react/24/outline';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import * as clustersAPI from '../../api/clusters';
import { useWorkspaceStore } from '../../store/workspaceStore';
import ClusterCard from './ClusterCard';
import type { Keyword } from '../../api/clusters';

function DraggableKeyword({ keyword }: { keyword: Keyword }) {
  const ref = useRef<HTMLDivElement>(null);
  const [{ isDragging }, drag] = useDrag(
    () => ({
      type: 'keyword',
      item: { id: keyword.id },
      collect: (monitor) => ({
        isDragging: !!monitor.isDragging(),
      }),
    }),
    [keyword.id]
  );

  useEffect(() => {
    if (ref.current) {
      drag(ref.current);
    }
  }, [drag]);

  return (
    <div
      ref={ref}
      className={`cursor-grab rounded bg-white px-3 py-2 text-sm shadow-sm hover:shadow ${
        isDragging ? 'opacity-50' : ''
      }`}
    >
      {keyword.keyword}
      {keyword.search_volume && (
        <span className="ml-2 text-xs text-gray-400">
          {keyword.search_volume.toLocaleString()}
        </span>
      )}
    </div>
  );
}

function KeywordPool({ keywords }: { keywords: Keyword[] }) {
  return (
    <div className="flex-1 rounded-lg border border-gray-200 bg-gray-50 p-4">
      <h3 className="mb-4 text-lg font-medium text-gray-900">
        Unclustered Keywords
      </h3>
      <div className="max-h-[600px] space-y-2 overflow-y-auto">
        {keywords.map((keyword) => (
          <DraggableKeyword key={keyword.id} keyword={keyword} />
        ))}
        {keywords.length === 0 && (
          <p className="py-8 text-center text-gray-400">
            All keywords are clustered
          </p>
        )}
      </div>
    </div>
  );
}

export default function DragDropClustering() {
  const { currentWorkspaceId } = useWorkspaceStore();
  const queryClient = useQueryClient();
  const [newClusterName, setNewClusterName] = useState('');
  const [showNewCluster, setShowNewCluster] = useState(false);
  const [clusterKeywords, setClusterKeywords] = useState<
    Record<string, Keyword[]>
  >({});

  // Fetch clusters
  const clustersQuery = useQuery({
    queryKey: ['clusters', currentWorkspaceId],
    queryFn: () => clustersAPI.getClusters(currentWorkspaceId!, 1, 100),
    enabled: !!currentWorkspaceId,
  });

  // Fetch unclustered keywords
  const unclusteredQuery = useQuery({
    queryKey: ['unclustered-keywords', currentWorkspaceId],
    queryFn: () =>
      clustersAPI.getUnclusteredKeywords(currentWorkspaceId!, 1, 100),
    enabled: !!currentWorkspaceId,
  });

  // Fetch keywords for each cluster
  useEffect(() => {
    const fetchClusterKeywords = async () => {
      if (!clustersQuery.data?.data) return;

      const keywordsMap: Record<string, Keyword[]> = {};
      for (const cluster of clustersQuery.data.data) {
        try {
          const result = await clustersAPI.getClusterKeywords(cluster.id);
          keywordsMap[cluster.id] = result.data;
        } catch {
          keywordsMap[cluster.id] = [];
        }
      }
      setClusterKeywords(keywordsMap);
    };

    fetchClusterKeywords();
  }, [clustersQuery.data]);

  // Mutations
  const createCluster = useMutation({
    mutationFn: clustersAPI.createCluster,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clusters'] });
      setNewClusterName('');
      setShowNewCluster(false);
    },
  });

  const deleteCluster = useMutation({
    mutationFn: clustersAPI.deleteCluster,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clusters'] });
      queryClient.invalidateQueries({ queryKey: ['unclustered-keywords'] });
    },
  });

  const addKeyword = useMutation({
    mutationFn: ({
      clusterId,
      keywordId,
    }: {
      clusterId: string;
      keywordId: string;
    }) => clustersAPI.addKeywordToCluster(clusterId, keywordId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clusters'] });
      queryClient.invalidateQueries({ queryKey: ['unclustered-keywords'] });
    },
  });

  const removeKeyword = useMutation({
    mutationFn: ({
      clusterId,
      keywordId,
    }: {
      clusterId: string;
      keywordId: string;
    }) => clustersAPI.removeKeywordFromCluster(clusterId, keywordId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clusters'] });
      queryClient.invalidateQueries({ queryKey: ['unclustered-keywords'] });
    },
  });

  const handleDrop = (keywordId: string, clusterId: string) => {
    addKeyword.mutate({ clusterId, keywordId });
  };

  const handleCreateCluster = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newClusterName.trim() || !currentWorkspaceId) return;
    createCluster.mutate({
      name: newClusterName,
      workspace_id: currentWorkspaceId,
    });
  };

  if (!currentWorkspaceId) {
    return (
      <div className="rounded-lg border border-gray-200 bg-white p-12 text-center">
        <p className="text-gray-500">Please select a workspace first</p>
      </div>
    );
  }

  if (clustersQuery.isLoading || unclusteredQuery.isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-600 border-t-transparent"></div>
      </div>
    );
  }

  return (
    <DndProvider backend={HTML5Backend}>
      <div className="flex gap-6">
        {/* Keyword Pool */}
        <KeywordPool keywords={unclusteredQuery.data?.data || []} />

        {/* Clusters */}
        <div className="flex-1">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-lg font-medium text-gray-900">Clusters</h3>
            <button
              onClick={() => setShowNewCluster(true)}
              className="flex items-center gap-2 rounded-md bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-700"
            >
              <PlusIcon className="h-4 w-4" />
              New Cluster
            </button>
          </div>

          {showNewCluster && (
            <form
              onSubmit={handleCreateCluster}
              className="mb-4 flex gap-2 rounded-lg border border-gray-200 bg-white p-3"
            >
              <input
                type="text"
                value={newClusterName}
                onChange={(e) => setNewClusterName(e.target.value)}
                placeholder="Cluster name"
                className="flex-1 rounded-md border border-gray-300 px-3 py-1.5 text-sm focus:border-indigo-500 focus:outline-none focus:ring-indigo-500"
                autoFocus
              />
              <button
                type="submit"
                disabled={createCluster.isPending}
                className="rounded-md bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
              >
                Create
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowNewCluster(false);
                  setNewClusterName('');
                }}
                className="rounded-md border border-gray-300 px-3 py-1.5 text-sm hover:bg-gray-50"
              >
                Cancel
              </button>
            </form>
          )}

          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            {clustersQuery.data?.data?.map((cluster) => (
              <ClusterCard
                key={cluster.id}
                id={cluster.id}
                name={cluster.name}
                keywords={clusterKeywords[cluster.id] || []}
                onDrop={handleDrop}
                onEdit={() => {
                  const newName = prompt('Enter new name:', cluster.name);
                  if (newName && newName !== cluster.name) {
                    clustersAPI
                      .updateCluster(cluster.id, { name: newName })
                      .then(() => {
                        queryClient.invalidateQueries({ queryKey: ['clusters'] });
                      });
                  }
                }}
                onDelete={() => {
                  if (
                    window.confirm(
                      'Delete this cluster? Keywords will be unclustered.'
                    )
                  ) {
                    deleteCluster.mutate(cluster.id);
                  }
                }}
                onRemoveKeyword={(keywordId) => {
                  removeKeyword.mutate({
                    clusterId: cluster.id,
                    keywordId,
                  });
                }}
              />
            ))}
          </div>

          {(!clustersQuery.data?.data ||
            clustersQuery.data.data.length === 0) &&
            !showNewCluster && (
              <div className="rounded-lg border-2 border-dashed border-gray-300 p-12 text-center">
                <p className="text-gray-500">No clusters yet</p>
                <button
                  onClick={() => setShowNewCluster(true)}
                  className="mt-2 text-indigo-600 hover:text-indigo-500"
                >
                  Create your first cluster
                </button>
              </div>
            )}
        </div>
      </div>
    </DndProvider>
  );
}
