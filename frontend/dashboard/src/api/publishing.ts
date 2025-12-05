/**
 * Publishing API functions
 */
import apiClient from './client';

export interface PublishRequest {
  article_id: string;
  site_id: string;
  publish_date?: string;
  schedule?: boolean;
}

export interface PublishedArticle {
  id: string;
  article_id: string;
  site_id: string;
  published_url: string | null;
  status: string;
  published_at: string | null;
  scheduled_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface PaginatedPublishedArticles {
  data: PublishedArticle[];
  total: number;
  page: number;
  page_size: number;
}

export async function publishArticle(
  data: PublishRequest
): Promise<PublishedArticle> {
  const response = await apiClient.post<PublishedArticle>(
    '/api/v1/publishing/publish',
    data
  );
  return response.data;
}

export async function schedulePublish(
  data: PublishRequest
): Promise<PublishedArticle> {
  const response = await apiClient.post<PublishedArticle>(
    '/api/v1/publishing/schedule',
    { ...data, schedule: true }
  );
  return response.data;
}

export async function getPublishedArticles(
  workspace_id: string,
  page: number = 1,
  page_size: number = 20,
  status?: string
): Promise<PaginatedPublishedArticles> {
  const params = new URLSearchParams({
    workspace_id,
    page: page.toString(),
    page_size: page_size.toString(),
  });
  if (status) {
    params.append('status', status);
  }
  const response = await apiClient.get<PaginatedPublishedArticles>(
    `/api/v1/publishing?${params.toString()}`
  );
  return response.data;
}

export async function unpublishArticle(publish_id: string): Promise<void> {
  await apiClient.delete(`/api/v1/publishing/${publish_id}`);
}
