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

- **Frontend:** AWS Amplify Hosting (from GitHub `main` branch)
- **Backend:** AWS Lambda (Python 3.12 + FastAPI + Mangum) behind API Gateway HTTP API
- **Database:** RDS PostgreSQL + PostGIS
- **Storage:** S3 for media and source data
- **Queue:** SQS for async media analysis
- **Secrets:** AWS Secrets Manager

## License

MIT
