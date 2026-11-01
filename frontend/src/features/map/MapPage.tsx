import { useEffect, useRef, useState } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import { useQuery } from '@tanstack/react-query';
import { apiFetch } from '../../lib/api';
import type { MapReportItem, RiskCellListItem, MapSummary, LayerMetadata } from '../../lib/types';
import { RiskBadge } from '../../components/RiskBadge';
import { Disclaimer } from '../../components/Disclaimer';
import { formatDate } from '../../lib/utils';

const LAGOS_CENTER: [number, number] = [3.3947, 6.4541]; // [lng, lat]

export function MapPage() {
  const mapContainer = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const [selectedReport, setSelectedReport] = useState<MapReportItem | null>(null);
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

  useEffect(() => {
    if (!mapContainer.current || mapRef.current) return;

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
          {
            id: 'background',
            type: 'raster',
            source: 'osm-tiles',
            minzoom: 0,
            maxzoom: 19,
          },
        ],
      },
      center: LAGOS_CENTER,
      zoom: 11,
    });

    map.addControl(new maplibregl.NavigationControl(), 'top-right');
    map.addControl(new maplibregl.ScaleControl(), 'bottom-left');

    map.on('load', () => {
      // Add reports source
      map.addSource('reports', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: [] },
      });

      // Add risk cells source
      map.addSource('risk-cells', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: [] },
      });

      // Report markers (circle)
      map.addLayer({
        id: 'reports-circle',
        type: 'circle',
        source: 'reports',
        paint: {
          'circle-radius': 6,
          'circle-color': [
            'match',
            ['get', 'severity'],
            'critical', '#991b1b',
            'high', '#ef4444',
            'moderate', '#f97316',
            'low', '#eab308',
            '#3380ff',
          ],
          'circle-stroke-width': 1.5,
          'circle-stroke-color': '#ffffff',
          'circle-opacity': 0.85,
        },
      });

      // Risk cells (circle for MVP — proper hex fill in production)
      map.addLayer({
        id: 'risk-cells-circle',
        type: 'circle',
        source: 'risk-cells',
        paint: {
          'circle-radius': 14,
          'circle-color': [
            'match',
            ['get', 'risk_band'],
            'very_high', '#991b1b',
            'high', '#ef4444',
            'elevated', '#f97316',
            'guarded', '#eab308',
            'low', '#22c55e',
            '#22c55e',
          ],
          'circle-opacity': 0.25,
          'circle-stroke-width': 1,
          'circle-stroke-color': [
            'match',
            ['get', 'risk_band'],
            'very_high', '#991b1b',
            'high', '#ef4444',
            'elevated', '#f97316',
            'guarded', '#eab308',
            'low', '#22c55e',
            '#22c55e',
          ],
          'circle-stroke-opacity': 0.6,
        },
      });

      // Click handler for reports
      map.on('click', 'reports-circle', (e) => {
        if (e.features && e.features[0]) {
          const props = e.features[0].properties;
          setSelectedReport(JSON.parse(props.raw || '{}'));
        }
      });

      // Cursor
      map.on('mouseenter', 'reports-circle', () => {
        map.getCanvas().style.cursor = 'pointer';
      });
      map.on('mouseleave', 'reports-circle', () => {
        map.getCanvas().style.cursor = '';
      });
    });

    mapRef.current = map;

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  // Update report markers when data changes
  useEffect(() => {
    if (!mapRef.current || !reports) return;
    const map = mapRef.current;
    if (!map.getSource('reports')) return;

    const features = reports.map((r) => ({
      type: 'Feature' as const,
      geometry: { type: 'Point' as const, coordinates: [r.longitude, r.latitude] },
      properties: {
        id: r.id,
        severity: r.severity || 'unknown',
        raw: JSON.stringify(r),
      },
    }));

    (map.getSource('reports') as maplibregl.GeoJSONSource).setData({
      type: 'FeatureCollection',
      features,
    });

    // Toggle visibility
    map.setLayoutProperty('reports-circle', 'visibility', visibleLayers.has('reports') ? 'visible' : 'none');
  }, [reports, visibleLayers]);

  // Update risk cells when data changes
  useEffect(() => {
    if (!mapRef.current || !riskCells) return;
    const map = mapRef.current;
    if (!map.getSource('risk-cells')) return;

    const features = riskCells.items.map((c) => ({
      type: 'Feature' as const,
      geometry: { type: 'Point' as const, coordinates: [c.longitude, c.latitude] },
      properties: {
        risk_band: c.risk_band,
        risk_score: c.risk_score,
        grid_index: c.grid_index,
      },
    }));

    (map.getSource('risk-cells') as maplibregl.GeoJSONSource).setData({
      type: 'FeatureCollection',
      features,
    });

    map.setLayoutProperty('risk-cells-circle', 'visibility', visibleLayers.has('risk-cells') ? 'visible' : 'none');
  }, [riskCells, visibleLayers]);

  const toggleLayer = (id: string) => {
    setVisibleLayers((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
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
            className="h-[400px] w-full overflow-hidden rounded-lg border border-slate-200 md:h-[600px]"
            role="application"
            aria-label="Interactive flood map"
          />

          {/* Legend */}
          <div className="mt-2 flex flex-wrap items-center gap-3 rounded-lg border border-slate-200 bg-white p-3 text-sm">
            <span className="font-medium text-slate-700">Legend:</span>
            <div className="flex items-center gap-1">
              <span className="h-3 w-3 rounded-full bg-red-900" aria-hidden="true" />
              <span>Very High</span>
            </div>
            <div className="flex items-center gap-1">
              <span className="h-3 w-3 rounded-full bg-red-500" aria-hidden="true" />
              <span>High</span>
            </div>
            <div className="flex items-center gap-1">
              <span className="h-3 w-3 rounded-full bg-orange-500" aria-hidden="true" />
              <span>Elevated</span>
            </div>
            <div className="flex items-center gap-1">
              <span className="h-3 w-3 rounded-full bg-yellow-500" aria-hidden="true" />
              <span>Guarded</span>
            </div>
            <div className="flex items-center gap-1">
              <span className="h-3 w-3 rounded-full bg-green-500" aria-hidden="true" />
              <span>Low</span>
            </div>
            <span className="ml-auto text-xs text-slate-400">
              Last updated: {summary ? formatDate(summary.last_updated) : '—'}
            </span>
          </div>
        </div>

        {/* Side panel */}
        <div className="w-full md:w-72 space-y-4">
          {/* Summary */}
          {summary && (
            <div className="card p-4">
              <h3 className="font-medium text-slate-900">Summary</h3>
              <dl className="mt-2 space-y-1 text-sm">
                <div className="flex justify-between">
                  <dt className="text-slate-600">Total reports</dt>
                  <dd className="font-medium">{summary.total_reports}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-slate-600">Verified</dt>
                  <dd className="font-medium">{summary.verified_incidents}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-slate-600">Pending</dt>
                  <dd className="font-medium">{summary.pending_reports}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-slate-600">High-risk zones</dt>
                  <dd className="font-medium">{summary.high_risk_cells}</dd>
                </div>
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
                <select
                  id="status-filter"
                  className="input"
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                >
                  <option value="">All</option>
                  <option value="submitted">Submitted</option>
                  <option value="under_review">Under Review</option>
                  <option value="verified">Verified</option>
                </select>
              </div>
              <div>
                <label className="label" htmlFor="hazard-filter">Hazard Type</label>
                <select
                  id="hazard-filter"
                  className="input"
                  value={hazardFilter}
                  onChange={(e) => setHazardFilter(e.target.value)}
                >
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
                  <label key={l.id} className="flex items-center gap-2 text-sm">
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

          {/* Selected report */}
          {selectedReport && (
            <div className="card p-4">
              <h3 className="font-medium text-slate-900">Selected Report</h3>
              <dl className="mt-2 space-y-1 text-sm">
                <div className="flex justify-between">
                  <dt className="text-slate-600">Type</dt>
                  <dd>{selectedReport.report_type}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-slate-600">Hazard</dt>
                  <dd>{selectedReport.hazard_type || '—'}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-slate-600">Severity</dt>
                  <dd>{selectedReport.severity || '—'}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-slate-600">Status</dt>
                  <dd>{selectedReport.status}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-slate-600">Reported</dt>
                  <dd>{formatDate(selectedReport.submitted_at)}</dd>
                </div>
              </dl>
            </div>
          )}

          {/* Disclaimer */}
          <Disclaimer compact />
        </div>
      </div>
    </div>
  );
}
