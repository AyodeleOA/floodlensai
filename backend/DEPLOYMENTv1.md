# AWS Lambda Deployment Guide

This guide covers deploying the AfriFashion3D API to AWS Lambda.

## Deployment Options

1. **Serverless Framework** (Recommended for development)
2. **AWS SAM** (Recommended for production)
3. **Manual Deployment** (For learning/testing)

---

## Option 1: Serverless Framework Deployment

### Prerequisites
```bash
npm install -g serverless
npm install --save-dev serverless-python-requirements serverless-dotenv-plugin
```

### Steps

1. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your actual values
```

2. **Deploy to AWS**
```bash
# Deploy to dev stage
serverless deploy --stage dev

# Deploy to production
serverless deploy --stage prod
```

3. **View logs**
```bash
serverless logs -f api --tail
```

4. **Remove deployment**
```bash
serverless remove --stage dev
```

### Serverless Framework Benefits
- Automatic API Gateway setup
- Easy environment management
- Built-in logging
- Simple rollback

---

## Option 2: AWS SAM Deployment

### Prerequisites
```bash
# Install AWS SAM CLI
pip install aws-sam-cli

# Or using Homebrew (macOS)
brew install aws-sam-cli
```

### Steps

1. **Build the application**
```bash
sam build
```

2. **Deploy (guided)**
```bash
sam deploy --guided
```

You'll be prompted for:
- Stack name: `afrifashion3d-api`
- AWS Region: `us-east-1`
- SecretKey: Your JWT secret (min 32 chars)
- S3BucketName: Your bucket name
- AllowedOrigins: Your frontend URLs
- Environment: `production`

3. **Deploy (subsequent deployments)**
```bash
sam deploy
```

4. **View logs**
```bash
sam logs -n FashionApiFunction --tail
```

5. **Delete stack**
```bash
sam delete
```

### SAM Benefits
- Infrastructure as Code
- Local testing with `sam local`
- CloudFormation integration
- Production-ready

---

## Option 3: Manual Lambda Deployment

### Steps

1. **Create deployment package**
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt -t package/

# Copy application code
cp -r app package/
cp lambda_function.py package/
cp main.py package/

# Create ZIP
cd package
zip -r ../deployment-package.zip .
cd ..
```

2. **Create Lambda function via AWS Console**
- Go to AWS Lambda Console
- Create function: "afrifashion3d-api"
- Runtime: Python 3.11
- Upload deployment-package.zip
- Set handler: `lambda_function.lambda_handler`
- Memory: 512 MB
- Timeout: 30 seconds

3. **Configure environment variables**
Add all variables from `.env.example`

4. **Create IAM role with policies**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::your-bucket/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:Query",
        "dynamodb:Scan"
      ],
      "Resource": [
        "arn:aws:dynamodb:*:*:table/fashion_users",
        "arn:aws:dynamodb:*:*:table/fashion_garments"
      ]
    },
    {
      "Effect": "Allow",
      "Action": "rekognition:DetectLabels",
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": "bedrock:InvokeModel",
      "Resource": "*"
    }
  ]
}
```

5. **Create API Gateway**
- Create HTTP API
- Add integration to Lambda function
- Configure CORS
- Deploy to stage

---

## Post-Deployment Setup

### 1. Create DynamoDB Tables
```bash
python setup_dynamodb.py
```

Or use the SAM template (tables created automatically).

### 2. Set up S3 Lifecycle Policy
```bash
python scripts/setup_s3_lifecycle.py
```

### 3. Test the API
```bash
# Get API URL from deployment output
export API_URL="https://your-api-id.execute-api.us-east-1.amazonaws.com"

# Test health endpoint
curl $API_URL/health

# Test signup
curl -X POST $API_URL/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!@#"}'
```

---

## Lambda Configuration

### Recommended Settings

**Memory**: 512 MB
- Sufficient for image processing
- Good balance of cost/performance

**Timeout**: 30 seconds
- Handles Bedrock API calls
- Allows for image processing

**Concurrency**: 
- Reserved: 5 (Free Tier: 1000 concurrent executions)
- Provisioned: 0 (use on-demand)

**Environment Variables**:
```
SECRET_KEY=<your-secret-key>
AWS_REGION=us-east-1
S3_BUCKET_NAME=<your-bucket>
ALLOWED_ORIGINS=https://your-frontend.com
ENVIRONMENT=production
MAX_FILE_SIZE=5242880
IMAGE_MAX_DIMENSION=1024
JPEG_QUALITY=85
MAX_UPLOADS_PER_USER_MONTH=10
MAX_AI_REQUESTS_PER_USER_MONTH=5
ENABLE_BEDROCK=true
BEDROCK_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0
BEDROCK_MAX_TOKENS=1000
```

---

## Cost Optimization for Lambda

### Lambda Free Tier
- **1 million requests per month**
- **400,000 GB-seconds of compute time**

### Estimated Costs (Beyond Free Tier)
- Requests: $0.20 per 1M requests
- Compute: $0.0000166667 per GB-second

### Example Usage (100% Free)
- 100 users
- 10 uploads/user/month = 1,000 requests
- 5 AI analyses/user/month = 500 requests
- Average execution: 3 seconds @ 512MB

**Total**: 1,500 requests × 3s × 0.5GB = 2,250 GB-seconds
**Cost**: FREE (well within limits)

---

## Monitoring

### CloudWatch Logs
```bash
# View logs
aws logs tail /aws/lambda/afrifashion3d-api --follow

# Filter errors
aws logs filter-pattern /aws/lambda/afrifashion3d-api --filter-pattern "ERROR"
```

### CloudWatch Metrics
- Invocations
- Duration
- Errors
- Throttles
- Concurrent executions

### Set up Alarms
```bash
aws cloudwatch put-metric-alarm \
  --alarm-name lambda-errors \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold
```

---

## Troubleshooting

### Common Issues

**1. Import errors**
```
Solution: Ensure all dependencies are in the deployment package
```

**2. Timeout errors**
```
Solution: Increase Lambda timeout to 30 seconds
```

**3. Memory errors**
```
Solution: Increase memory to 512MB or 1024MB
```

**4. Permission errors**
```
Solution: Check IAM role has required policies
```

**5. Cold start latency**
```
Solution: Use provisioned concurrency or keep functions warm
```

---

## CI/CD Pipeline

### GitHub Actions Example
```yaml
name: Deploy to Lambda

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Deploy with Serverless
        run: |
          npm install -g serverless
          serverless deploy --stage prod
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
```

---

## Security Best Practices

1. **Use AWS Secrets Manager** for sensitive data
2. **Enable AWS WAF** for API Gateway
3. **Use VPC** for Lambda (if accessing private resources)
4. **Enable CloudTrail** for audit logging
5. **Use least privilege IAM roles**
6. **Enable API Gateway throttling**
7. **Use custom domain with SSL**

---

## Performance Optimization

1. **Reduce cold starts**
   - Keep functions warm with CloudWatch Events
   - Use provisioned concurrency for critical functions

2. **Optimize package size**
   - Remove unnecessary dependencies
   - Use Lambda layers for common libraries

3. **Connection pooling**
   - Reuse AWS SDK clients
   - Cache DynamoDB connections

4. **Async processing**
   - Use SQS for long-running tasks
   - Offload heavy processing to Step Functions

---

## Rollback Strategy

### Serverless Framework
```bash
serverless rollback --timestamp <timestamp>
```

### AWS SAM
```bash
aws cloudformation update-stack \
  --stack-name afrifashion3d-api \
  --use-previous-template
```

### Manual
- Use Lambda versions and aliases
- Keep previous deployment packages
- Use CloudFormation change sets

---

## Additional Resources

- [AWS Lambda Documentation](https://docs.aws.amazon.com/lambda/)
- [Serverless Framework Docs](https://www.serverless.com/framework/docs)
- [AWS SAM Documentation](https://docs.aws.amazon.com/serverless-application-model/)
- [Mangum Documentation](https://mangum.io/)
