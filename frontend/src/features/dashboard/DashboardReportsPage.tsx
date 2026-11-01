import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { apiFetch } from '../../lib/api';
import type { AdminReportListItem } from '../../lib/types';
import { StatusBadge } from '../../components/RiskBadge';
import { formatDate } from '../../lib/utils';

export function DashboardReportsPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['admin-reports'],
    queryFn: () => apiFetch<{ items: AdminReportListItem[] }>('/api/v1/admin/reports?limit=50'),
  });

  return (
    <div className="mx-auto max-w-5xl px-4 py-6">
      <h1 className="text-2xl font-bold text-slate-900">Review Queue</h1>
      <p className="mt-1 text-sm text-slate-600">All submitted reports for moderation.</p>

      {isLoading ? (
        <div className="mt-4 text-slate-500">Loading...</div>
      ) : !data?.items?.length ? (
        <div className="mt-4 text-slate-500">No reports found.</div>
      ) : (
        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-left text-slate-500">
                <th className="py-2 pr-4 font-medium">Type</th>
                <th className="py-2 pr-4 font-medium">Hazard</th>
                <th className="py-2 pr-4 font-medium">Severity</th>
                <th className="py-2 pr-4 font-medium">Status</th>
                <th className="py-2 pr-4 font-medium">Media</th>
                <th className="py-2 pr-4 font-medium">AI</th>
                <th className="py-2 pr-4 font-medium">Submitted</th>
                <th className="py-2 pr-4 font-medium"></th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((r) => (
                <tr key={r.id} className="border-b border-slate-100 hover:bg-slate-50">
                  <td className="py-2 pr-4">{r.report_type}</td>
                  <td className="py-2 pr-4">{r.hazard_type || '—'}</td>
                  <td className="py-2 pr-4">{r.severity || '—'}</td>
                  <td className="py-2 pr-4"><StatusBadge status={r.status} /></td>
                  <td className="py-2 pr-4">{r.media_count}</td>
                  <td className="py-2 pr-4">{r.ai_analysis_count}</td>
                  <td className="py-2 pr-4 text-slate-500">{formatDate(r.submitted_at)}</td>
                  <td className="py-2 pr-4">
                    <Link
                      to={`/dashboard/reports/${r.id}`}
                      className="text-floodlens-600 hover:underline"
                    >
                      View
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
