# FloodLens AI — Data Sources

## Initial Demo Geography

Lagos, Nigeria is the initial demonstration geography. The application supports multiple cities through configuration and database records.

All demo data is synthetic and clearly labelled `is_synthetic=true` / `is_illustrative=true`.

## Data Sources

| Source | Type | Licence | Coverage |
|---|---|---|---|
| NASA GPM IMERG | Rainfall | Public Domain | Lagos (demo) |
| Copernicus DEM | Elevation | Copernicus Programme | Lagos (demo) |
| OpenStreetMap | Drainage / Roads / Waterways | ODbL | Lagos (partial) |
| Lagos Facilities | Facilities | Open Government Data | Lagos (demo) |

## Ingestion Behaviour

Each source adapter has `fetch`, `validate`, `normalise`, `persist`, and `health_check` operations.

- Scheduled jobs (EventBridge / worker) for periodic ingestion
- Raw source files persisted in S3
- Normalised geospatial features in PostGIS
- Failed ingestion attempts and source freshness recorded
- Seeded GeoJSON for the demo map when external feeds unavailable
- Seeded data is never labelled as live data

## Data Source Records

The `data_sources` table records: source name, licence, attribution, source URL, spatial/temporal coverage, retrieval date, update frequency, and limitations.
