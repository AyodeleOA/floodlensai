import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useState } from 'react';
import { ArrowLeft, CheckCircle2, XCircle, RefreshCw, Clock } from 'lucide-react';
import { apiFetch } from '../../lib/api';
import { StatusBadge } from '../../components/RiskBadge';
import { formatDate } from '../../lib/utils';

interface AdminReportDetail {
  id: string;
  report_type: string;
  hazard_type: string | null;
  severity: string | null;
  status: string;
  latitude: number;
  longitude: number;
  description: string | null;
  landmark: string | null;
  water_level: string | null;
  affects_roads: boolean | null;
  affects_homes: boolean | null;
  affects_shops: boolean | null;
  affects_facilities: boolean | null;
  reporter_contact: string | null;
  voice_transcript: string | null;
  reported_at: string | null;
  submitted_at: string;
  is_synthetic: boolean;
  media_assets: { id: string; media_type: string; mime_type: string; file_size: number; processing_status: string; uploaded_at: string }[];
  ai_analyses: { id: string; provider: string; model_id: string; status: string; scene_summary: string | null; confidence: number | null; limitations: string[] | null; processing_ms: number | null }[];
  moderation_history: { id: string; action: string; reason: string | null; previous_status: string; new_status: string; created_at: string }[];
}

export function DashboardReportDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [verifyReason, setVerifyReason] = useState('');

  const { data: report, isLoading } = useQuery({
    queryKey: ['admin-report', id],
    queryFn: () => apiFetch<AdminReportDetail>(`/api/v1/admin/reports/${id}`),
    enabled: !!id,
  });

  const verifyMutation = useMutation({
    mutationFn: () => apiFetch(`/api/v1/admin/reports/${id}/verify`, {
      method: 'POST',
      body: JSON.stringify({ reason: verifyReason || 'Verified by reviewer' }),
    }),
  });

  const reanalyzeMutation = useMutation({
    mutationFn: () => apiFetch(`/api/v1/admin/reports/${id}/reanalyze`, { method: 'POST' }),
  });

  if (isLoading) return <div className="px-4 py-8 text-slate-500">Loading...</div>;
  if (!report) return <div className="px-4 py-8 text-red-500">Report not found.</div>;

  return (
    <div className="mx-auto max-w-3xl px-4 py-6">
      <Link to="/dashboard/reports" className="flex items-center gap-1 text-sm text-slate-500 hover:text-slate-700">
        <ArrowLeft className="h-4 w-4" /> Back to Queue
      </Link>

      <div className="mt-4 flex items-center gap-3">
        <h1 className="text-2xl font-bold text-slate-900">Report Detail</h1>
        <StatusBadge status={report.status} />
        {report.is_synthetic && <span className="badge bg-amber-100 text-amber-800">Synthetic</span>}
      </div>

      {/* Report details */}
      <div className="card mt-4 p-5">
        <dl className="space-y-2 text-sm">
          <div className="flex justify-between">
            <dt className="text-slate-600">Type</dt>
            <dd className="font-medium">{report.report_type}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-slate-600">Hazard</dt>
            <dd>{report.hazard_type || '—'}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-slate-600">Severity</dt>
            <dd>{report.severity || '—'}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-slate-600">Location</dt>
            <dd>{report.latitude.toFixed(4)}, {report.longitude.toFixed(4)}</dd>
          </div>
          {report.landmark && (
            <div className="flex justify-between">
              <dt className="text-slate-600">Landmark</dt>
              <dd>{report.landmark}</dd>
            </div>
          )}
          {report.water_level && (
            <div className="flex justify-between">
              <dt className="text-slate-600">Water Level</dt>
              <dd>{report.water_level}</dd>
            </div>
          )}
          <div className="flex justify-between">
            <dt className="text-slate-600">Submitted</dt>
            <dd>{formatDate(report.submitted_at)}</dd>
          </div>
        </dl>

        {report.description && (
          <div className="mt-4 border-t border-slate-100 pt-3">
            <p className="text-sm font-medium text-slate-700">Description</p>
            <p className="mt-1 text-sm text-slate-600">{report.description}</p>
          </div>
        )}

        {/* Affected areas */}
        <div className="mt-3 flex flex-wrap gap-3">
          {report.affects_roads && <span className="badge bg-slate-100 text-slate-700">Roads</span>}
          {report.affects_homes && <span className="badge bg-slate-100 text-slate-700">Homes</span>}
          {report.affects_shops && <span className="badge bg-slate-100 text-slate-700">Shops</span>}
          {report.affects_facilities && <span className="badge bg-slate-100 text-slate-700">Facilities</span>}
        </div>

        {report.voice_transcript && (
          <div className="mt-4 border-t border-slate-100 pt-3">
            <p className="text-sm font-medium text-slate-700">Voice Transcript (unverified)</p>
            <p className="mt-1 text-sm italic text-slate-600">"{report.voice_transcript}"</p>
          </div>
        )}

        {report.reporter_contact && (
          <div className="mt-4 border-t border-slate-100 pt-3">
            <p className="text-sm font-medium text-slate-700">Reporter Contact (private)</p>
            <p className="mt-1 text-sm text-slate-600">{report.reporter_contact}</p>
          </div>
        )}
      </div>

      {/* AI Analyses */}
      {report.ai_analyses.length > 0 && (
        <div className="card mt-4 p-5">
          <h3 className="font-medium text-slate-900">AI Analysis</h3>
          {report.ai_analyses.map((ai) => (
            <div key={ai.id} className="mt-3 border-t border-slate-100 pt-3">
              <div className="flex items-center gap-2 text-sm">
                <span className="font-medium">{ai.provider}</span>
                <span className="text-slate-400">·</span>
                <span className="text-slate-500">{ai.model_id}</span>
                {ai.confidence !== null && (
                  <span className="badge bg-blue-50 text-blue-700">
                    {Math.round(ai.confidence * 100)}% confidence
                  </span>
                )}
              </div>
              {ai.scene_summary && (
                <p className="mt-1 text-sm text-slate-600">{ai.scene_summary}</p>
              )}
              {ai.limitations && ai.limitations.length > 0 && (
                <ul className="mt-1 list-disc pl-5 text-xs text-slate-500">
                  {ai.limitations.map((l, i) => <li key={i}>{l}</li>)}
                </ul>
              )}
              {ai.processing_ms !== null && (
                <p className="mt-1 text-xs text-slate-400">Processed in {ai.processing_ms}ms</p>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Media assets */}
      {report.media_assets.length > 0 && (
        <div className="card mt-4 p-5">
          <h3 className="font-medium text-slate-900">Media</h3>
          <div className="mt-2 space-y-2">
            {report.media_assets.map((m) => (
              <div key={m.id} className="flex items-center justify-between text-sm">
                <span>{m.media_type} · {m.mime_type}</span>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-slate-400">{(m.file_size / 1024).toFixed(0)} KB</span>
                  <span className={`badge ${
                    m.processing_status === 'completed' ? 'bg-green-100 text-green-700' :
                    m.processing_status === 'failed' ? 'bg-red-100 text-red-700' :
                    'bg-amber-100 text-amber-700'
                  }`}>{m.processing_status}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Moderation history */}
      {report.moderation_history.length > 0 && (
        <div className="card mt-4 p-5">
          <h3 className="font-medium text-slate-900">Moderation History</h3>
          <div className="mt-2 space-y-2">
            {report.moderation_history.map((m) => (
              <div key={m.id} className="flex items-center gap-2 text-sm">
                <Clock className="h-3.5 w-3.5 text-slate-400" />
                <span className="text-slate-600">{m.action}:</span>
                <span className="text-slate-400">{m.previous_status} → {m.new_status}</span>
                {m.reason && <span className="text-slate-500">({m.reason})</span>}
                <span className="ml-auto text-xs text-slate-400">{formatDate(m.created_at)}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="mt-4 flex flex-wrap gap-3">
        {report.status !== 'verified' && (
          <div className="flex items-center gap-2">
            <input
              className="input max-w-xs"
              placeholder="Verification reason (optional)"
              value={verifyReason}
              onChange={(e) => setVerifyReason(e.target.value)}
            />
            <button
              className="btn-primary"
              onClick={() => verifyMutation.mutate()}
              disabled={verifyMutation.isPending}
            >
              <CheckCircle2 className="h-4 w-4" />
              {verifyMutation.isPending ? 'Verifying...' : 'Verify'}
            </button>
          </div>
        )}
        <button
          className="btn-secondary"
          onClick={() => reanalyzeMutation.mutate()}
          disabled={reanalyzeMutation.isPending}
        >
          <RefreshCw className="h-4 w-4" />
          {reanalyzeMutation.isPending ? 'Reanalyzing...' : 'Reanalyze'}
        </button>
        {verifyMutation.isSuccess && (
          <span className="flex items-center gap-1 text-sm text-green-600">
            <CheckCircle2 className="h-4 w-4" /> Verified
          </span>
        )}
        {reanalyzeMutation.isSuccess && (
          <span className="flex items-center gap-1 text-sm text-floodlens-600">
            <RefreshCw className="h-4 w-4" /> Reanalysis enqueued
          </span>
        )}
      </div>
    </div>
  );
}
