/**
 * Authentication hook
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import * as authAPI from '../api/auth';

export function useAuth() {
  const queryClient = useQueryClient();

  const login = useMutation({
    mutationFn: authAPI.login,
    onSuccess: (data) => {
      localStorage.setItem('jwt_token', data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);
      queryClient.invalidateQueries({ queryKey: ['me'] });
    },
  });

  const register = useMutation({
    mutationFn: authAPI.register,
  });

  const me = useQuery({
    queryKey: ['me'],
    queryFn: authAPI.getMe,
    enabled: !!localStorage.getItem('jwt_token'),
    retry: false,
  });

  const logout = () => {
    localStorage.removeItem('jwt_token');
    localStorage.removeItem('refresh_token');
    queryClient.clear();
    window.location.href = '/login';
  };

  const isAuthenticated = !!localStorage.getItem('jwt_token');

  return {
    login,
    register,
    me,
    logout,
    isAuthenticated,
  };
}
