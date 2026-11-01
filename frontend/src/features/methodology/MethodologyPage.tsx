import { Disclaimer } from '../../components/Disclaimer';

export function MethodologyPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-6">
      <h1 className="text-2xl font-bold text-slate-900">Risk Methodology</h1>

      <section className="mt-6">
        <h2 className="text-lg font-semibold text-slate-900">Flood Risk Index (FRI)</h2>
        <p className="mt-2 text-sm text-slate-600">
          FloodLens AI uses a transparent, configurable Flood Risk Index for prioritisation.
          It is a decision-support indicator, not a hydrological forecast or an official warning.
        </p>
      </section>

      <section className="mt-6">
        <h2 className="text-lg font-semibold text-slate-900">Risk Dimensions (0–100)</h2>
        <div className="mt-2 overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-left text-slate-500">
                <th className="py-2 pr-4 font-medium">Dimension</th>
                <th className="py-2 pr-4 font-medium">Max</th>
                <th className="py-2 pr-4 font-medium">Inputs</th>
              </tr>
            </thead>
            <tbody>
              {[
                { dim: 'Observed Flooding', max: 30, inputs: 'Verified reports, observed extent, recurrence, evidence quality' },
                { dim: 'Rainfall Conditions', max: 25, inputs: 'Recent accumulation, forecast (if configured)' },
                { dim: 'Terrain Susceptibility', max: 20, inputs: 'Elevation, slope, depressions, flow accumulation' },
                { dim: 'Drainage Condition', max: 15, inputs: 'Proximity to drainage, blockage reports, density/gaps' },
                { dim: 'Exposure / Vulnerability', max: 10, inputs: 'Roads, markets, schools, health facilities, settlements' },
              ].map((r) => (
                <tr key={r.dim} className="border-b border-slate-100">
                  <td className="py-2 pr-4 font-medium text-slate-700">{r.dim}</td>
                  <td className="py-2 pr-4">{r.max}</td>
                  <td className="py-2 pr-4 text-slate-600">{r.inputs}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="mt-2 text-xs text-amber-600">
          Weights are labelled <code className="rounded bg-amber-50 px-1">illustrative_unvalidated</code> until
          calibrated with local flood records and domain experts.
        </p>
      </section>

      <section className="mt-6">
        <h2 className="text-lg font-semibold text-slate-900">Risk Bands</h2>
        <div className="mt-2 flex flex-wrap gap-2">
          {[
            { band: 'Low', range: '0–19', cls: 'bg-green-100 text-green-800' },
            { band: 'Guarded', range: '20–39', cls: 'bg-yellow-100 text-yellow-800' },
            { band: 'Elevated', range: '40–59', cls: 'bg-orange-100 text-orange-800' },
            { band: 'High', range: '60–79', cls: 'bg-red-100 text-red-800' },
            { band: 'Very High', range: '80–100', cls: 'bg-red-900 text-red-100' },
          ].map((b) => (
            <div key={b.band} className={`rounded-lg px-4 py-2 text-center ${b.cls}`}>
              <p className="font-medium">{b.band}</p>
              <p className="text-xs">{b.range}</p>
            </div>
          ))}
        </div>
        <p className="mt-2 text-xs text-slate-500">
          Visual styling uses neutral tones plus clear text and icons. Never relies on colour alone.
        </p>
      </section>

      <section className="mt-6">
        <h2 className="text-lg font-semibold text-slate-900">Missing Data Handling</h2>
        <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-600">
          <li>Missing inputs are <strong>not</strong> treated as zero risk.</li>
          <li>Re-normalise only across available dimensions.</li>
          <li>Lower the confidence score when data is missing.</li>
          <li>Each risk cell records <code>missing_inputs[]</code>.</li>
        </ul>
      </section>

      <section className="mt-6">
        <h2 className="text-lg font-semibold text-slate-900">Confidence and Freshness</h2>
        <p className="mt-2 text-sm text-slate-600">
          Every risk cell includes risk_score, risk_band, confidence_score, data_completeness,
          calculation_version, calculated_at, valid_until, contributing_factors[], missing_inputs[],
          and source_ids[]. Risk confidence is separate from risk score. A high score with low
          confidence is visibly labelled as needing verification.
        </p>
      </section>

      <section className="mt-6">
        <h2 className="text-lg font-semibold text-slate-900">Grid Aggregation</h2>
        <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-600">
          <li>H3 hexagonal grid (configurable resolution, default 8).</li>
          <li>Reports assigned to grid cells via coordinates.</li>
          <li>Aggregation within configurable time window.</li>
          <li>Duplicate protection via media hashes, time/location proximity, and moderator review.</li>
          <li>Point-level evidence stored separately from aggregated risk cells.</li>
          <li>No interpolation beyond data coverage without low-confidence marking.</li>
        </ul>
      </section>

      <section className="mt-6">
        <h2 className="text-lg font-semibold text-slate-900">AI Model Limitations</h2>
        <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-600">
          <li>AI confidence is model confidence, not a calibrated probability of flooding.</li>
          <li>Models do not infer exact water depth, flow velocity, or structural integrity.</li>
          <li>Models do not predict future flood probability from a single image.</li>
          <li>All model-generated assessments require human verification for consequential decisions.</li>
          <li>Never presented as a confirmed emergency alert.</li>
        </ul>
      </section>

      <div className="mt-6">
        <Disclaimer />
      </div>
    </div>
  );
}
