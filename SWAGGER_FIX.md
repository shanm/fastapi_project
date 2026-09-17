# Swagger UI rendering fix

## Root cause

`SecurityHeadersMiddleware` applied `Content-Security-Policy: default-src 'none'` to every response. FastAPI's `/docs` page loads Swagger UI CSS/JavaScript from `cdn.jsdelivr.net` and uses an inline bootstrap script, so the browser blocked the required assets and rendered a blank page.

## Fix

The middleware now:
- keeps the strict CSP for normal application/API responses;
- allows only the required Swagger UI resources on `/docs`;
- provides a compatible CSP for `/redoc`;
- keeps `object-src 'none'`, `base-uri 'self'`, and `frame-ancestors 'none'`.

A regression test was added in `tests/api/test_docs.py`.
