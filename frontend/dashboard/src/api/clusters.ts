/**
 * Clusters API functions
 */
import apiClient from './client';

export interface Cluster {
  id: string;
  name: string;
  workspace_id: string;
  keyword_count: number;
  created_at: string;
  updated_at: string;
}

export interface Keyword {
  id: string;
  keyword: string;
  cluster_id: string | null;
  search_volume: number | null;
  difficulty: number | null;
}

export interface PaginatedClusters {
  data: Cluster[];
  total: number;
  page: number;
  page_size: number;
}

export async function getClusters(
  workspace_id: string,
  page: number = 1,
  page_size: number = 20
): Promise<PaginatedClusters> {
  const params = new URLSearchParams({
    workspace_id,
    page: page.toString(),
    page_size: page_size.toString(),
  });
  const response = await apiClient.get<PaginatedClusters>(
    `/api/v1/clusters?${params.toString()}`
  );
  return response.data;
}

export async function createCluster(data: {
  name: string;
  workspace_id: string;
}): Promise<Cluster> {
  const response = await apiClient.post<Cluster>('/api/v1/clusters', data);
  return response.data;
}

export async function getCluster(cluster_id: string): Promise<Cluster> {
  const response = await apiClient.get<Cluster>(
    `/api/v1/clusters/${cluster_id}`
  );
  return response.data;
}

export async function updateCluster(
  cluster_id: string,
  data: { name: string }
): Promise<Cluster> {
  const response = await apiClient.put<Cluster>(
    `/api/v1/clusters/${cluster_id}`,
    data
  );
  return response.data;
}

export async function deleteCluster(cluster_id: string): Promise<void> {
  await apiClient.delete(`/api/v1/clusters/${cluster_id}`);
}

export async function addKeywordToCluster(
  cluster_id: string,
  keyword_id: string
): Promise<void> {
  await apiClient.post(`/api/v1/clusters/${cluster_id}/keywords`, {
    keyword_id,
  });
}

export async function removeKeywordFromCluster(
  cluster_id: string,
  keyword_id: string
): Promise<void> {
  await apiClient.delete(
    `/api/v1/clusters/${cluster_id}/keywords/${keyword_id}`
  );
}

export async function getUnclusteredKeywords(
  workspace_id: string,
  page: number = 1,
  page_size: number = 50
): Promise<{ data: Keyword[]; total: number }> {
  const params = new URLSearchParams({
    workspace_id,
    page: page.toString(),
    page_size: page_size.toString(),
  });
  const response = await apiClient.get<{ data: Keyword[]; total: number }>(
    `/api/v1/keywords/unclustered?${params.toString()}`
  );
  return response.data;
}

export async function getClusterKeywords(
  cluster_id: string,
  page: number = 1,
  page_size: number = 50
): Promise<{ data: Keyword[]; total: number }> {
  const params = new URLSearchParams({
    page: page.toString(),
    page_size: page_size.toString(),
  });
  const response = await apiClient.get<{ data: Keyword[]; total: number }>(
    `/api/v1/clusters/${cluster_id}/keywords?${params.toString()}`
  );
  return response.data;
}
