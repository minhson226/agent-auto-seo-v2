/**
 * Workspaces API functions
 */
import apiClient from './client';

export interface Workspace {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  owner_id: string;
  created_at: string;
  updated_at: string;
}

export interface WorkspaceMember {
  user_id: string;
  workspace_id: string;
  role: string;
  joined_at: string;
  email?: string;
  full_name?: string;
}

export interface Site {
  id: string;
  name: string;
  domain: string;
  workspace_id: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export async function getWorkspaces(): Promise<Workspace[]> {
  const response = await apiClient.get<Workspace[]>('/api/v1/workspaces');
  return response.data;
}

export async function getWorkspace(workspace_id: string): Promise<Workspace> {
  const response = await apiClient.get<Workspace>(
    `/api/v1/workspaces/${workspace_id}`
  );
  return response.data;
}

export async function createWorkspace(data: {
  name: string;
  slug: string;
  description?: string;
}): Promise<Workspace> {
  const response = await apiClient.post<Workspace>('/api/v1/workspaces', data);
  return response.data;
}

export async function updateWorkspace(
  workspace_id: string,
  data: { name?: string; description?: string }
): Promise<Workspace> {
  const response = await apiClient.put<Workspace>(
    `/api/v1/workspaces/${workspace_id}`,
    data
  );
  return response.data;
}

export async function deleteWorkspace(workspace_id: string): Promise<void> {
  await apiClient.delete(`/api/v1/workspaces/${workspace_id}`);
}

export async function getWorkspaceMembers(
  workspace_id: string
): Promise<WorkspaceMember[]> {
  const response = await apiClient.get<WorkspaceMember[]>(
    `/api/v1/workspaces/${workspace_id}/members`
  );
  return response.data;
}

export async function addWorkspaceMember(
  workspace_id: string,
  data: { email: string; role: string }
): Promise<WorkspaceMember> {
  const response = await apiClient.post<WorkspaceMember>(
    `/api/v1/workspaces/${workspace_id}/members`,
    data
  );
  return response.data;
}

export async function removeWorkspaceMember(
  workspace_id: string,
  user_id: string
): Promise<void> {
  await apiClient.delete(
    `/api/v1/workspaces/${workspace_id}/members/${user_id}`
  );
}

// Sites
export async function getSites(workspace_id: string): Promise<Site[]> {
  const response = await apiClient.get<Site[]>(
    `/api/v1/workspaces/${workspace_id}/sites`
  );
  return response.data;
}

export async function getSite(site_id: string): Promise<Site> {
  const response = await apiClient.get<Site>(`/api/v1/sites/${site_id}`);
  return response.data;
}

export async function createSite(
  workspace_id: string,
  data: { name: string; domain: string; description?: string }
): Promise<Site> {
  const response = await apiClient.post<Site>(
    `/api/v1/workspaces/${workspace_id}/sites`,
    data
  );
  return response.data;
}

export async function updateSite(
  site_id: string,
  data: { name?: string; domain?: string; description?: string }
): Promise<Site> {
  const response = await apiClient.put<Site>(`/api/v1/sites/${site_id}`, data);
  return response.data;
}

export async function deleteSite(site_id: string): Promise<void> {
  await apiClient.delete(`/api/v1/sites/${site_id}`);
}
