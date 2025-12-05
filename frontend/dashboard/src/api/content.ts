/**
 * Content/Articles API functions
 */
import apiClient from './client';

export interface ContentPlan {
  id: string;
  workspace_id: string;
  title: string;
  target_keywords: string[];
  estimated_word_count: number;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface Article {
  id: string;
  workspace_id: string;
  plan_id: string | null;
  title: string;
  content: string;
  status: string;
  ai_model_used: string | null;
  cost_usd: number | null;
  word_count: number | null;
  metadata: Record<string, unknown> | null;
  images: ArticleImage[];
  created_at: string;
  updated_at: string;
}

export interface ArticleListItem {
  id: string;
  workspace_id: string;
  plan_id: string | null;
  title: string;
  status: string;
  ai_model_used: string | null;
  cost_usd: number | null;
  word_count: number | null;
  image_count: number;
  created_at: string;
  updated_at: string;
}

export interface ArticleImage {
  id: string;
  article_id: string;
  filename: string;
  original_filename: string;
  content_type: string;
  size_bytes: number;
  storage_path: string;
  created_at: string;
}

export interface PaginatedArticles {
  data: ArticleListItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface PaginatedContentPlans {
  data: ContentPlan[];
  total: number;
  page: number;
  page_size: number;
}

export async function getContentPlans(
  workspace_id: string,
  page: number = 1,
  page_size: number = 20
): Promise<PaginatedContentPlans> {
  const params = new URLSearchParams({
    workspace_id,
    page: page.toString(),
    page_size: page_size.toString(),
  });
  const response = await apiClient.get<PaginatedContentPlans>(
    `/api/v1/content-plans?${params.toString()}`
  );
  return response.data;
}

export async function createContentPlan(data: {
  workspace_id: string;
  title: string;
  target_keywords: string[];
  estimated_word_count: number;
}): Promise<ContentPlan> {
  const response = await apiClient.post<ContentPlan>(
    '/api/v1/content-plans',
    data
  );
  return response.data;
}

export async function getContentPlan(plan_id: string): Promise<ContentPlan> {
  const response = await apiClient.get<ContentPlan>(
    `/api/v1/content-plans/${plan_id}`
  );
  return response.data;
}

export async function updateContentPlan(
  plan_id: string,
  data: Partial<ContentPlan>
): Promise<ContentPlan> {
  const response = await apiClient.put<ContentPlan>(
    `/api/v1/content-plans/${plan_id}`,
    data
  );
  return response.data;
}

export async function deleteContentPlan(plan_id: string): Promise<void> {
  await apiClient.delete(`/api/v1/content-plans/${plan_id}`);
}

// Articles
export async function getArticles(
  workspace_id: string,
  page: number = 1,
  page_size: number = 20,
  status?: string
): Promise<PaginatedArticles> {
  const params = new URLSearchParams({
    workspace_id,
    page: page.toString(),
    page_size: page_size.toString(),
  });
  if (status) {
    params.append('status', status);
  }
  const response = await apiClient.get<PaginatedArticles>(
    `/api/v1/articles?${params.toString()}`
  );
  return response.data;
}

export async function getArticle(article_id: string): Promise<Article> {
  const response = await apiClient.get<Article>(
    `/api/v1/articles/${article_id}`
  );
  return response.data;
}

export async function createArticle(data: {
  workspace_id: string;
  title: string;
  content: string;
  plan_id?: string;
}): Promise<Article> {
  const response = await apiClient.post<Article>('/api/v1/articles', data);
  return response.data;
}

export async function updateArticle(
  article_id: string,
  data: { title?: string; content?: string; status?: string }
): Promise<Article> {
  const response = await apiClient.put<Article>(
    `/api/v1/articles/${article_id}`,
    data
  );
  return response.data;
}

export async function deleteArticle(article_id: string): Promise<void> {
  await apiClient.delete(`/api/v1/articles/${article_id}`);
}

export async function generateArticle(plan_id: string): Promise<Article> {
  const response = await apiClient.post<Article>('/api/v1/articles/generate', {
    plan_id,
  });
  return response.data;
}

export async function uploadArticleImage(
  article_id: string,
  file: File
): Promise<ArticleImage> {
  const formData = new FormData();
  formData.append('file', file);
  const response = await apiClient.post<ArticleImage>(
    `/api/v1/articles/${article_id}/images`,
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }
  );
  return response.data;
}

export async function deleteArticleImage(
  article_id: string,
  image_id: string
): Promise<void> {
  await apiClient.delete(`/api/v1/articles/${article_id}/images/${image_id}`);
}
