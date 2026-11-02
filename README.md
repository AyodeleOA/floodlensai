# FloodLens AI

Community-powered flood observation, geospatial risk mapping, and decision-support for African communities.

## Quick Start

### Prerequisites

- Python 3.12 with `venv` / `pip`
- Node.js 20+ (LTS recommended)
- PostgreSQL 16+ with PostGIS extension
- Git
- Optional: AWS CLI for deployment

### Backend Setup (No Docker Required)

1. Create a Python virtual environment and install dependencies:

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
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

2. Configure PostgreSQL / PostGIS:

```sql
CREATE DATABASE floodlens;
CREATE USER floodlens WITH PASSWORD 'floodlens';
GRANT ALL PRIVILEGES ON DATABASE floodlens TO floodlens;
\connect floodlens
CREATE EXTENSION IF NOT EXISTS postgis;
```

3. Configure environment:

```bash
cp .env.example backend/.env
```

4. Run migrations:

```bash
alembic -c backend/alembic.ini upgrade head
```

5. Start the API:

```bash
uvicorn app.main:app --app-dir backend --reload --host 127.0.0.1 --port 8000
```

API docs available at http://localhost:8000/docs

6. Run backend tests:

```bash
pytest backend/tests -q
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at http://localhost:5173

### Default Ports

| Service | Port |
|---|---|
| Backend API | 8000 |
| Frontend Dev | 5173 |
| PostgreSQL | 5432 |

## Project Structure

```
floodlens-ai/
├── frontend/          # React + Vite + TypeScript + Tailwind + MapLibre
├── backend/           # FastAPI + SQLAlchemy + PostGIS + Mangum
├── infrastructure/     # AWS SAM / CDK templates
├── docs/              # Architecture, methodology, data sources
├── data/              # Demo data and schemas
├── .github/workflows/ # CI
├── amplify.yml        # AWS Amplify build spec
└── reference.md       # Project specification
```

## AI Providers

| Provider | Type | Default |
|---|---|---|
| Muse Spark | Hosted Meta API | Configurable |
| Muse Wonder | Hosted Meta API | Configurable |
| Muse Image | Hosted Meta API | Configurable |
| Muse Voice | Hosted Meta API | Configurable |
| SAM 3.1 | Hosted Meta API | Configurable |
| Muse Glimmer | Open-Weight | Disabled |
| Muse Spark Open | Open-Weight | Disabled |
| Demo | Mock | Default |

Set `AI_PROVIDER_MODE=mock` for local development without Meta API credentials.

## Environment Variables

See `.env.example` for all configuration options. Never commit real secrets.

## Deployment

### Architecture

```
Amplify Hosting (React frontend)
       | HTTPS API calls
       v
API Gateway HTTP API
       | Lambda proxy integration
       v
AWS Lambda (Python 3.12 + FastAPI + Mangum)
    |          |          |
    |          |          +--> RDS PostgreSQL + PostGIS
    |          +-----------> S3 media / source files
    |
    +--> SQS media-analysis queue --> SQS-triggered worker Lambda(s)
                                        |       |
                                        |       +--> SAM 3.1 / Muse Spark / Voice
                                        +----------> Glimmer / Spark Open endpoint

Secrets Manager --> API and worker secrets
CloudWatch ------> logs, metrics, alarms
```

### Frontend (AWS Amplify Hosting)

1. Push code to GitHub repository `floodlens-ai`
2. Create an AWS Amplify Hosting application connected to the repo
3. Select `main` branch for deployment
4. Set frontend app root to `frontend`
5. The `amplify.yml` at the repo root handles the build
6. Configure environment variables in Amplify:
   - `VITE_API_BASE_URL` — your deployed API Gateway HTTPS URL (e.g. `https://abc123.execute-api.us-east-1.amazonaws.com/prod`)
   - Do NOT add `MODEL_API_KEY`, `DATABASE_URL`, or any secrets to Amplify env vars
7. SPA rewrite rules are handled by Amplify for client-side routes

### Backend (API Gateway + Lambda)

Detailed deployment guide: [backend/DEPLOYMENT.md](backend/DEPLOYMENT.md)

#### Quick deployment with AWS SAM

```bash
cd infrastructure/aws-sam
sam build
sam deploy --guided
```

When prompted:
- **Stack Name**: `floodlens-ai`
- **AWS Region**: `us-east-1` (or your preferred region)
- **AppEnv**: `demo` or `prod`
- **FrontendOrigin**: your Amplify frontend URL (e.g. `https://main.d12345.amplifyapp.com`)
- **ApiGatewayStage**: `prod`

#### Post-deployment steps

1. Run database migrations against RDS:
   ```bash
   export DATABASE_URL="postgresql+psycopg://<user>:<password>@<rds-endpoint>:5432/floodlens"
   alembic -c backend/alembic.ini upgrade head
   ```

2. Store secrets in AWS Secrets Manager:
   - `MODEL_API_KEY` — Meta Model API key
   - `DATABASE_URL` — RDS connection string
   - Open-weight endpoint keys (if enabled)

3. Set `VITE_API_BASE_URL` in Amplify to the API Gateway URL from SAM output

4. Test the deployed API:
   ```bash
   export API_URL="https://your-api-id.execute-api.us-east-1.amazonaws.com/prod"
   curl $API_URL/health/live
   curl $API_URL/api/v1/system/capabilities | python -m json.tool
   ```

### Production Environment Configuration

**Frontend (Amplify env vars):**

| Variable | Value | Example |
|---|---|---|
| `VITE_API_BASE_URL` | API Gateway HTTPS URL | `https://abc123.execute-api.us-east-1.amazonaws.com/prod` |

**Backend (Lambda env vars):**

| Variable | Value | Source |
|---|---|---|
| `APP_ENV` | `demo` or `prod` | Direct |
| `FRONTEND_ORIGIN` | Amplify URL | Direct |
| `DATABASE_URL` | RDS connection string | Secrets Manager |
| `S3_MEDIA_BUCKET` | S3 bucket name | Direct |
| `MODEL_API_KEY` | Meta API key | Secrets Manager |
| `AI_PROVIDER_MODE` | `live` | Direct |
| `ENABLE_AI_IMAGE_ANALYSIS` | `true` | Direct |
| `SQS_MEDIA_ANALYSIS_QUEUE_URL` | SQS queue URL | Direct |
| `DEMO_MODE` | `false` | Direct |

### Services

| Component | AWS Service |
|---|---|
| Frontend hosting | AWS Amplify Hosting |
| Backend compute | AWS Lambda (Python 3.12 + Mangum) |
| API gateway | Amazon API Gateway HTTP API |
| Database | RDS PostgreSQL + PostGIS |
| Object storage | S3 (media, thumbnails, masks, source data) |
| Async queue | SQS (media analysis + dead-letter queue) |
| Scheduled jobs | EventBridge |
| Secrets | AWS Secrets Manager |
| Monitoring | CloudWatch (logs, metrics, alarms) |
| Auth | Amazon Cognito (staff accounts) |

## License

MIT
