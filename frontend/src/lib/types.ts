// API response types

export interface PublicReport {
  id: string;
  report_type: string;
  hazard_type: string | null;
  severity: string | null;
  status: string;
  latitude_coarse: number;
  longitude_coarse: number;
  reported_at: string | null;
  submitted_at: string;
  is_synthetic: boolean;
}

export interface MapReportItem {
  id: string;
  report_type: string;
  hazard_type: string | null;
  severity: string | null;
  status: string;
  latitude: number;
  longitude: number;
  reported_at: string | null;
  submitted_at: string;
  is_synthetic: boolean;
}

export interface MapSummary {
  total_reports: number;
  verified_incidents: number;
  pending_reports: number;
  high_risk_cells: number;
  last_updated: string;
  bbox: string;
  is_seeded: boolean;
}

export interface RiskCellListItem {
  id: string;
  grid_index: string;
  latitude: number;
  longitude: number;
  risk_score: number;
  risk_band: string;
  confidence_score: number;
  data_completeness: number;
  is_illustrative: boolean;
  calculated_at: string;
}

export interface LayerMetadata {
  id: string;
  name: string;
  type: string;
  visible: boolean;
  source: string | null;
  last_updated: string | null;
  is_seeded: boolean;
  attribution: string | null;
}

export interface SystemCapabilities {
  app_name: string;
  app_env: string;
  demo_mode: boolean;
  ai_provider_mode: string;
  features: Record<string, boolean>;
  enabled_layers: string[];
  model_statuses: { id: string; status: string }[];
  disclaimer: { text: string };
  api_version: string;
  server_time: string;
}

export interface AnalyticsOverview {
  total_reports: number;
  verified_incidents: number;
  pending_review: number;
  high_risk_zones: number;
  very_high_risk_zones: number;
  open_reports: number;
  rejected_reports: number;
  duplicate_reports: number;
  ai_analyses_completed: number;
  ai_analyses_pending: number;
  ai_analyses_failed: number;
  rainfall_source_fresh: boolean;
  rainfall_last_updated: string | null;
  period_start: string;
  period_end: string;
}

export interface HotspotItem {
  risk_cell_id: string;
  grid_index: string;
  latitude: number;
  longitude: number;
  risk_score: number;
  risk_band: string;
  confidence_score: number;
  report_count: number;
  last_evidence_at: string | null;
  top_contributing_factors: string[];
  is_illustrative: boolean;
}

export interface ModelStatusItem {
  id: string;
  name: string;
  model_id: string;
  provider_type: string;
  status: string;
  enabled: boolean;
  endpoint: string | null;
  last_health_check: string | null;
}

export interface AdminReportListItem {
  id: string;
  report_type: string;
  hazard_type: string | null;
  severity: string | null;
  status: string;
  latitude: number;
  longitude: number;
  reported_at: string | null;
  submitted_at: string;
  is_synthetic: boolean;
  media_count: number;
  ai_analysis_count: number;
}

export interface ReportCreated {
  id: string;
  status: string;
  submitted_at: string;
  receipt_url: string;
}

export interface ReportReceipt {
  id: string;
  status: string;
  submitted_at: string;
  report_type: string;
  hazard_type: string | null;
  latitude_coarse: number;
  longitude_coarse: number;
  media_count: number;
  ai_analysis_status: string | null;
  is_synthetic: boolean;
}

export function riskBandClass(band: string): string {
  const classes: Record<string, string> = {
    low: 'badge-low',
    guarded: 'badge-guarded',
    elevated: 'badge-elevated',
    high: 'badge-high',
    'very_high': 'badge-very-high',
  };
  return classes[band] || 'badge-low';
}

export function severityLabel(severity: string | null): string {
  if (!severity) return 'Unknown';
  return severity.charAt(0).toUpperCase() + severity.slice(1);
}

export function statusLabel(status: string): string {
  const labels: Record<string, string> = {
    submitted: 'Submitted',
    under_review: 'Under Review',
    verified: 'Verified',
    rejected: 'Rejected',
    duplicate: 'Duplicate',
  };
  return labels[status] || status;
}
