# FloodLens AI — Security

## Authentication & Authorization

- Amazon Cognito or standards-based identity provider for staff/authority accounts
- Public reports may be anonymous, but rate-limited and abuse-protected
- Roles: `public`, `reporter`, `reviewer`, `authority_admin`, `platform_admin`
- Permissions enforced in the backend, not only by hiding frontend controls

## API Key & Secrets Management

- All Meta API credentials remain server-side
- Browser never calls Meta Model API directly or receives MODEL_API_KEY
- Secrets stored in AWS Secrets Manager
- Never commit `.env`, API keys, credentials, model weights, personal data, or production media to GitHub

## S3 & Media

- Short-lived presigned S3 URLs for uploads
- Private buckets with block-public-access enabled
- EXIF/GPS stripped from public image derivatives
- Original evidence preserved privately only where justified
- File uploads validated using magic bytes, not only filename or browser MIME type

## Network & Transport

- TLS in transit for all connections
- CORS allow-list (only intended frontend origins)
- Secure headers and request validation
- CSRF protection where cookie auth is used

## Privacy

- Reporter identity, phone number, exact address, and original media not exposed publicly
- Public map uses approximate/aggregated location for sensitive reports
- Public APIs return only coarse coordinates (2 decimal places)
- Full coordinates restricted to authorised reviewers
- Retention and deletion policies for reporter data and media

## Audit

- Audit trails for staff access to private evidence
- Moderation actions and risk recalculations logged
- Audit logs include actor, action, resource, timestamp, and metadata
