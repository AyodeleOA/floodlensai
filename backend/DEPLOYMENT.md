# FloodLens AI — Backend Deployment Guide

This guide covers deploying the FloodLens AI FastAPI backend to AWS Lambda behind API Gateway, with RDS PostgreSQL + PostGIS, S3, SQS, and Secrets Manager.

## Architecture

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
```

---

## Prerequisites

- Python 3.12 and `venv`
- AWS CLI configured with appropriate credentials
- AWS SAM CLI installed
- PostgreSQL 16+ with PostGIS (for local dev only)
- No Docker required on the developer machine

```bash
# Install AWS SAM CLI
pip install aws-sam-cli

# Verify
sam --version
```

---

## Option 1: AWS SAM Deployment (Recommended for Production)

### 1. Build the application

```bash
cd infrastructure/aws-sam
sam build
```

### 2. First deployment (guided)

```bash
sam deploy --guided
```

You will be prompted for:
- **Stack Name**: `floodlens-ai`
- **AWS Region**: `us-east-1` (or your preferred region)
- **AppEnv**: `demo` or `prod`
- **FrontendOrigin**: Your Amplify frontend URL (e.g. `https://main.dmpm2yei4pgxa.amplifyapp.com/`)
- **ApiGatewayStage**: `prod`
- **Confirm changes before deploy**: Y
- **Allow SAM CLI IAM role creation**: Y
- **Save parameters to samconfig.toml**: Y

### 3. Subsequent deployments

```bash
sam deploy
```

### 4. View logs

```bash
sam logs -n FloodLensApiFunction --tail
sam logs -n FloodLensWorkerFunction --tail
```

### 5. Delete stack (teardown)

```bash
sam delete
```

### SAM Benefits
- Infrastructure as Code (CloudFormation)
- Local testing with `sam local start-api`
- ZIP-based Lambda packaging (no Docker needed)
- Automatic API Gateway, SQS, S3, and RDS provisioning

---

## Option 2: Manual Lambda Deployment

### 1. Create deployment package

```bash
# From the backend directory, with .venv activated
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1   # Windows
# source .venv/bin/activate     # macOS/Linux

pip install -e ".[dev]"

# Install dependencies into a package directory
pip install -e . -t package/
cp -r app package/

# Create ZIP
cd package
# Windows PowerShell:
Compress-Archive -Path * -DestinationPath ../deployment-package.zip
# macOS/Linux:
# zip -r ../deployment-package.zip .
cd ..
```

### 2. Create Lambda function via AWS Console

- Go to AWS Lambda Console
- Create function: `floodlens-ai-api`
- Runtime: Python 3.12
- Upload `deployment-package.zip`
- Handler: `app.lambda_handler.handler`
- Memory: 512 MB
- Timeout: 30 seconds

### 3. Configure environment variables

Set the following environment variables on the Lambda function:

```
APP_ENV=demo
API_V1_PREFIX=/api/v1
FRONTEND_ORIGIN=https://main.d12345.amplifyapp.com
DATABASE_URL=postgresql+psycopg://<rds-user>:<rds-password>@<rds-endpoint>:5432/floodlens
S3_MEDIA_BUCKET=floodlens-media-us-east-1-123456789
AWS_REGION=us-east-1
MODEL_API_BASE_URL=https://api.meta.ai/v1
AI_PROVIDER_MODE=live
ENABLE_AI_IMAGE_ANALYSIS=true
DEMO_MODE=false
SQS_MEDIA_ANALYSIS_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/123456789/floodlens-media-analysis
```

Store `MODEL_API_KEY` and database credentials in **Secrets Manager**, not as plaintext env vars.

### 4. Create API Gateway HTTP API

- Create HTTP API in API Gateway Console
- Add integration: Lambda function `floodlens-ai-api`
- Configure routes:
  - `ANY /{proxy+}` → Lambda proxy integration
  - `GET /health/live` → Lambda
  - `GET /health/ready` → Lambda
- Configure CORS:
  - Allow origins: your Amplify frontend URL
  - Allow methods: GET, POST, PUT, PATCH, DELETE, OPTIONS
  - Allow headers: Content-Type, X-User-Role, X-User-Id, X-User-Email, X-User-Organisation
- Deploy to stage: `prod`

### 5. Get the API Gateway URL

After deployment, your API URL will be:
```
https://{api-id}.execute-api.{region}.amazonaws.com/prod
```

Set this as `VITE_API_BASE_URL` in your Amplify frontend environment variables.

---

## Post-Deployment Setup

### 1. Run database migrations

Run Alembic migrations against the RDS instance as a controlled deployment step:

```bash
# Set DATABASE_URL to your RDS instance
export DATABASE_URL="postgresql+psycopg://<user>:<password>@<rds-endpoint>:5432/floodlens"

# Run migrations
alembic -c backend/alembic.ini upgrade head
```

Do NOT run migrations on every Lambda cold start. Run them as a one-time deployment step.

### 2. Configure Secrets Manager

Store these secrets in AWS Secrets Manager:

```
floodlens/meta-api-key        → Your Meta Model API key
floodlens/database-url         → RDS PostgreSQL connection string
floodlens/glimmer-api-key      → Muse Glimmer endpoint key (if enabled)
floodlens/spark-open-api-key   → Muse Spark Open endpoint key (if enabled)
```

### 3. Create SQS-triggered worker Lambda

Create a second Lambda function for the SQS worker:
- Handler: `app.workers.media_analysis.sqs_handler`
- Memory: 1024 MB (image processing needs more)
- Timeout: 120 seconds
- SQS trigger: the media analysis queue
- Batch size: 5
- Visibility timeout: 120
- Dead letter queue: `floodlens-media-analysis-dlq`

### 4. Test the API

```bash
# Get API URL from deployment output
export API_URL="https://your-api-id.execute-api.us-east-1.amazonaws.com/prod"

# Test health endpoint
curl $API_URL/health/live

# Test ready endpoint
curl $API_URL/health/ready

# Test system capabilities
curl $API_URL/api/v1/system/capabilities | python -m json.tool

# Test creating a report
curl -X POST $API_URL/api/v1/reports \
  -H "Content-Type: application/json" \
  -d '{
    "report_type": "flooding",
    "latitude": 6.4541,
    "longitude": 3.3947,
    "hazard_type": "floodwater",
    "severity": "high",
    "privacy_consent": true
  }'
```

---

## Frontend Amplify Configuration

After the backend is deployed, configure the frontend on AWS Amplify Hosting:

1. Connect your GitHub repository to AWS Amplify
2. Set frontend app root to `frontend`
3. Set environment variables in Amplify:
   - `VITE_API_BASE_URL` = your API Gateway URL (e.g. `https://abc123.execute-api.us-east-1.amazonaws.com/prod`)
   - Do NOT add `MODEL_API_KEY`, `DATABASE_URL`, or any secrets to Amplify env vars
4. The `amplify.yml` at the repo root handles the build

---

## Lambda Configuration

### Recommended Settings

**API Lambda**:
- Memory: 512 MB
- Timeout: 30 seconds
- Reserved concurrency: 10 (prevent database connection exhaustion)

**Worker Lambda**:
- Memory: 1024 MB
- Timeout: 120 seconds
- Reserved concurrency: 5

### Environment Variables (API Lambda)

| Variable | Value | Source |
|---|---|---|
| APP_ENV | demo or prod | Direct |
| FRONTEND_ORIGIN | Amplify URL | Direct |
| DATABASE_URL | RDS connection string | Secrets Manager |
| S3_MEDIA_BUCKET | bucket name | Direct |
| MODEL_API_KEY | Meta API key | Secrets Manager |
| AI_PROVIDER_MODE | live | Direct |
| ENABLE_AI_IMAGE_ANALYSIS | true | Direct |
| SQS_MEDIA_ANALYSIS_QUEUE_URL | SQS URL | Direct |
| DEMO_MODE | false | Direct |

---

## Cost Optimization

### Lambda Free Tier
- 1 million requests per month
- 400,000 GB-seconds of compute time

### RDS Proxy
Use RDS Proxy to manage database connections and prevent Lambda concurrency spikes from exhausting the connection pool.

### SQS Worker
Offload long-running AI analysis to SQS-triggered workers. This keeps the API Lambda fast and within timeout limits.

---

## Monitoring

### CloudWatch Logs
```bash
# API logs
aws logs tail /aws/lambda/floodlens-ai-api --follow

# Worker logs
aws logs tail /aws/lambda/floodlens-ai-worker --follow

# Filter errors
aws logs filter-pattern /aws/lambda/floodlens-ai-api --filter-pattern "ERROR"
```

### CloudWatch Alarms

Set up alarms for:
- API errors (5xx responses)
- Lambda duration approaching timeout
- Lambda throttles
- SQS queue depth
- DLQ message count
- Database connection exhaustion
- Model provider failures

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name floodlens-api-errors \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --dimensions Name=FunctionName,Value=floodlens-ai-api \
  --statistic Sum \
  --period 300 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold
```

---

## Troubleshooting

### Common Issues

**1. Import errors in Lambda**
- Ensure all dependencies are in the deployment package
- Check that `psycopg[binary]` is used (not `psycopg[c]` which requires compilation)

**2. Database connection errors**
- Verify RDS security group allows Lambda access
- Use RDS Proxy to manage connection pooling
- Check DATABASE_URL format: `postgresql+psycopg://user:pass@host:5432/db`

**3. CORS errors from frontend**
- Verify `FRONTEND_ORIGIN` matches your Amplify URL exactly (including https://)
- Check API Gateway CORS configuration

**4. Cold start latency**
- Increase memory to reduce cold start time
- Use provisioned concurrency for production
- Keep the deployment package as small as possible

**5. Lambda timeout on AI calls**
- Move long-running AI calls to SQS worker Lambda
- API Lambda should only enqueue jobs and return 202 Accepted
- Worker Lambda has 120s timeout for AI processing

---

## CI/CD Pipeline

### GitHub Actions for backend deployment

```yaml
name: Deploy Backend

on:
  push:
    branches: [main]
    paths:
      - 'backend/**'
      - 'infrastructure/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python 3.12
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install SAM CLI
        run: pip install aws-sam-cli

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1

      - name: Build and deploy
        run: |
          cd infrastructure/aws-sam
          sam build
          sam deploy --no-confirm-changeset --no-fail-on-empty-changeset
```

---

## Security Best Practices

1. Use **AWS Secrets Manager** for MODEL_API_KEY, database credentials, and inference endpoint keys
2. Enable **AWS WAF** on API Gateway for throttling and abuse protection
3. Use **least privilege IAM roles** for both API and worker Lambdas
4. Enable **CloudTrail** for audit logging
5. Use **RDS encryption at rest** and TLS in transit
6. S3 bucket: **block all public access**, use presigned URLs only
7. Strip GPS EXIF from public image derivatives
8. Never package secrets into the Lambda ZIP or frontend build
9. Validate file uploads using magic bytes
10. Rate-limit anonymous reporting

---

## Rollback Strategy

### AWS SAM
```bash
# View deployed versions
aws cloudformation describe-change-set --change-set-name <name> --stack-name floodlens-ai

# Roll back to previous stack version
aws cloudformation rollback-stack --stack-name floodlens-ai --rollback-configuration ...
```

### Manual
- Keep previous deployment ZIPs
- Use Lambda versions and aliases
- Use CloudFormation change sets for review

---

## Additional Resources

- [AWS SAM Documentation](https://docs.aws.amazon.com/serverless-application-model/)
- [Mangum Documentation](https://mangum.io/)
- [FastAPI on Lambda](https://docs.aws.amazon.com/lambda/latest/dg/services-apigateway.html)
- [RDS Proxy for Lambda](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/rds-proxy.html)
- [AWS Secrets Manager](https://docs.aws.amazon.com/secretsmanager/latest/userguide/intro.html)
