# FloodLens AI — Backend

Community-powered flood observation, geospatial risk mapping, and decision-support backend.

## Quick Start (No Docker Required)

### 1. Create a Python 3.12 virtual environment

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

### 2. Configure PostgreSQL / PostGIS

```sql
CREATE DATABASE floodlens;
CREATE USER floodlens WITH PASSWORD 'floodlens';
GRANT ALL PRIVILEGES ON DATABASE floodlens TO floodlens;
\connect floodlens
CREATE EXTENSION IF NOT EXISTS postgis;
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env with your DATABASE_URL
```

### 4. Run migrations

```bash
alembic -c backend/alembic.ini upgrade head
```

### 5. Start the API

```bash
uvicorn app.main:app --app-dir backend --reload --host 127.0.0.1 --port 8000
```

API docs available at http://localhost:8000/docs

### 6. Run tests

```bash
pytest backend/tests -q
```

## Architecture

- **FastAPI** with Pydantic v2 schemas
- **SQLAlchemy 2** async with PostgreSQL + PostGIS
- **Alembic** for migrations
- **Mangum** adapter for AWS Lambda deployment
- **Provider abstraction** for Meta Model API and open-weight models
- **ModelRouter** for task→provider routing
- **RiskEngine** for configurable Flood Risk Index calculation

## AI Providers

| Provider | Type | Status |
|---|---|---|
| Muse Spark | Hosted Meta API | Configurable |
| Muse Wonder | Hosted Meta API | Configurable |
| Muse Image | Hosted Meta API | Configurable |
| Muse Voice | Hosted Meta API | Configurable |
| SAM 3.1 | Hosted Meta API | Configurable |
| Muse Glimmer | Open-Weight | Configurable |
| Muse Spark Open | Open-Weight | Configurable |
| Demo | Mock | Default |

Set `AI_PROVIDER_MODE=mock` for local development without Meta API credentials.

## Environment Variables

See `.env.example` for all configuration options. Never commit real secrets.
