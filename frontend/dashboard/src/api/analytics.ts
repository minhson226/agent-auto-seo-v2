/**
 * Analytics API functions
 */
import apiClient from './client';

export interface PerformanceDataInput {
  url: string;
  date: string;
  impressions: number;
  clicks: number;
  position: number;
  workspace_id?: string;
  article_id?: string;
  ai_model_used?: string;
  prompt_id?: string;
  cost_usd?: number;
}

export interface Summary {
  workspace_id: string;
  date_from: string;
  date_to: string;
  total_impressions: number;
  total_clicks: number;
  avg_position: number;
  articles_ranking: number;
  top_articles: TopArticle[];
}

export interface TopArticle {
  url: string;
  impressions: number;
  clicks: number;
  position: number;
}

export interface ArticlePerformance {
  date: string;
  impressions: number;
  clicks: number;
  position: number;
}

export interface ArticlePerformanceResponse {
  article_id: string;
  data: ArticlePerformance[];
}

export async function recordPerformance(
  data: PerformanceDataInput
): Promise<{ success: boolean; message: string; url_hash: string }> {
  const response = await apiClient.post<{
    success: boolean;
    message: string;
    url_hash: string;
  }>('/api/v1/analytics/performance', data);
  return response.data;
}

export async function getSummary(
  workspace_id: string,
  date_from?: string,
  date_to?: string
): Promise<Summary> {
  const params = new URLSearchParams({ workspace_id });
  if (date_from) {
    params.append('date_from', date_from);
  }
  if (date_to) {
    params.append('date_to', date_to);
  }
  const response = await apiClient.get<Summary>(
    `/api/v1/analytics/summary?${params.toString()}`
  );
  return response.data;
}

export async function getArticlePerformance(
  article_id: string,
  days: number = 30
): Promise<ArticlePerformanceResponse> {
  const params = new URLSearchParams({ days: days.toString() });
  const response = await apiClient.get<ArticlePerformanceResponse>(
    `/api/v1/analytics/articles/${article_id}/performance?${params.toString()}`
  );
  return response.data;
}
