# FloodLens AI — Implementation Plan

## Milestones

### Phase 0 — Planning (Complete)
- Read reference.md, produce architecture and implementation plan docs.

### Phase 1 — Foundation
- Monorepo structure
- Backend: FastAPI + SQLAlchemy + Alembic + PostGIS
- Frontend: React + Vite + TypeScript + Tailwind
- Mangum Lambda handler
- Health endpoints, config validation, structured logging
- Mock AI provider and synthetic seed data
- CI pipeline (lint, typecheck, test)

### Phase 2 — UI and Demo Map
- Product shell, landing page, responsive nav
- MapLibre map with seeded Lagos GeoJSON
- Legend, filters, data attribution
- Incident list and detail drawer
- Graceful degradation

### Phase 3 — Reports and Offline
- Report creation and validation
- GPS and manual location selection
- Presigned S3 uploads
- IndexedDB offline draft queue
- Submission receipt and status
- Role-based access and audit logging

### Phase 4 — Meta Model API Integrations
1. Muse Spark image analysis + structured JSON
2. SAM 3.1 segmentation + visual overlay
3. Muse Voice Transcribe
4. Muse Wonder evidence synthesis
5. Muse Image preparedness visuals

### Phase 5 — Open-Weight Integration
- Muse Glimmer adapter (OpenAI-compatible endpoint)
- Muse Spark Open adapter (private GPU endpoint)
- Provider selection and honest status display

### Phase 6 — Risk Engine and Data Ingestion
- Configurable 0–100 FRI with explainable contributors
- Missing-data handling, confidence scoring
- Grid aggregation (H3), duplicate protection
- Rainfall, elevation, drainage, exposure adapters
- Source freshness monitoring
- Unit tests for all risk calculations

### Phase 7 — Security, QA, Deployment
- Permission and privacy tests
- E2E tests (resident + reviewer journeys)
- Accessibility and mobile checks
- Lambda + API Gateway deployment (SAM/CDK)
- SQS worker Lambdas with retry/DLQ
- Amplify frontend deployment
- Monitoring, secrets, demo data
- Acceptance criteria verification

## Dependencies
- Python 3.12, PostgreSQL 16+ with PostGIS
- Node.js 20+
- AWS account (dev/demo/prod)
- Meta Model API credentials (live AI features)

## Risks
- PostGIS installation complexity on local dev machines
- Lambda package size with geospatial libraries
- Meta Model API availability and cost
- Open-weight model hardware requirements (Spark Open especially)
- External data feed reliability
