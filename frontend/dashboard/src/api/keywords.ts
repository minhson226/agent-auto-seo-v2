/**
 * Keywords API functions
 */
import apiClient from './client';

export interface KeywordList {
  id: string;
  name: string;
  description: string | null;
  workspace_id: string;
  status: string;
  source: string;
  source_file_url: string | null;
  total_keywords: number;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface PaginatedKeywordLists {
  data: KeywordList[];
  total: number;
  page: number;
  page_size: number;
}

export interface KeywordListStats {
  total_keywords: number;
  clustered_keywords: number;
  unclustered_keywords: number;
  avg_search_volume: number | null;
}

export async function getKeywordLists(
  workspace_id: string,
  page: number = 1,
  page_size: number = 20,
  status?: string
): Promise<PaginatedKeywordLists> {
  const params = new URLSearchParams({
    workspace_id,
    page: page.toString(),
    page_size: page_size.toString(),
  });
  if (status) {
    params.append('status_filter', status);
  }
  const response = await apiClient.get<PaginatedKeywordLists>(
    `/api/v1/keyword-lists?${params.toString()}`
  );
  return response.data;
}

export async function getKeywordList(list_id: string): Promise<KeywordList> {
  const response = await apiClient.get<KeywordList>(
    `/api/v1/keyword-lists/${list_id}`
  );
  return response.data;
}

export async function uploadKeywords(
  formData: FormData
): Promise<KeywordList> {
  const response = await apiClient.post<KeywordList>(
    '/api/v1/keyword-lists',
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }
  );
  return response.data;
}

export async function deleteKeywordList(list_id: string): Promise<void> {
  await apiClient.delete(`/api/v1/keyword-lists/${list_id}`);
}

export async function getKeywordListStats(
  list_id: string
): Promise<KeywordListStats> {
  const response = await apiClient.get<KeywordListStats>(
    `/api/v1/keyword-lists/${list_id}/stats`
  );
  return response.data;
}
