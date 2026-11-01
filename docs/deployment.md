# FloodLens AI — Deployment Guide

## AWS Amplify Hosting (Frontend)

1. Push code to GitHub repository `floodlens-ai`
2. Create an AWS Amplify Hosting application connected to the repo
3. Select `main` branch for demo deployment
4. Set frontend app root to `frontend`
5. The `amplify.yml` at the repository root handles the build
6. Configure environment variables in Amplify:
   - `VITE_API_BASE_URL` — deployed API Gateway URL (public, safe for frontend)
   - Do NOT put MODEL_API_KEY, database passwords, or private keys in Amplify env vars
7. SPA rewrite rules are handled by Amplify for client-side routes

## Backend (API Gateway + Lambda)

### Using AWS SAM

```bash
cd infrastructure/aws-sam
sam build
sam deploy --guided
```

The SAM template provisions:
- API Gateway HTTP API (Lambda proxy integration)
- FastAPI Lambda function (Python 3.12 + Mangum)
- SQS media analysis queue with dead-letter queue
- SQS-triggered worker Lambda
- S3 media bucket (private, block-public-access enabled)
- RDS PostgreSQL instance

### Lambda Packaging
- ZIP-based packaging via SAM (no Docker required on developer machine)
- Python 3.12 runtime
- Mangum adapter wraps the FastAPI app

### Database Migrations
Run Alembic migrations as a controlled deployment step:
```bash
alembic -c backend/alembic.ini upgrade head
```
Do not run migrations on every Lambda cold start.

### Secrets
Store in AWS Secrets Manager:
- MODEL_API_KEY
- Database credentials
- Open-weight endpoint keys

## Environment Configuration

### Local Development
- Frontend: `VITE_API_BASE_URL=` (empty) — Vite proxies `/api` and `/health` to `localhost:8000`
- Backend: Copy `backend/.env.example` to `backend/.env`, set `DATABASE_URL` to local PostgreSQL
- Use `AI_PROVIDER_MODE=mock` and `DEMO_MODE=true` — no live AI calls needed

### Production (Amplify + API Gateway)

**Frontend (AWS Amplify Hosting environment variables):**
- `VITE_API_BASE_URL` — your deployed API Gateway HTTPS URL (e.g. `https://abc123.execute-api.us-east-1.amazonaws.com/prod`)
- Do NOT set any `MODEL_API_KEY`, `DATABASE_URL`, `AWS_SECRET_ACCESS_KEY`, or other secrets in Amplify env vars
- Only `VITE_` prefixed variables are exposed to the browser

**Backend (Lambda environment variables / Secrets Manager):**
- `APP_ENV` — `demo` or `prod`
- `FRONTEND_ORIGIN` — your Amplify frontend URL (e.g. `https://main.d12345.amplifyapp.com`) for CORS
- `DATABASE_URL` — RDS PostgreSQL connection string (from Secrets Manager)
- `S3_MEDIA_BUCKET` — the provisioned S3 bucket name
- `MODEL_API_KEY` — from Secrets Manager, not in env vars directly
- `AI_PROVIDER_MODE` — `live` for real Meta API calls, `mock` for demo
- `ENABLE_AI_IMAGE_ANALYSIS`, `ENABLE_AI_VOICE_TRANSCRIPTION`, etc. — enable as needed
- `SQS_MEDIA_ANALYSIS_QUEUE_URL` — the deployed SQS queue URL
- `DEMO_MODE` — `false` for production

**API Gateway CORS:**
The SAM template configures CORS to allow the Amplify frontend origin. When you know your Amplify domain, update the `FrontendOrigin` parameter to match.

- [ ] GitHub repository created and code pushed
- [ ] CI passes
- [ ] Amplify GitHub App authorised
- [ ] Amplify main branch deploy succeeds
- [ ] SPA rewrite rules work on direct page refresh
- [ ] API Gateway HTTP API invokes the FastAPI Lambda handler
- [ ] Health endpoint reachable over HTTPS
- [ ] Lambda package targets Python 3.12
- [ ] SQS worker Lambda retry and DLQ tested
- [ ] CORS allows only intended frontend origins
- [ ] S3 bucket is private, presigned uploads work
- [ ] Secrets Manager contains server-side Meta key
- [ ] Database migrations have run
- [ ] CloudWatch logs and alarms configured
- [ ] Demo data is visibly labelled
