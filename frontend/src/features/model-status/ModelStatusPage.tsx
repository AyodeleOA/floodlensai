import { useQuery } from '@tanstack/react-query';
import { apiFetch } from '../../lib/api';
import type { ModelStatusItem } from '../../lib/types';

export function ModelStatusPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['model-status'],
    queryFn: () => apiFetch<{ items: ModelStatusItem[]; ai_provider_mode: string; demo_mode: boolean }>('/api/v1/admin/model-status'),
  });

  return (
    <div className="mx-auto max-w-3xl px-4 py-6">
      <h1 className="text-2xl font-bold text-slate-900">AI Model Status</h1>
      <p className="mt-1 text-sm text-slate-600">
        Status of all AI model adapters. Honest status — no endpoint is shown as connected when it is not.
      </p>

      {data && (
        <div className="mt-3 flex gap-3">
          <span className="badge bg-slate-100 text-slate-700">Mode: {data.ai_provider_mode}</span>
          {data.demo_mode && <span className="badge bg-amber-100 text-amber-700">Demo Mode</span>}
        </div>
      )}

      {isLoading ? (
        <div className="mt-4 text-slate-500">Loading...</div>
      ) : (
        <div className="mt-4 space-y-3">
          {data?.items.map((m) => (
            <div key={m.id} className="card p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-slate-900">{m.name}</p>
                  <p className="text-xs text-slate-500">
                    {m.model_id} · {m.provider_type}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  {m.enabled && <span className="badge bg-blue-50 text-blue-700">Enabled</span>}
                  <span className={`badge ${
                    m.status === 'connected' ? 'bg-green-100 text-green-700' :
                    m.status === 'demo_mode' ? 'bg-amber-100 text-amber-700' :
                    m.status === 'unavailable' ? 'bg-red-100 text-red-700' :
                    'bg-slate-100 text-slate-500'
                  }`}>
                    {m.status === 'demo_mode' ? 'Demo Mode' :
                     m.status === 'connected' ? 'Connected' :
                     m.status === 'unavailable' ? 'Unavailable' :
                     'Not Configured'}
                  </span>
                </div>
              </div>
              {m.endpoint && (
                <p className="mt-2 text-xs text-slate-400">Endpoint: {m.endpoint}</p>
              )}
            </div>
          ))}
        </div>
      )}

      <div className="mt-6 rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
        <p className="font-medium">Open-Weight Model Notes</p>
        <p className="mt-1">
          Muse Glimmer and Muse Spark Open adapters connect to separately hosted endpoints.
          They do not load model weights into the application. If not configured, hosted Muse Spark
          is used for the user-facing workflow and the open-weight adapter is shown as not connected.
        </p>
        <p className="mt-2 text-xs text-amber-700">
          Muse Spark Open requires specialised multi-GPU infrastructure (1.65 TB BF16 / 537 GB NVFP4).
          It is an optional advanced deployment, not a default MVP dependency.
        </p>
      </div>
    </div>
  );
}
