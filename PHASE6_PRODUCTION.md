# Phase 6 - Production Readiness

Implemented:
- Liveness: `GET /api/v1/health/live`
- Readiness: `GET /api/v1/health/ready` (PostgreSQL + Redis)
- Prometheus metrics: `GET /api/v1/health/metrics`
- Request ID propagation via `X-Request-ID`
- Structured Loguru logging
- Global validation/application/unhandled exception handlers
- SQLAlchemy pool configuration and pre-ping
- Redis health checks and graceful shutdown
- Optional OpenTelemetry FastAPI instrumentation
- Route-template based Prometheus labels to avoid high cardinality

Before production:
- Set `OTEL_ENABLED=true` only when an OTLP collector is available.
- Tune DB pool size against RDS max connections and ECS task count.
- Protect `/api/v1/health/metrics` at the network/load-balancer layer if exposed externally.
