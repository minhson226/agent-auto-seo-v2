/**
 * System Status and Monitoring page
 */
import { useQuery } from '@tanstack/react-query';
import {
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline';
import * as diagnosticsAPI from '../api/diagnostics';

export default function SystemStatus() {
  const { data: diagnostics, isLoading, error } = useQuery({
    queryKey: ['diagnostics'],
    queryFn: diagnosticsAPI.getDiagnostics,
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircleIcon className="h-6 w-6 text-green-500" />;
      case 'degraded':
        return <ExclamationTriangleIcon className="h-6 w-6 text-yellow-500" />;
      case 'unhealthy':
        return <XCircleIcon className="h-6 w-6 text-red-500" />;
      case 'timeout':
        return <ClockIcon className="h-6 w-6 text-orange-500" />;
      default:
        return <XCircleIcon className="h-6 w-6 text-gray-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'bg-green-50 border-green-200';
      case 'degraded':
        return 'bg-yellow-50 border-yellow-200';
      case 'unhealthy':
        return 'bg-red-50 border-red-200';
      case 'timeout':
        return 'bg-orange-50 border-orange-200';
      default:
        return 'bg-gray-50 border-gray-200';
    }
  };

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="text-gray-500">Loading system status...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-md bg-red-50 p-4">
        <div className="flex">
          <XCircleIcon className="h-5 w-5 text-red-400" />
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800">
              Failed to load system diagnostics
            </h3>
            <p className="mt-1 text-sm text-red-700">
              {error instanceof Error ? error.message : 'Unknown error'}
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">System Status</h1>
        <p className="mt-1 text-sm text-gray-500">
          Monitor the health and status of all microservices
        </p>
      </div>

      {/* Overall Status Card */}
      <div
        className={`rounded-lg border-2 p-6 ${getStatusColor(
          diagnostics?.overall_status || 'unknown'
        )}`}
      >
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">
              Overall System Status
            </h2>
            <p className="mt-1 text-sm text-gray-600">
              {diagnostics?.healthy_services} of {diagnostics?.total_services}{' '}
              services are healthy
            </p>
            <p className="mt-1 text-xs text-gray-500">
              Last checked: {new Date(diagnostics?.timestamp || '').toLocaleString()}
            </p>
          </div>
          <div className="flex items-center">
            {getStatusIcon(diagnostics?.overall_status || 'unknown')}
            <span className="ml-2 text-xl font-bold capitalize text-gray-900">
              {diagnostics?.overall_status}
            </span>
          </div>
        </div>
      </div>

      {/* Services Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {diagnostics?.services?.map((service: any) => (
          <div
            key={service.name}
            className={`rounded-lg border p-4 ${getStatusColor(service.status)}`}
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center">
                  {getStatusIcon(service.status)}
                  <h3 className="ml-2 font-semibold text-gray-900">
                    {service.name}
                  </h3>
                </div>
                <p className="mt-1 text-sm text-gray-600 capitalize">
                  Status: {service.status}
                </p>
                {service.response_time_ms && (
                  <p className="mt-1 text-xs text-gray-500">
                    Response time: {service.response_time_ms}ms
                  </p>
                )}
                {service.error && (
                  <p className="mt-1 text-xs text-red-600">{service.error}</p>
                )}
              </div>
            </div>
            <div className="mt-2 text-xs text-gray-500">
              <code className="break-all">{service.url}</code>
            </div>
          </div>
        ))}
      </div>

      {/* Build Information */}
      {diagnostics?.build && (
        <div className="rounded-lg border border-gray-200 bg-white p-6">
          <h3 className="text-lg font-semibold text-gray-900">Build Information</h3>
          <dl className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <dt className="text-sm font-medium text-gray-500">Version</dt>
              <dd className="mt-1 text-sm text-gray-900">
                {diagnostics.build.version}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Git Commit</dt>
              <dd className="mt-1 text-sm text-gray-900">
                <code>{diagnostics.build.git_commit}</code>
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Image Tag</dt>
              <dd className="mt-1 text-sm text-gray-900">
                {diagnostics.build.image_tag}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Build Date</dt>
              <dd className="mt-1 text-sm text-gray-900">
                {diagnostics.build.build_date}
              </dd>
            </div>
          </dl>
        </div>
      )}

      {/* Environment Information */}
      {diagnostics?.environment && (
        <div className="rounded-lg border border-gray-200 bg-white p-6">
          <h3 className="text-lg font-semibold text-gray-900">
            Environment Configuration
          </h3>
          <dl className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <dt className="text-sm font-medium text-gray-500">Environment</dt>
              <dd className="mt-1 text-sm text-gray-900">
                {diagnostics.environment.environment}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Debug Mode</dt>
              <dd className="mt-1 text-sm text-gray-900">
                {diagnostics.environment.debug_mode ? 'Enabled' : 'Disabled'}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Log Level</dt>
              <dd className="mt-1 text-sm text-gray-900">
                {diagnostics.environment.log_level}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">CORS Origins</dt>
              <dd className="mt-1 text-sm text-gray-900">
                {Array.isArray(diagnostics.environment.cors_origins)
                  ? diagnostics.environment.cors_origins.join(', ')
                  : diagnostics.environment.cors_origins}
              </dd>
            </div>
          </dl>
        </div>
      )}
    </div>
  );
}
