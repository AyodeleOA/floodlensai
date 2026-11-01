# FloodLens AI — Architecture

## Overview

FloodLens AI is a community-powered flood observation and risk mapping platform for African communities. The system combines community-submitted reports, environmental data, and AI-assisted analysis to produce explainable risk indicators on interactive maps.

## High-Level Architecture

```mermaid
graph TB
    subgraph "Client"
        FE[React + Vite PWA<br/>Amplify Hosting]
    end

    subgraph "API Layer"
        AGW[API Gateway HTTP API]
        LAMBDA[Lambda: FastAPI + Mangum]
    end

    subgraph "Async Processing"
        SQS[SQS Media Analysis Queue]
        WORKER[Lambda: Worker Functions]
        DLQ[SQS Dead Letter Queue]
    end

    subgraph "Data Layer"
        RDS[(RDS PostgreSQL<br/>+ PostGIS)]
        S3[(S3 Media + Source Data)]
    end

    subgraph "AI Providers"
        META[Meta Model API<br/>Muse Spark / Wonder / Image<br/>Voice Transcribe / SAM 3.1]
        GLIMMER[Muse Glimmer<br/>Open-Weight Endpoint]
        SPARKOPEN[Muse Spark Open<br/>Private GPU Endpoint]
    end

    subgraph "Scheduled Jobs"
        EB[EventBridge]
        INGEST[Lambda: Ingestion / Recalc]
    end

    subgraph "Security"
        SM[Secrets Manager]
        COG[Cognito User Pools]
    end

    FE -->|HTTPS| AGW
    AGW -->|Lambda Proxy| LAMBDA
    LAMBDA -->|SQL| RDS
    LAMBDA -->|Presigned URLs| S3
    LAMBDA -->|Enqueue| SQS
    SQS -->|Trigger| WORKER
    WORKER -->|Read/Write| S3
    WORKER -->|Invoke| META
    WORKER -->|Invoke| GLIMMER
    WORKER -->|Invoke| SPARKOPEN
    WORKER -->|Write Results| RDS
    SQS -.->|Failures| DLQ
    EB -->|Schedule| INGEST
    INGEST -->|Fetch/Store| S3
    INGEST -->|Normalise/Persist| RDS
    SM -->|Secrets| LAMBDA
    SM -->|Secrets| WORKER
    COG -->|Auth| FE
    COG -->|Auth| AGW
```

## Data Flows

### Report Submission Flow

```mermaid
sequenceDiagram
    participant R as Resident (PWA)
    participant API as FastAPI Lambda
    participant DB as PostgreSQL/PostGIS
    participant S3 as S3 Bucket
    participant SQS as SQS Queue
    participant W as Worker Lambda
    participant AI as Muse Spark API

    R->>API: POST /api/v1/reports
    API->>DB: Insert report record
    API-->>R: Return report_id
    R->>API: POST /reports/{id}/media-upload-url
    API->>S3: Generate presigned URL
    API-->>R: Return presigned URL
    R->>S3: PUT photo (direct upload)
    R->>API: POST /reports/{id}/media-complete
    API->>S3: Validate media (magic bytes, hash)
    API->>DB: Store media_asset record
    API->>SQS: Enqueue analysis job
    API-->>R: 202 Accepted + receipt
    SQS->>W: Trigger worker
    W->>AI: Analyze image
    AI-->>W: Structured JSON analysis
    W->>DB: Store ai_analysis record
    W->>DB: Recalculate risk cell
```

### Risk Calculation Flow

```mermaid
flowchart LR
    A[Reports + Evidence] --> B[Risk Engine]
    C[Rainfall Data] --> B
    D[Terrain/Elevation] --> B
    E[Drainage Condition] --> B
    F[Exposure/Vulnerability] --> B
    B --> G{Missing inputs?}
    G -->|Yes| H[Re-normalise available<br/>Lower confidence]
    G -->|No| I[Full calculation]
    H --> J[Risk Cell: score, band,<br/>confidence, contributors]
    I --> J
    J --> K[PostGIS Storage]
```

## Component Separation

| Layer | Technology | Responsibility |
|---|---|---|
| Frontend | React + TypeScript + Vite + Tailwind | UI, maps, offline drafts, PWA |
| API | FastAPI + Mangum (Lambda) | Request handling, validation, orchestration |
| Database | PostgreSQL + PostGIS | Spatial data, reports, risk cells, audit |
| Storage | S3 | Media, thumbnails, masks, source datasets |
| Queue | SQS | Async media analysis jobs |
| AI Providers | Meta API + Open-Weight Adapters | Image analysis, segmentation, voice, synthesis |
| Risk Engine | Python service | Configurable FRI calculation |
| Ingestion | Scheduled Lambda | Environmental data adapters |
| Auth | Cognito / role-based | Staff authentication, public anonymity |
| Secrets | Secrets Manager | API keys, DB credentials |
