import { Outlet, Link, useLocation } from 'react-router-dom';
import { Droplets, Map as MapIcon, FilePlus, LayoutDashboard, Info, ShieldAlert } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { apiFetch } from '../lib/api';
import type { SystemCapabilities } from '../lib/types';
import { cn } from '../lib/utils';

export function Layout() {
  const location = useLocation();
  const { data: caps } = useQuery({
    queryKey: ['capabilities'],
    queryFn: () => apiFetch<SystemCapabilities>('/api/v1/system/capabilities'),
    staleTime: 120_000,
  });

  const navItems = [
    { to: '/', label: 'Home', icon: Droplets },
    { to: '/map', label: 'Map', icon: MapIcon },
    { to: '/report', label: 'Report', icon: FilePlus },
    { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/about/methodology', label: 'Methodology', icon: Info },
  ];

  const isAdminArea = location.pathname.startsWith('/dashboard');

  return (
    <div className="flex min-h-screen flex-col">
      {/* Demo mode banner */}
      {caps?.demo_mode && (
        <div className="flex items-center gap-2 bg-amber-50 border-b border-amber-200 px-4 py-1.5 text-sm text-amber-800">
          <ShieldAlert className="h-4 w-4 shrink-0" />
          <span>Demo Mode — Data is synthetic. Not for operational use.</span>
        </div>
      )}

      {/* Header */}
      <header className="sticky top-0 z-50 border-b border-slate-200 bg-white/95 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3">
          <Link to="/" className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-floodlens-600 text-white">
              <Droplets className="h-5 w-5" />
            </div>
            <span className="text-lg font-semibold text-slate-900">FloodLens AI</span>
          </Link>

          <nav className="hidden md:flex items-center gap-1">
            {navItems.map((item) => {
              const active = location.pathname === item.to;
              return (
                <Link
                  key={item.to}
                  to={item.to}
                  className={cn(
                    'flex items-center gap-1.5 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                    active ? 'bg-floodlens-50 text-floodlens-700' : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                  )}
                >
                  <item.icon className="h-4 w-4" />
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Mobile nav */}
        <nav className="flex items-center gap-1 overflow-x-auto border-t border-slate-100 px-2 py-1.5 md:hidden">
          {navItems.map((item) => {
            const active = location.pathname === item.to;
            return (
              <Link
                key={item.to}
                to={item.to}
                className={cn(
                  'flex shrink-0 items-center gap-1 rounded-lg px-2.5 py-1.5 text-xs font-medium',
                  active ? 'bg-floodlens-50 text-floodlens-700' : 'text-slate-600'
                )}
              >
                <item.icon className="h-3.5 w-3.5" />
                {item.label}
              </Link>
            );
          })}
        </nav>
      </header>

      {/* Main content */}
      <main className="flex-1">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200 bg-white px-4 py-6 text-center text-sm text-slate-500">
        <p className="mx-auto max-w-3xl">
          FloodLens AI provides community observations and data-informed risk indicators for situational
          awareness. It is not an official emergency warning system. In an emergency, contact local
          emergency services.
        </p>
        {caps && (
          <p className="mt-2 text-xs text-slate-400">
            {caps.app_env === 'local' ? 'Local Development' : caps.app_env} · {caps.ai_provider_mode} mode
          </p>
        )}
      </footer>
    </div>
  );
}
