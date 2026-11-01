import { useQuery } from '@tanstack/react-query';
import { apiFetch } from '../../lib/api';
import { formatDate } from '../../lib/utils';

interface DataSourceStatus {
  id: string;
  name: string;
  source_type: string;
  status: string;
  licence: string | null;
  attribution: string | null;
  last_success_at: string | null;
  update_frequency: string | null;
  limitations: string | null;
}

export function DashboardDataPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['data-source-status'],
    queryFn: () => apiFetch<{ items: DataSourceStatus[] }>('/api/v1/admin/data-source-status'),
  });

  return (
    <div className="mx-auto max-w-3xl px-4 py-6">
      <h1 className="text-2xl font-bold text-slate-900">Data Sources</h1>
      <p className="mt-1 text-sm text-slate-600">
        Environmental data source freshness, coverage, and attribution.
      </p>

      {isLoading ? (
        <div className="mt-4 text-slate-500">Loading...</div>
      ) : !data?.items?.length ? (
        <div className="mt-4 text-slate-500">No data sources configured.</div>
      ) : (
        <div className="mt-4 space-y-3">
          {data.items.map((s) => (
            <div key={s.id} className="card p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-slate-900">{s.name}</p>
                  <p className="text-xs text-slate-500">{s.source_type}</p>
                </div>
                <span className={`badge ${
                  s.status === 'seeded' ? 'bg-amber-100 text-amber-700' :
                  s.status === 'live' ? 'bg-green-100 text-green-700' :
                  'bg-slate-100 text-slate-500'
                }`}>
                  {s.status}
                </span>
              </div>

              <dl className="mt-3 space-y-1 text-sm">
                {s.licence && (
                  <div className="flex justify-between">
                    <dt className="text-slate-500">Licence</dt>
                    <dd>{s.licence}</dd>
                  </div>
                )}
                {s.attribution && (
                  <div className="flex justify-between">
                    <dt className="text-slate-500">Attribution</dt>
                    <dd>{s.attribution}</dd>
                  </div>
                )}
                {s.update_frequency && (
                  <div className="flex justify-between">
                    <dt className="text-slate-500">Update Frequency</dt>
                    <dd>{s.update_frequency}</dd>
                  </div>
                )}
                {s.last_success_at && (
                  <div className="flex justify-between">
                    <dt className="text-slate-500">Last Updated</dt>
                    <dd>{formatDate(s.last_success_at)}</dd>
                  </div>
                )}
              </dl>

              {s.limitations && (
                <p className="mt-2 text-xs text-amber-600">{s.limitations}</p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
