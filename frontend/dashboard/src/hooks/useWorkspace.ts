/**
 * Workspace hook
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import * as workspacesAPI from '../api/workspaces';
import { useWorkspaceStore } from '../store/workspaceStore';

export function useWorkspace() {
  const queryClient = useQueryClient();
  const { currentWorkspaceId, setCurrentWorkspace } = useWorkspaceStore();

  const workspaces = useQuery({
    queryKey: ['workspaces'],
    queryFn: workspacesAPI.getWorkspaces,
  });

  const currentWorkspace = useQuery({
    queryKey: ['workspace', currentWorkspaceId],
    queryFn: () => workspacesAPI.getWorkspace(currentWorkspaceId!),
    enabled: !!currentWorkspaceId,
  });

  const createWorkspace = useMutation({
    mutationFn: workspacesAPI.createWorkspace,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workspaces'] });
    },
  });

  const updateWorkspace = useMutation({
    mutationFn: ({
      workspace_id,
      data,
    }: {
      workspace_id: string;
      data: { name?: string; description?: string };
    }) => workspacesAPI.updateWorkspace(workspace_id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workspaces'] });
      queryClient.invalidateQueries({ queryKey: ['workspace'] });
    },
  });

  const deleteWorkspace = useMutation({
    mutationFn: workspacesAPI.deleteWorkspace,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workspaces'] });
    },
  });

  return {
    workspaces,
    currentWorkspace,
    currentWorkspaceId,
    setCurrentWorkspace,
    createWorkspace,
    updateWorkspace,
    deleteWorkspace,
  };
}

export function useSites(workspace_id?: string) {
  const queryClient = useQueryClient();

  const sites = useQuery({
    queryKey: ['sites', workspace_id],
    queryFn: () => workspacesAPI.getSites(workspace_id!),
    enabled: !!workspace_id,
  });

  const createSite = useMutation({
    mutationFn: ({
      workspace_id,
      data,
    }: {
      workspace_id: string;
      data: { name: string; domain: string; description?: string };
    }) => workspacesAPI.createSite(workspace_id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sites'] });
    },
  });

  const updateSite = useMutation({
    mutationFn: ({
      site_id,
      data,
    }: {
      site_id: string;
      data: { name?: string; domain?: string; description?: string };
    }) => workspacesAPI.updateSite(site_id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sites'] });
    },
  });

  const deleteSite = useMutation({
    mutationFn: workspacesAPI.deleteSite,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sites'] });
    },
  });

  return {
    sites,
    createSite,
    updateSite,
    deleteSite,
  };
}
