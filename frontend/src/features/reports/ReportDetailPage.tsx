import { useParams, Link, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  ArrowLeft, MapPin, Camera, Mic, CheckCircle2, Clock, AlertTriangle,
  Eye, Info, ShieldAlert,
} from 'lucide-react';
import { apiFetch } from '../../lib/api';
import { StatusBadge } from '../../components/RiskBadge';
import { formatDate } from '../../lib/utils';
import { Disclaimer } from '../../components/Disclaimer';

interface MediaItem {
  id: string;
  media_type: string;
  mime_type: string;
  file_size: number;
  processing_status: string;
  uploaded_at: string;
  download_url: string | null;
  public_thumbnail_key: string | null;
}

interface HazardDetection {
  type: string;
  visible_evidence: string;
  confidence: number;
  severity_observation: string;
  bounding_box: number[] | null;
  requires_human_verification: boolean;
}

interface AIAnalysisItem {
  id: string;
  provider: string;
  model_id: string;
  status: string;
  scene_summary: string | null;
  structured_result: {
    hazards?: HazardDetection[];
    water_presence?: string;
    infrastructure_observations?: string[];
    limitations?: string[];
    recommended_review_actions?: string[];
  } | null;
  confidence: number | null;
  limitations: string[] | null;
  processing_ms: number | null;
  created_at: string;
}

interface ReportDetail {
  id: string;
  report_type: string;
  hazard_type: string | null;
  severity: string | null;
  status: string;
  description: string | null;
  landmark: string | null;
  water_level: string | null;
  affects_roads: boolean | null;
  affects_homes: boolean | null;
  affects_shops: boolean | null;
  affects_facilities: boolean | null;
  latitude_coarse: number;
  longitude_coarse: number;
  reported_at: string | null;
  submitted_at: string;
  is_synthetic: boolean;
  voice_transcript: string | null;
  media: MediaItem[];
  ai_analyses: AIAnalysisItem[];
}

function severityColor(severity: string) {
  const c: Record<string, string> = {
    critical: 'text-red-700 bg-red-50 border-red-200',
    high: 'text-red-600 bg-red-50 border-red-100',
    moderate: 'text-orange-600 bg-orange-50 border-orange-100',
    low: 'text-yellow-600 bg-yellow-50 border-yellow-100',
    unknown: 'text-slate-500 bg-slate-50 border-slate-100',
  };
  return c[severity] ?? c.unknown;
}

function waterPresenceLabel(w: string | undefined) {
  const labels: Record<string, string> = {
    none: 'No water visible',
    possible: 'Possible water',
    visible: 'Water visible',
    extensive: 'Extensive flooding',
    uncertain: 'Uncertain',
  };
  return labels[w ?? ''] ?? w ?? '—';
}

export function ReportDetailPage() {
  const { id } = useParams<{ id: string }>();

  const { data: report, isLoading, error } = useQuery({
    queryKey: ['report-detail', id],
    queryFn: () => apiFetch<ReportDetail>(`/api/v1/reports/${id}/detail`),
    enabled: !!id,
  });

  if (isLoading) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-8">
        <div className="animate-pulse space-y-4">
          <div className="h-6 w-48 rounded bg-slate-200" />
          <div className="h-48 rounded-lg bg-slate-200" />
          <div className="h-32 rounded-lg bg-slate-200" />
        </div>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-8">
        <p className="text-red-500">Could not load report details.</p>
        <Link to="/map" className="btn-secondary mt-4">Back to Map</Link>
      </div>
    );
  }

  const photoAssets = report.media.filter(m => m.media_type === 'photo');
  const voiceAssets = report.media.filter(m => m.media_type === 'voice');
  const latestAnalysis = report.ai_analyses.find(a => a.status === 'completed');

  return (
    <div className="mx-auto max-w-3xl px-4 py-6">
      {/* Back link */}
      <Link to="/map" className="flex items-center gap-1 text-sm text-slate-500 hover:text-slate-700">
        <ArrowLeft className="h-4 w-4" />
        Back to Map
      </Link>

      {/* Header */}
      <div className="mt-4 flex items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">
            {report.report_type.replace('_', ' ').replace(/\b\w/g, c => c.toUpperCase())} Report
          </h1>
          <div className="mt-1 flex flex-wrap items-center gap-2">
            <StatusBadge status={report.status} />
            {report.severity && (
              <span className={`badge border ${severityColor(report.severity)}`}>
                {report.severity.charAt(0).toUpperCase() + report.severity.slice(1)} severity
              </span>
            )}
            {report.hazard_type && (
              <span className="badge bg-slate-100 text-slate-700">
                {report.hazard_type.replace('_', ' ')}
              </span>
            )}
            {report.is_synthetic && (
              <span className="badge bg-amber-100 text-amber-700">Synthetic / Demo</span>
            )}
          </div>
        </div>
        <p className="shrink-0 text-xs text-slate-400">{formatDate(report.submitted_at)}</p>
      </div>

      {/* Location & details */}
      <div className="card mt-4 p-5">
        <h2 className="text-sm font-medium text-slate-700">Details</h2>
        <dl className="mt-2 space-y-2 text-sm">
          <div className="flex items-start gap-2">
            <MapPin className="mt-0.5 h-4 w-4 shrink-0 text-slate-400" />
            <dd className="text-slate-600">
              {report.latitude_coarse.toFixed(2)}, {report.longitude_coarse.toFixed(2)} (approx.)
              {report.landmark && <span> — {report.landmark}</span>}
            </dd>
          </div>
          {report.water_level && (
            <div className="flex justify-between">
              <dt className="text-slate-500">Water level</dt>
              <dd className="font-medium">{report.water_level.replace('_', ' ')}</dd>
            </div>
          )}
          {report.description && (
            <div className="mt-2 rounded-lg bg-slate-50 p-3 text-slate-700">
              "{report.description}"
            </div>
          )}
          {/* Affected areas */}
          <div className="flex flex-wrap gap-2 pt-1">
            {report.affects_roads && <span className="badge bg-slate-100 text-slate-600">Roads</span>}
            {report.affects_homes && <span className="badge bg-slate-100 text-slate-600">Homes</span>}
            {report.affects_shops && <span className="badge bg-slate-100 text-slate-600">Shops</span>}
            {report.affects_facilities && <span className="badge bg-slate-100 text-slate-600">Facilities</span>}
          </div>
        </dl>
      </div>

      {/* Photos */}
      {photoAssets.length > 0 && (
        <div className="card mt-4 p-5">
          <h2 className="flex items-center gap-2 text-sm font-medium text-slate-700">
            <Camera className="h-4 w-4" />
            Photos ({photoAssets.length})
          </h2>
          <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-3">
            {photoAssets.map(m => (
              <div key={m.id} className="group relative overflow-hidden rounded-lg border border-slate-200 bg-slate-100">
                {m.download_url ? (
                  <a href={m.download_url} target="_blank" rel="noopener noreferrer">
                    <img
                      src={m.download_url}
                      alt="Flood report photo"
                      className="h-36 w-full object-cover transition-transform group-hover:scale-105"
                      onError={(e) => {
                        (e.target as HTMLImageElement).style.display = 'none';
                      }}
                    />
                    <div className="absolute inset-0 flex items-center justify-center opacity-0 transition-opacity group-hover:opacity-100">
                      <span className="rounded bg-black/60 px-2 py-1 text-xs text-white">
                        <Eye className="inline h-3 w-3 mr-1" />View full
                      </span>
                    </div>
                  </a>
                ) : (
                  <div className="flex h-36 items-center justify-center text-slate-400">
                    <Camera className="h-8 w-8" />
                  </div>
                )}
                <div className="px-2 py-1">
                  <p className="text-xs text-slate-500">
                    {(m.file_size / 1024).toFixed(0)} KB · {m.processing_status}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* AI Analysis */}
      {latestAnalysis && (
        <div className="card mt-4 p-5">
          <h2 className="flex items-center gap-2 text-sm font-medium text-slate-700">
            <Eye className="h-4 w-4" />
            AI Analysis
            <span className="ml-auto text-xs font-normal text-slate-400">
              {latestAnalysis.provider} · {latestAnalysis.model_id}
              {latestAnalysis.processing_ms && ` · ${latestAnalysis.processing_ms}ms`}
            </span>
          </h2>

          {latestAnalysis.scene_summary && (
            <p className="mt-3 rounded-lg bg-blue-50 p-3 text-sm text-blue-900">
              {latestAnalysis.scene_summary}
            </p>
          )}

          {/* Water presence */}
          {latestAnalysis.structured_result?.water_presence && (
            <div className="mt-3 flex items-center gap-2 text-sm">
              <span className="text-slate-500">Water presence:</span>
              <span className={`font-medium ${
                latestAnalysis.structured_result.water_presence === 'extensive' ? 'text-red-600' :
                latestAnalysis.structured_result.water_presence === 'visible' ? 'text-orange-600' :
                latestAnalysis.structured_result.water_presence === 'possible' ? 'text-yellow-600' :
                'text-slate-700'
              }`}>
                {waterPresenceLabel(latestAnalysis.structured_result.water_presence)}
              </span>
            </div>
          )}

          {/* Detected hazards */}
          {latestAnalysis.structured_result?.hazards && latestAnalysis.structured_result.hazards.length > 0 && (
            <div className="mt-4">
              <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Detected Hazards</p>
              <div className="mt-2 space-y-2">
                {latestAnalysis.structured_result.hazards.map((h, i) => (
                  <div key={i} className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-sm">
                    <div className="flex items-center justify-between">
                      <span className={`font-medium ${
                        h.severity_observation === 'critical' ? 'text-red-700' :
                        h.severity_observation === 'high' ? 'text-red-600' :
                        h.severity_observation === 'moderate' ? 'text-orange-600' :
                        'text-slate-700'
                      }`}>
                        {h.type.replace('_', ' ')}
                      </span>
                      <div className="flex items-center gap-2">
                        <span className="badge bg-slate-100 text-slate-600">
                          {Math.round(h.confidence * 100)}% confidence
                        </span>
                        {h.severity_observation !== 'unknown' && (
                          <span className={`badge ${severityColor(h.severity_observation)}`}>
                            {h.severity_observation}
                          </span>
                        )}
                      </div>
                    </div>
                    <p className="mt-1 text-slate-600">{h.visible_evidence}</p>
                    {h.requires_human_verification && (
                      <p className="mt-1 flex items-center gap-1 text-xs text-amber-600">
                        <AlertTriangle className="h-3 w-3" />
                        Requires human verification
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Infrastructure observations */}
          {latestAnalysis.structured_result?.infrastructure_observations &&
            latestAnalysis.structured_result.infrastructure_observations.length > 0 && (
            <div className="mt-4">
              <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Infrastructure</p>
              <ul className="mt-1 list-disc pl-5 text-sm text-slate-600">
                {latestAnalysis.structured_result.infrastructure_observations.map((obs, i) => (
                  <li key={i}>{obs}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Limitations */}
          {latestAnalysis.limitations && latestAnalysis.limitations.length > 0 && (
            <div className="mt-4 rounded-lg border border-amber-100 bg-amber-50 p-3">
              <p className="flex items-center gap-1 text-xs font-medium text-amber-700">
                <Info className="h-3.5 w-3.5" />
                Analysis Limitations
              </p>
              <ul className="mt-1 list-disc pl-5 text-xs text-amber-700">
                {latestAnalysis.limitations.map((l, i) => <li key={i}>{l}</li>)}
              </ul>
            </div>
          )}

          {/* Confidence indicator */}
          {latestAnalysis.confidence !== null && (
            <div className="mt-3 flex items-center gap-2 text-xs text-slate-500">
              <span>Overall confidence:</span>
              <div className="flex-1 rounded-full bg-slate-200">
                <div
                  className="rounded-full bg-floodlens-500 py-1"
                  style={{ width: `${Math.round(latestAnalysis.confidence * 100)}%` }}
                />
              </div>
              <span className="font-medium text-slate-700">{Math.round(latestAnalysis.confidence * 100)}%</span>
            </div>
          )}
        </div>
      )}

      {/* No analysis yet */}
      {report.ai_analyses.length === 0 && report.media.filter(m => m.media_type === 'photo').length > 0 && (
        <div className="card mt-4 p-5">
          <div className="flex items-center gap-2 text-sm text-slate-500">
            <Clock className="h-4 w-4 text-amber-500" />
            AI analysis pending for uploaded photos.
          </div>
        </div>
      )}

      {/* Voice transcript */}
      {(report.voice_transcript || voiceAssets.length > 0) && (
        <div className="card mt-4 p-5">
          <h2 className="flex items-center gap-2 text-sm font-medium text-slate-700">
            <Mic className="h-4 w-4" />
            Voice Note
            {voiceAssets.length > 0 && (
              <span className="ml-auto text-xs text-slate-400">{voiceAssets.length} recording(s)</span>
            )}
          </h2>

          {voiceAssets.map(v => v.download_url && (
            <div key={v.id} className="mt-3">
              <audio controls className="w-full" aria-label="Voice note recording">
                <source src={v.download_url} type={v.mime_type} />
                Your browser does not support audio playback.
              </audio>
            </div>
          ))}

          {report.voice_transcript ? (
            <div className="mt-3">
              <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Transcript (unverified)</p>
              <blockquote className="mt-1 rounded-lg bg-slate-50 p-3 text-sm italic text-slate-700">
                "{report.voice_transcript}"
              </blockquote>
              <p className="mt-1 flex items-center gap-1 text-xs text-amber-600">
                <ShieldAlert className="h-3 w-3" />
                Transcript is unverified and may contain errors. Do not use to establish flood severity.
              </p>
            </div>
          ) : voiceAssets.length > 0 && (
            <p className="mt-3 text-sm text-slate-500">
              <Clock className="inline h-3.5 w-3.5 text-amber-400 mr-1" />
              Transcription pending.
            </p>
          )}
        </div>
      )}

      {/* Actions */}
      <div className="mt-6 flex flex-wrap gap-3">
        <Link to="/map" className="btn-secondary">
          <ArrowLeft className="h-4 w-4" />
          Back to Map
        </Link>
        <Link to={`/report/${id}`} className="btn-secondary">
          <CheckCircle2 className="h-4 w-4" />
          View Receipt
        </Link>
      </div>

      <div className="mt-6">
        <Disclaimer compact />
      </div>
    </div>
  );
}
