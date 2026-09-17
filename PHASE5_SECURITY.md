# Phase 5 — Security

Implemented:
- Redis fixed-window login rate limiting: 5 attempts per minute per IP + username.
- CORS configuration via `CORS_ALLOW_ORIGINS`.
- Security response headers.
- Request ID generation/propagation via `X-Request-ID`.
- Audit log model, repository, migration, and middleware for mutating requests.
- Idempotency-Key enforcement on user update/delete operations.
- Email normalization and Pydantic input validation retained.

Production notes:
- Keep `.env` out of source control and use AWS Secrets Manager/SSM in deployment.
- Replace localhost CORS origins with the actual frontend origins in production.
- The idempotency implementation currently rejects duplicate keys; response replay can be added later if required by the business API contract.
- Rate limiting is Redis-backed and therefore shared across application instances.
