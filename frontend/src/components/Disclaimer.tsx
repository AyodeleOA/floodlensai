import { ShieldAlert } from 'lucide-react';

export function Disclaimer({ compact = false }: { compact?: boolean }) {
  return (
    <div className={`rounded-lg border border-amber-200 bg-amber-50 ${compact ? 'p-3' : 'p-4'}`}>
      <div className="flex gap-2">
        <ShieldAlert className="h-5 w-5 shrink-0 text-amber-600" aria-hidden="true" />
        <div className="text-sm text-amber-900">
          <p className="font-medium">Public Safety Notice</p>
          <p className={`mt-1 ${compact ? '' : 'leading-relaxed'}`}>
            FloodLens AI provides community observations and data-informed risk indicators for situational
            awareness. It is not an official emergency warning system, does not guarantee that any location
            is safe, and does not replace instructions from emergency-management authorities. Risk estimates
            may be incomplete or inaccurate where observations or environmental data are missing, delayed, or
            unverified. In an emergency, contact the appropriate local emergency services and follow official
            guidance.
          </p>
        </div>
      </div>
    </div>
  );
}
