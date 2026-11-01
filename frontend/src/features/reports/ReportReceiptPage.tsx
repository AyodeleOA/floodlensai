import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { CheckCircle2, Clock, MapPin, Camera, Mic } from 'lucide-react';
import { apiFetch } from '../../lib/api';
import type { ReportReceipt } from '../../lib/types';

export function ReportReceiptPage() {
  const { id } = useParams<{ id: string }>();

  const { data: receipt, isLoading, error } = useQuery({
    queryKey: ['report-receipt', id],
    queryFn: () => apiFetch<ReportReceipt>(`/api/v1/reports/${id}/receipt`),
    enabled: !!id,
  });

  if (isLoading) {
    return <div className="mx-auto max-w-lg px-4 py-8 text-slate-500">Loading receipt...</div>;
  }

  if (error || !receipt) {
    return (
      <div className="mx-auto max-w-lg px-4 py-8">
        <p className="text-red-500">Could not load receipt.</p>
        <Link to="/report" className="btn-secondary mt-4">Back to Report Form</Link>
      </div>
    );
  }

  const statusSteps = ['submitted', 'under_review', 'verified'];
  const currentStep = statusSteps.indexOf(receipt.status);

  return (
    <div className="mx-auto max-w-lg px-4 py-8">
      {/* Success header */}
      <div className="text-center">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-green-50">
          <CheckCircle2 className="h-8 w-8 text-green-500" />
        </div>
        <h1 className="mt-3 text-xl font-bold text-slate-900">Report Submitted</h1>
        <p className="mt-1 text-sm text-slate-600">
          Your report has been received. Save this receipt to check status.
        </p>
      </div>

      {/* Receipt details */}
      <div className="card mt-6 p-5">
        <dl className="space-y-3 text-sm">
          <div className="flex justify-between">
            <dt className="text-slate-600">Report ID</dt>
            <dd className="font-mono text-xs">{receipt.id}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-slate-600">Type</dt>
            <dd>{receipt.report_type}</dd>
          </div>
          {receipt.hazard_type && (
            <div className="flex justify-between">
              <dt className="text-slate-600">Hazard</dt>
              <dd>{receipt.hazard_type}</dd>
            </div>
          )}
          <div className="flex justify-between">
            <dt className="text-slate-600">Location</dt>
            <dd>
              <MapPin className="inline h-3.5 w-3.5 text-slate-400" />
              {' '}{receipt.latitude_coarse.toFixed(2)}, {receipt.longitude_coarse.toFixed(2)} (approx.)
            </dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-slate-600">Submitted</dt>
            <dd>{new Date(receipt.submitted_at).toLocaleString('en-GB')}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-slate-600">Media</dt>
            <dd>{receipt.media_count} item(s)</dd>
          </div>
          {receipt.is_synthetic && (
            <p className="text-xs text-amber-600">This is a synthetic demo report.</p>
          )}
        </dl>
      </div>

      {/* Status tracker */}
      <div className="mt-4 card p-5">
        <h2 className="text-sm font-medium text-slate-700">Status</h2>
        <ol className="mt-3 space-y-3">
          {statusSteps.map((step, i) => {
            const isDone = i <= currentStep;
            const isCurrent = i === currentStep;
            return (
              <li key={step} className="flex items-center gap-3">
                {isDone ? (
                  <CheckCircle2 className="h-5 w-5 text-green-500" />
                ) : (
                  <Clock className="h-5 w-5 text-slate-300" />
                )}
                <span className={isCurrent ? 'font-medium text-slate-900' : 'text-slate-400'}>
                  {step.replace('_', ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
                </span>
              </li>
            );
          })}
        </ol>
        {receipt.ai_analysis_status && (
          <p className="mt-3 text-xs text-slate-500">
            AI Analysis: {receipt.ai_analysis_status}
          </p>
        )}
      </div>

      {/* Upload hint */}
      <div className="mt-4 flex gap-3">
        <Link to="/report" className="btn-secondary">
          <Camera className="h-4 w-4" />
          New Report
        </Link>
        <Link to="/map" className="btn-secondary">
          View Map
        </Link>
      </div>
    </div>
  );
}
