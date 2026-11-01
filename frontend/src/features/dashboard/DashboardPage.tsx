import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  FileText, CheckCircle2, AlertTriangle, Clock, Eye, BarChart3, Database, ShieldAlert
} from 'lucide-react';
import { apiFetch } from '../../lib/api';
import type { AnalyticsOverview } from '../../lib/types';
import { formatDate } from '../../lib/utils';

export function DashboardPage() {
  const { data: analytics, isLoading } = useQuery({
    queryKey: ['analytics'],
    queryFn: () => apiFetch<AnalyticsOverview>('/api/v1/admin/analytics/overview'),
  });

  if (isLoading) {
    return <div className="mx-auto max-w-5xl px-4 py-8 text-slate-500">Loading dashboard...</div>;
  }

  if (!analytics) {
    return <div className="mx-auto max-w-5xl px-4 py-8 text-slate-500">No data available.</div>;
  }

  const kpis = [
    { label: 'Open Reports', value: analytics.open_reports, icon: FileText, color: 'text-blue-600', bg: 'bg-blue-50' },
    { label: 'Verified Incidents', value: analytics.verified_incidents, icon: CheckCircle2, color: 'text-green-600', bg: 'bg-green-50' },
    { label: 'High Risk Zones', value: analytics.high_risk_zones + analytics.very_high_risk_zones, icon: AlertTriangle, color: 'text-red-600', bg: 'bg-red-50' },
    { label: 'Pending Review', value: analytics.pending_review, icon: Clock, color: 'text-amber-600', bg: 'bg-amber-50' },
  ];

  return (
    <div className="mx-auto max-w-5xl px-4 py-6">
      <h1 className="text-2xl font-bold text-slate-900">Authority Dashboard</h1>
      <p className="mt-1 text-sm text-slate-600">
        Overview of reports, incidents, and risk zones.
      </p>

      {/* KPI cards */}
      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {kpis.map((kpi) => (
          <div key={kpi.label} className="card p-4">
            <div className="flex items-center justify-between">
              <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${kpi.bg}`}>
                <kpi.icon className={`h-5 w-5 ${kpi.color}`} />
              </div>
            </div>
            <p className="mt-3 text-2xl font-bold text-slate-900">{kpi.value}</p>
            <p className="text-sm text-slate-500">{kpi.label}</p>
          </div>
        ))}
      </div>

      {/* Additional stats */}
      <div className="mt-4 grid gap-4 md:grid-cols-2">
        <div className="card p-4">
          <h3 className="font-medium text-slate-900">Report Status</h3>
          <dl className="mt-2 space-y-1 text-sm">
            <div className="flex justify-between">
              <dt className="text-slate-600">Total</dt>
              <dd className="font-medium">{analytics.total_reports}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-slate-600">Verified</dt>
              <dd className="font-medium">{analytics.verified_incidents}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-slate-600">Open</dt>
              <dd className="font-medium">{analytics.open_reports}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-slate-600">Pending Review</dt>
              <dd className="font-medium">{analytics.pending_review}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-slate-600">Rejected</dt>
              <dd className="font-medium">{analytics.rejected_reports}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-slate-600">Duplicates</dt>
              <dd className="font-medium">{analytics.duplicate_reports}</dd>
            </div>
          </dl>
        </div>

        <div className="card p-4">
          <h3 className="font-medium text-slate-900">AI Processing</h3>
          <dl className="mt-2 space-y-1 text-sm">
            <div className="flex justify-between">
              <dt className="text-slate-600">Completed</dt>
              <dd className="font-medium">{analytics.ai_analyses_completed}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-slate-600">Pending</dt>
              <dd className="font-medium">{analytics.ai_analyses_pending}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-slate-600">Failed</dt>
              <dd className="font-medium">{analytics.ai_analyses_failed}</dd>
            </div>
          </dl>
          <div className="mt-3 border-t border-slate-100 pt-3">
            <p className="text-sm text-slate-600">Rainfall Source</p>
            {analytics.rainfall_source_fresh ? (
              <p className="flex items-center gap-1 text-sm text-green-600">
                <CheckCircle2 className="h-4 w-4" /> Fresh
              </p>
            ) : (
              <p className="flex items-center gap-1 text-sm text-amber-600">
                <ShieldAlert className="h-4 w-4" /> Stale or unavailable
              </p>
            )}
            {analytics.rainfall_last_updated && (
              <p className="text-xs text-slate-400">Last: {formatDate(analytics.rainfall_last_updated)}</p>
            )}
          </div>
        </div>
      </div>

      {/* Quick links */}
      <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Link to="/dashboard/reports" className="card flex items-center gap-3 p-4 transition-colors hover:bg-slate-50">
          <FileText className="h-5 w-5 text-floodlens-600" />
          <span className="text-sm font-medium text-slate-700">Review Queue</span>
        </Link>
        <Link to="/dashboard/hotspots" className="card flex items-center gap-3 p-4 transition-colors hover:bg-slate-50">
          <AlertTriangle className="h-5 w-5 text-red-500" />
          <span className="text-sm font-medium text-slate-700">Hotspots</span>
        </Link>
        <Link to="/dashboard/data" className="card flex items-center gap-3 p-4 transition-colors hover:bg-slate-50">
          <Database className="h-5 w-5 text-floodlens-600" />
          <span className="text-sm font-medium text-slate-700">Data Sources</span>
        </Link>
        <Link to="/dashboard/model-status" className="card flex items-center gap-3 p-4 transition-colors hover:bg-slate-50">
          <BarChart3 className="h-5 w-5 text-floodlens-600" />
          <span className="text-sm font-medium text-slate-700">Model Status</span>
        </Link>
      </div>
    </div>
  );
}
