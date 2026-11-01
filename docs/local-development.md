# FloodLens AI — Local Development

## Prerequisites

- Python 3.12 with `venv` / `pip`
- Node.js 20+ (LTS recommended)
- PostgreSQL 16+ with PostGIS extension installed
- Git
- Optional: AWS CLI for deployment

## Backend Setup (No Docker Required)

### 1. Create Python virtual environment

On Windows (PowerShell):
```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

On macOS / Linux:
```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

### 2. Configure PostgreSQL / PostGIS

Create a local development database:
```sql
CREATE DATABASE floodlens;
CREATE USER floodlens WITH PASSWORD 'floodlens';
GRANT ALL PRIVILEGES ON DATABASE floodlens TO floodlens;
\connect floodlens
CREATE EXTENSION IF NOT EXISTS postgis;
```

### 3. Configure environment

```bash
cp .env.example backend/.env
# Edit backend/.env with your local DATABASE_URL
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

### 6. Run backend tests

```bash
pytest backend/tests -q
```

## Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at http://localhost:5173

## Environment Variables

See `.env.example` for all configuration options. Never commit real secrets.
Use `AI_PROVIDER_MODE=mock` for local development without Meta API credentials.

## Default Ports

| Service | Port |
|---|---|
| Backend API | 8000 |
| Frontend Dev | 5173 |
| PostgreSQL | 5432 |
