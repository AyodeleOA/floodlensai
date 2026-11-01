# FloodLens AI — Project Reference for Kiro

> **Purpose:** This document is the source of truth for building the FloodLens AI demonstration platform. Kiro should read this file before making architectural or implementation decisions, follow the phases in order, and keep the implementation aligned with the acceptance criteria.
>
> **Product:** FloodLens AI — community-powered flood observation, geospatial risk mapping, and decision-support for African communities.
>
> **Primary deployment:** AWS Amplify Hosting for the React frontend, with source code maintained in GitHub. The Python FastAPI backend is developed locally in a Python virtual environment (no Docker requirement) and deployed as AWS Lambda functions exposed through Amazon API Gateway.
>
> **AI requirement:** Integrate Meta Muse models through Meta Model API and provide separate inference adapters for the open-weight Muse models.

---

## 1. Product vision

FloodLens AI helps residents, community organisations, emergency-response teams, and local authorities understand where flooding is being observed, which locations may be vulnerable, and where inspections or interventions should be prioritised.

FloodLens AI combines:

- Community-submitted photographs, optional short videos, voice reports, GPS coordinates, timestamps, and structured observations.
- Rainfall observations and, where available, rainfall forecasts.
- Terrain/elevation and derived slope information.
- Drainage networks, waterways, roads, buildings, public facilities, and other exposure layers.
- Historical incident reports and verified field observations.
- AI-assisted visual interpretation and object segmentation.

The platform converts these inputs into traceable, explainable location-based risk indicators and interactive maps.

### 1.1 Intended users

1. **Residents / community reporters:** Submit a flood or drainage report with minimal steps, including on low-bandwidth connections.
2. **Community moderators / field officers:** Review reports, correct locations, add evidence, and verify incidents.
3. **Emergency and local-authority users:** View hotspots, assess evidence, filter by severity and time, and prioritise field inspections.
4. **Public visitors:** View a carefully limited public map and preparedness information without seeing private reporter details.

### 1.2 Product principles

- Mobile-first, accessible, low-bandwidth, and usable on modest Android devices.
- Map-first, but never make the map the only way to understand an incident.
- Explainable risk scoring: show the contributing factors, source dates, confidence, and data gaps.
- Human verification for consequential decisions.
- Privacy by default: do not expose reporter identity, phone number, exact home address, or original media publicly.
- Graceful degradation when AI, rainfall feeds, or network connectivity are unavailable.
- Never present a model-generated assessment as a confirmed emergency alert.
- Do not claim predictive accuracy until the system has been calibrated and independently evaluated against local historical flood data.

---

## 2. Scope

### 2.1 MVP features — must be implemented

1. Responsive landing page explaining the product and showing a demo map.
2. Interactive flood map with:
   - Community incident markers.
   - Risk zones / grid cells.
   - Filters for time, report status, risk level, and hazard type.
   - Layer controls for rainfall, elevation, drainage, roads, waterways, and facilities.
   - Legend, scale, source attribution, and last-updated time.
3. Community report workflow:
   - Upload one or more photographs.
   - Optional short video (configurable size/duration limit).
   - Capture or manually select a location.
   - Capture time and optional reporter contact details (private).
   - Select hazard type and severity observations.
   - Optional text and voice description.
   - Save an offline draft and retry upload when connectivity returns.
   - Show a submission receipt and report status.
4. AI image analysis:
   - Identify visible floodwater, waterlogging, blocked drains, overflowing channels, damaged roads, and exposed infrastructure.
   - Return structured observations, confidence, and limitations.
   - Use SAM 3.1 to segment relevant visible objects when appropriate.
5. Voice-to-text report input using Muse Voice Transcribe.
6. Risk assessment service that combines verified observations and environmental/geospatial features.
7. Authority dashboard:
   - KPI cards for open reports, verified incidents, high-risk zones, and reports awaiting review.
   - Prioritised hotspot list.
   - Incident detail drawer with media, AI findings, evidence, data provenance, and review actions.
   - Map and list views.
8. Role-based access for public reporters, reviewers, and administrators.
9. Audit trail for moderation, risk recalculation, and administrative changes.
10. Demo data clearly labelled as synthetic / illustrative where it is not sourced from a live feed.
11. Health/status view for AI model adapters and environmental data sources.
12. GitHub repository with automated AWS Amplify frontend deployment.

### 2.2 Later enhancements — design for, but do not block MVP

- SMS / USSD / WhatsApp reporting gateway.
- Local-language voice and text support after validation for target languages.
- Community-level notifications and opt-in geofenced alerts.
- Rainfall forecast ingestion and forecast-based risk indicators.
- Hydrological modelling and calibrated flood-depth estimation.
- Satellite-derived flood extent.
- Road accessibility and safe-route planning.
- Integration with official emergency-management systems.
- Dedicated offline field-worker application.
- Multi-country / multi-tenant deployment and country-specific data governance.

### 2.3 Out of scope

- Autonomous emergency dispatch.
- Automated evacuation orders.
- Guaranteeing that a place is safe because no reports exist.
- Replacing hydrologists, emergency managers, municipal engineers, or official warnings.
- Estimating precise water depth from an ordinary photograph unless a separately validated method and calibration data are available.
- Generating authoritative flood forecasts from images alone.

---

## 3. Meta model integration requirements

All Meta API credentials must remain server-side. The browser must never call Meta Model API directly or receive `MODEL_API_KEY`.

Use a provider abstraction so the product can switch between hosted Meta Model API, local open-weight inference, and a clearly labelled demo/mock provider without changing business logic.

### 3.1 Hosted models — Meta Model API

Base URL: `https://api.meta.ai/v1`

Authentication: `Authorization: Bearer ${MODEL_API_KEY}`

Use the current official Meta Model API documentation for the exact request and response schema. Do not invent endpoint payloads or assume every model uses the same endpoint. Build typed adapters and contract tests around the documented API.

| Model | Model ID / interface | FloodLens AI responsibility | Required behaviour |
|---|---|---|---|
| Muse Spark | `muse-spark-1.3` (make version configurable) | Primary multimodal scene interpretation and structured incident assessment | Analyse submitted image(s) and contextual metadata; identify visible hazards; return schema-constrained JSON; explicitly distinguish observation from inference |
| Muse Wonder | `muse-wonder-1.0` | Complex analyst workflow and deeper synthesis of multiple reports / evidence | Optional reviewer-requested analysis; not called for every image; produce evidence-linked explanation and uncertainty |
| Muse Image | `muse-image-1.0` | Generate optional educational illustrations, UI demonstration assets, and non-authoritative preparedness visuals | Never generate or alter evidence photographs; generated images must be watermarked/labelled as AI-generated |
| Muse Voice Transcribe | `muse-voice-transcribe-1.0` | Convert resident voice reports to text | Preserve original audio privately; store transcript, language if available, timestamps, and transcription status; user can edit transcript |
| SAM 3.1 | `sam-3.1` | Segment objects / regions in submitted photos or video frames | Prompt for visible objects such as floodwater, drain opening, debris, road surface, vehicle, or building; store masks/boxes and source-media linkage |

**Muse Spark analysis output schema (normalise provider response to this internal schema):**

```json
{
  "scene_summary": "string",
  "hazards": [
    {
      "type": "floodwater | blocked_drain | overflowing_drain | damaged_road | exposed_infrastructure | other",
      "visible_evidence": "string",
      "confidence": 0.0,
      "severity_observation": "low | moderate | high | critical | unknown",
      "bounding_box": [0, 0, 0, 0],
      "requires_human_verification": true
    }
  ],
  "water_presence": "none | possible | visible | extensive | uncertain",
  "infrastructure_observations": ["string"],
  "limitations": ["string"],
  "recommended_review_actions": ["string"]
}
```

- Validate model output against a strict schema.
- Reject or safely repair malformed JSON; never silently accept unvalidated free text as structured risk data.
- Confidence is model confidence / assessment confidence, not a calibrated probability of flooding.
- Do not let the model infer exact depth, flow velocity, structural integrity, or future flood probability from a single image.
- Store model name, model version, prompt version, request ID if available, processing time, and normalised response.
- Apply retries with exponential backoff for transient errors and respect provider rate limits.
- Add per-user and per-IP request throttling, file-size limits, and cost controls.
- Cache only when the media hash and analysis configuration match; do not reuse a result for a different location/context without recording that it is reused.

### 3.2 Open-weight models — separate inference adapters

These models are not called through Meta Model API in the same way as hosted models. Create an `OpenWeightInferenceProvider` interface that calls an OpenAI-compatible private endpoint. Do not attempt to load large model weights into Amplify Hosting, Lambda, or the browser.

| Model | Deployment facts | FloodLens AI role |
|---|---|---|
| Muse Glimmer | 30B multimodal model; Apache 2.0; can run using supported runtimes such as vLLM, SGLang, llama.cpp, Ollama, or hosted inference. Published BF16 weights are around 60 GB; quantised builds are smaller. | Local / edge or separately hosted inference for offline-capable field hubs, private deployments, or fallback image interpretation. |
| Muse Spark Open | 816B total parameters / 42B active; sparse MoE. BF16 weights around 1.65 TB; NVFP4 around 537 GB. Requires specialised multi-GPU infrastructure or a suitable hosted inference provider. | Advanced optional inference profile for a separately funded GPU deployment or partner-hosted endpoint. Not a default MVP dependency. |

**Implementation rules:**

1. Build `MuseGlimmerProvider` and `MuseSparkOpenProvider` adapters with configurable base URL, model name, timeout, and health check.
2. Never bundle weights in GitHub or the frontend build.
3. Never pretend the open-weight models are running when their endpoint is not configured.
4. The demo must display an honest model status: `Connected`, `Not configured`, `Unavailable`, or `Demo mode`.
5. Provide a local development profile for Glimmer using an OpenAI-compatible local runtime (Ollama / llama.cpp / vLLM as supported by the chosen checkpoint).
6. Provide a documented Spark Open deployment profile that calls a partner-hosted endpoint or a separately provisioned GPU cluster. Keep this profile disabled unless credentials and endpoint are configured.
7. If no endpoint is available, use Muse Spark hosted inference for the user-facing workflow and clearly show that the open-weight adapter is not connected.
8. Include an integration test using a mocked OpenAI-compatible endpoint; include a separate live smoke test that is opt-in and requires credentials.
9. Record whether an analysis came from hosted Muse Spark, Muse Glimmer, Muse Spark Open, or demo fixtures.

**Important feasibility note:** Muse Spark Open is exceptionally large. The reference hardware figures are not ordinary cloud VM requirements. Treat it as an optional advanced deployment, not a requirement for a low-cost student/demo AWS environment.

### 3.3 Muse Code

Muse Code is a development coding agent, not a runtime feature of FloodLens AI. Developers may use Muse Code alongside Kiro to accelerate implementation, debugging, refactoring, and test generation. Do not expose Muse Code as an end-user feature or claim it is part of the deployed inference pipeline.

---

## 4. Flood risk methodology

FloodLens AI must use a transparent, configurable **Flood Risk Index (FRI)** for prioritisation. It is a decision-support indicator, not a hydrological forecast or an official warning.

### 4.1 Risk dimensions

For an MVP, calculate a 0–100 score from normalised, documented inputs:

- **Observed flooding (0–30):** verified recent reports, observed extent, recurrence, and evidence quality.
- **Rainfall conditions (0–25):** recent rainfall accumulation and, only if a reliable forecast source is configured, forecast rainfall.
- **Terrain susceptibility (0–20):** elevation relative to the local area, slope, depressions, and flow accumulation where data exists.
- **Drainage condition (0–15):** proximity to mapped drainage, verified blockage reports, drainage density / gaps, and inspection recency.
- **Exposure / vulnerability (0–10):** proximity to roads, markets, schools, health facilities, dense settlements, and other configured assets.

These are initial demo weights. Keep weights in configuration and label them `illustrative_unvalidated` until calibrated with local flood records and domain experts. Missing inputs must not be silently treated as zero risk. Re-normalise only across available dimensions and lower the confidence score when data is missing.

### 4.2 Risk bands

- 0–19: Low
- 20–39: Guarded
- 40–59: Elevated
- 60–79: High
- 80–100: Very High

Use neutral visual styling plus clear text and icons; never rely on colour alone.

### 4.3 Confidence and freshness

Every risk cell / location must include:

- `risk_score`
- `risk_band`
- `confidence_score`
- `data_completeness`
- `calculation_version`
- `calculated_at`
- `valid_until` or freshness state
- `contributing_factors[]`
- `missing_inputs[]`
- `source_ids[]`

Risk confidence is separate from risk score. A high score with low confidence must be visibly labelled as needing verification.

### 4.4 Geospatial aggregation

- Use a consistent grid system for the MVP (e.g. H3 hexagons or a regular grid) and store the grid resolution as configuration.
- Assign reports to grid cells using coordinates.
- Aggregate incident evidence within a configurable time window.
- Prevent duplicate reports from inflating a hotspot: use media hashes, time/location proximity, and moderator review.
- Keep point-level incident evidence and aggregated risk cells separately.
- Use PostGIS for spatial queries and geometry operations.
- Never interpolate a risk zone beyond the spatial coverage of the available data without marking it as modelled / low-confidence.

---

## 5. Environmental and geospatial data

Build a pluggable data-ingestion layer. Do not hard-code a single city or assume that open datasets contain complete drainage information.

### 5.1 Initial demo geography

Use **Lagos, Nigeria** as the initial demonstration geography unless project configuration specifies another city. The application must support multiple cities through configuration and database records, not hard-coded frontend conditions.

Use synthetic incidents for a reliable demo if live verified observations are not available. Label all synthetic records and illustrative risk surfaces clearly.

### 5.2 Data-source strategy

Potential sources to evaluate and integrate through adapters:

- **Rainfall:** NASA GPM IMERG or another documented, accessible rainfall feed. Store observation period, units, spatial resolution, source URL, and retrieval time.
- **Elevation:** Copernicus DEM or another openly licensed elevation source. Derive slope / local relative elevation only with documented processing.
- **Drainage / waterways / roads / buildings:** OpenStreetMap extracts and verified municipal GIS layers where available. OSM drainage coverage may be incomplete; show coverage gaps.
- **Flood extent / historical context:** Copernicus Emergency Management Service products, GloFAS / other suitable public datasets where access and licensing permit.
- **Administrative boundaries / population / exposure:** appropriate open government or global settlement datasets with attribution and licence tracking.

Do not scrape websites or violate dataset terms. Maintain a `data_sources` table with source name, licence, attribution, spatial/temporal coverage, retrieval date, update frequency, and limitations.

### 5.3 Data ingestion behaviour

- Each source adapter must have `fetch`, `validate`, `normalise`, `persist`, and `health_check` operations.
- Use scheduled jobs (EventBridge / worker) for periodic ingestion.
- Persist raw source files in S3 and normalised geospatial features in PostGIS.
- Record failed ingestion attempts and source freshness.
- Provide seeded GeoJSON for the demo map so the UI remains useful if an external feed is unavailable.
- Never label seeded data as live data.

---

## 6. Recommended technical architecture

Use a modular monolith for the MVP, with clear provider interfaces. Avoid premature microservices.

### 6.1 Frontend

- React + TypeScript + Vite.
- Tailwind CSS and a consistent accessible component system (shadcn/ui or equivalent).
- MapLibre GL JS for interactive maps; use a documented basemap source and correct attribution.
- TanStack Query for server state; React Hook Form + Zod for forms.
- IndexedDB for offline drafts and an upload retry queue.
- PWA manifest and service worker for installability and static asset caching.
- Responsive layout designed for mobile first, then tablet and desktop.
- Charts for rainfall / report trends and risk distribution.
- Do not put Meta API keys, AWS secret keys, or privileged credentials in Vite environment variables. Only public configuration may use `VITE_` variables.

### 6.2 Backend and runtime architecture

Recommended MVP backend:

- Python 3.12 + FastAPI, with Pydantic v2 request / response schemas.
- SQLAlchemy 2 + Alembic migrations.
- PostgreSQL with PostGIS. For local development, install PostgreSQL and the PostGIS extension directly on the developer machine; do not require Docker or Docker Compose.
- S3 for original media, thumbnails, derived masks, and source datasets.
- SQS for asynchronous media-analysis jobs.
- AWS Lambda as the default backend compute runtime, with FastAPI adapted for Lambda using Mangum (or a currently supported equivalent).
- Amazon API Gateway HTTP API as the public HTTPS API entry point, integrated with the Lambda handler. API Gateway is the gateway/routing layer; Lambda executes the Python application code.
- Separate SQS-triggered Lambda functions for short, bounded asynchronous tasks where execution time, memory, package size, and native geospatial dependencies fit Lambda limits.
- EventBridge for scheduled data ingestion and stale-risk recalculation.
- Secrets Manager for Meta API credentials and other private secrets.
- CloudWatch logs, metrics, alarms, and traces.
- AWS WAF / throttling where appropriate and supported by the selected API Gateway configuration.
- RDS PostgreSQL with PostGIS for hosted database persistence; evaluate RDS Proxy or another connection-management strategy to protect the database from Lambda connection bursts.

The frontend is hosted on AWS Amplify Hosting. Amplify does not host the Python API. API Gateway exposes the backend and invokes Lambda. Keep the Lambda deployment package compatible with Python 3.12 and the target Lambda architecture. Prefer ZIP-based Lambda packaging/deployment through AWS SAM or CDK so a local Docker installation is not required. If a dependency later requires a Lambda container image, document that as a separate AWS build/deployment choice; it must not become a local development prerequisite.

**Lambda suitability boundary:** Do not force every workload into Lambda. Keep synchronous API requests short. Use SQS for asynchronous work. If a model call, geospatial operation, batch import, or inference workload exceeds Lambda duration, memory, temporary-storage, concurrency, or package constraints, run it on a separately provisioned service such as ECS Fargate, AWS Batch, or a dedicated inference endpoint. This is an exception for workloads that need it, not the default API hosting architecture. Never run long-running analysis inside an API Gateway request.

### 6.3 AWS deployment topology

```text
Residents / Authority users
          |
          v
AWS Amplify Hosting (React + Vite + PWA)
          | HTTPS API calls
          v
Amazon API Gateway HTTP API
          | Lambda proxy integration
          v
AWS Lambda (Python 3.12 + FastAPI + Mangum)
     |          |           |
     |          |           +--> RDS PostgreSQL + PostGIS
     |          |                (consider RDS Proxy)
     |          +--> S3 media / geospatial source files
     |
     +--> SQS media-analysis queue
                 |
                 v
          SQS-triggered worker Lambda(s)
             |       |       |
             |       |       +--> SAM 3.1 (Meta Model API)
             |       +----------> Muse Spark / Wonder / Image / Voice
             |
             +------------------> Glimmer / Spark Open private inference endpoint

EventBridge --> scheduled ingestion / recalculation Lambda(s)
SQS DLQ ------> failed asynchronous jobs for inspection and retry

Secrets Manager --> API and worker secrets
CloudWatch ------> logs, metrics, alarms

Exception path: workloads that exceed Lambda limits --> ECS Fargate / AWS Batch /
dedicated inference endpoint, with status and results returned asynchronously.
```

### 6.4 Deployment environments

- `local`: Python virtual environment, FastAPI + Uvicorn, locally installed PostgreSQL/PostGIS, and mock model provider. No Docker or Docker Compose is required or assumed.
- `dev`: AWS API Gateway, Lambda, database, S3, SQS, Secrets Manager, and test data.
- `demo`: stable, seeded demonstration data; AI live calls can be feature-flagged.
- `prod`: not part of the first demo; require security review, data agreements, operational runbooks, and calibrated risk methodology.

Keep AWS region configurable. Select an AWS region based on service availability, latency, data residency, and cost. Do not assume every AWS service is available in every African region.

---

## 7. Data model

Use UUID primary keys and UTC timestamps. Store coordinates in WGS84 (EPSG:4326); use suitable projected CRS for metric distance/area calculations.

### 7.1 Core tables

**users**
- id, email, phone (nullable), display_name, password/auth_subject, role, organisation_id, is_active, created_at, updated_at.

**organisations**
- id, name, organisation_type, city, country_code, created_at.

**reports**
- id, reporter_user_id (nullable for anonymous), organisation_id (nullable), report_type, description, latitude, longitude, location (PostGIS geography/geometry), reported_at, submitted_at, status, source_channel, is_synthetic, duplicate_of_report_id (nullable), created_at.

**media_assets**
- id, report_id, s3_key, media_type, sha256, mime_type, file_size, captured_at, uploaded_at, exif_removed, processing_status, public_thumbnail_key (nullable).

**ai_analyses**
- id, report_id, media_asset_id, provider, model_id, model_version, prompt_version, status, scene_summary, structured_result JSONB, confidence, limitations JSONB, request_id, processing_ms, created_at.

**segmentation_assets**
- id, media_asset_id, provider, model_id, prompt_text, mask_s3_key, bounding_boxes JSONB, object_labels JSONB, created_at.

**environmental_observations**
- id, source_id, observation_type, geometry, observed_at, value, unit, quality_flag, raw_s3_key, metadata JSONB, ingested_at.

**data_sources**
- id, name, source_type, licence, attribution, source_url, spatial_coverage, temporal_coverage, update_frequency, last_success_at, status, limitations.

**risk_cells**
- id, grid_system, grid_index, geometry, risk_score, risk_band, confidence_score, data_completeness, contributing_factors JSONB, missing_inputs JSONB, calculation_version, calculated_at, valid_until, is_illustrative.

**risk_cell_evidence**
- risk_cell_id, evidence_type, evidence_id, contribution, source_timestamp.

**moderation_actions**
- id, report_id, moderator_user_id, action, reason, previous_status, new_status, created_at.

**audit_logs**
- id, actor_user_id, action, resource_type, resource_id, metadata JSONB, ip_hash (if retained), created_at.

**notifications**
- id, recipient_user_id, channel, message_template, payload JSONB, status, sent_at, created_at.

### 7.2 Indexes

- GiST indexes on geometry columns.
- B-tree indexes on timestamps, status, report type, provider, and risk band.
- Unique constraint on media SHA-256 where appropriate.
- Index report coordinates / grid assignment for aggregation.
- Partition high-volume time-series observations by time when needed.

---

## 8. API design

Use `/api/v1` prefix, OpenAPI documentation, typed response schemas, pagination, filtering, and consistent error responses.

### Public / resident

- `POST /api/v1/reports` — create report metadata.
- `POST /api/v1/reports/{report_id}/media-upload-url` — request a short-lived presigned S3 upload URL.
- `POST /api/v1/reports/{report_id}/media-complete` — confirm upload and enqueue analysis.
- `POST /api/v1/reports/{report_id}/voice-upload-url` — presigned voice upload URL.
- `GET /api/v1/reports/{report_id}/receipt` — retrieve safe submission receipt.
- `GET /api/v1/reports/public` — public-safe report list with coarse location and redacted details.

### Map / risk

- `GET /api/v1/map/summary?bbox=...`
- `GET /api/v1/map/reports?bbox=...&from=...&to=...&status=...`
- `GET /api/v1/map/risk-cells?bbox=...&band=...`
- `GET /api/v1/risk-cells/{cell_id}`
- `GET /api/v1/layers` — layer metadata and freshness.

### Authority / moderation

- `GET /api/v1/admin/reports`
- `GET /api/v1/admin/reports/{report_id}`
- `PATCH /api/v1/admin/reports/{report_id}/status`
- `POST /api/v1/admin/reports/{report_id}/verify`
- `POST /api/v1/admin/reports/{report_id}/reanalyze`
- `GET /api/v1/admin/hotspots`
- `GET /api/v1/admin/analytics/overview`
- `GET /api/v1/admin/model-status`
- `GET /api/v1/admin/data-source-status`

### Voice

- `POST /api/v1/reports/{report_id}/transcribe` — enqueue transcription of uploaded audio.
- `GET /api/v1/transcriptions/{transcription_id}` — retrieve status and transcript.

### System

- `GET /health/live`
- `GET /health/ready`
- `GET /api/v1/system/capabilities` — safe frontend feature flags, provider status, and enabled layers. Never return secrets.

### API rules

- Validate bounding boxes, coordinate ranges, MIME types, upload size, and role permissions.
- Use presigned S3 uploads; do not proxy large media through the FastAPI process.
- Validate uploaded media using magic bytes, not only the filename or browser MIME type.
- Make asynchronous endpoints return `202 Accepted` with a job/report status.
- Add idempotency keys to report submission and upload completion.
- Rate-limit anonymous reporting and protect endpoints against abuse.
- Return only coarse coordinates in public APIs; full coordinates are restricted to authorised reviewers.
- Use cursor pagination for reports and audit logs.

---

## 9. AI processing workflows

### 9.1 Photo workflow

1. Resident selects photo and location.
2. Frontend stores a local draft and uploads the photo to S3 using a presigned URL.
3. Backend validates media, strips EXIF from public derivatives, calculates SHA-256, and records provenance.
4. Backend places an analysis job on SQS.
5. Worker invokes Muse Spark with the image and a controlled prompt.
6. If segmentation is useful, worker invokes SAM 3.1 with targeted noun phrases.
7. Worker normalises outputs into the internal schema and stores the result.
8. Worker computes preliminary evidence attributes, but does not independently mark the incident verified.
9. Risk engine recalculates the affected grid cell(s).
10. Reviewer sees original evidence, AI annotations, confidence, limitations, and source metadata.
11. Reviewer verifies, rejects, or requests more information.

### 9.2 Voice workflow

1. Resident records a short voice note.
2. Audio is uploaded to private S3 storage.
3. Worker calls Muse Voice Transcribe.
4. Transcript is stored as unverified text and shown to the reporter for correction where possible.
5. Transcript keywords may assist report categorisation, but must not independently establish flood severity.
6. Retain audio only according to configured retention policy.

### 9.3 Multi-report synthesis

- Use Muse Spark for routine summaries of a hotspot's recent evidence.
- Use Muse Wonder only for reviewer-triggered complex synthesis across multiple reports and environmental observations.
- Supply only relevant, permission-filtered evidence.
- Every generated summary must link to source report IDs and identify missing/conflicting evidence.
- Never let a model write directly to official-warning status or perform emergency actions.

### 9.4 Muse Image

- Generate optional preparedness illustrations (e.g. how to avoid walking through moving floodwater) and product demo illustrations.
- Mark every generated image as AI-generated.
- Do not use generated imagery as incident evidence or as a real map layer.
- Avoid generating false depictions of actual affected communities.

### 9.5 Provider routing

Create a central `ModelRouter` with:
- Task type: `image_assessment`, `segmentation`, `voice_transcription`, `evidence_synthesis`, `preparedness_visual`.
- Preferred provider/model.
- Fallback provider where safe.
- Timeout, retry, token / media limits, and cost ceiling.
- Feature flag and health status.
- Audit metadata.

Never silently fall back from a real model to a mock response. The UI must show `Demo analysis` if fixtures are used.

---

## 10. User experience and visual design

### 10.1 Brand direction

- Product name: **FloodLens AI**.
- Tone: trustworthy, calm, practical, community-centred, and evidence-led.
- Visual language: clean geospatial dashboard, accessible typography, restrained use of hazard colours, clear map legend.
- Avoid disaster sensationalism, frightening imagery, or unsupported claims.
- Design for low-end mobile screens and poor connectivity.

### 10.2 Main pages

1. `/` — Landing page with clear value proposition, CTA to view map / report flooding, how it works, data disclaimer, and demo status.
2. `/map` — Public interactive map, legend, filters, report cards, and source freshness.
3. `/report` — Mobile-friendly report form with photo, location, voice, and offline draft.
4. `/report/:id` — Safe receipt/status page.
5. `/dashboard` — Authority overview (protected).
6. `/dashboard/reports` — Moderation queue.
7. `/dashboard/reports/:id` — Evidence review and AI analysis.
8. `/dashboard/hotspots` — Ranked hotspots and map.
9. `/dashboard/data` — Environmental source freshness and coverage.
10. `/dashboard/settings` — Organisation and role settings.
11. `/about/methodology` — Risk index explanation, data sources, model limitations, and disclaimer.

### 10.3 Dashboard content

Show:
- Total reports in selected period.
- Verified active incidents.
- High / very-high risk cells.
- Reports pending review.
- Rainfall source freshness.
- AI processing status.
- Top hotspots with score, confidence, last evidence time, and key contributors.
- Recent reports with image thumbnail, location label, status, and timestamp.

### 10.4 Report form details

Required:
- Hazard category.
- Location (GPS or map pin).
- At least one of photograph, text description, or voice note.
- Consent / privacy acknowledgement.

Optional:
- Additional photos/video.
- Voice note.
- Landmark / nearest road.
- Water level observation chosen from non-technical options (e.g. ankle / knee / waist / above waist) with a warning that this is self-reported and approximate.
- Whether roads / homes / shops / facilities are affected.
- Reporter contact details for follow-up (private).

The form must work with keyboard navigation, screen readers, clear error messages, and large touch targets.

---

## 11. Authentication, authorisation, privacy, and security

- Use Amazon Cognito or another supported standards-based identity provider for staff / authority accounts.
- Public reports may be anonymous, but must be rate-limited and abuse-protected.
- Roles: `public`, `reporter`, `reviewer`, `authority_admin`, `platform_admin`.
- Enforce permissions in the backend, not only by hiding frontend controls.
- Use short-lived presigned S3 URLs and private buckets with block-public-access enabled.
- Encrypt S3, RDS, backups, and secrets at rest; use TLS in transit.
- Never commit `.env`, API keys, credentials, model weights, personal data, or production media to GitHub.
- Strip GPS EXIF from public image derivatives; preserve original evidence privately only where justified.
- Public map should use approximate / aggregated location for sensitive reports.
- Provide retention and deletion policies for reporter data and media.
- Record consent and privacy notice version.
- Validate file uploads and scan for malicious content where practical.
- Add CORS allow-list, CSRF protection where cookie auth is used, secure headers, and request validation.
- Keep audit trails for staff access to private evidence.
- Follow applicable Nigerian data protection requirements and other relevant country laws; obtain legal review before production use.
- Do not expose AI prompts, internal error traces, or model credentials to end users.

---

## 12. Offline and low-connectivity behaviour

- Build the report form as a PWA.
- Store drafts and pending media metadata in IndexedDB.
- Compress images client-side before upload, retaining an appropriate private original only when configured.
- Queue uploads and retry with exponential backoff when connectivity returns.
- Display upload progress and explicit states: `Saved on device`, `Uploading`, `Submitted`, `Analysis pending`, `Reviewed`.
- Do not show `Submitted` until the backend confirms receipt.
- If GPS is unavailable, allow manual map pin and landmark description.
- Keep the core form usable without map tiles; use a coordinate / landmark fallback.
- Do not cache private media or sensitive report payloads in a shared browser cache.
- Provide a clear way to remove a locally stored draft.

---

## 13. Observability and operational controls

- Structured JSON logs with request ID, report ID, job ID, provider, model, and duration.
- Do not log raw media, voice recordings, access tokens, or unnecessary personal data.
- Track queue depth, failed jobs, retry count, model latency, model errors, cost estimates, API response time, and data-source freshness.
- Dead-letter queue for failed SQS jobs and an admin retry action.
- Alert on API errors, queue backlog, repeated model failures, database connection exhaustion, and stale rainfall data.
- Add a `demo mode` banner and model/data-source status indicators.
- Add a cost guardrail: per-report model-call cap, maximum image dimensions / file sizes, rate limits, and optional admin kill switch for AI calls.

---

## 14. Repository structure

Use a monorepo:

```text
floodlens-ai/
├── README.md
├── reference.md
├── .gitignore
├── .env.example
├── amplify.yml
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   ├── features/
│   │   │   ├── map/
│   │   │   ├── reports/
│   │   │   ├── dashboard/
│   │   │   ├── auth/
│   │   │   └── model-status/
│   │   ├── lib/
│   │   ├── routes/
│   │   └── styles/
│   └── public/
├── backend/
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── local-dev.md
│   ├── app/
│   │   ├── main.py
│   │   ├── lambda_handler.py  # Mangum adapter for AWS Lambda
│   │   ├── api/v1/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   │   ├── risk_engine/
│   │   │   ├── geospatial/
│   │   │   ├── media/
│   │   │   ├── ingestion/
│   │   │   └── model_router/
│   │   ├── providers/
│   │   │   ├── meta_model_api/
│   │   │   ├── muse_glimmer/
│   │   │   ├── muse_spark_open/
│   │   │   └── demo/
│   │   ├── workers/
│   │   └── tasks/
│   └── tests/
├── infrastructure/
│   ├── aws-sam/ or cdk/       # API Gateway, Lambda, queues, database, IAM
│   └── scripts/
├── data/
│   ├── demo/
│   └── schemas/
├── docs/
│   ├── architecture.md
│   ├── risk-methodology.md
│   ├── data-sources.md
│   ├── model-integrations.md
│   ├── security.md
│   ├── local-development.md
│   └── deployment.md
└── .github/
    └── workflows/
```


Kiro may refine this structure if there is a strong technical reason, but it must preserve the separation between frontend, backend, model providers, risk engine, data ingestion, and infrastructure.

---

## 15. Local development without Docker

Local backend development and testing must use a Python virtual environment. Docker and Docker Compose are not required, must not be included as mandatory setup steps, and must not be used as the default local workflow.

### 15.1 Prerequisites

- Python 3.12 and `venv` / `pip`.
- Node.js version supported by the current frontend toolchain.
- PostgreSQL installed directly on the developer machine, with the PostGIS extension installed and enabled.
- Git.
- Optional AWS CLI for deployment and integration against AWS resources.

### 15.2 Create and activate the virtual environment

Run from the repository root. On Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".\backend[dev]"
```

On macOS / Linux:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

Kiro must verify the actual `pyproject.toml` packaging configuration and adjust the install command if the backend package is not configured as an installable project. Keep the environment isolated and add `.venv/`, `venv/`, and Python caches to `.gitignore`.

### 15.3 Configure local PostgreSQL/PostGIS

Install PostgreSQL and the PostGIS extension using the operating system's supported installer/package manager. Create a local development database and enable PostGIS:

```sql
CREATE DATABASE floodlens_dev;
\connect floodlens_dev
CREATE EXTENSION IF NOT EXISTS postgis;
```

Configure the local database URL in the backend environment file. Use a dedicated local database user with only the permissions required for development. Do not use production credentials locally.

### 15.4 Run migrations, API, and tests

```bash
# From the repository root, with .venv activated
cp backend/.env.example backend/.env  # if this template exists; otherwise create it from documented variables
alembic -c backend/alembic.ini upgrade head
uvicorn app.main:app --app-dir backend --reload --host 127.0.0.1 --port 8000
pytest backend/tests -q
```

The API should expose its OpenAPI documentation at `/docs` in local development. If Alembic configuration or import paths differ in the implemented repository, document the exact working commands in `README.md` and `backend/local-dev.md`; do not leave example commands that fail. Use the mock/demo model provider by default so local testing does not require live Meta credentials.

### 15.5 Local environment and secrets

- Keep local values in ignored `.env` files; commit only `.env.example` with placeholders.
- Never place Meta API keys, AWS credentials, database passwords, or private inference keys in frontend `VITE_` variables.
- Local API tests should use the local PostgreSQL/PostGIS instance and mock external model providers.
- Integration tests against AWS must be explicitly opt-in and clearly separated from normal local unit tests.

---

## 16. Environment variables

Create `.env.example` with placeholders only. Never commit real values.

```dotenv
APP_ENV=local
APP_NAME=FloodLens AI
API_V1_PREFIX=/api/v1
FRONTEND_ORIGIN=http://localhost:5173

DATABASE_URL=postgresql+psycopg://floodlens:floodlens@localhost:5432/floodlens
S3_MEDIA_BUCKET=
AWS_REGION=us-east-1
AWS_ENDPOINT_URL=

MODEL_API_BASE_URL=https://api.meta.ai/v1
MODEL_API_KEY=
MUSE_SPARK_MODEL=muse-spark-1.3
MUSE_WONDER_MODEL=muse-wonder-1.0
MUSE_IMAGE_MODEL=muse-image-1.0
MUSE_VOICE_MODEL=muse-voice-transcribe-1.0
SAM_MODEL=sam-3.1

MUSE_GLIMMER_ENABLED=false
MUSE_GLIMMER_BASE_URL=
MUSE_GLIMMER_MODEL=
MUSE_GLIMMER_API_KEY=

MUSE_SPARK_OPEN_ENABLED=false
MUSE_SPARK_OPEN_BASE_URL=
MUSE_SPARK_OPEN_MODEL=
MUSE_SPARK_OPEN_API_KEY=

AI_PROVIDER_MODE=mock
ENABLE_AI_IMAGE_ANALYSIS=false
ENABLE_AI_VOICE_TRANSCRIPTION=false
ENABLE_SAM_SEGMENTATION=false
ENABLE_MUSE_IMAGE_GENERATION=false
ENABLE_MUSE_WONDER_ANALYST=false

SQS_MEDIA_ANALYSIS_QUEUE_URL=
SQS_MEDIA_ANALYSIS_DLQ_URL=
COGNITO_USER_POOL_ID=
COGNITO_CLIENT_ID=

RISK_WEIGHTS_PROFILE=illustrative_unvalidated
RISK_GRID_SYSTEM=h3
RISK_GRID_RESOLUTION=8
DEMO_MODE=true
```

- Production secrets belong in AWS Secrets Manager / secure runtime configuration.
- Do not use `VITE_MODEL_API_KEY` or any frontend-exposed Meta credential.
- `AI_PROVIDER_MODE=mock` must be clearly labelled in the UI and never be the production default.

---

## 17. Testing strategy

### Backend tests

- Unit tests for risk-score normalisation, missing-data handling, confidence calculation, grid assignment, duplicate detection, and permissions.
- Provider contract tests for Muse Spark, Muse Wonder, Muse Image, Muse Voice Transcribe, SAM 3.1, Glimmer, and Spark Open.
- Mock external providers in normal CI.
- Live Meta API smoke tests only when secrets are available and an explicit CI flag is enabled.
- Test malformed model responses, timeouts, 429 rate limits, 5xx errors, and retries.
- Test S3 presigned upload lifecycle and media validation.
- Test that anonymous users cannot access private coordinates, reporter contact details, or original media.
- Test migrations on a clean PostGIS database.

### Frontend tests

- Unit tests for report form validation, map filters, risk legend, offline queue, and status rendering.
- Accessibility checks for keyboard use, labels, contrast, and screen-reader names.
- Playwright end-to-end tests for report submission, offline draft, map filtering, reviewer verification, and dashboard access.
- Test small-screen layouts and slow network conditions.

### Acceptance criteria

- A resident can submit a report from a mobile browser with a photo and GPS or manual location.
- An offline draft remains on device and can be retried.
- A completed upload produces a server-confirmed receipt.
- A queued job invokes the configured AI provider or returns an explicitly labelled demo result.
- AI output is validated and stored with provider / model / prompt provenance.
- SAM masks / boxes can be viewed as overlays when returned.
- Voice transcription is editable and not automatically treated as verified fact.
- Risk cells show score, band, confidence, contributing factors, missing inputs, and freshness.
- A reviewer can verify / reject a report and the action is audited.
- Public endpoints do not reveal reporter identity or exact sensitive coordinates.
- Frontend deploys from GitHub to Amplify Hosting.
- No Meta secret or private AWS credential exists in frontend assets or Git history.
- The system remains usable with unavailable external feeds and unavailable open-weight endpoints.

---

## 18. AWS Amplify + GitHub deployment

### 18.1 GitHub

- Create a repository named `floodlens-ai`.
- Use `main` as the production/demo branch and `develop` for integration.
- Require pull requests for changes to `main`.
- Add `.gitignore` for `.env*` (except `.env.example`), `node_modules`, Python virtual environments, caches, build outputs, media uploads, model weights, and local databases.
- Add CI to run frontend lint/typecheck/tests and backend lint/tests.
- Keep infrastructure definitions and deployment instructions in the repository.

### 18.2 Amplify Hosting

- Create an AWS Amplify Hosting application and connect it to the GitHub repository using the AWS Amplify GitHub App.
- Select the `main` branch for the demo deployment.
- Configure the frontend app root as `frontend`.
- Use the repository `amplify.yml` build specification.
- Configure only public frontend values in Amplify environment variables, e.g. `VITE_API_BASE_URL` and public map style configuration.
- Do not store `MODEL_API_KEY`, database passwords, AWS secret keys, or private inference keys in frontend environment variables.
- Add a custom domain only after the default Amplify deployment works.
- Enable pull-request previews if useful for review.
- Add SPA rewrite rules so client-side routes such as `/map` and `/dashboard` resolve to the frontend entry point.
- Keep API and worker deployments separate from Amplify Hosting.

Example `amplify.yml` for a Vite frontend in `frontend/`:

```yaml
version: 1
applications:
  - appRoot: frontend
    frontend:
      phases:
        preBuild:
          commands:
            - npm ci
        build:
          commands:
            - npm run build
      artifacts:
        baseDirectory: dist
        files:
          - '**/*'
      cache:
        paths:
          - node_modules/**/*
```

Kiro must verify this configuration against the actual repository layout and current Amplify build specification before deployment.

### 18.3 Backend deployment: API Gateway + Lambda

For the demo, deploy the FastAPI application to AWS Lambda (Python 3.12) and expose it through an Amazon API Gateway HTTP API using Lambda proxy integration. Use Mangum or a currently supported ASGI-to-Lambda adapter. Prefer ZIP-based packaging and deployment with AWS SAM or CDK so Docker is not required on the developer workstation. Provision RDS PostgreSQL with PostGIS, S3, SQS, Secrets Manager, IAM roles/policies, CloudWatch, and any required networking using repeatable infrastructure as code.

Implementation requirements:

1. Add a Lambda entry point, for example `backend/app/lambda_handler.py`, that exports the Mangum handler wrapping the FastAPI application. Keep the normal FastAPI app entry point usable with local Uvicorn.
2. Define API Gateway routes, stage, CORS, throttling, access logging, and Lambda permissions in infrastructure code. Configure the frontend `VITE_API_BASE_URL` with the deployed API Gateway URL.
3. Use least-privilege IAM roles. Store Meta credentials and database secrets in Secrets Manager; never package them into the Lambda ZIP or frontend.
4. Use SQS-triggered worker Lambda functions for bounded background tasks, with visibility timeout, batch size, retry policy, idempotency, and a dead-letter queue configured deliberately.
5. Protect database connections from Lambda concurrency spikes. Evaluate RDS Proxy, connection pooling behaviour, and conservative Lambda reserved concurrency. Run Alembic migrations as a controlled deployment step, not on every Lambda cold start.
6. Keep Lambda handlers stateless. Store durable uploads and outputs in S3 and job state/results in the database. Use presigned S3 uploads for media rather than proxying large files through API Gateway.
7. Keep long-running or resource-heavy geospatial processing and inference outside synchronous API requests. If a worker exceeds Lambda limits, use a separately provisioned ECS Fargate task, AWS Batch job, or dedicated inference endpoint and report progress asynchronously. This does not change the default API Gateway + Lambda hosting plan.
8. Add CloudWatch dashboards/alarms for API errors, Lambda duration/throttles/concurrency, SQS age/depth, DLQ messages, database connections, and model-provider failures.
9. Document deployment, rollback, environment configuration, cost controls, and teardown.

Do not deploy the primary API as an ECS service by default. ECS/Fargate is an optional execution target only for workloads demonstrated to exceed Lambda constraints. Do not put the backend database or Meta API secret in Amplify frontend configuration.

### 18.4 Deployment checklist

- [ ] GitHub repository created and code pushed.
- [ ] CI passes.
- [ ] Amplify GitHub App authorised for this repository only.
- [ ] Amplify `main` branch deploy succeeds.
- [ ] SPA rewrite rules work on direct page refresh.
- [ ] API Gateway HTTP API invokes the FastAPI Lambda handler and the health endpoint is reachable over HTTPS.
- [ ] Lambda package targets Python 3.12 and deploys without requiring Docker on the developer workstation.
- [ ] Lambda concurrency and database connection management are configured safely.
- [ ] SQS worker Lambda retry policy and dead-letter queue are tested.
- [ ] CORS allows only intended frontend origins.
- [ ] S3 bucket is private and presigned uploads work.
- [ ] Secrets Manager contains server-side Meta key.
- [ ] Database migrations have run.
- [ ] SQS worker consumes jobs.
- [ ] CloudWatch logs and alarms are configured.
- [ ] Demo data is visibly labelled.
- [ ] Open-weight model status is honest and reflects actual endpoint health.

---

## 19. Kiro execution instructions

Kiro must work incrementally. Do not generate the entire application in one unreviewed pass.

### Phase 0 — Inspect and plan

1. Read this `reference.md` completely.
2. Inspect the existing repository before changing files.
3. Produce `docs/implementation-plan.md` with architecture, milestones, dependencies, and risks.
4. Produce `docs/architecture.md` and Mermaid diagrams for the main data flows.
5. Identify all external credentials and services needed. Do not ask for secrets in chat or write them to source control.
6. Ask only for decisions that genuinely block implementation. Use safe defaults for non-blocking details.

### Phase 1 — Foundation

1. Create the monorepo structure.
2. Set up React + TypeScript + Vite frontend.
3. Set up FastAPI backend, SQLAlchemy, Alembic, and PostGIS. Create and document a Python 3.12 virtual environment workflow; do not add Docker Compose as a prerequisite.
4. Add the Mangum Lambda handler and AWS SAM/CDK infrastructure definitions for API Gateway + Lambda.
5. Add health endpoints, configuration validation, structured logging, linting, formatting, and CI.
6. Add mock provider and synthetic seed-data mechanism.
7. Ensure frontend and backend run locally using documented `venv`, PostgreSQL/PostGIS, and Uvicorn commands.

### Phase 2 — UI and demo map

1. Implement product shell, landing page, responsive navigation, map, legend, filters, and dashboard.
2. Use MapLibre with seeded GeoJSON for the initial Lagos demo.
3. Display synthetic data labels, data source attribution, and freshness.
4. Implement incident list and detail drawer.
5. Ensure the app remains usable when map tiles or external APIs fail.

### Phase 3 — Reports and offline

1. Implement report creation and validation.
2. Add GPS and manual map pin selection.
3. Add private S3 presigned uploads.
4. Add IndexedDB draft queue and retry behaviour.
5. Add submission receipt and report status.
6. Add role-based access and audit logging.

### Phase 4 — Meta Model API integrations

Implement adapters one at a time in this order:

1. Muse Spark image understanding and structured JSON output.
2. SAM 3.1 segmentation and visual overlay.
3. Muse Voice Transcribe.
4. Muse Wonder evidence synthesis.
5. Muse Image preparedness / demo illustrations.

For each adapter:
- Read current official model documentation.
- Implement typed request and response mapping.
- Add timeout, retry, rate-limit, and error handling.
- Add mock contract tests and opt-in live smoke tests.
- Store model provenance.
- Add UI status and error states.
- Never leak the API key.

### Phase 5 — Open-weight integration

1. Implement Glimmer adapter using a configurable OpenAI-compatible endpoint.
2. Document local/hosted Glimmer runtime setup and health checks.
3. Implement Spark Open adapter using a configurable private hosted endpoint.
4. Document GPU requirements and the cost/operational implications.
5. Add provider selection and status display.
6. Do not download model weights in CI or commit them to GitHub.
7. If an endpoint is unavailable, mark it `Not configured`; do not fake inference.

### Phase 6 — Risk engine and data ingestion

1. Implement the configurable 0–100 risk index and explainable contributors.
2. Add missing-data and confidence handling.
3. Add grid aggregation and duplicate report protection.
4. Add rainfall, elevation, drainage, and exposure adapters, starting with seeded data.
5. Add ingestion metadata, source freshness, and failed-job monitoring.
6. Clearly label the first risk profile as illustrative and unvalidated.
7. Add unit tests for every risk calculation.

### Phase 7 — Security, QA, and deployment

1. Complete permission and privacy tests.
2. Add end-to-end tests for resident and reviewer journeys.
3. Run accessibility and mobile responsiveness checks.
4. Package and deploy the FastAPI backend to Lambda and expose it through API Gateway using AWS SAM/CDK; do not make local Docker a deployment prerequisite.
5. Deploy SQS-triggered worker Lambdas and configure retry/DLQ behaviour.
6. Connect GitHub to Amplify Hosting and deploy the frontend.
7. Configure HTTPS, CORS, secrets, database connection management, monitoring, and demo data.
8. Verify every acceptance criterion and produce `docs/demo-runbook.md`.

### Required Kiro working behaviour

- Before editing, state the phase and files to be changed.
- Prefer small, reviewable changes.
- Do not overwrite working files without inspecting them.
- Do not invent live API responses, live rainfall readings, or verified flood incidents.
- Do not put secrets in code, logs, screenshots, frontend bundles, or Git.
- Do not create dead buttons or decorative controls that appear functional.
- Every form, filter, map layer, and dashboard action must work or be explicitly marked as a prototype.
- Use typed interfaces and dependency injection for all model and data-source providers.
- Add tests with each meaningful feature, not only at the end.
- Keep README setup instructions accurate as the project evolves.
- When blocked by missing credentials, complete the mockable integration and document exactly what is needed for live activation.
- Do not claim the project is production-ready until security, data validity, model evaluation, operational readiness, and local calibration are complete.

---

## 20. Demo storyline

The demo should tell a complete story in approximately 3–4 minutes:

1. Open the FloodLens AI landing page and explain the community flood-intelligence problem.
2. Open the Lagos demo map and show sample hotspots, rainfall / drainage layers, risk legend, and source freshness.
3. Submit a report with a photograph, location, and optional voice note.
4. Show Muse Voice Transcribe producing editable text (if enabled).
5. Show Muse Spark identifying visible flood / blocked-drain evidence and SAM 3.1 overlaying the relevant region.
6. Show the report entering the review queue.
7. Open the authority dashboard and show how risk factors and confidence explain why a location is prioritised.
8. Verify the incident and show the risk cell / hotspot update.
9. Show the model status panel distinguishing hosted Meta API models from open-weight endpoints.
10. Close with the public-safety disclaimer and the value of community intelligence.

Use seeded demo data and a preconfigured live-model demo path so the presentation does not depend on unpredictable external data feeds. Clearly label any seeded content.

---

## 21. Public-safety disclaimer

Display this notice on the map, report workflow, and methodology page:

> FloodLens AI provides community observations and data-informed risk indicators for situational awareness. It is not an official emergency warning system, does not guarantee that any location is safe, and does not replace instructions from emergency-management authorities. Risk estimates may be incomplete or inaccurate where observations or environmental data are missing, delayed, or unverified. In an emergency, contact the appropriate local emergency services and follow official guidance.

---

## 22. Reference documentation

Kiro should treat the following official documentation as the primary source for current model and deployment details. Re-check model IDs, API schemas, limits, pricing, and supported regions before implementation.

### Meta

- Meta Model API overview: https://dev.meta.ai/docs/overview
- Meta models catalogue: https://dev.meta.ai/docs/models
- Meta Model API pricing and rate limits: https://dev.meta.ai/docs/pricing-rate-limits
- SAM 3.1 overview: https://dev.meta.ai/docs/sam/overview
- SAM media segmentation guide: https://dev.meta.ai/docs/media-segmentation
- Muse Spark Open deployment / hardware: https://dev.meta.ai/docs/muse-spark-open
- Muse Spark Open hardware platforms: https://dev.meta.ai/docs/muse-spark-open/hardware-platforms
- Muse Glimmer overview: https://dev.meta.ai/docs/muse-glimmer
- Muse Glimmer deployment: https://dev.meta.ai/docs/muse-glimmer/deploy
- Muse Code: https://dev.meta.ai/lp/muse-code

### AWS

- Amplify Hosting overview: https://docs.aws.amazon.com/amplify/latest/userguide/welcome.html
- Connect Amplify to GitHub: https://docs.aws.amazon.com/amplify/latest/userguide/setting-up-GitHub-access.html
- Amplify build settings: https://docs.aws.amazon.com/amplify/latest/userguide/build-settings.html
- Amplify environment variables: https://docs.aws.amazon.com/amplify/latest/userguide/setting-env-vars.html
- Amazon Location Service: https://docs.aws.amazon.com/location/latest/APIReference/

### Environmental data discovery

- Copernicus Emergency Management Service data: https://emergency.copernicus.eu/data/
- NASA GPM: https://gpm.nasa.gov/data
- OpenStreetMap: https://www.openstreetmap.org/
- Copernicus Data Space Ecosystem: https://dataspace.copernicus.eu/

---

## 23. Definition of done

The MVP is complete when:

- A new developer can clone the GitHub repository, create a Python 3.12 virtual environment, install dependencies, run PostgreSQL/PostGIS locally, and start the API with Uvicorn using the README; Docker is not required.
- The frontend deploys automatically to AWS Amplify from the selected GitHub branch.
- The FastAPI backend is deployed as AWS Lambda behind API Gateway, and asynchronous workers use SQS-triggered Lambda functions where suitable; workloads beyond Lambda limits use a documented separate compute target.
- The backend and worker deploy independently and securely.
- A resident can submit a location-aware report with media or text.
- The system can process an image with a real Meta Model API integration when credentials are configured.
- SAM 3.1 can return segmentation output and the frontend can display it.
- Voice transcription works when configured.
- Muse Wonder and Muse Image adapters exist and are tested.
- Muse Glimmer and Muse Spark Open adapters exist, their separate deployment profiles are documented, and their status is not misrepresented.
- The map and risk engine work with seeded data when external feeds are unavailable.
- Risk calculations are explainable, versioned, and labelled unvalidated until locally calibrated.
- A reviewer can verify a report and see an audit record.
- Privacy, security, offline, and error-handling acceptance tests pass.
- The demo storyline can be completed reliably without depending on an external live feed.

**Build the smallest reliable end-to-end slice first:** submit report → store media → analyse with Muse Spark → optionally segment with SAM 3.1 → review evidence → update an explainable demo risk map. Expand only after that vertical slice works.
