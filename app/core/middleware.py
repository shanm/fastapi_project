import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.audit import write_audit_log
from app.core.logging import logger
from app.core.metrics import (
    HTTP_REQUEST_DURATION_SECONDS,
    HTTP_REQUESTS_IN_PROGRESS,
    HTTP_REQUESTS_TOTAL,
)
from app.db.session import AsyncSessionLocal


def _route_template(request: Request) -> str:
    # BaseHTTPMiddleware runs outside Starlette's router, so scope["route"] is
    # not reliably populated here. Never use arbitrary URL paths as metric
    # labels because IDs can create unbounded Prometheus cardinality.
    route = request.scope.get("route")
    path = getattr(route, "path", None)
    if path:
        return path

    segments = [segment for segment in request.url.path.split("/") if segment]
    if len(segments) >= 4 and segments[0] == "api" and segments[1].startswith("v"):
        return "/" + "/".join(segments[:3]) + "/:id"
    return request.url.path


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        # Swagger UI and ReDoc are browser-facing documentation pages. FastAPI's
        # default documentation HTML loads its UI bundles from their official CDNs
        # and uses a small inline bootstrap script. Keep the strict application CSP
        # everywhere else, but allow only the documentation resources that are
        # required for /docs and /redoc to render.
        path = request.url.path
        if path == "/docs" or path.startswith("/docs/"):
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "base-uri 'self'; "
                "object-src 'none'; "
                "frame-ancestors 'none'; "
                "script-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; "
                "style-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; "
                "img-src 'self' data: https://fastapi.tiangolo.com; "
                "connect-src 'self'"
            )
        elif path == "/redoc" or path.startswith("/redoc/"):
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "base-uri 'self'; "
                "object-src 'none'; "
                "frame-ancestors 'none'; "
                "script-src 'self' https://cdn.redoc.ly 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com data:; "
                "img-src 'self' data:; "
                "connect-src 'self'"
            )
        else:
            response.headers["Content-Security-Policy"] = (
                "default-src 'none'; frame-ancestors 'none'"
            )
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=()"
        )
        return response


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        started = time.perf_counter()
        route = _route_template(request)
        HTTP_REQUESTS_IN_PROGRESS.labels(request.method, route).inc()
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception:
            status_code = 500
            raise
        finally:
            duration = time.perf_counter() - started
            HTTP_REQUESTS_TOTAL.labels(
                request.method, route, str(status_code)
            ).inc()
            HTTP_REQUEST_DURATION_SECONDS.labels(
                request.method, route
            ).observe(duration)
            HTTP_REQUESTS_IN_PROGRESS.labels(request.method, route).dec()


class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        if request.method in {"POST", "PUT", "PATCH", "DELETE"} and request.url.path != "/":
            try:
                async with AsyncSessionLocal() as db:
                    await write_audit_log(
                        db,
                        action=f"HTTP_{request.method}",
                        method=request.method,
                        path=request.url.path,
                        status_code=response.status_code,
                        user_id=getattr(request.state, "user_id", None),
                        request_id=getattr(request.state, "request_id", None),
                        ip_address=request.client.host if request.client else None,
                    )
            except Exception as exc:
                logger.warning("audit_log_write_failed error={}", exc)
        return response
