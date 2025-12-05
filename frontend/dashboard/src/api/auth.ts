/**
 * Authentication API functions
 */
import apiClient from './client';

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  first_name?: string;
  last_name?: string;
}

export interface Token {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface User {
  id: string;
  email: string;
  first_name: string | null;
  last_name: string | null;
  is_active: boolean;
  is_verified: boolean;
  is_superuser: boolean;
  created_at: string;
  updated_at: string;
  full_name: string | null;
}

export async function login(data: LoginRequest): Promise<Token> {
  const response = await apiClient.post<Token>('/api/v1/auth/login', data);
  return response.data;
}

export async function register(data: RegisterRequest): Promise<User> {
  const response = await apiClient.post<User>('/api/v1/auth/register', data);
  return response.data;
}

export async function refreshToken(refresh_token: string): Promise<Token> {
  const response = await apiClient.post<Token>('/api/v1/auth/refresh-token', {
    refresh_token,
  });
  return response.data;
}

export async function getMe(): Promise<User> {
  const response = await apiClient.get<User>('/api/v1/auth/me');
  return response.data;
}
