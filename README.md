# FloodLens AI

**Community-powered flood observation, geospatial risk mapping, and decision-support for African communities.**
**Demo URL: https://main.dmpm2yei4pgxa.amplifyapp.com/ **

FloodLens AI enables residents, community organisations, emergency-response teams, and local authorities to understand where flooding is being observed, which locations are vulnerable, and where inspections or interventions should be prioritised. It combines community-submitted reports with AI-assisted image analysis, environmental data, and a transparent Flood Risk Index to produce explainable, location-based risk indicators on an interactive map.

> **Public Safety Notice:** FloodLens AI provides community observations and data-informed risk indicators for situational awareness. It is not an official emergency warning system, does not guarantee that any location is safe, and does not replace instructions from emergency-management authorities. In an emergency, contact local emergency services and follow official guidance.

---

## What It Does

### Community Flood Reporting
Residents submit flood or drainage reports directly from a mobile browser — even on low-bandwidth connections. Each report can include:
- One or more photographs of the flooding or drainage issue
- A GPS location or manually placed map pin
- Voice notes (converted to text by AI)
- Hazard type, self-reported severity, and water level
- Optional landmark and description
- Information about affected roads, homes, shops, or facilities

Submitted reports are saved as offline drafts if connectivity is unavailable and automatically retried when the connection returns. Reporters receive a confirmation receipt with a report ID and real-time status tracking.

### AI-Assisted Image Analysis
Each uploaded photo is analysed by **Muse Spark** (Meta Model API multimodal model), which identifies visible flood-related hazards including floodwater, blocked drains, overflowing drains, damaged roads, and exposed infrastructure. The analysis returns:
- A scene summary describing the overall situation
- Detected hazards with type, visible evidence, confidence score, and severity observation
- Water presence classification (none / possible / visible / extensive)
- Infrastructure observations
- Analysis limitations and recommended review actions

**SAM 3.1** (Segment Anything Model) segments relevant objects in photos — floodwater, drain openings, debris, road surface — and overlays bounding boxes for reviewer inspection.

All AI outputs include confidence scores, limitations, and provenance metadata (provider, model ID, prompt version). Findings are clearly labelled as requiring human verification before any consequential decision.

### Voice Transcription
Voice notes recorded by residents are transcribed to text by **Muse Voice Transcribe**. Transcripts are stored as unverified text, shown to the reporter for correction, and used to assist report categorisation. Transcripts do not independently establish flood severity and the original audio is retained privately.

### Interactive Flood Map
The public map displays community report markers and risk zones across the demonstration area (Lagos, Nigeria by default). Features include:
- Colour-coded report markers by severity (critical, high, moderate, low)
- Risk zone overlays showing the Flood Risk Index per grid cell
- Click any marker for an instant popup with report summary and a direct link to the full report
- Filters by report status and hazard type
- Layer controls for rainfall, elevation, drainage, roads, waterways, and facilities
- Legend, scale, source attribution, and last-updated time

### Report Detail View
Clicking a report or map marker opens a full detail page showing:
- Photo gallery with direct image display via presigned S3 URLs
- AI analysis results: scene summary, hazard detections, confidence indicators, water presence, infrastructure observations, and limitations
- Embedded voice note audio player and full transcript
- Affected areas (roads, homes, shops, facilities)
- Report status and moderation history

### Flood Risk Index (FRI)
FloodLens AI computes a transparent, configurable 0–100 Flood Risk Index for each grid cell (H3 hexagonal grid, configurable resolution). The FRI combines five dimensions:

| Dimension | Max Score | Inputs |
|---|---|---|
| Observed Flooding | 30 | Verified reports, observed extent, recurrence, evidence quality |
| Rainfall Conditions | 25 | Recent accumulation and forecast (if configured) |
| Terrain Susceptibility | 20 | Elevation, slope, depressions, flow accumulation |
| Drainage Condition | 15 | Proximity to drainage, blockage reports, density/gaps |
| Exposure / Vulnerability | 10 | Roads, markets, schools, health facilities, settlements |

Risk bands: **Low (0–19) · Guarded (20–39) · Elevated (40–59) · High (60–79) · Very High (80–100)**

Every risk cell includes a confidence score, data completeness indicator, contributing factors, missing inputs, calculation version, and freshness timestamp. Missing data is never silently treated as zero risk — confidence is lowered when data is incomplete. Weights are labelled `illustrative_unvalidated` until calibrated against local historical flood records.

### Authority Dashboard
Staff and authority users access a protected dashboard with:
- KPI cards: open reports, verified incidents, high/very-high risk zones, reports pending review
- Moderation queue with full report detail, media, AI findings, evidence provenance, and reviewer actions (verify, reject, request more information)
- Ranked hotspot list showing risk score, confidence, report count, and top contributing factors
- Map and list views for spatial situational awareness
- Data source freshness panel
- AI model status panel showing which models are connected, in demo mode, or not configured

### Role-Based Access
Five roles with enforced backend permissions:
- **Public** — view public map and submit reports anonymously
- **Reporter** — submit and track own reports
- **Reviewer** — review all reports, verify incidents, request reanalysis
- **Authority Admin** — full moderation, settings management
- **Platform Admin** — system configuration

### Audit Trail
All moderation actions, risk recalculations, and administrative changes are recorded in a tamper-evident audit log with actor, action, resource, timestamp, and metadata.

---

## AI Models

| Model | Type | Role |
|---|---|---|
| **Muse Spark** (`muse-spark-1.3`) | Hosted Meta API | Primary multimodal image analysis and hazard detection |
| **Muse Wonder** (`muse-wonder-1.0`) | Hosted Meta API | Reviewer-requested multi-report evidence synthesis |
| **Muse Image** (`muse-image-1.0`) | Hosted Meta API | Preparedness illustrations and demo assets (never evidence) |
| **Muse Voice Transcribe** (`muse-voice-transcribe-1.0`) | Hosted Meta API | Voice-to-text for resident voice notes |
| **SAM 3.1** (`sam-3.1`) | Hosted Meta API | Object and region segmentation in photos |
| **Muse Glimmer** | Open-weight, Apache 2.0 | Local/edge fallback inference via OpenAI-compatible endpoint |
| **Muse Spark Open** | Open-weight, sparse MoE | Advanced optional inference for separately provisioned GPU |

All Meta API credentials are server-side only. The browser never calls Meta Model API directly. Model outputs always include confidence, limitations, and provenance — never presented as confirmed emergency alerts.

---

## Architecture

```
Residents / Authority users
          │ HTTPS
          ▼
AWS Amplify Hosting (React + Vite + PWA)
          │ HTTPS API calls
          ▼
Amazon API Gateway HTTP API
          │ Lambda proxy integration
          ▼
AWS Lambda (Python 3.12 + FastAPI + Mangum)
     │          │           │
     │          │           └──► RDS PostgreSQL + PostGIS
     │          └──────────────► S3 (media, thumbnails, masks, source data)
     │
     └──► SQS media-analysis queue
                   │
                   ▼
          SQS-triggered Worker Lambda
               │       │       │
               │       │       └──► SAM 3.1 / Muse Spark (Meta API)
               │       └──────────► Muse Voice / Wonder / Image (Meta API)
               └──────────────────► Glimmer / Spark Open (private endpoint)

EventBridge ──► Scheduled ingestion / risk recalculation Lambdas
Secrets Manager ──► API and worker secrets
CloudWatch ──► Logs, metrics, alarms
```

### Tech Stack

**Frontend**
- React 18 + TypeScript + Vite
- Tailwind CSS
- MapLibre GL JS (interactive maps with OSM basemap)
- TanStack Query (server state)
- React Hook Form + Zod (form validation)
- Progressive Web App — installable, offline-capable

**Backend**
- Python 3.12 + FastAPI + Pydantic v2
- SQLAlchemy 2 (async) + Alembic migrations
- PostgreSQL 16 + PostGIS (spatial queries and H3 grid)
- Mangum (ASGI → AWS Lambda adapter)
- boto3 (S3, SQS, Secrets Manager)
- h3, Pillow, httpx

** Other Services**
- AWS Amplify Hosting (frontend CDN)
- API Gateway HTTP API (API entry point)
- Lambda (compute — API and workers)
- RDS PostgreSQL + PostGIS (database)
- S3 (media and source data)
- SQS (async analysis queue + DLQ)
- EventBridge (scheduled ingestion)
- Secrets Manager (credentials)
- CloudWatch (observability)

---

## Quick Start (Local Development — No Docker Required)

### Prerequisites
- Python 3.12, Node.js 20+, PostgreSQL 16+ with PostGIS, Git

### Backend

```powershell
# Windows PowerShell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

```bash
# macOS / Linux
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Create PostgreSQL database:
```sql
CREATE DATABASE floodlens;
CREATE USER floodlens WITH PASSWORD 'floodlens';
GRANT ALL PRIVILEGES ON DATABASE floodlens TO floodlens;
\connect floodlens
CREATE EXTENSION IF NOT EXISTS postgis;
```

Run migrations and start the API:
```bash
cp .env.example backend/.env
alembic -c backend/alembic.ini upgrade head
uvicorn app.main:app --app-dir backend --reload --host 127.0.0.1 --port 8000
```

API docs: http://localhost:8000/docs

Run tests:
```bash
pytest backend/tests -q
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend: http://localhost:5173

### Default Ports

| Service | Port |
|---|---|
| Backend API | 8000 |
| Frontend Dev | 5173 |
| PostgreSQL | 5432 |

---

## Production Deployment (AWS)

Full guide: [backend/DEPLOYMENTv1.md](backend/DEPLOYMENTv1.md)

### Step 1: Deploy backend with AWS SAM

```bash
cd infrastructure/aws-sam
sam build
sam deploy --guided
```

Key parameters:
- **AppEnv** — `demo` or `prod`
- **FrontendOrigin** — your Amplify domain (e.g. `https://main.d12345.amplifyapp.com`)
- **DBPassword** — strong alphanumeric password
- **ModelApiKey** — Meta Model API key (or leave empty for demo mode)

After deployment, note the `ApiUrl` output.

### Step 2: Run database migrations

```bash
export DATABASE_URL="postgresql+psycopg://floodlens:<password>@<rds-endpoint>:5432/floodlens"
alembic -c backend/alembic.ini upgrade head
```

### Step 3: Deploy frontend to Amplify

1. Connect GitHub repo to AWS Amplify Hosting
2. Select `main` branch
3. Set environment variable in Amplify:
   - `VITE_API_BASE_URL` = your API Gateway URL (e.g. `https://abc123.execute-api.us-east-1.amazonaws.com/prod`)
4. Deploy

### Environment Variables

**Frontend (Amplify — public only):**
| Variable | Example |
|---|---|
| `VITE_API_BASE_URL` | `https://abc123.execute-api.us-east-1.amazonaws.com/prod` |

**Backend (Lambda — server-side only):**
| Variable | Description |
|---|---|
| `APP_ENV` | `demo` or `prod` |
| `FRONTEND_ORIGIN` | Amplify domain for CORS |
| `DATABASE_URL` | RDS PostgreSQL connection string |
| `S3_MEDIA_BUCKET` | S3 bucket name |
| `MODEL_API_KEY` | Meta Model API key |
| `AI_PROVIDER_MODE` | `live` (real AI) or `mock` (demo fixtures) |
| `ENABLE_AI_IMAGE_ANALYSIS` | `true` to enable Muse Spark |
| `ENABLE_AI_VOICE_TRANSCRIPTION` | `true` to enable Muse Voice |
| `ENABLE_SAM_SEGMENTATION` | `true` to enable SAM 3.1 |
| `SQS_MEDIA_ANALYSIS_QUEUE_URL` | SQS queue URL for async analysis |
| `DEMO_MODE` | `false` for production |

---

## Project Structure

```
floodlens-ai/
├── frontend/                    # React + Vite + TypeScript + Tailwind
│   ├── src/
│   │   ├── features/
│   │   │   ├── map/             # Interactive flood map (MapLibre GL)
│   │   │   ├── reports/         # Report form, receipt, detail page
│   │   │   ├── dashboard/       # Authority dashboard and moderation
│   │   │   ├── landing/         # Landing page
│   │   │   └── model-status/    # AI model health display
│   │   ├── components/          # Shared UI components
│   │   └── lib/                 # API client, types, utils
│   └── public/                  # PWA manifest, icons
├── backend/
│   ├── app/
│   │   ├── api/v1/              # FastAPI route handlers
│   │   ├── models/              # SQLAlchemy ORM models
│   │   ├── schemas/             # Pydantic v2 request/response schemas
│   │   ├── services/
│   │   │   ├── risk_engine/     # Configurable FRI calculator
│   │   │   ├── geospatial/      # H3 grid assignment
│   │   │   ├── media/           # S3 presigned URLs, validation
│   │   │   ├── ingestion/       # Synthetic demo data seeding
│   │   │   └── model_router/    # AI task → provider routing
│   │   ├── providers/
│   │   │   ├── meta_model_api/  # Muse Spark, Wonder, Image, Voice, SAM
│   │   │   ├── muse_glimmer/    # Open-weight inference adapter
│   │   │   ├── muse_spark_open/ # Sparse MoE adapter
│   │   │   └── demo/            # Mock/fixture providers
│   │   ├── workers/             # SQS worker: media analysis, voice
│   │   └── tasks/               # Seed data tasks
│   ├── alembic/                 # Database migrations
│   └── tests/                   # pytest test suite (41 tests)
├── infrastructure/
│   └── aws-sam/                 # SAM template: API GW, Lambda, RDS, S3, SQS
├── docs/
│   ├── architecture.md
│   ├── risk-methodology.md
│   ├── model-integrations.md
│   ├── data-sources.md
│   ├── security.md
│   ├── deployment.md
│   └── local-development.md
├── amplify.yml                  # Amplify build spec
├── .env.example                 # Environment variable template
└── reference.md                 # Full product specification
```

---

## Key Principles

- **Explainable risk** — every score shows contributing factors, data sources, confidence, and gaps
- **Human verification** — AI findings are never acted on without reviewer confirmation
- **Privacy by default** — reporter identity, contact details, and original media are never exposed publicly
- **Honest AI status** — model adapters display their actual state: Connected / Demo Mode / Not Configured
- **Graceful degradation** — the app remains usable when AI services, rainfall feeds, or open-weight endpoints are unavailable
- **Mobile first** — designed for modest Android devices on low-bandwidth connections
- **No Docker required** — local development uses a Python virtual environment and locally installed PostgreSQL

---

## License

MIT