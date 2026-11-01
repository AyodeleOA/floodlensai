// API base URL configuration
//
// Local development:
//   VITE_API_BASE_URL is empty — Vite dev server proxies /api and /health
//   to http://localhost:8000 (see vite.config.ts proxy config).
//   All requests use relative paths (e.g. /api/v1/reports).
//
// Production (AWS Amplify Hosting → API Gateway):
//   VITE_API_BASE_URL is set to the deployed API Gateway HTTPS URL.
//   All requests use absolute URLs (e.g. https://{api-id}.execute-api.{region}.amazonaws.com/prod/api/v1/reports).
//   This avoids same-origin restrictions since Amplify and API Gateway are on different domains.
//
// Never put MODEL_API_KEY, DATABASE_URL, or other secrets in VITE_ variables.
// The browser must never call Meta Model API directly or receive MODEL_API_KEY.

const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  // In production: API_BASE is the API Gateway URL, path is relative (/api/v1/...)
  // In local dev: API_BASE is empty, path is relative and proxied by Vite
  const url = `${API_BASE}${path}`;

  const res = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ error: 'Request failed', message: res.statusText }));
    throw new Error(error.message || error.error || `HTTP ${res.status}`);
  }

  return res.json();
}

export { apiFetch, API_BASE };
