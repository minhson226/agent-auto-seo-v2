/**
 * System diagnostics API functions
 */
import apiClient from './client';

export interface ServiceHealth {
  name: string;
  status: string;
  url: string;
  response_time_ms?: number;
  details?: any;
  error?: string;
}

export interface BuildInfo {
  version: string;
  git_commit: string;
  build_date: string;
  image_tag: string;
}

export interface EnvironmentInfo {
  environment: string;
  debug_mode: boolean;
  log_level: string;
  cors_origins: string[];
}

export interface Diagnostics {
  timestamp: string;
  overall_status: string;
  healthy_services: number;
  total_services: number;
  services: ServiceHealth[];
  environment: EnvironmentInfo;
  build: BuildInfo;
}

export interface HealthSummary {
  healthy: number;
  total: number;
  services: Record<string, { status: string; response_time_ms?: number }>;
}

export async function getDiagnostics(): Promise<Diagnostics> {
  const response = await apiClient.get<Diagnostics>('/api/v1/diagnostics/');
  return response.data;
}

export async function getHealthSummary(): Promise<HealthSummary> {
  const response = await apiClient.get<HealthSummary>(
    '/api/v1/diagnostics/health-summary'
  );
  return response.data;
}
