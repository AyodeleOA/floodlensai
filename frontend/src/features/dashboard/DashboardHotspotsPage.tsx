import { useQuery } from '@tanstack/react-query';
import { apiFetch } from '../../lib/api';
import type { HotspotItem } from '../../lib/types';
import { RiskBadge } from '../../components/RiskBadge';
import { formatDate } from '../../lib/utils';

export function DashboardHotspotsPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['hotspots'],
    queryFn: () => apiFetch<{ items: HotspotItem[]; total: number }>('/api/v1/admin/hotspots?limit=20'),
  });

  return (
    <div className="mx-auto max-w-3xl px-4 py-6">
      <h1 className="text-2xl font-bold text-slate-900">Priority Hotspots</h1>
      <p className="mt-1 text-sm text-slate-600">
        Ranked by risk score. Click a hotspot to view details on the map.
      </p>

      {isLoading ? (
        <div className="mt-4 text-slate-500">Loading...</div>
      ) : !data?.items?.length ? (
        <div className="mt-4 text-slate-500">No hotspots found.</div>
      ) : (
        <div className="mt-4 space-y-3">
          {data.items.map((h, i) => (
            <div key={h.risk_cell_id} className="card p-4">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <span className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-100 text-sm font-bold text-slate-600">
                    {i + 1}
                  </span>
                  <div>
                    <p className="font-medium text-slate-900">Cell {h.grid_index.slice(0, 12)}...</p>
                    <p className="text-xs text-slate-500">
                      {h.latitude.toFixed(4)}, {h.longitude.toFixed(4)}
                    </p>
                  </div>
                </div>
                <RiskBadge band={h.risk_band} score={h.risk_score} />
              </div>

              <div className="mt-3 grid grid-cols-3 gap-2 text-sm">
                <div>
                  <p className="text-xs text-slate-500">Confidence</p>
                  <p className="font-medium">{Math.round(h.confidence_score * 100)}%</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500">Reports</p>
                  <p className="font-medium">{h.report_count}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500">Last Evidence</p>
                  <p className="font-medium">{formatDate(h.last_evidence_at)}</p>
                </div>
              </div>

              {h.top_contributing_factors.length > 0 && (
                <div className="mt-2">
                  <p className="text-xs text-slate-500">Top Contributors</p>
                  <div className="mt-1 flex flex-wrap gap-1">
                    {h.top_contributing_factors.map((f, j) => (
                      <span key={j} className="badge bg-slate-100 text-slate-600">{f}</span>
                    ))}
                  </div>
                </div>
              )}

              {h.is_illustrative && (
                <p className="mt-2 text-xs text-amber-600">Illustrative — unvalidated</p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
