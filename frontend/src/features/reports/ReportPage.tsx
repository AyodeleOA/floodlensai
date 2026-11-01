import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useMutation } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { Camera, MapPin, Mic, Send, Check } from 'lucide-react';
import { apiFetch } from '../../lib/api';
import type { ReportCreated } from '../../lib/types';
import { Disclaimer } from '../../components/Disclaimer';

const reportSchema = z.object({
  report_type: z.enum(['flooding', 'drainage', 'road_damage', 'other'], {
    errorMap: () => ({ message: 'Select a hazard category' }),
  }),
  description: z.string().max(5000).optional(),
  latitude: z.number().min(-90).max(90, { message: 'Invalid latitude' }),
  longitude: z.number().min(-180).max(180, { message: 'Invalid longitude' }),
  severity: z.enum(['low', 'moderate', 'high', 'critical', 'unknown']).optional(),
  landmark: z.string().max(255).optional(),
  water_level: z.enum(['ankle', 'knee', 'waist', 'above_waist']).optional(),
  affects_roads: z.boolean().optional(),
  affects_homes: z.boolean().optional(),
  affects_shops: z.boolean().optional(),
  affects_facilities: z.boolean().optional(),
  reporter_contact: z.string().max(255).optional(),
  privacy_consent: z.boolean().refine((v) => v, { message: 'You must acknowledge the privacy notice' }),
});

type ReportFormData = z.infer<typeof reportSchema>;

export function ReportPage() {
  const navigate = useNavigate();
  const [locationStatus, setLocationStatus] = useState<'idle' | 'getting' | 'success' | 'error'>('idle');

  const { register, handleSubmit, setValue, watch, formState: { errors } } = useForm<ReportFormData>({
    resolver: zodResolver(reportSchema),
    defaultValues: {
      report_type: 'flooding',
      latitude: 6.4541,
      longitude: 3.3947,
      privacy_consent: false,
    },
  });

  const mutation = useMutation({
    mutationFn: (data: ReportFormData) => {
      return apiFetch<ReportCreated>('/api/v1/reports', {
        method: 'POST',
        body: JSON.stringify(data),
      });
    },
    onSuccess: (data) => {
      navigate(`/report/${data.id}`);
    },
  });

  const getLocation = () => {
    setLocationStatus('getting');
    if (!navigator.geolocation) {
      setLocationStatus('error');
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setValue('latitude', Number(pos.coords.latitude.toFixed(6)));
        setValue('longitude', Number(pos.coords.longitude.toFixed(6)));
        setLocationStatus('success');
      },
      () => setLocationStatus('error'),
      { enableHighAccuracy: true, timeout: 10_000 }
    );
  };

  const onSubmit = (data: ReportFormData) => {
    mutation.mutate(data);
  };

  return (
    <div className="mx-auto max-w-2xl px-4 py-6">
      <h1 className="text-2xl font-bold text-slate-900">Report Flooding</h1>
      <p className="mt-1 text-sm text-slate-600">
        Submit a flood or drainage observation with your location and details.
      </p>

      <form onSubmit={handleSubmit(onSubmit)} className="mt-6 space-y-5">
        {/* Hazard type */}
        <div>
          <label className="label" htmlFor="report_type">Hazard Category <span className="text-red-500">*</span></label>
          <select id="report_type" className="input" {...register('report_type')}>
            <option value="flooding">Flooding</option>
            <option value="drainage">Drainage Issue</option>
            <option value="road_damage">Road Damage</option>
            <option value="other">Other</option>
          </select>
          {errors.report_type && <p className="mt-1 text-sm text-red-500">{errors.report_type.message}</p>}
        </div>

        {/* Location */}
        <div>
          <label className="label">
            Location (GPS or coordinates) <span className="text-red-500">*</span>
          </label>
          <div className="flex gap-2">
            <input
              type="number"
              step="0.000001"
              className="input"
              placeholder="Latitude"
              {...register('latitude', { valueAsNumber: true })}
              aria-label="Latitude"
            />
            <input
              type="number"
              step="0.000001"
              className="input"
              placeholder="Longitude"
              {...register('longitude', { valueAsNumber: true })}
              aria-label="Longitude"
            />
            <button
              type="button"
              className="btn-secondary shrink-0"
              onClick={getLocation}
              disabled={locationStatus === 'getting'}
            >
              {locationStatus === 'getting' ? (
                <span className="animate-pulse">...</span>
              ) : locationStatus === 'success' ? (
                <Check className="h-4 w-4 text-green-500" />
              ) : (
                <MapPin className="h-4 w-4" />
              )}
              <span className="hidden sm:inline">GPS</span>
            </button>
          </div>
          {errors.latitude && <p className="mt-1 text-sm text-red-500">{errors.latitude.message}</p>}
          {errors.longitude && <p className="mt-1 text-sm text-red-500">{errors.longitude.message}</p>}
          {locationStatus === 'error' && (
            <p className="mt-1 text-sm text-amber-600">Could not get GPS location. Enter coordinates manually.</p>
          )}
          <p className="mt-1 text-xs text-slate-500">Default: Lagos, Nigeria. Tap GPS to use your current location.</p>
        </div>

        {/* Severity */}
        <div>
          <label className="label" htmlFor="severity">Severity (self-reported)</label>
          <select id="severity" className="input" {...register('severity')}>
            <option value="">Unknown</option>
            <option value="low">Low</option>
            <option value="moderate">Moderate</option>
            <option value="high">High</option>
            <option value="critical">Critical</option>
          </select>
          <p className="mt-1 text-xs text-slate-500">Self-reported severity is approximate and unverified.</p>
        </div>

        {/* Water level */}
        <div>
          <label className="label" htmlFor="water_level">Water Level (if applicable)</label>
          <select id="water_level" className="input" {...register('water_level')}>
            <option value="">Not specified</option>
            <option value="ankle">Ankle</option>
            <option value="knee">Knee</option>
            <option value="waist">Waist</option>
            <option value="above_waist">Above waist</option>
          </select>
        </div>

        {/* Description */}
        <div>
          <label className="label" htmlFor="description">Description</label>
          <textarea
            id="description"
            className="input min-h-[100px]"
            placeholder="Describe what you see — floodwater, blocked drains, road conditions, etc."
            {...register('description')}
          />
        </div>

        {/* Landmark */}
        <div>
          <label className="label" htmlFor="landmark">Nearest Landmark / Road</label>
          <input id="landmark" className="input" placeholder="e.g. Near Lagos Island roundabout" {...register('landmark')} />
        </div>

        {/* Affected areas */}
        <fieldset>
          <legend className="label">What is affected?</legend>
          <div className="flex flex-wrap gap-4">
            {[
              { name: 'affects_roads' as const, label: 'Roads' },
              { name: 'affects_homes' as const, label: 'Homes' },
              { name: 'affects_shops' as const, label: 'Shops' },
              { name: 'affects_facilities' as const, label: 'Facilities' },
            ].map((cb) => (
              <label key={cb.name} className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  className="h-4 w-4 rounded border-slate-300 text-floodlens-600 focus:ring-floodlens-500"
                  {...register(cb.name)}
                />
                {cb.label}
              </label>
            ))}
          </div>
        </fieldset>

        {/* Reporter contact (private) */}
        <div>
          <label className="label" htmlFor="reporter_contact">
            Contact for follow-up (private — never shown publicly)
          </label>
          <input
            id="reporter_contact"
            className="input"
            placeholder="Phone or email (optional)"
            {...register('reporter_contact')}
          />
        </div>

        {/* Privacy consent */}
        <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
          <label className="flex items-start gap-2">
            <input
              type="checkbox"
              className="mt-0.5 h-4 w-4 rounded border-slate-300 text-floodlens-600 focus:ring-floodlens-500"
              {...register('privacy_consent')}
            />
            <span className="text-sm text-slate-700">
              I acknowledge that my report location and details will be shared with authorised
              reviewers. My contact details will remain private. This is not an emergency alert system.
            </span>
          </label>
          {errors.privacy_consent && <p className="mt-1 text-sm text-red-500">{errors.privacy_consent.message}</p>}
        </div>

        {/* Photo placeholder */}
        <div className="rounded-lg border border-dashed border-slate-300 bg-slate-50 p-4 text-center">
          <Camera className="mx-auto h-8 w-8 text-slate-400" />
          <p className="mt-2 text-sm text-slate-500">Photo upload available after report submission</p>
          <p className="text-xs text-slate-400">You can add photos via the report receipt page</p>
        </div>

        {/* Voice placeholder */}
        <div className="rounded-lg border border-dashed border-slate-300 bg-slate-50 p-4 text-center">
          <Mic className="mx-auto h-8 w-8 text-slate-400" />
          <p className="mt-2 text-sm text-slate-500">Voice note upload available after submission</p>
        </div>

        {/* Submit */}
        <div className="flex items-center gap-3">
          <button type="submit" className="btn-primary" disabled={mutation.isPending}>
            <Send className="h-4 w-4" />
            {mutation.isPending ? 'Submitting...' : 'Submit Report'}
          </button>
          {mutation.isError && (
            <p className="text-sm text-red-500">
              Error: {mutation.error instanceof Error ? mutation.error.message : 'Submission failed'}
            </p>
          )}
        </div>
      </form>

      <div className="mt-6">
        <Disclaimer compact />
      </div>
    </div>
  );
}
