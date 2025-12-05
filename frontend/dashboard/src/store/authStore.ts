/**
 * Auth store for persisting authentication state
 */
import type { User } from '../api/auth';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
}

const initialState: AuthState = {
  user: null,
  isAuthenticated: !!localStorage.getItem('jwt_token'),
};

let authState = { ...initialState };
const listeners: Set<() => void> = new Set();

export const authStore = {
  getState: () => authState,
  
  setUser: (user: User | null) => {
    authState = { ...authState, user, isAuthenticated: !!user };
    listeners.forEach((listener) => listener());
  },
  
  logout: () => {
    localStorage.removeItem('jwt_token');
    localStorage.removeItem('refresh_token');
    authState = { user: null, isAuthenticated: false };
    listeners.forEach((listener) => listener());
  },
  
  subscribe: (listener: () => void) => {
    listeners.add(listener);
    return () => listeners.delete(listener);
  },
};
