# FloodLens AI — Model Integrations

## Hosted Models (Meta Model API)

Base URL: `https://api.meta.ai/v1`
Auth: `Authorization: Bearer ${MODEL_API_KEY}`

| Model | Model ID | Role |
|---|---|---|
| Muse Spark | `muse-spark-1.3` | Primary multimodal scene interpretation |
| Muse Wonder | `muse-wonder-1.0` | Complex multi-report evidence synthesis |
| Muse Image | `muse-image-1.0` | Preparedness illustrations (never evidence) |
| Muse Voice | `muse-voice-transcribe-1.0` | Voice-to-text transcription |
| SAM 3.1 | `sam-3.1` | Object/region segmentation |

## Open-Weight Models

| Model | Deployment | Role |
|---|---|---|
| Muse Glimmer | 30B, Apache 2.0, OpenAI-compatible endpoint | Fallback/edge image interpretation |
| Muse Spark Open | 816B MoE, private GPU endpoint | Advanced optional inference profile |

## Provider Abstraction

The `ModelRouter` maps task types to providers:
- `image_assessment` → Muse Spark / Glimmer / Spark Open / Demo
- `segmentation` → SAM 3.1 / Demo
- `voice_transcription` → Muse Voice / Demo
- `evidence_synthesis` → Muse Wonder / Demo
- `preparedness_visual` → Muse Image / Demo

Never silently falls back from real to mock. UI shows "Demo analysis" when fixtures are used.

## Provenance

Every AI analysis records: provider, model_id, model_version, prompt_version, request_id, processing_ms, and normalised response.

## Reference Documentation

- Meta Model API: https://dev.meta.ai/docs/overview
- Meta models catalogue: https://dev.meta.ai/docs/models
- SAM 3.1: https://dev.meta.ai/docs/sam/overview
- Muse Glimmer: https://dev.meta.ai/docs/muse-glimmer
- Muse Spark Open: https://dev.meta.ai/docs/muse-spark-open
