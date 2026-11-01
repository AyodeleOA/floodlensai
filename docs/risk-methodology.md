# FloodLens AI — Risk Methodology

## Flood Risk Index (FRI)

The FRI is a transparent, configurable decision-support indicator. It is **not** a hydrological forecast or official warning.

## Scoring Dimensions (0–100)

| Dimension | Max | Inputs |
|---|---|---|
| Observed Flooding | 30 | Verified reports, observed extent, recurrence, evidence quality |
| Rainfall Conditions | 25 | Recent accumulation, forecast (if configured) |
| Terrain Susceptibility | 20 | Elevation, slope, depressions, flow accumulation |
| Drainage Condition | 15 | Proximity to drainage, blockage reports, density/gaps |
| Exposure / Vulnerability | 10 | Roads, markets, schools, health facilities, settlements |

Weights are in configuration, labelled `illustrative_unvalidated` until calibrated.

## Risk Bands

| Band | Range |
|---|---|
| Low | 0–19 |
| Guarded | 20–39 |
| Elevated | 40–59 |
| High | 60–79 |
| Very High | 80–100 |

Visual styling uses neutral tones + text + icons. Never relies on colour alone.

## Missing Data Handling

- Missing inputs are **not** treated as zero risk.
- Re-normalise only across available dimensions.
- Lower confidence score when data is missing.
- Each risk cell records `missing_inputs[]`.

## Confidence and Freshness

Every risk cell includes: `risk_score`, `risk_band`, `confidence_score`, `data_completeness`, `calculation_version`, `calculated_at`, `valid_until`, `contributing_factors[]`, `missing_inputs[]`, `source_ids[]`.

High score with low confidence is visibly labelled as needing verification.

## Grid Aggregation

- H3 hexagonal grid (configurable resolution, default 8).
- Reports assigned to grid cells via coordinates.
- Aggregation within configurable time window.
- Duplicate protection via media hashes, time/location proximity, moderator review.
- Point-level evidence stored separately from aggregated risk cells.
- No interpolation beyond data coverage without low-confidence marking.
