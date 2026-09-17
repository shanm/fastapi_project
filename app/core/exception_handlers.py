from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.exceptions import AppException


def _request_id(request: Request) -> str | None:
    return getattr(request.state, 'request_id', None)


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            'detail': 'Request validation failed.',
            'errors': exc.errors(),
            'request_id': _request_id(request),
        },
    )


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    status_code = getattr(exc, 'status_code', 400)
    return JSONResponse(
        status_code=status_code,
        content={'detail': str(exc) or exc.__class__.__name__, 'request_id': _request_id(request)},
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    from app.core.logging import logger

    logger.exception('unhandled_exception request_id={}', _request_id(request))
    return JSONResponse(
        status_code=500,
        content={'detail': 'Internal server error.', 'request_id': _request_id(request)},
    )
