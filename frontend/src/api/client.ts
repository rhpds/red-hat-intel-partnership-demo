const API_BASE = import.meta.env.VITE_API_URL || '';
const AUTH_TOKEN = import.meta.env.VITE_AUTH_TOKEN || '';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const headers: Record<string, string> = {
    ...(options?.body ? { 'Content-Type': 'application/json' } : {}),
    ...(AUTH_TOKEN ? { 'X-API-Key': AUTH_TOKEN } : {}),
    ...(options?.headers as Record<string, string> || {}),
  };
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
    credentials: 'same-origin',
  });
  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }
  return response.json();
}

export const api = {
  getHealth: () => request<import('./types').HealthStatus>('/health'),

  getBackends: () => request<{ backends: import('./types').BackendInfo[] }>('/v1/backends'),
  getRoutes: () => request<{ routes: import('./types').Route[] }>('/v1/routes'),

  routeRequest: (body: Record<string, unknown>, signal?: AbortSignal) =>
    request<import('./types').RouteResponse>('/v1/route', {
      method: 'POST',
      body: JSON.stringify(body),
      signal,
    }),

  getRequests: (params?: Record<string, string>) => {
    const qs = params ? '?' + new URLSearchParams(params).toString() : '';
    return request<import('./types').PaginatedResponse<import('./types').InferenceRequest>>(`/api/v1/requests${qs}`);
  },

  getDecisions: (params?: Record<string, string>) => {
    const qs = params ? '?' + new URLSearchParams(params).toString() : '';
    return request<import('./types').PaginatedResponse<import('./types').GovernanceDecision>>(`/api/v1/decisions${qs}`);
  },

  approveDecision: (id: string, approvedBy: string) =>
    request<{ status: string }>(`/api/v1/decisions/${id}/approve`, {
      method: 'POST',
      body: JSON.stringify({ approved_by: approvedBy }),
    }),

  getRoutingRules: () => request<{ data: import('./types').RoutingRule[] }>('/api/v1/routing-rules'),

  getCostSummary: (days = 30) =>
    request<import('./types').AnalyticsResponse<import('./types').CostSummaryItem>>(`/api/v1/cost-summary?days=${days}`),

  getRoutingDistribution: (days = 7) =>
    request<import('./types').AnalyticsResponse<import('./types').RoutingDistribution>>(`/api/v1/analytics/routing-distribution?days=${days}`),

  getLatencyPercentiles: (days = 7) =>
    request<import('./types').AnalyticsResponse<import('./types').LatencyPercentiles>>(`/api/v1/analytics/latency-percentiles?days=${days}`),

  getCostByTask: (days = 30) =>
    request<import('./types').AnalyticsResponse<import('./types').CostSummaryItem>>(`/api/v1/analytics/cost-by-task?days=${days}`),

  getGovernanceSummary: (days = 30) =>
    request<import('./types').AnalyticsResponse<import('./types').GovernanceSummaryItem>>(`/api/v1/analytics/governance-summary?days=${days}`),

  overdriveRoute: (body: Record<string, unknown>) =>
    request<Record<string, unknown>>('/v1/overdrive/route', {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  overdriveBatch: (requests: Record<string, unknown>[]) =>
    request<Record<string, unknown>>('/v1/overdrive/batch', {
      method: 'POST',
      body: JSON.stringify({ requests }),
    }),

  overdriveStatus: () =>
    request<Record<string, unknown>>('/v1/overdrive/status'),

  overdriveSetHealth: (lane: string, healthy: boolean) =>
    request<Record<string, unknown>>(`/v1/overdrive/health/${lane}?healthy=${healthy}`, {
      method: 'POST',
    }),
};
