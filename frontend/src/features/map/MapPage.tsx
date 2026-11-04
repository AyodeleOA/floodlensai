import { useEffect, useRef, useState, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import { useQuery } from '@tanstack/react-query';
import { apiFetch } from '../../lib/api';
import type { MapReportItem, RiskCellListItem, MapSummary, LayerMetadata } from '../../lib/types';
import { Disclaimer } from '../../components/Disclaimer';
import { formatDate } from '../../lib/utils';

const LAGOS_CENTER: [number, number] = [3.3947, 6.4541]; // [lng, lat]

const SEVERITY_COLORS: Record<string, string> = {
  critical: '#991b1b',
  high: '#ef4444',
  moderate: '#f97316',
  low: '#eab308',
};

const STATUS_LABELS: Record<string, string> = {
  submitted: 'Submitted',
  under_review: 'Under Review',
  verified: 'Verified',
  rejected: 'Rejected',
};

export function MapPage() {
  const navigate = useNavigate();
  const mapContainer = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const popupRef = useRef<maplibregl.Popup | null>(null);
  const [visibleLayers, setVisibleLayers] = useState<Set<string>>(new Set(['reports', 'risk-cells']));
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [hazardFilter, setHazardFilter] = useState<string>('');

  const { data: reports } = useQuery({
    queryKey: ['map-reports', statusFilter, hazardFilter],
    queryFn: () => {
      const params = new URLSearchParams({ limit: '500' });
      if (statusFilter) params.set('status', statusFilter);
      if (hazardFilter) params.set('hazard', hazardFilter);
      return apiFetch<MapReportItem[]>(`/api/v1/map/reports?${params}`);
    },
  });

  const { data: riskCells } = useQuery({
    queryKey: ['map-risk-cells'],
    queryFn: () => apiFetch<{ items: RiskCellListItem[] }>('/api/v1/map/risk-cells?limit=500'),
  });

  const { data: summary } = useQuery({
    queryKey: ['map-summary'],
    queryFn: () => apiFetch<MapSummary>('/api/v1/map/summary'),
    staleTime: 60_000,
  });

  const { data: layers } = useQuery({
    queryKey: ['layers'],
    queryFn: () => apiFetch<LayerMetadata[]>('/api/v1/map/layers'),
  });

  // Build popup HTML for a report marker
  const buildPopupHTML = useCallback((r: MapReportItem): string => {
    const severityBadge = r.severity
      ? `<span style="background:${SEVERITY_COLORS[r.severity] ?? '#94a3b8'};color:#fff;padding:2px 6px;border-radius:4px;font-size:11px;">${r.severity}</span>`
      : '';
    const statusLabel = STATUS_LABELS[r.status] ?? r.status;
    const syntheticNote = r.is_synthetic ? '<p style="margin:4px 0 0;font-size:10px;color:#d97706;">Demo data</p>' : '';
    const hazard = r.hazard_type ? r.hazard_type.replace(/_/g, ' ') : '—';
    const date = new Date(r.submitted_at).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });

    return `
      <div style="min-width:200px;font-family:system-ui,sans-serif;">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;">
          <strong style="font-size:13px;color:#0f172a;">${r.report_type.replace(/_/g, ' ')}</strong>
          ${severityBadge}
        </div>
        <table style="width:100%;font-size:12px;border-collapse:collapse;">
          <tr><td style="color:#64748b;padding:2px 0;">Hazard</td><td style="color:#1e293b;">${hazard}</td></tr>
          <tr><td style="color:#64748b;padding:2px 0;">Status</td><td style="color:#1e293b;">${statusLabel}</td></tr>
          <tr><td style="color:#64748b;padding:2px 0;">Date</td><td style="color:#1e293b;">${date}</td></tr>
        </table>
        ${syntheticNote}
        <div style="margin-top:10px;">
          <a
            href="/reports/${r.id}"
            style="display:inline-block;background:#3380ff;color:#fff;padding:5px 12px;border-radius:6px;font-size:12px;font-weight:500;text-decoration:none;"
            onclick="window.__floodlensNavigate && window.__floodlensNavigate('/reports/${r.id}'); return false;"
          >View Full Report →</a>
        </div>
      </div>
    `;
  }, []);

  useEffect(() => {
    if (!mapContainer.current || mapRef.current) return;

    // Expose navigate for popup link clicks
    (window as any).__floodlensNavigate = (path: string) => navigate(path);

    const map = new maplibregl.Map({
      container: mapContainer.current,
      style: {
        version: 8,
        sources: {
          'osm-tiles': {
            type: 'raster',
            tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
            tileSize: 256,
            attribution: '&copy; OpenStreetMap contributors',
          },
        },
        layers: [
          { id: 'background', type: 'raster', source: 'osm-tiles', minzoom: 0, maxzoom: 19 },
        ],
      },
      center: LAGOS_CENTER,
      zoom: 11,
    });

    map.addControl(new maplibregl.NavigationControl(), 'top-right');
    map.addControl(new maplibregl.ScaleControl(), 'bottom-left');

    map.on('load', () => {
      map.addSource('reports', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } });
      map.addSource('risk-cells', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } });

      // Risk cell fill (behind report markers)
      map.addLayer({
        id: 'risk-cells-circle',
        type: 'circle',
        source: 'risk-cells',
        paint: {
          'circle-radius': 16,
          'circle-color': ['match', ['get', 'risk_band'],
            'very_high', '#991b1b', 'high', '#ef4444', 'elevated', '#f97316',
            'guarded', '#eab308', 'low', '#22c55e', '#22c55e'],
          'circle-opacity': 0.2,
          'circle-stroke-width': 1.5,
          'circle-stroke-color': ['match', ['get', 'risk_band'],
            'very_high', '#991b1b', 'high', '#ef4444', 'elevated', '#f97316',
            'guarded', '#eab308', 'low', '#22c55e', '#22c55e'],
          'circle-stroke-opacity': 0.5,
        },
      });

      // Report markers (on top)
      map.addLayer({
        id: 'reports-circle',
        type: 'circle',
        source: 'reports',
        paint: {
          'circle-radius': ['interpolate', ['linear'], ['zoom'], 10, 6, 14, 9],
          'circle-color': ['match', ['get', 'severity'],
            'critical', '#991b1b', 'high', '#ef4444', 'moderate', '#f97316', 'low', '#eab308', '#3380ff'],
          'circle-stroke-width': 2,
          'circle-stroke-color': '#ffffff',
          'circle-opacity': 0.9,
        },
      });

      // Click — show popup
      map.on('click', 'reports-circle', (e) => {
        if (!e.features?.[0]) return;
        const props = e.features[0].properties;
        const report: MapReportItem = JSON.parse(props.raw ?? '{}');
        const coords = (e.features[0].geometry as GeoJSON.Point).coordinates as [number, number];

        // Close existing popup
        popupRef.current?.remove();

        popupRef.current = new maplibregl.Popup({ closeButton: true, maxWidth: '280px' })
          .setLngLat(coords)
          .setHTML(buildPopupHTML(report))
          .addTo(map);
      });

      // Cursor pointer on hover
      map.on('mouseenter', 'reports-circle', () => { map.getCanvas().style.cursor = 'pointer'; });
      map.on('mouseleave', 'reports-circle', () => { map.getCanvas().style.cursor = ''; });

      // Close popup when clicking empty map
      map.on('click', (e) => {
        const features = map.queryRenderedFeatures(e.point, { layers: ['reports-circle'] });
        if (features.length === 0) popupRef.current?.remove();
      });
    });

    mapRef.current = map;

    return () => {
      (window as any).__floodlensNavigate = undefined;
      popupRef.current?.remove();
      map.remove();
      mapRef.current = null;
    };
  }, [buildPopupHTML, navigate]);

  // Update report markers
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !reports) return;
    if (!map.getSource('reports')) return;

    const features = reports.map((r) => ({
      type: 'Feature' as const,
      geometry: { type: 'Point' as const, coordinates: [r.longitude, r.latitude] },
      properties: { id: r.id, severity: r.severity ?? 'unknown', raw: JSON.stringify(r) },
    }));

    (map.getSource('reports') as maplibregl.GeoJSONSource).setData({ type: 'FeatureCollection', features });
    map.setLayoutProperty('reports-circle', 'visibility', visibleLayers.has('reports') ? 'visible' : 'none');
  }, [reports, visibleLayers]);

  // Update risk cells
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !riskCells) return;
    if (!map.getSource('risk-cells')) return;

    const features = riskCells.items.map((c) => ({
      type: 'Feature' as const,
      geometry: { type: 'Point' as const, coordinates: [c.longitude, c.latitude] },
      properties: { risk_band: c.risk_band, risk_score: c.risk_score },
    }));

    (map.getSource('risk-cells') as maplibregl.GeoJSONSource).setData({ type: 'FeatureCollection', features });
    map.setLayoutProperty('risk-cells-circle', 'visibility', visibleLayers.has('risk-cells') ? 'visible' : 'none');
  }, [riskCells, visibleLayers]);

  const toggleLayer = (id: string) => {
    setVisibleLayers((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  };

  return (
    <div className="mx-auto max-w-7xl px-4 py-4">
      <div className="flex flex-col gap-4 md:flex-row">
        {/* Map */}
        <div className="flex-1">
          <div
            ref={mapContainer}
            className="h-[450px] w-full overflow-hidden rounded-lg border border-slate-200 md:h-[620px]"
            role="application"
            aria-label="Interactive flood map — click a marker to view report details"
          />

          {/* Legend */}
          <div className="mt-2 flex flex-wrap items-center gap-3 rounded-lg border border-slate-200 bg-white p-3 text-sm">
            <span className="font-medium text-slate-700">Report severity:</span>
            {[
              { label: 'Critical', color: 'bg-red-900' },
              { label: 'High', color: 'bg-red-500' },
              { label: 'Moderate', color: 'bg-orange-500' },
              { label: 'Low', color: 'bg-yellow-400' },
              { label: 'Unknown', color: 'bg-floodlens-500' },
            ].map(({ label, color }) => (
              <span key={label} className="flex items-center gap-1">
                <span className={`h-3 w-3 rounded-full ${color}`} aria-hidden="true" />
                <span className="text-xs text-slate-600">{label}</span>
              </span>
            ))}
            <span className="ml-auto text-xs text-slate-400">
              Updated: {summary ? formatDate(summary.last_updated) : '—'}
            </span>
          </div>

          {/* Report list (clickable) */}
          {reports && reports.length > 0 && (
            <div className="mt-4">
              <p className="mb-2 text-sm font-medium text-slate-700">
                Reports ({reports.length}) — click a row or map marker to view details
              </p>
              <div className="space-y-1.5">
                {reports.slice(0, 15).map((r) => (
                  <Link
                    key={r.id}
                    to={`/reports/${r.id}`}
                    className="card flex items-center justify-between px-3 py-2 transition-colors hover:bg-slate-50"
                  >
                    <div className="min-w-0 flex items-center gap-2">
                      <span
                        className="h-2.5 w-2.5 shrink-0 rounded-full"
                        style={{ background: SEVERITY_COLORS[r.severity ?? ''] ?? '#3380ff' }}
                        aria-hidden="true"
                      />
                      <div className="min-w-0">
                        <span className="truncate text-sm font-medium text-slate-800">
                          {r.report_type.replace('_', ' ')}
                          {r.hazard_type ? ` — ${r.hazard_type.replace(/_/g, ' ')}` : ''}
                        </span>
                        <span className="ml-2 text-xs text-slate-400">{STATUS_LABELS[r.status] ?? r.status}</span>
                        {r.is_synthetic && <span className="ml-1 text-xs text-amber-500">demo</span>}
                      </div>
                    </div>
                    <span className="ml-3 shrink-0 text-xs text-floodlens-600">Details →</span>
                  </Link>
                ))}
                {reports.length > 15 && (
                  <p className="text-center text-xs text-slate-400">
                    +{reports.length - 15} more — use filters to narrow down
                  </p>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Side panel */}
        <div className="w-full md:w-72 space-y-4">
          {/* Summary */}
          {summary && (
            <div className="card p-4">
              <h3 className="font-medium text-slate-900">Summary</h3>
              <dl className="mt-2 space-y-1 text-sm">
                {[
                  { label: 'Total reports', value: summary.total_reports },
                  { label: 'Verified', value: summary.verified_incidents },
                  { label: 'Pending', value: summary.pending_reports },
                  { label: 'High-risk zones', value: summary.high_risk_cells },
                ].map(({ label, value }) => (
                  <div key={label} className="flex justify-between">
                    <dt className="text-slate-600">{label}</dt>
                    <dd className="font-medium">{value}</dd>
                  </div>
                ))}
              </dl>
              {summary.is_seeded && (
                <p className="mt-2 text-xs text-amber-600">Showing synthetic demo data</p>
              )}
            </div>
          )}

          {/* Filters */}
          <div className="card p-4">
            <h3 className="font-medium text-slate-900">Filters</h3>
            <div className="mt-2 space-y-2">
              <div>
                <label className="label" htmlFor="status-filter">Status</label>
                <select id="status-filter" className="input" value={statusFilter} onChange={e => setStatusFilter(e.target.value)}>
                  <option value="">All</option>
                  <option value="submitted">Submitted</option>
                  <option value="under_review">Under Review</option>
                  <option value="verified">Verified</option>
                </select>
              </div>
              <div>
                <label className="label" htmlFor="hazard-filter">Hazard Type</label>
                <select id="hazard-filter" className="input" value={hazardFilter} onChange={e => setHazardFilter(e.target.value)}>
                  <option value="">All</option>
                  <option value="floodwater">Floodwater</option>
                  <option value="blocked_drain">Blocked Drain</option>
                  <option value="overflowing_drain">Overflowing Drain</option>
                  <option value="damaged_road">Damaged Road</option>
                  <option value="exposed_infrastructure">Exposed Infrastructure</option>
                </select>
              </div>
            </div>
          </div>

          {/* Layers */}
          {layers && (
            <div className="card p-4">
              <h3 className="font-medium text-slate-900">Layers</h3>
              <div className="mt-2 space-y-1.5">
                {layers.map((l) => (
                  <label key={l.id} className="flex items-center gap-2 text-sm cursor-pointer">
                    <input
                      type="checkbox"
                      className="h-4 w-4 rounded border-slate-300 text-floodlens-600 focus:ring-floodlens-500"
                      checked={visibleLayers.has(l.id)}
                      onChange={() => toggleLayer(l.id)}
                    />
                    <span className="text-slate-700">{l.name}</span>
                    {l.is_seeded && <span className="text-xs text-amber-500">· demo</span>}
                  </label>
                ))}
              </div>
            </div>
          )}

          {/* Risk cell legend */}
          <div className="card p-4">
            <h3 className="font-medium text-slate-900">Risk Zones</h3>
            <div className="mt-2 space-y-1.5">
              {[
                { label: 'Very High (80–100)', color: 'bg-red-900' },
                { label: 'High (60–79)', color: 'bg-red-500' },
                { label: 'Elevated (40–59)', color: 'bg-orange-500' },
                { label: 'Guarded (20–39)', color: 'bg-yellow-400' },
                { label: 'Low (0–19)', color: 'bg-green-500' },
              ].map(({ label, color }) => (
                <div key={label} className="flex items-center gap-2 text-sm">
                  <span className={`h-3 w-3 rounded-full ${color} opacity-70`} aria-hidden="true" />
                  <span className="text-slate-600 text-xs">{label}</span>
                </div>
              ))}
              <p className="mt-1 text-xs text-amber-600">Illustrative — unvalidated</p>
            </div>
          </div>

          {/* Disclaimer */}
          <Disclaimer compact />
        </div>
      </div>
    </div>
  );
}
