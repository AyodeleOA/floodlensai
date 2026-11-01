import { riskBandClass } from '../lib/types';

export function RiskBadge({ band, score }: { band: string; score?: number }) {
  const label = band.replace('_', '-').replace(/\b\w/g, (c) => c.toUpperCase());
  const cls = riskBandClass(band);
  return (
    <span className={cls} role="status" aria-label={`Risk level: ${label}${score !== undefined ? `, score ${score}` : ''}`}>
      {label}{score !== undefined ? ` · ${score}` : ''}
    </span>
  );
}

export function StatusBadge({ status }: { status: string }) {
  const classes: Record<string, string> = {
    submitted: 'badge bg-blue-100 text-blue-800',
    under_review: 'badge bg-purple-100 text-purple-800',
    verified: 'badge bg-green-100 text-green-800',
    rejected: 'badge bg-red-100 text-red-800',
    duplicate: 'badge bg-slate-100 text-slate-600',
  };
  const labels: Record<string, string> = {
    submitted: 'Submitted',
    under_review: 'Under Review',
    verified: 'Verified',
    rejected: 'Rejected',
    duplicate: 'Duplicate',
  };
  return <span className={classes[status] || classes.submitted}>{labels[status] || status}</span>;
}
