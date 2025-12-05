/**
 * Workspace store for current workspace state
 */
import { useSyncExternalStore } from 'react';

interface WorkspaceState {
  currentWorkspaceId: string | null;
}

const STORAGE_KEY = 'current_workspace_id';

const initialState: WorkspaceState = {
  currentWorkspaceId: localStorage.getItem(STORAGE_KEY),
};

let workspaceState = { ...initialState };
const listeners: Set<() => void> = new Set();

function getSnapshot() {
  return workspaceState;
}

function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

function setCurrentWorkspace(workspaceId: string | null) {
  if (workspaceId) {
    localStorage.setItem(STORAGE_KEY, workspaceId);
  } else {
    localStorage.removeItem(STORAGE_KEY);
  }
  workspaceState = { currentWorkspaceId: workspaceId };
  listeners.forEach((listener) => listener());
}

export function useWorkspaceStore() {
  const state = useSyncExternalStore(subscribe, getSnapshot);
  
  return {
    currentWorkspaceId: state.currentWorkspaceId,
    setCurrentWorkspace,
  };
}
