# FloodLens AI — Backend Deployment Guide (v1)

## Architecture

```
Amplify Hosting (React frontend)
        │ HTTPS
        ▼
API Gateway HTTP API ──► Lambda (FastAPI + Mangum)
                              │
                   ┌──────────┼──────────┐
                   │          │          │
                   ▼          ▼          ▼
              RDS PG      S3 Media    SQS Queue
              + PostGIS    Bucket     (analysis jobs)
                                        │
                                        ▼
                                   Worker Lambda
                                   (SQS-triggered)
                                        │
                                   ┌────┴────┐
                                   ▼         ▼
                              Meta API   Secrets Manager
                              (Muse, SAM)
```

## Prerequisites

- AWS CLI configured with appropriate credentials
- AWS SAM CLI installed (`pip install aws-sam-cli`)
- Python 3.12 (for local testing)
- PostgreSQL with PostGIS (for local development only)
- No Docker required

## Step 1: Local Development Setup

```powershell
# Create virtual environment
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

Configure local PostgreSQL/PostGIS:
```sql
CREATE DATABASE floodlens;
CREATE USER floodlens WITH PASSWORD 'floodlens';
GRANT ALL PRIVILEGES ON DATABASE floodlens TO floodlens;
\connect floodlens
CREATE EXTENSION IF NOT EXISTS postgis;
```

```bash
cp .env.example .env
# Edit .env — set DATABASE_URL, keep AI_PROVIDER_MODE=mock for local
alembic -c backend/alembic.ini upgrade head
uvicorn app.main:app --app-dir backend --reload --host 127.0.0.1 --port 8000
```

Verify: http://localhost:8000/docs

## Step 2: Deploy Backend to AWS (API Gateway + Lambda)

### 2.1 Build and deploy with SAM

```bash
cd infrastructure/aws-sam
sam build
sam deploy --guided
```

SAM will prompt for:
- **Stack Name:** `floodlens-ai`
- **AWS Region:** your target region (e.g. `us-east-1`)
- **AppEnv:** `demo` (for demo deployment) or `prod`
- **FrontendOrigin:** your Amplify URL (e.g. `https://main.d12345.amplifyapp.com`)
- **ApiGatewayStage:** `prod`
- **DBName:** `floodlens`
- **DBUser:** `floodlens`
- **DBPassword:** set a strong alphanumeric password (8-41 chars)
- **Confirm changes before deploy:** y
- **Allow SAM CLI IAM role creation:** y
- **Save arguments to samconfig.toml:** y

SAM provisions:
- API Gateway HTTP API (Lambda proxy integration)
- FastAPI Lambda function (Python 3.12 + Mangum)
- SQS media analysis queue with dead-letter queue
- SQS-triggered worker Lambda
- S3 media bucket (private, block-public-access)
- RDS PostgreSQL instance

### 2.2 Note the outputs

After deployment, SAM outputs the `ApiUrl`. This is your API Gateway endpoint:
```
https://abc123.execute-api.us-east-1.amazonaws.com/prod
```

### 2.3 Verify the health endpoint

```bash
curl https://abc123.execute-api.us-east-1.amazonaws.com/prod/health/live
# Expected: {"status":"ok","timestamp":"..."}
```

## Step 3: Run Database Migrations on RDS

```bash
# Set DATABASE_URL to the RDS endpoint from SAM outputs
export DATABASE_URL="postgresql+psycopg://floodlens:<password>@<rds-endpoint>:5432/floodlens"
alembic -c backend/alembic.ini upgrade head
```

## Step 4: Configure Secrets in AWS Secrets Manager

Store these secrets in AWS Secrets Manager (never in env vars or Git):

```bash
aws secretsmanager create-secret \
  --name floodlens/model-api-key \
  --secret-string "your-meta-api-key"

aws secretsmanager create-secret \
  --name floodlens/db-credentials \
  --secret-string '{"username":"floodlens","password":"<password>","engine":"postgres","host":"<rds-endpoint>","port":5432,"dbname":"floodlens"}'
```

The Lambda function has IAM permission to read from Secrets Manager.
Update the Lambda environment to fetch secrets at runtime:

```bash
# Update the deployed Lambda to use Secrets Manager
aws lambda update-function-configuration \
  --function-name floodlens-ai-FloodLensApiFunction-XXXXX \
  --environment Variables='{APP_ENV=demo,AI_PROVIDER_MODE=live,...}'
```

## Step 5: Deploy Frontend to AWS Amplify

1. Push code to GitHub repository `floodlens-ai`
2. In AWS Console → Amplify Hosting → Create app → Connect to GitHub
3. Select the repository and `main` branch
4. Amplify auto-detects `amplify.yml` at the repo root
5. Set Amplify environment variables:
   - `VITE_API_BASE_URL` = your API Gateway URL from Step 2 (e.g. `https://abc123.execute-api.us-east-1.amazonaws.com/prod`)
6. Do NOT set any of these in Amplify:
   - `MODEL_API_KEY`
   - `DATABASE_URL`
   - `AWS_SECRET_ACCESS_KEY`
   - Any private inference keys
7. Deploy and verify the frontend loads

## Step 6: Configure CORS

The SAM template configures CORS on API Gateway to allow the `FrontendOrigin` parameter.
After your Amplify domain is known, update the stack:

```bash
cd infrastructure/aws-sam
sam deploy --parameter-overrides FrontendOrigin=https://main.d12345.amplifyapp.com
```

## Step 7: Enable AI Features (Optional)

To enable live Meta Model API calls:

1. Store `MODEL_API_KEY` in Secrets Manager (Step 4)
2. Update Lambda environment:
   - `AI_PROVIDER_MODE=live`
   - `ENABLE_AI_IMAGE_ANALYSIS=true`
   - `ENABLE_AI_VOICE_TRANSCRIPTION=true` (if needed)
   - `ENABLE_SAM_SEGMENTATION=true` (if needed)
   - `DEMO_MODE=false`
3. Redeploy: `sam deploy`

## Environment Variables Reference

### Frontend (Amplify — public only)
| Variable | Example | Description |
|---|---|---|
| `VITE_API_BASE_URL` | `https://abc123.execute-api.us-east-1.amazonaws.com/prod` | API Gateway URL |

### Backend (Lambda — server-side only)
| Variable | Example | Description |
|---|---|---|
| `APP_ENV` | `demo` | Environment |
| `FRONTEND_ORIGIN` | `https://main.d12345.amplifyapp.com` | CORS origin |
| `DATABASE_URL` | `postgresql+psycopg://...` | RDS connection |
| `S3_MEDIA_BUCKET` | `floodlens-media-us-east-1-123456` | Media bucket |
| `MODEL_API_KEY` | (from Secrets Manager) | Meta API key |
| `AI_PROVIDER_MODE` | `live` or `mock` | AI mode |
| `ENABLE_AI_IMAGE_ANALYSIS` | `true` | Enable Muse Spark |
| `ENABLE_AI_VOICE_TRANSCRIPTION` | `true` | Enable Muse Voice |
| `ENABLE_SAM_SEGMENTATION` | `true` | Enable SAM 3.1 |
| `SQS_MEDIA_ANALYSIS_QUEUE_URL` | `https://sqs...` | SQS queue |
| `DEMO_MODE` | `false` | Demo banner |

## Teardown

```bash
cd infrastructure/aws-sam
sam delete --stack-name floodlens-ai
```

## Troubleshooting

| Issue | Fix |
|---|---|
| CORS error in browser | Ensure `FRONTEND_ORIGIN` matches your Amplify domain exactly |
| 500 on API calls | Check CloudWatch logs for the Lambda function |
| DB connection errors | Verify RDS security group allows Lambda access |
| SQS jobs not processing | Check worker Lambda CloudWatch logs and DLQ |
| AI calls failing | Verify `MODEL_API_KEY` in Secrets Manager and `AI_PROVIDER_MODE=live` |
