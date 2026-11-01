import { Link } from 'react-router-dom';
import { Droplets, Map as MapIcon, FilePlus, ShieldCheck, Users, Eye, Activity } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { apiFetch } from '../../lib/api';
import type { SystemCapabilities } from '../../lib/types';
import { Disclaimer } from '../../components/Disclaimer';

export function LandingPage() {
  const { data: caps } = useQuery({
    queryKey: ['capabilities'],
    queryFn: () => apiFetch<SystemCapabilities>('/api/v1/system/capabilities'),
    staleTime: 120_000,
  });

  return (
    <div className="mx-auto max-w-5xl px-4 py-8 md:py-12">
      {/* Hero */}
      <section className="text-center">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-floodlens-600 text-white">
          <Droplets className="h-8 w-8" />
        </div>
        <h1 className="mt-4 text-3xl font-bold text-slate-900 md:text-4xl">
          FloodLens AI
        </h1>
        <p className="mx-auto mt-3 max-w-2xl text-lg text-slate-600">
          Community-powered flood observation, geospatial risk mapping, and
          decision-support for African communities.
        </p>
        <div className="mt-6 flex flex-wrap justify-center gap-3">
          <Link to="/map" className="btn-primary">
            <MapIcon className="h-4 w-4" />
            View Flood Map
          </Link>
          <Link to="/report" className="btn-secondary">
            <FilePlus className="h-4 w-4" />
            Report Flooding
          </Link>
        </div>
        {caps?.demo_mode && (
          <p className="mt-3 text-sm text-amber-600">
            Demo Mode — showing synthetic data for Lagos, Nigeria
          </p>
        )}
      </section>

      {/* How it works */}
      <section className="mt-12">
        <h2 className="text-xl font-semibold text-slate-900">How It Works</h2>
        <div className="mt-4 grid gap-4 md:grid-cols-3">
          <div className="card p-5">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-floodlens-50 text-floodlens-600">
              <Users className="h-5 w-5" />
            </div>
            <h3 className="mt-3 font-medium text-slate-900">1. Community Reports</h3>
            <p className="mt-1 text-sm text-slate-600">
              Residents submit photos, location, and observations of flooding,
              blocked drains, and road damage — even on low-bandwidth connections.
            </p>
          </div>
          <div className="card p-5">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-floodlens-50 text-floodlens-600">
              <Eye className="h-5 w-5" />
            </div>
            <h3 className="mt-3 font-medium text-slate-900">2. AI-Assisted Analysis</h3>
            <p className="mt-1 text-sm text-slate-600">
              Muse Spark identifies visible hazards in submitted photos. SAM 3.1
              segments floodwater, drains, and debris. All results include
              confidence and limitations.
            </p>
          </div>
          <div className="card p-5">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-floodlens-50 text-floodlens-600">
              <Activity className="h-5 w-5" />
            </div>
            <h3 className="mt-3 font-medium text-slate-900">3. Risk Mapping</h3>
            <p className="mt-1 text-sm text-slate-600">
              A transparent Flood Risk Index combines observations, rainfall,
              terrain, drainage, and exposure into explainable risk indicators
              shown on interactive maps.
            </p>
          </div>
        </div>
      </section>

      {/* Key principles */}
      <section className="mt-10">
        <h2 className="text-xl font-semibold text-slate-900">Principles</h2>
        <div className="mt-4 grid gap-3 md:grid-cols-2">
          {[
            { icon: ShieldCheck, title: 'Human Verification', desc: 'AI assists but never makes consequential decisions alone.' },
            { icon: Eye, title: 'Explainable Risk', desc: 'Every risk score shows contributing factors, sources, and data gaps.' },
            { icon: Users, title: 'Privacy by Default', desc: 'Reporter identity and contact details are never exposed publicly.' },
            { icon: Droplets, title: 'Low-Bandwidth First', desc: 'Designed for modest Android devices and poor connectivity.' },
          ].map((p) => (
            <div key={p.title} className="flex items-start gap-3 rounded-lg border border-slate-200 bg-white p-4">
              <p.icon className="h-5 w-5 shrink-0 text-floodlens-600" aria-hidden="true" />
              <div>
                <p className="font-medium text-slate-900">{p.title}</p>
                <p className="text-sm text-slate-600">{p.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Model status preview */}
      {caps && (
        <section className="mt-10">
          <h2 className="text-xl font-semibold text-slate-900">AI Model Status</h2>
          <div className="mt-4 grid gap-2 sm:grid-cols-3">
            {caps.model_statuses.map((m) => (
              <div key={m.id} className="flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2">
                <span className={`h-2.5 w-2.5 rounded-full ${
                  m.status === 'connected' ? 'bg-green-500' :
                  m.status === 'demo_mode' ? 'bg-amber-400' :
                  'bg-slate-300'
                }`} aria-hidden="true" />
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium text-slate-900">{m.id}</p>
                  <p className="text-xs text-slate-500">
                    {m.status === 'demo_mode' ? 'Demo Mode' :
                     m.status === 'connected' ? 'Connected' : 'Not Configured'}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Disclaimer */}
      <section className="mt-10">
        <Disclaimer />
      </section>
    </div>
  );
}
